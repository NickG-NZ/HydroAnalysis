"""
HydroFoil model
Origin is at quarter chord, x-axis lies along chord, z-axis is upward normal

* Computes the forces and moments given the speed and angle-of-attack using flat plate airfoil theory
* Assumes laminar flow

@ref: http://www.aerodynamics4students.com/subsonic-aerofoil-and-wing-theory/flat-plate-lift.php
@ref: https://en.wikipedia.org/wiki/Oswald_efficiency_number#:~:text=The%20Oswald%20efficiency%2C%20similar%20to,and%20an%20elliptical%20lift%20distribution.
"""
import numpy as np

from ForceMoment import ForceMoment
from utils import reynolds_number
import constants


class HydroFoil:

    def __init__(self, span, chord, frame, cd0, span_efficiency=0.9):  # Oswald's number?
        self._span = span
        self._chord = chord
        self._frame = frame
        self._span_efficiency = span_efficiency

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

        lift = self._lift(angle_of_attack, speed)
        drag = self._drag(angle_of_attack, speed)

        fx = lift * np.sin(angle_of_attack) - drag * np.cos(angle_of_attack)
        fz = lift * np.cos(angle_of_attack) + drag * np.sin(angle_of_attack)
        my = self._moment(angle_of_attack, speed)

    def _lift(self, angle_of_attack, speed):
        pass

    @staticmethod
    def _lift_coefficient(self, angle_of_attack):
        return 2 * np.pi * angle_of_attack

    def _drag(self, angle_of_attack, speed):
        """
        Need components
            * lift induced drag (for finite span wing) w/ Oswald factor
            * skin friction drag (use Blasius solution)
            * pressure drag (assume zero, flow attached)

        :param angle_of_attack:
        :param speed:
        :return:
        """
        Re = reynolds_number(speed, constants.WATER_KINEMATIC_VISCOSITY, self._chord)
        cd_skin_friction = 1.328 / np.sqrt(Re)

        cd_induced =

        drag +

        pass

    def _moment(self, angle_of_attack, speed):
        """
        Flat plate theory quarter chord moment coefficient
        """
        cm = -np.pi * angle_of_attack / 2
        moment = 0.5 * cm * self._chord * constants.WATER_DENSITY * self._area_ref * (speed ** 2)

        return moment
