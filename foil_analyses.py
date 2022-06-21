"""
Parameter sweeps to investigate the effects of hydrofoils
on ship efficiency
"""
import numpy as np

from HydroAnalysis import HydroAnalysis, MassComponent
from Hull import Hull
from HydroFoil import HydroFoil
from Frame import Frame
from Material import Steel
from VPP import *


def main():

    # hull definition
    hull_mass = 350e3  # [kg]
    length = 35.5  # [m]
    beam = 7.9  # [m]
    height = 3  # [m]
    bow_fraction = 0.25
    hull = Hull(length, beam, height, bow_fraction)

    # main foil definitions
    span = 3.0  # [m]
    chord = 1.2  # [m]
    angle_of_attack = np.deg2rad(5)
    foil_port = HydroFoil(span, chord, Frame(hull.frame, length / 2, height / 4, -angle_of_attack), thickness_ratio=0.2)
    foil_stbd = HydroFoil(span, chord, Frame(hull.frame, length / 2, height / 4, -angle_of_attack), thickness_ratio=0.2)

    # compute foil structural mass
    max_angle_of_attack = np.deg2rad(10)
    max_speed_mps = 12
    foil_mass = foil_port.structural_mass(max_angle_of_attack, max_speed_mps, Steel(), fos=1.3, scaling_factor=1.3)

    # set up analysis
    hydro_analysis = HydroAnalysis(hull)
    hydro_analysis.add_mass_component(MassComponent(hull_mass, *hull.mass_reference_point()))
    hydro_analysis.add_foil(foil_port, MassComponent(foil_mass, -chord / 4, 0))
    hydro_analysis.add_foil(foil_stbd, MassComponent(foil_mass, -chord / 4, 0))

    # solve VPP
    speed = 10

    try:
        equilib_sink = run_vpp(hydro_analysis, speed)
    except VPPSolverError as e:
        print(e)


if __name__ == "__main__":
    main()



