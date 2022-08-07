"""
HydroFoil model
Origin is at quarter chord, x-axis lies along chord, z-axis is upward normal

* Computes the forces and moments given the speed and angle-of-attack using flat plate airfoil theory
* Assumes laminar flow

@ref: http://www.aerodynamics4students.com/subsonic-aerofoil-and-wing-theory/flat-plate-lift.php
@ref: https://www.c23434.net/resources/MKMM1313/Chapter-04/0-C4-01.pdf
@ref: Marine Hydrodynamics 2018 - Newman
"""
import numpy as np
from enum import Enum

from Frame import Frame
from ForceMoment import ForceMoment, MassComponent
from utils import reynolds_number, schoenherr_drag_coeff
import constants


class DragModel(Enum):
    BLASIUS = 0,
    SCHOENHERR = 1,  # Newman, 2018


class HydroFoil:

    class FoilError(Exception):
        pass

    def __init__(self, span, chord, frame, oswald_efficiency=0.7, drag_model=DragModel.SCHOENHERR, thickness_ratio=0.1,
                end_plate_factor=1):
        self._span = span
        self._chord = chord
        self.frame = frame
        self._oswald_efficiency = oswald_efficiency  # default is for rectangular wing
        self._drag_model = drag_model
        self._thickness_ratio = thickness_ratio  # thickness to chord ratio (too high => cavitation at higher speeds)
        self.end_plate_factor = max(2, min(1.0, end_plate_factor))

        # Channels to log
        self._lift_N = 0
        self._drag_N = 0
        self._my_Nm = 0
        self._LD = 0
        self._angle_of_attack_rad = 0
        self._cl = 0
        self._cd_induced = 0
        self._cd_skin_friction = 0
        self._fx_N = 0
        self._fz_N = 0
        self._bending_moment_Nm = 0
        self._area_ref = 0
        self._aspect_ratio = 0
        self._aspect_ratio_effective = 0
        self._thickness_req_m = 0
        self._load_density_Pa = 0

        self._compute_derived_geo()

    def set_location(self, pos_x, pos_z, rot_y):
        """
        Change location relative to existing reference frame
        """
        ref_frame = self.frame.ref_frame()
        self.frame = Frame(ref_frame, pos_x, pos_z, rot_y)

    def get_location(self):
        """
        Get location relative to existing reference frame
        """
        return self.frame.location()

    def resize(self, span, chord, thickness_ratio):
        if span <= 0:
            raise ValueError("Span must be positive")

        if chord <= 0:
            raise ValueError("Chord must be positive")
        self._span = span
        self._chord = chord
        self._thickness_ratio = thickness_ratio
        self._compute_derived_geo()

    def cavitation_check(self):
        """
        Hydrofoils often cavitate when the load density reaches 60 kPa
        This check throws, so any code running a hyrdofoil sim should
        be wrapped in an exception block
        @ref Practical Ship Hydrodynamics - Bertram 2000
        """
        return self._load_density_Pa < 6e4

    def force_moment(self, speed):
        """
        Computes the forces in the foil's own frame
        Includes a submersion factor which accounts for force reduction as the foil approaches the free surface

        :param speed: [m/s] assumed to lie in datum frame x-axis
        :returns ForceMoment(Fx, Fz, My)
        """
        # 100 mm below the surface, full lift is achieved
        submersion_force_scaling = np.clip(-10 * self.frame.origin_in_datum()[1], 0, 1)

        self._angle_of_attack_rad = -self.frame.rotation_in_datum()  # +ve nose down trim creates -ve lift
        aero_frame = Frame(self.frame, 0, 0, self._angle_of_attack_rad - np.pi / 2)  # x=lift, z = drag

        self._compute_lift(speed)
        self._compute_drag(speed)
        self._lift_N *= submersion_force_scaling
        self._drag_N *= submersion_force_scaling

        self._LD = self._lift_N / self._drag_N

        self._fx_N, self._fz_N = aero_frame.vector_to_frame(self._lift_N, self._drag_N, self.frame)
        self._compute_moment(speed)

        # Cavitation loading check
        self._foil_loading_cavitation_check()

        return ForceMoment(self._fx_N, self._fz_N, self._my_Nm)

    def structural_mass(self, max_angle_of_attack, max_speed, material, fos=1.3, scaling_factor=1.8, share_frac=0.2):
        """
        Model the structural mass using a simple cantilever calc with an estimated wing thickness
        proportional to the chord defining the main spar size.
        The spar is modelled as a square hollow section.
        A scaling factor is applied for the ribs and skin mass

        :param max_angle_of_attack: can be estimated using the foil mounting angle and max hull trim
        :param max_speed:
        :param material: instance of Material class
        :param fos: Factor of Safety
        :param scaling_factor: multiplied by main spar mass to account for ribs, secondary spars and skin
        :param share_frac: fraction of bending load carried by secondary members (other than main spar)
                            can also be used to account for wing taper effects
        """
        # temporarily set the trim angle to a maximum
        pos_x, pos_z, rot_y = self.get_location()
        self.set_location(pos_x, pos_z, -max_angle_of_attack)

        # solve for spar thickness
        max_force_moment = self.force_moment(max_speed)
        self._bending_moment_Nm = np.linalg.norm(max_force_moment.force()) * self._span / 2
        spar_height = self._thickness_ratio * self._chord

        Ixx_req = (self._bending_moment_Nm * spar_height * 0.5 * fos * (1 - share_frac)) / material.yield_strength  # sigma = My/I
        self._thickness_req_m = spar_height - ((spar_height ** 4) - (Ixx_req * 12)) ** (1 / 4)

        if np.isnan(self._thickness_req_m):
            raise HydroFoil.FoilError("Maximum Foil Load Exceeds Geometric Strength Limits")

        structural_mass = self._thickness_req_m * spar_height * 4 * self._span * material.density * scaling_factor

        # revert the foil back to its original trim angle
        self.set_location(pos_x, pos_z, rot_y)

        return MassComponent(structural_mass, -self._chord / 4, 0)

    def _compute_lift(self, speed):
        self._cl = self._lift_coefficient(self._angle_of_attack_rad)
        self._lift_N = 0.5 * self._cl * constants.WATER_DENSITY * self._area_ref * (speed ** 2)

    def _lift_coefficient(self, angle_of_attack):
        """
        Accounts for finite wing effects
        """
        dCl0_dalpha = 2 * np.pi
        dCl_dalpha = dCl0_dalpha / (1 + dCl0_dalpha / (np.pi * self._aspect_ratio_effective * self._oswald_efficiency))
        Cl = dCl_dalpha * angle_of_attack

        return Cl

    def _compute_drag(self, speed):
        """
        Need components
            * lift induced drag (for finite span wing) w/ Oswald factor
            * skin friction drag
            * pressure drag (assume zero, flow attached)
        """
        Re = reynolds_number(speed, constants.WATER_KINEMATIC_VISCOSITY, self._chord)
        cd_blasius = 1.328 / np.sqrt(Re)

        if self._drag_model == DragModel.BLASIUS:
            self._cd_skin_friction = cd_blasius

        elif self._drag_model == DragModel.SCHOENHERR:
            self._cd_skin_friction = schoenherr_drag_coeff(Re, initial_guess=cd_blasius)
        else:
            raise ValueError("Invalid drag model argument")

        self._cd_induced = (self._lift_coefficient(self._angle_of_attack_rad) ** 2) /\
                           (np.pi * self._aspect_ratio_effective * self._oswald_efficiency)

        drag_coeff = self._cd_skin_friction + self._cd_induced
        self._drag_N = 0.5 * drag_coeff * constants.WATER_DENSITY * self._area_ref * (speed ** 2)

    def _compute_moment(self, speed):
        """
        Flat plate theory quarter chord moment coefficient
        """
        cm = np.pi * self._angle_of_attack_rad / 2
        self._my_Nm = 0.5 * cm * self._chord * constants.WATER_DENSITY * self._area_ref * (speed ** 2)

    def _compute_derived_geo(self):
        self._area_ref = self._span * self._chord
        self._aspect_ratio = (self._span ** 2) / self._area_ref

        # Account for winglets/endplates and /or sindle sided wing mounted to side of hull (near perfect end-plate)
        self._aspect_ratio_effective = self._aspect_ratio * self.end_plate_factor

    def _foil_loading_cavitation_check(self):
        self._load_density_Pa = self._fz_N / self._area_ref

    def add_log_channels(self, logger, group_name):
        logger.add_group(group_name, self)
        logger.add_channel_to_group('_lift_N', group_name, alias='Lift_N')
        logger.add_channel_to_group('_drag_N', group_name, alias='Drag_N')
        logger.add_channel_to_group('_my_Nm', group_name, alias='My_Nm')
        logger.add_channel_to_group('_LD', group_name, alias='LD')
        logger.add_channel_to_group('_angle_of_attack_rad', group_name, alias='AoA_rad')
        logger.add_channel_to_group('_cl', group_name, alias='CL')
        logger.add_channel_to_group('_cd_induced', group_name, alias='CDi')
        logger.add_channel_to_group('_cd_skin_friction', group_name, alias='CD_SkinFriction')
        logger.add_channel_to_group('_fx_N', group_name, alias='Fx_N')
        logger.add_channel_to_group('_fz_N', group_name, alias='Fz_N')
        logger.add_channel_to_group('_span', group_name, alias='Span_m')
        logger.add_channel_to_group('_chord', group_name, alias='Chord_m')
        logger.add_channel_to_group('_area_ref', group_name, alias='Area_m')
        logger.add_channel_to_group('_aspect_ratio', group_name, alias='AspectRatio')
        logger.add_channel_to_group('_aspect_ratio_effective', group_name, alias='AspectRatioEffective')
        logger.add_channel_to_group('_thickness_ratio', group_name, alias='ThicknessRatio')
        logger.add_channel_to_group('_bending_moment_Nm', group_name, alias='BendingMoment_Nm')
        logger.add_channel_to_group('_load_density_Pa', group_name, alias='LoadDensity_Pa')
