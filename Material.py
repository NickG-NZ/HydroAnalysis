"""
Material Properties
"""
from abc import ABC, abstractmethod


class Material(ABC):

    @property
    @abstractmethod
    def density(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def yield_strength(self):
        raise NotImplementedError


class Steel(Material):

    def __init__(self):
        self._density = 7800  # [kg/m^3]
        self._yield_strength = 400e6  # [Pa]

    @property
    def density(self):
        return self._density

    @property
    def yield_strength(self):
        return self._yield_strength
