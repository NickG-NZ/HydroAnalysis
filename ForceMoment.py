"""
Convenience class for passing around wrenches (force-moment pairs)
"""

class ForceMoment:

    def __init__(self, fx: float, fz: float, my: float):
        self._fx = fx
        self._fz = fz
        self._my = my

    def force(self) -> (float, float):
        return self._fx, self._fz

    def moment(self) -> float:
        return self._my

    def add(self, force_moment: 'ForceMoment'):
        self._fx += force_moment.force()[0]
        self._fz += force_moment.force()[1]
        self._my += force_moment.moment()
