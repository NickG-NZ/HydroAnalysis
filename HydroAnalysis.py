"""
Define a ship configuration consisting of a hull and zero or more hydrofoils
Computes the net forces and moments given the trim, speed and sink of the vessel

The model is currently 1D (sink only)
"""
import numpy as np
from collections import namedtuple

import constants
from ForceMoment import ForceMoment
from Frame import Datum


MassComponent = namedtuple("MassComponent", ["mass", "pos_x", "pos_z"])


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

        # convert the location of the mass from foil co-ords to hull coords
        foil_pos_hull = np.array(self._foil_location_on_hull(foil))
        mass_pos_hull = np.array(self._hull.frame.vector_from_frame(foil_mass.pos_x, foil_mass.pos_z, foil.frame)) + foil_pos_hull
        foil_mass = MassComponent(foil_mass.mass, *mass_pos_hull)
        self._mass_components.append(foil_mass)

    def add_mass_component(self, mass):
        """
        :param mass:
        """
        self._mass_components.append(mass)

    def set_state(self, sink, trim):
        """
        Set the boat state
        Only have to set hull, since foils should reference its frame
        :param sink: z position in Datum frame (+ve up)
        :param trim: y rotation in Datum frame (+ve bow down)
        """
        self._hull.set_state(sink, trim)

    def force_moment_body(self, speed):
        """
        Compute the net forces in the hull body frame acting on the boat
        """
        fm_body = self._gravitational_forces()
        fm_body.add(self._hull.force_moment(speed))

        for foil in self._foils:
            fm_foil = foil.force_moment(speed)
            fm_foil_B = ForceMoment(*self._hull.frame.vector_from_frame(*fm_foil.force(), foil.frame), fm_foil.moment())
            fm_body.add(fm_foil_B)

        return fm_body

    def force_moment_waterplane(self, speed):
        """
        Return the net forces acting on the boat in the waterplane 'Datum' frame
        """
        fm_body = self.force_moment_body(speed)
        forces_waterplane = self._hull.frame.vector_to_frame(*fm_body.force(), Datum())

        return ForceMoment(*forces_waterplane, fm_body.moment())

    def _gravitational_forces(self):
        """
        Compute net gravitational force in hull frame
        """
        net_mass = np.sum([component.mass for component in self._mass_components])
        weight = net_mass * constants.GRAVITY
        fx, fz = self._hull.frame.vector_from_frame(0, -weight, Datum())

        # TODO: compute moment

        return ForceMoment(fx, fz, 0)

    def _foil_location_on_hull(self, foil):
        """
        Expressed in hull co-ords
        """
        pos_relative_H = np.array(foil.frame.origin_in_datum()) - np.array(self._hull.frame.origin_in_datum())
        return self._hull.frame.vector_from_frame(*pos_relative_H, Datum())

    def _foil_trim_on_hull(self, foil):
        """
        """
        return foil.frame.rotation_in_datum() - self._hull.frame.rotation_in_datum()

