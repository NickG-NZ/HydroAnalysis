"""
Coordinate frame for specifying force and moment components

2D only x, z position + y rotation (nose down positive)
"""
import numpy as np


class Frame:

    def __init__(self, ref_frame, pos_x, pos_z, rot_y):
        self._ref_frame = ref_frame
        self._pos_x = pos_x
        self._pos_z = pos_z
        self._rot_y = rot_y

    def origin_in_datum(self):
        pos_x_D, pos_z_D = self._ref_frame.origin_in_waterplane()
        rot_y_D = self.rotation_in_datum()
        pos_x_D += self._pos_x * np.cos(rot_y_D) + self._pos_z * np.sin(rot_y_D)
        pos_z_D += -self._pos_x * np.sin(rot_y_D) + self._pos_z * np.cos(rot_y_D)

        return pos_x_D, pos_z_D

    def rotation_in_datum(self):
        rot_y_D = self._ref_frame.rotation_in_datum()

        return rot_y_D + self._rot_y


class Datum(Frame):

    def __init__(self):
        super().__init__(None, 0, 0, 0)

    def origin_in_datum(self):  # override
        return 0, 0, 0

    def rotation_in_datum(self):  # override
        return 0
