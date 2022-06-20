"""
Define a ship configuration consisting of a hull and zero or more hydrofoils
Computes the net forces and moments given the trim, speed and sink of the vessel

The model is currently 1D (sink only)
"""
from collections import namedtuple

import constants


MassComponent = namedtuple("MassComponent", ["mass", "frame"])


class HydroAnalysis:

    def __init__(self, hull):
        self._hull = hull
        self._foils = []
        self._mass_components = []

    def add_foil(self, foil, foil_mass):
        """
        :param foil: Foil model defining shape and location/angle
        :param foil_mass: MassComponent for the selected foil
        """
        self._foils.append(foil)
        self._mass_components.append(foil_mass)

    def add_mass_component(self, mass, coords):
        """
        :param mass:
        :param coords: 2D coordinates of the mass component (in hull frame)
        """
        self._mass_components.append(mass)

    def force_moments_body(self, speed, trim, sink):
        """
        ret
        """
        pass

    def force_moments_waterplane(self):
        """
        :return:
        """
        pass

    def _gravitational_forces(self):
        pass




