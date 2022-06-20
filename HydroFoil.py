"""
HydroFoil model
Origin is at quarter chord, x-axis lies along chord, z-axis is upward normal

* Computes the forces and moments given the speed and angle-of-attack using flat plate airfoil theory
* Assumes laminar flow

@ref: http://www.aerodynamics4students.com/subsonic-aerofoil-and-wing-theory/flat-plate-lift.php
@ref: https://en.wikipedia.org/wiki/Oswald_efficiency_number#:~:text=The%20Oswald%20efficiency%2C%20similar%20to,and%20an%20elliptical%20lift%20distribution.
@ref: https://www.c23434.net/resources/MKMM1313/Chapter-04/0-C4-01.pdf
@ref: Marine Hydrodynamics 2018 - Newman
"""
import numpy as np
from enum import Enum

from Frame import Frame
from ForceMoment import ForceMoment
from utils import reynolds_number, schoenherr_drag_coeff
import constants


class DragModel(Enum):
    BLASIUS = 0,
    SCHOENHERR = 1,  # Newman, 2018


class HydroFoil:

    def __init__(self, span, chord, frame, oswald_efficiency=0.7, drag_model=DragModel.SCHOENHERR):
        self._span = span
        self._chord = chord
        self._frame = frame
        self._oswald_efficiency = oswald_efficiency  # default is for rectangular wing
        self._drag_model = drag_model

        self._area_ref = self._span * self._chord
        self._aspect_ratio = (self._span ** 2) / self._area_ref  # s/c or s^2/A

    def position_on_hull(self, hull_frame):
        """
        """
        return self._frame.origin_in_datum() - hull_frame.origin_in_datum()

    def trim_on_hull(self, hull_frame):
        """
        """
        return self._frame.rotation_in_datum() - hull_frame.rotation_in_datum()

    def force_moment(self, speed):
        """
        Computes the forces in the foil's own frame
        :param speed: [m/s] assumed to lie in datum frame x-axis
        :returns ForceMoment(Fx, Fz, My)
        """
        angle_of_attack = -self._frame.rotation_in_datum()  # +ve nose down trim creates -ve lift
        aero_frame = Frame(self._frame, 0, 0, angle_of_attack + np.pi)  # x=lift, z = drag

        lift = self._lift(angle_of_attack, speed)
        drag = self._drag(angle_of_attack, speed)

        fx, fz = aero_frame.vector_in_frame(lift, drag, self._frame)
        # fx = lift * np.sin(angle_of_attack) - drag * np.cos(angle_of_attack)
        # fz = lift * np.cos(angle_of_attack) + drag * np.sin(angle_of_attack)
        my = self._moment(angle_of_attack, speed)

        return ForceMoment(fx, fz, my)

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
        Re = reynolds_number(speed, constants.WATER_KINEMATIC_VISCOSITY, self._chord)

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
        cm = -np.pi * angle_of_attack / 2
        moment = 0.5 * cm * self._chord * constants.WATER_DENSITY * self._area_ref * (speed ** 2)

        return moment
