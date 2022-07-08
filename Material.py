"""
Material Properties
"""
from dataclasses import dataclass


@dataclass
class Material:
    density: float
    yield_strength: float


# Material Definitions
Steel = Material(7800, 400e6)
SteelAISI1340 = Material(7870, 565e6)  # https://www.matweb.com/search/datasheet.aspx?MatGUID=6e1830ea7a334716bc6209316464b487
