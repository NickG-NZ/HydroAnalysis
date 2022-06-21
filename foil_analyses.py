"""
Parameter sweeps to investigate the effects of hydrofoils
on ship efficiency
"""
import numpy as np
import matplotlib.pyplot as plt

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

    # Run sweep with no foils
    speed = 25  # [kts]
    draft_sweep(hydro_analysis, speed, title="Hull Only - Draft Sweep")

    # Run VPP to compute equilib
    equilib_draft = -vpp_equilib(hydro_analysis, speed, [-1.2])
    print(f"Equilibrium Draft (no foils): {equilib_draft:.3f} m")

    # Add foils and re-run sweep
    hydro_analysis.add_foil(foil_port, MassComponent(foil_mass, -chord / 4, 0))
    hydro_analysis.add_foil(foil_stbd, MassComponent(foil_mass, -chord / 4, 0))
    draft_sweep(hydro_analysis, speed, title="Hull + Foils - Draft Sweep")

    # Run VPP
    equilib_draft = -vpp_equilib(hydro_analysis, speed, [-1.2])
    print(f"Equilibrium Draft (w/ foils): {equilib_draft:.3f} m")


def draft_sweep(hydro_analysis, speed, title="Draft Sweep"):
    """
    Sweep the boat through a range of draft states (hull immersions)
    and plot. There should be a clear equilibrium point
    """
    drafts = np.arange(0.1, 3, 0.1)
    Fzs = []
    for draft in drafts:
        hydro_analysis.set_state(-draft, 0)
        net_force = hydro_analysis.force_moment_waterplane(speed).force()

        Fzs.append(net_force[1])

    fig, ax = plt.subplots()
    ax.plot(drafts, np.array(Fzs) / 1000)
    ax.set(xlabel="Draft [m]", ylabel="Fz [kN]", title=title)
    ax.grid()
    plt.show()


def vpp_equilib(hydro_analysis, speed, initial_sink):
    """
    Use the VPP solver to find the equilibirum sink point for the hull
    """
    try:
        equilib_sink = run_vpp(hydro_analysis, speed, [initial_sink])
    except VPPSolverError as e:
        print(e)
        equilib_sink = np.nan

    return equilib_sink


if __name__ == "__main__":
    main()



