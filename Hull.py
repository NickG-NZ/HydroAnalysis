"""
Ship hull definition
Currently just a box with a triangular prism in front as the bow and a triangular prism on the bottom as the v
The bottom 'v' prism runs from the tip of the bow to the transom. However, the volume and area of the section overlapping
the bow are halved to better approximate a real geometry.
The end (triangular) areas of the prisms are not included in area calculations

Origin is transom at bottom of hull

* Computes the hydrostatic and drag forces at a given sink (1D only for now)
  In future should account for ship trim angle
"""
from Frame import Frame, Datum
from ForceMoment import ForceMoment
from utils import *


class Hull:

    def __init__(self, length, beam, height, bow_fraction, chine_fraction):
        self.length = length  # nominally parallel to waterline
        self.beam = beam
        self.height = height
        self.bow_fraction = bow_fraction  # fraction of total length which is the tapered bow
        # self.stern_fraction = stern_fraction  # fraction of total length which is tapered stern
        self.chine_fraction = chine_fraction  # fraction of total height below chine (hull v depth)
        self.frame = Frame(Datum(), 0, -height / 3, 0)  # initialize with some submersion

        if self.chine_fraction > 1 or self.chine_fraction < 0:
            raise ValueError("chine fraction must be in range [0, 1]")

        if self.bow_fraction > 1 or self.bow_fraction < 0:
            raise ValueError("bow fraction must be in range [0, 1]")

        # if self.stern_fraction > 1 or self.stern_fraction < 0:
        #     raise ValueError("stern fraction must be in range [0, 1]")
        #
        # if self.stern_fraction + self.bow_fraction >= 1:
        #     raise ValueError("stern fraction + bow fraction must be less than 1")

        self._bow_length = self.bow_fraction * self.length
        # self._stern_length = self.stern_fraction * self.length
        self._v_depth = self.chine_fraction * self.height

        # Channels to log
        self._fx_N = 0
        self._fz_N = 0
        self._cd_skin_friction = 0
        self._friction_drag_N = 0
        self._wave_drag_N = 0
        self._drag_N = 0
        self._buoyancy_N = 0
        self._wetted_area = 0
        self._displaced_volume = 0
        self._draft = 0
        self._Cp = 0
        self._Cwp = 0
        self._Cm = 0

    @classmethod
    def from_iges(cls, filepath, frame):
        raise NotImplementedError("Not implemented")

    def set_state(self, sink, trim):
        """
        Specify state relative to Datum frame
        :param sink: z position in Datum frame (+ve up)
        :param trim: y rotation in Datum frame (+ve bow down)
        """
        self.frame = Frame(Datum(), 0, sink, trim)
        self._draft = max(0, -1 * self.frame.origin_in_datum()[1])

    def mass_reference_point(self):
        """
        Estimate COM as centre of length at 1/3 height
        """
        return self.length / 2, self.height / 3

    def draft(self):
        return self._draft

    def force_moment(self, speed):
        """
        Computes the forces and moments acting on the hull (in hull coords)
        Ignores any trim angle (Assumes buoyancy is aligned with hull z-axis and drag aligned with x-axis
        """
        self._update_geometric_parameters()
        self._compute_drag(speed)
        self._compute_buoyancy()
        return ForceMoment(-self._drag_N, self._buoyancy_N, 0)

    def _update_geometric_parameters(self):
        """
        Compute all the parameters and coefficients derived from the immersed hull geometry
        """
        # Submerged geometry
        self._compute_wetted_surface_area()
        self._compute_displaced_volume()

        # Hull Geometry Coefficients
        # prismatic_coeff: Cp = V / (AmxL)
        # where V is displaced volume, Am is midship cross section and L is length (on waterline)
        self._Cp = self._displaced_volume / (self._submerged_cross_section() * self.length)

        # midship_section_coeff: Cm = Am / (B * d)
        self._Cm = self._submerged_cross_section() / (self.beam * self.draft())

        # waterplane_area_coefficient Cwp = Awp / (L * B)
        self._Cwp = self._waterplane_area() / (self.beam * self.length)

    def _compute_drag(self, speed):
        """
        Combined wave drag and skin friction
        """
        # Skin Friction
        self._cd_skin_friction = self._skin_friction_coeff(speed)
        self._friction_drag_N = 0.5 * self._cd_skin_friction * constants.WATER_DENSITY * self._wetted_area * (speed ** 2)

        # Wave Resistance
        self._compute_wave_resistance(speed)

        self._drag_N = self._friction_drag_N + self._wave_drag_N

    def _skin_friction_coeff(self, speed):
        """
        Use the Schoenherr semi-empirical formula (Marine Hydrodynamics - Newton)
        Have to solve iteratively
        Can also approximate this in closed form with ITTC - 1957 formula:
        Cf = 0.075 / (np.log10(Re) - 2) ** 2
        and a correction factor (1 + k1) dependant on the Prismatic coefficient, LCB and other hull parameters
        """
        Re = reynolds_number(speed, constants.WATER_KINEMATIC_VISCOSITY, self.length)
        cd_skin_friction = schoenherr_drag_coeff(Re, initial_guess=0.002)

        return cd_skin_friction

    def _compute_wave_resistance(self, speed):
        """
        Wave resistance empirical formulation from 'Holtrop-Mennen' paper:
        https://thenavalarch.com/how-to-use-empirical-formulas-to-estimate-the-resistance-of-a-ship/
        Note capital 'T' is moulded draft (eg. design draft). Measured draft is used here
        """
        Fn = froude_number(speed, self.length)
        aspect_ratio = self.beam / self.length
        draft = self.draft()
        lcb = 0  # pos of LCB forward of 0.5*L as percentage of L

        # c7
        if aspect_ratio < 0.11:
            c7 = 0.229577 * (aspect_ratio ** (1 / 3))
        elif aspect_ratio < 0.25:
            c7 = aspect_ratio
        else:
            c7 = 0.5 - 0.0625 / aspect_ratio

        L_R = self.length * (1 - self._Cp + 0.06 * self._Cp * lcb / (4 * self._Cp - 1))
        iE = 1 + 89 * np.exp(-((1 / aspect_ratio) ** 0.80856) * ((1 - self._Cwp) ** 0.30484) * ((1 - self._Cp - 0.0225 * lcb) ** 0.6367) *\
                             ((L_R / self.beam) ** 0.34574) * ((100 * self._displaced_volume / (self.length ** 3)) ** 0.16302))

        c1 = 2223105 * (c7 ** 3.78613) * ((draft / self.beam) ** 1.07961) * ((90 - iE) ** -1.37565)
        c2 = 1  # drag reduction due to bulbous bow, ignore for now

        # c5
        immersed_transom_area = self._submerged_cross_section() * 0.5  # 0.5 accounts for realistic hull shape
        c5 = 1 - 0.8 * immersed_transom_area / (self.beam * draft * self._Cm)

        # lambda
        if (1 / aspect_ratio) < 12:
            lambd = 1.446 * self._Cp - 0.03 / aspect_ratio
        else:
            lambd = 1.446 * self._Cp - 0.36

        # c16
        if self._Cp < 0.8:
            c16 = 8.07981 * self._Cp - 13.8673 * (self._Cp ** 2) + 6.984388 * (self._Cp ** 3)
        else:
            c16 = 1.73014 - 0.7067 * self._Cp

        m1 = 0.0140407 * self.length / draft - 1.75254 * (self._displaced_volume ** (1 / 3) / self.length) -\
            4.79323 * aspect_ratio - c16

        # c15
        if (self.length ** 3) / self._displaced_volume < 512:
            c15 = -1.69385
        elif (self.length ** 3) / self._displaced_volume < 1727:
            c15 = -1.69385 + ((self.length / self._displaced_volume ** (1 / 3)) - 8) / 2.36
        else:
            c15 = 0

        m2 = c15 * self._Cp ** 2 * np.exp(-0.1 * Fn ** (-2))

        wave_resistance = c1 * c2 * c5 * self._displaced_volume * constants.WATER_DENSITY * constants.GRAVITY *\
                                    np.exp(m1 * (Fn ** -0.9) + m2 * np.cos(lambd * (Fn ** -2)))

        # Transom Immersion Resistance
        FnT = speed / np.sqrt(2 * constants.GRAVITY * immersed_transom_area / (self.beam * (1 + self._Cwp)))
        c6 = max(0, 0.2 * (1 - 0.2 * FnT))  # = 0 at FnT = 5
        transom_resistance = 0.5 * constants.WATER_DENSITY * (speed * 2) * immersed_transom_area * c6

        self._wave_drag_N = wave_resistance + transom_resistance

    def _compute_buoyancy(self):
        """
        Compute the buoyancy force using the curent hull state
        Note that a z position of 0m, indicates the bottom of the hull is just touching the surface of the water
        """
        self._buoyancy_N = self._displaced_volume * constants.WATER_DENSITY * constants.GRAVITY

    def _compute_wetted_surface_area(self):
        """
        Estimate the wetted surface area using the hull state
        """
        draft = self.draft()
        wp_beam = self._waterplane_beam()

        if abs(draft) < 1e-6:
            wetted_area = 0
        else:
            # v area (area at bow is halved)
            v_angled_length = np.sqrt(min(self._v_depth, draft) ** 2 + (wp_beam / 2) ** 2)  # [m]
            wetted_area = 2 * v_angled_length * self.length * (1 - 0.5 * self.bow_fraction)

            if draft > self._v_depth:
                # side area
                perimeter_bow = 2 * np.sqrt((self.length * self.bow_fraction) ** 2 + (0.5 * self.beam) ** 2)
                perimeter = perimeter_bow + 2 * self.length * (1 - self.bow_fraction) + self.beam
                wetted_area += perimeter * (draft - self._v_depth)

        self._wetted_area = wetted_area

    def _compute_displaced_volume(self):
        """
        """
        self._displaced_volume = self._submerged_cross_section() * self.length * (1 - 0.5 * self.bow_fraction)

    def _waterplane_beam(self):
        """
        If the v-shaped bottom of the hull is not fully immersed, the beam will be narrower
        at the water-plane than the full ship beam
        """
        draft = self.draft()
        if draft >= self._v_depth:
            wp_beam = self.beam
        else:
            wp_beam = self.beam * draft / self._v_depth

        return wp_beam

    def _submerged_cross_section(self):
        """
        Area of transverse cross section underwater (treated as constant along length of boat for now)
        """
        draft = self.draft()
        wp_beam = self._waterplane_beam()

        # triangular component
        cross_section = 0.5 * wp_beam * min(draft, self._v_depth)  # v
        if draft > self._v_depth:
            # rectangular component
            cross_section += (draft - self._v_depth) * self.beam

        return cross_section

    def _waterplane_area(self):
        """
        Compute the plan-view cross-sectional area at the waterplane
        """
        wp_area = self._waterplane_beam() * self.length * (1 - 0.5 * self.bow_fraction)

        return wp_area

    def add_log_channels(self, logger, group_name):
        logger.add_group(group_name, self)
        logger.add_channel_to_group('_fx_N', group_name, alias='Fx_N')
        logger.add_channel_to_group('_fz_N', group_name, alias='Fz_N')
        logger.add_channel_to_group('_cd_skin_friction', group_name, alias='Cd_SkinFriction')
        logger.add_channel_to_group('_friction_drag_N', group_name, alias='FrictionDrag_N')
        logger.add_channel_to_group('_wave_drag_N', group_name, alias='WaveDrag_N')
        logger.add_channel_to_group('_drag_N', group_name, alias='Drag_N')
        logger.add_channel_to_group('_buoyancy_N', group_name, alias='Buoyancy_N')
        logger.add_channel_to_group('_wetted_area', group_name, alias='WettedArea_m2')
        logger.add_channel_to_group('_displaced_volume', group_name, alias='DisplacedVolume_m3')
        logger.add_channel_to_group('_draft', group_name, alias='Draft_m')
        logger.add_channel_to_group('_Cp', group_name, alias='Cp')
        logger.add_channel_to_group('_Cwp', group_name, alias='Cwp')
        logger.add_channel_to_group('_Cm', group_name, alias='Cm')
