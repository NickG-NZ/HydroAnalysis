"""
Ship hull definition (just a box with a triangular prism in front for now)
Origin is transom at bottom of hull

* Computes the hydrostatic and drag forces at a given sink (1D only for now)
  In future should account for ship trim angle
"""
import numpy as np

from Frame import Frame, Datum
from ForceMoment import ForceMoment
from utils import *


class Hull:

    def __init__(self, length, beam, height, bow_fraction):
        self.length = length  # nominally parallel to waterline
        self.beam = beam
        self.height = height
        self.bow_fraction = bow_fraction  # fraction of total length which is the tapered bow
        self._frame = Frame(Datum, 0, 0, 0)  # initialize at origin

    @classmethod
    def from_iges(cls, filepath, frame):
        raise NotImplementedError("Not implemented")

    def set_state(self, frame):
        self._frame = frame

    def mass_reference_point(self):
        """
        Estimate COM as centre of length at 1/3 height
        """
        return self.length / 2, self.height / 3

    def draft(self):
        return -1 * self._frame.origin_in_datum()[1]

    def force_moment(self, speed):
        """
        Computes the forces and moments acting on the hull
        Ignores any trim angle (Assumes buoyancy is aligned with hull z-axis and drag aligned with x-axis
        """
        drag = self._drag(speed)
        buoyancy = self._buoyancy()
        return ForceMoment(-drag, buoyancy, 0)

    def _drag(self, speed):
        """
        Combined wave drag and skin friction
        Note, even the simplest analytical wave drag computations are extremely complex
        Hence a scaling factor is applied to the skin friction based on Figure 2.11, Marine Hydrodynamics
        """
        cd = self._skin_friction_coeff(speed)

        # compute scaling factor based on speed (Froude number)
        # At speeds below 5kts (2.5m/s), the drag is almost all skin friction. At 15 kts (7.5m/s) at the reynolds number
        # of interest ~10^8.4, the drag has increased above the skin friction estimate by a factor of 2.5
        cd_wave_scaling = min(3.0, (speed - 2.5) * 2.5 / (7.5 - 2.5))

        wetted_area = self._wetted_surface_area()
        drag = 0.5 * cd * cd_wave_scaling * constants.WATER_DENSITY * wetted_area * (speed ** 2)

        return drag

    def _skin_friction_coeff(self, speed):
        """
        Use the Schoenherr semi-empirical formula (Marine Hydrodynamics - Newton)
        Have to solve iteratively
        Can also approximate this in closed form with:
        Cf = 0.075 / (np.log10(Re) - 2) ** 2
        """
        Re = reynolds_number(speed, constants.WATER_KINEMATIC_VISCOSITY, self.length)
        cd_skin_friction = schoenherr_drag_coeff(Re, initial_guess=0.002)

        return cd_skin_friction

    def _wetted_surface_area(self):
        """
        Estimate the wetted surface area using the hull state
        """
        bottom_area = self.beam * self.length * (1 - 0.5 * self.bow_fraction)
        perimeter_bow = 2 * np.sqrt((self.length * self.bow_fraction) ** 2 + (0.5 * self.beam) ** 2)
        perimeter = perimeter_bow + 2 * self.length * (1 - self.bow_fraction) + self.beam
        wetted_area = bottom_area + perimeter * self.draft()

        return wetted_area

    def _buoyancy(self):
        """
        Compute the buoyancy force using the curent hull state
        Note that a z position of 0m, indicates the bottom of the hull is just touching the surface of the water
        """
        bottom_area = self.beam * self.length * (1 - 0.5 * self.bow_fraction)
        displaced_volume = bottom_area * self.draft()
        force = displaced_volume * constants.WATER_DENSITY * constants.GRAVITY

        return force

