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

from Frame import Frame, Datum
from ForceMoment import ForceMoment
from utils import reynolds_number, schoenherr_drag_coeff
import constants


class DragModel(Enum):
    BLASIUS = 0,
    SCHOENHERR = 1,  # Newman, 2018


class HydroFoil:

    class FoilError(Exception):
        pass

    def __init__(self, span, chord, frame, oswald_efficiency=0.7, drag_model=DragModel.SCHOENHERR, thickness_ratio=0.1):
        self.span = span
        self.chord = chord
        self.frame = frame
        self._oswald_efficiency = oswald_efficiency  # default is for rectangular wing
        self._drag_model = drag_model
        self._thickness_ratio = thickness_ratio  # thickness to chord ratio (too high => cavitation at higher speeds)

        self._area_ref = self.span * self.chord
        self._aspect_ratio = (self.span ** 2) / self._area_ref  # s/c or s^2/A

    def set_location(self, pos_x, pos_z, rot_y):
        """
        Change location relative to existing reference frame
        """
        ref_frame = self.frame.ref_frame()
        self.frame = Frame(ref_frame, pos_x, pos_z, rot_y)

    def force_moment(self, speed):
        """
        Computes the forces in the foil's own frame
        Includes a submersion factor which accounts for lift reduction as the foil approaches the free surface

        :param speed: [m/s] assumed to lie in datum frame x-axis
        :returns ForceMoment(Fx, Fz, My)
        """
        # 100 mm below the surface, full lift is achieved
        submersion_lift_scaling = np.clip(-10 * self.frame.origin_in_datum()[1], 0, 1)

        angle_of_attack = -self.frame.rotation_in_datum()  # +ve nose down trim creates -ve lift
        aero_frame = Frame(self.frame, 0, 0, angle_of_attack - np.pi / 2)  # x=lift, z = drag

        lift = self._lift(angle_of_attack, speed) * submersion_lift_scaling
        drag = self._drag(angle_of_attack, speed)

        fx, fz = aero_frame.vector_to_frame(lift, drag, self.frame)
        my = self._moment(angle_of_attack, speed)

        return ForceMoment(fx, fz, my)

    def structural_mass(self, max_angle_of_attack, max_speed, material, fos=1.3, scaling_factor=1.3):
        """
        Model the structural mass using a simple cantilever calc with an estimated wing thickness
        proportional to the chord defining the main spar size.
        The spar is modelled as a square hollow section.
        A scaling factor is applied for the ribs and skin mass

        :param fos: Factor of Safety
        """
        # temporarily set the trim angle to a maximum
        pos_x, pos_z, rot_y = self.frame.location()
        self.set_location(pos_x, pos_z, -max_angle_of_attack)

        # solve for spar thickness
        max_force_moment = self.force_moment(max_speed)
        bending_moment = np.linalg.norm(max_force_moment.force()) * self.span / 2
        spar_height = self._thickness_ratio * self.chord

        Ixx_req = (bending_moment * spar_height * 0.5 * fos) / material.yield_strength  # sigma = My/I
        thickness_req = spar_height - ((spar_height ** 4) - (Ixx_req * 12)) ** (1 / 4)

        if np.isnan(thickness_req) :
            raise HydroFoil.FoilError("Maximum Foil Load Exceeds Geometric Strength Limits")

        structural_mass = thickness_req * spar_height * 4 * self.span * material.density * scaling_factor

        # revert the foil back to its original trim angle
        self.set_location(pos_x, pos_z, rot_y)

        return structural_mass

    def _lift(self, angle_of_attack, speed):
        cl = self._lift_coefficient(angle_of_attack)
        lift_force = 0.5 * cl * constants.WATER_DENSITY * self._area_ref * (speed ** 2)

        return lift_force

    @staticmethod
    def _lift_coefficient(angle_of_attack):
        return 2 * np.pi * angle_of_attack

    def _drag(self, angle_of_attack, speed):
        """
        Need components
            * lift induced drag (for finite span wing) w/ Oswald factor
            * skin friction drag
            * pressure drag (assume zero, flow attached)
        """
        Re = reynolds_number(speed, constants.WATER_KINEMATIC_VISCOSITY, self.chord)

        if self._drag_model == DragModel.BLASIUS:
            cd_skin_friction = 1.328 / np.sqrt(Re)

        elif self._drag_model == DragModel.SCHOENHERR:
            cd_skin_friction = schoenherr_drag_coeff(Re, initial_guess=0.0025)
        else:
            raise ValueError("Invalid drag model argument")

        cd_induced = (self._lift_coefficient(angle_of_attack) ** 2) / (np.pi * self._aspect_ratio * self._oswald_efficiency)

        drag_coeff = cd_skin_friction + cd_induced
        drag_force = 0.5 * drag_coeff * constants.WATER_DENSITY * self._area_ref * (speed ** 2)

        return drag_force

    def _moment(self, angle_of_attack, speed):
        """
        Flat plate theory quarter chord moment coefficient
        """
        cm = np.pi * angle_of_attack / 2
        moment = 0.5 * cm * self.chord * constants.WATER_DENSITY * self._area_ref * (speed ** 2)

        return moment

