"""
Example of setting up a hull with some hydrofoils and computing the equilibirium state
using the VPP
"""
import sys, os
import numpy as np
import matplotlib.pyplot as plt

sys.path.append(os.path.join(os.path.abspath(__file__), os.pardir))

from HydroAnalysis import HydroAnalysis, MassComponent
from Hull import Hull
from HydroFoil import HydroFoil
from Frame import Frame
from Material import Steel
from VPP import *
from utils import propulsive_power


def main():

    # hull definition
    hull_mass = 350e3  # [kg]
    length = 35.5  # [m]
    beam = 7.9  # [m]
    height = 3  # [m]
    bow_fraction = 0.2
    chine_fraction = 0.1  # near flat bottom
    hull = Hull(length, beam, height, bow_fraction, chine_fraction)

    # main foil definitions
    span = 4.0  # [m]
    chord = 1.5  # [m]
    angle_of_attack = np.deg2rad(5)
    foil_port = HydroFoil(span, chord, Frame(hull.frame, length / 2, height / 4, -angle_of_attack), thickness_ratio=0.2)
    foil_stbd = HydroFoil(span, chord, Frame(hull.frame, length / 2, height / 4, -angle_of_attack), thickness_ratio=0.2)

    # compute foil structural mass
    max_angle_of_attack = np.deg2rad(8)
    max_speed_mps = 12
    foil_mass = foil_port.structural_mass(max_angle_of_attack, max_speed_mps, Steel, fos=1.3, scaling_factor=1.6)

    # set up analysis
    hydro_analysis = HydroAnalysis(hull)
    hydro_analysis.add_mass_component(MassComponent(hull_mass, *hull.mass_reference_point()))

    # Run sweep with no foils
    speed = 15  # [m/s]
    # hull_draft_sweep(hydro_analysis, speed, title="Hull Only - Draft Sweep")

    # Run VPP to compute equilib
    equilib_draft = -vpp_equilib(hydro_analysis, speed, [-1.2])
    equilib_forces = hydro_analysis.force_moment_waterplane(speed).force()
    power_req = propulsive_power(speed, -equilib_forces[0])
    print(f"Equilibrium Draft [m] (no foils): {equilib_draft:.3f} m")
    print(f"Equilibrium Power [kW]: {power_req / 1000:.2f}")

    # Add foils and re-run sweep
    hydro_analysis.add_foil(foil_port, MassComponent(foil_mass, -chord / 4, 0))
    hydro_analysis.add_foil(foil_stbd, MassComponent(foil_mass, -chord / 4, 0))
    # hull_draft_sweep(hydro_analysis, speed, title="Hull + Foils - Draft Sweep")

    # Run VPP
    equilib_draft = -vpp_equilib(hydro_analysis, speed, [-1.2])
    equilib_forces = hydro_analysis.force_moment_waterplane(speed).force()
    power_req = propulsive_power(speed, -equilib_forces[0])
    print(f"Equilibrium Draft [m] (with foils): {equilib_draft:.3f} m")
    print(f"Equilibrium Power [kW]: {power_req / 1000:.2f}")


def hull_draft_sweep(hydro_analysis, speed, title="Draft Sweep"):
    """
    Sweep the boat through a range of draft states (hull immersions)
    and plot. There should be a clear equilibrium point
    """
    drafts = np.arange(0.1, 3, 0.1)
    Fzs = []
    Fxs = []
    for draft in drafts:
        hydro_analysis.set_state(-draft, 0)
        net_force = hydro_analysis.force_moment_waterplane(speed).force()

        Fxs.append(net_force[0])
        Fzs.append(net_force[1])

    fig, ax = plt.subplots(2, 1)
    fig.suptitle(title)
    ax[0].plot(drafts, np.array(Fxs) / 1000)
    ax[0].set(ylabel="Fx [kN]")
    ax[0].grid()
    ax[1].plot(drafts, np.array(Fzs) / 1000)
    ax[1].set(xlabel="Draft [m]", ylabel="Fz [kN]")
    ax[1].grid()
    plt.show()


def vpp_equilib(hydro_analysis, speed, initial_sink):
    """
    Use the VPP solver to find the equilibirum sink point for the hull.
    The drag (and hence power) can then be obtained at this point
    """
    try:
        equilib_sink = run_vpp(hydro_analysis, speed, [initial_sink])
    except VPPSolverError as e:
        print(e)
        equilib_sink = np.nan
    except HydroFoil.FoilError as e:
        print(e)
        equilib_sink = np.nan

    return equilib_sink


if __name__ == "__main__":
    main()

