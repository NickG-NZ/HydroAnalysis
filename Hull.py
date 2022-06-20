"""
Ship hull definition (just a box with a triangular prism in front for now)
Origin is transom at bottom of hull

* Computes the hydrostatic forces (buoyancy) at a given sink (1D only for now)
TODO: In the future this should load an IGES CAD model surface mesh
"""
from Frame import Frame, Datum
from ForceMoment import ForceMoment


class Hull:

    def __init__(self, length, beam, height, bow_fraction):
        self.length = length  # nominally parallel to waterline
        self.beam = beam
        self.height = height
        self.bow_fraction = bow_fraction  # fraction of total length which is the tapered bow
        self._frame = Frame(Datum, 0, 0, 0)  # initialize at origin

    @classmethod
    def from_iges(cls, filepath):
        raise NotImplementedError("Not implemented")

    def set_state(self, frame):
        self._frame = frame

    def mass_reference_point(self):
        """
        Estimate COM as centre of length at 1/3 height
        """
        return self.length / 2, self.height / 3

    def force_moment(self):
        """
        Computes the forces and moments in the Hull's own frame
        """
        pass

    def _wave_drag(self, speed):
        pass

    def _skin_friction_drag(self):
        pass

    def _pressure_drag(self):
        pass

    def _buoyancy(self):
        pass

