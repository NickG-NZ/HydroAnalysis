"""
Coordinate frame

2D only
x, z position + y rotation (nose down positive) relative to a reference frame
"""
import numpy as np


class Frame:

    def __init__(self, ref_frame, pos_x, pos_z, rot_y):
        self._ref_frame = ref_frame
        self._pos_x = pos_x  # [m]
        self._pos_z = pos_z  # [m]
        self._rot_y = rot_y  # [rad]

    def ref_frame(self):
        return self._ref_frame

    def location(self):
        return self._pos_x, self._pos_z, self._rot_y

    def origin_in_datum(self):
        pos_x_D, pos_z_D = self._ref_frame.origin_in_datum()
        rot_y_D = self.rotation_in_datum()
        pos_x_D += self._pos_x * np.cos(rot_y_D) + self._pos_z * np.sin(rot_y_D)
        pos_z_D += -self._pos_x * np.sin(rot_y_D) + self._pos_z * np.cos(rot_y_D)

        return pos_x_D, pos_z_D

    def rotation_in_datum(self):
        rot_y_D = self._ref_frame.rotation_in_datum()

        return rot_y_D + self._rot_y

    def vector_in_frame(self, x, z, frame):
        """
        Takes a vector with components (x, z) expressed in this frame's coords and transforms it into the target
        frame's coords
        """
        rot_y_rel = self.rotation_in_datum() - frame.rotation_in_datum()
        x_f = x * np.cos(rot_y_rel) + z * np.sin(rot_y_rel)
        z_f = -x * np.sin(rot_y_rel) + z * np.cos(rot_y_rel)

        return x_f, z_f

    def vector_from_frame(self, x, z, frame):
        """
        Takes a vector with components (x, z) expressed in another frame's coords and transforms it into this frame's
        coords
        """
        rot_y_rel = self.rotation_in_datum() - frame.rotation_in_datum()
        x_f = x * np.cos(rot_y_rel) - z * np.sin(rot_y_rel)
        z_f = x * np.sin(rot_y_rel) + z * np.cos(rot_y_rel)

        return x_f, z_f


class Datum(Frame):

    def __init__(self):
        super().__init__(None, 0, 0, 0)

    def origin_in_datum(self):  # override
        return 0, 0, 0

    def rotation_in_datum(self):  # override
        return 0
