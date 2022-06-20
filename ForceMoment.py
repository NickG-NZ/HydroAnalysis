"""
Convenience class for passing around wrenches (force-moment pairs)
"""

class ForceMoment:

    def __init__(self, fx, fz, my):
        self._fx = fx
        self._fz = fz
        self._my = my

    def force(self):
        return self._fx, self._fz

    def moment(self):
        return self._my
