"""
Small 4, 18, 40 TEU vessel sweeps over speed

No Foils drag vs Speed
    +
Fully foiling drag and take-off power vs. Speed
"""
import sys, os
import matplotlib.pyplot as plt

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir))

from HydroAnalysis import HydroAnalysis
from Logger import Logger, LogObject
from PlotWindow import PlotWindow, PlotWindowApplication
from Hull import Hull
from HydroFoil import HydroFoil
from Frame import Frame
from ForceMoment import MassComponent
from Material import SteelAISI1340
from VPP import *
from utils import *
from ForceMoment import ForceMoment


# Turning on either of these checks invalidates all the foil assist results
STRUCTURAL_CHECKS = True
CAVITATION_CHECKS = True

TEU_LENGTH = ft_to_m(20)
TEU_WIDTH = ft_to_m(8)
TEU_MASS = 18e3  # [kg]

TEU1000_POWER_24KTS = 15  # [kW/TEU]
TEU5000_POWER_24KTS = 5  # [kW/TEU]


def main():
    speeds_kts = np.arange(20, 50, 1)
    speeds = [kts_to_mps(s_kts) for s_kts in speeds_kts]

    pw_app = PlotWindowApplication()
    pw = PlotWindow("Feeder Comparisons")
    logsA = run_a(speeds, pw)
    logsB = run_b(speeds, pw)
    logsC = run_c(speeds, pw)

    # Compare the 150 and 300 TEU vessels (in all 3 configurations)
    ylim_sets = [[0, 40e3], [0, 160]]
    for i, k in enumerate(logsA.keys()):
        fig, ax = plt.subplots()

        # The results arrays may be different sizes since the solver rejects invalid structural foils and cavitation
        res_speeds_A = logsA[k].get_channel_log("OperatingProfile", "Speed_kts")
        power_per_TEU_A = logsA[k].get_channel_log("OperatingProfile", "PowerPerTEU_kW")

        res_speeds_B = logsB[k].get_channel_log("OperatingProfile", "Speed_kts")
        power_per_TEU_B = logsB[k].get_channel_log("OperatingProfile", "PowerPerTEU_kW")

        res_speeds_C = logsC[k].get_channel_log("OperatingProfile", "Speed_kts")
        power_per_TEU_C = logsC[k].get_channel_log("OperatingProfile", "PowerPerTEU_kW")

        ax.scatter(res_speeds_A, power_per_TEU_A, label=f"4 TEU-{k}")
        ax.scatter(res_speeds_B, power_per_TEU_B, label=f"20 TEU-{k}")
        ax.scatter(res_speeds_C, power_per_TEU_C, label=f"40 TEU-{k}")
        ax.scatter([24], [TEU1000_POWER_24KTS], label="1000 TEU-displacement")
        ax.scatter([24], [TEU5000_POWER_24KTS], label="5000 TEU-displacement")
        ax.set(xlabel="Speed [kts]", ylabel="Power per TEU [kW]", ylim=ylim_sets[i])
        ax.grid(True)
        ax.legend()
        pw.add_plot(f"Size Comparison - {k}", fig)

    # Plot takeoff power for fully foiling case
    fig, ax = plt.subplots()
    logs = [logsA, logsB, logsC]
    keys = ['4', '20', '40']
    for i in range(3):
        res_speeds = logs[i]['foiling'].get_channel_log("OperatingProfile", "Speed_kts")
        ax.scatter(res_speeds, logs[i]['foiling'].get_channel_log("OperatingProfile", "TakeOffPowerPerTEU_kW"), label=keys[i])
    ax.set(xlabel="Max Foiling Speed [kts] (determines min. take-off speed)", ylabel="Takeoff Power per TEU [kW]")
    ax.grid(True)
    ax.legend()
    pw.add_plot("Takeoff Power (per TEU)", fig)

    pw_app.run()


def run_a(speeds, pw):
    """
    4 TEU
    Stack 2 long, 2 wide, 1 layer
    """
    num_teus = 4
    payload_mass = num_teus * TEU_MASS
    vessel_mass = payload_mass * 1.3  # [kg]
    length = 2 * TEU_LENGTH * 1.4  # [m]
    beam = TEU_WIDTH * 2.1  # [m]
    height = 2 * 2.8  # [m]
    bow_fraction = 0.25
    chine_fraction = 0.2

    print(f"{num_teus} TEU Payload Mass = {payload_mass/1e3:.2f} T")
    print(f"{num_teus} TEU Vessel Mass = {vessel_mass/1e3:.2f} T")

    hull = Hull(length, beam, height, bow_fraction, chine_fraction)

    return configuration_comparison(speeds, pw, hull, num_teus, vessel_mass)


def run_b(speeds, pw):
    """
    20 TEU
    Stack 2 long, 5 wide, 2 layer
    """
    num_teus = 20
    payload_mass = num_teus * 18e3
    vessel_mass = payload_mass * 1.2  # [kg]
    length = 2 * TEU_LENGTH * 1.3  # [m]
    beam = TEU_WIDTH * 5.05  # [m]
    height = 2 * 3.5  # [m]
    bow_fraction = 0.25
    chine_fraction = 0.2

    print(f"{num_teus} TEU Payload Mass = {payload_mass/1e3:.2f} T")
    print(f"{num_teus} TEU Vessel Mass = {vessel_mass/1e3:.2f} T")

    hull = Hull(length, beam, height, bow_fraction, chine_fraction)

    return configuration_comparison(speeds, pw, hull, num_teus, vessel_mass)


def run_c(speeds, pw):
    """
    40 TEU
    Stack 4 long, 5 wide, 2 layer
    """
    num_teus = 40
    payload_mass = num_teus * TEU_MASS
    vessel_mass = payload_mass * 1.15 # [kg]
    length = 4 * TEU_LENGTH * 1.2 # [m]
    beam = TEU_WIDTH * 5.05 # [m]
    height = 2 * 3.8  # [m]
    bow_fraction = 0.25
    chine_fraction = 0.2

    print(f"{num_teus} TEU Payload Mass = {payload_mass/1e3:.2f} T")
    print(f"{num_teus} TEU Vessel Mass = {vessel_mass/1e3:.2f} T")

    hull = Hull(length, beam, height, bow_fraction, chine_fraction)

    return configuration_comparison(speeds, pw, hull, num_teus, vessel_mass)


def configuration_comparison(speeds, pw, hull, num_teus, vessel_mass):
    """

    """
    hydro_analysis = HydroAnalysis(hull)
    hydro_analysis.add_mass_component(MassComponent(vessel_mass, *hull.mass_reference_point()))

    # No Foils
    base_results = Logger(f"Base{num_teus}")
    hull.add_log_channels(base_results, "Hull")
    no_foils(num_teus, hydro_analysis, base_results, speeds)

    # Fully foiling
    foiling_results = Logger(f"Foiling{num_teus}")
    hull.add_log_channels(foiling_results, "Hull")
    hydro_analysis = HydroAnalysis(hull)  # reset to remove old foils
    hydro_analysis.add_mass_component(MassComponent(vessel_mass, *hull.mass_reference_point()))
    fully_foiling(num_teus, hydro_analysis, foiling_results, speeds)

    # Overlay results sets
    results = {'displacement': base_results, 'foiling': foiling_results}

    # Power per TEU
    fig1, ax1 = plt.subplots()
    ax1.set(xlabel="Speed [kts]", ylabel="Power per TEU [kW]")
    ax1.grid(True)

    # Hull draft
    fig2, ax2 = plt.subplots()
    ax2.set(xlabel="Speed [kts]", ylabel="Draft [m]")
    ax2.grid(True)

    for i, k in enumerate(results.keys()):
        speeds_kts = results[k].get_channel_log("OperatingProfile", "Speed_kts")
        ax1.scatter(speeds_kts, results[k].get_channel_log("OperatingProfile", "PowerPerTEU_kW"), label=k)

        if k is not "foiling":
            ax2.scatter(speeds_kts, results[k].get_channel_log("Hull", "Draft_m"), label=k)

    ax1.legend()
    ax2.legend()
    pw.add_plot(f"PowerPerTEU ({num_teus})", fig1)
    # pw.add_plot(f"HullDraft ({num_teus})", fig2)

    return results


def no_foils(num_teus, hydro_analysis, logger, speeds):
    """
    """
    # Operating profile
    ops_profile = LogObject()
    ops_profile.speed_kts = 0
    ops_profile.power_required_kW = 0
    ops_profile.power_per_TEU_kW = 0

    logger.add_group('OperatingProfile', ops_profile)
    logger.add_channel_to_group('speed_kts', 'OperatingProfile', alias='Speed_kts')
    logger.add_channel_to_group('power_required_kW', 'OperatingProfile', alias='PowerRequired_kW')
    logger.add_channel_to_group('power_per_TEU_kW', 'OperatingProfile', alias='PowerPerTEU_kW')

    for speed in speeds:
        _ = run_sink_vpp(hydro_analysis, speed, -1)
        equilib_forces = hydro_analysis.force_moment_waterplane(speed).force()
        power_req_base = propulsive_power(speed, -equilib_forces[0])

        ops_profile.speed_kts = mps_to_kts(speed)
        ops_profile.power_required_kW = power_req_base / 1000
        ops_profile.power_per_TEU_kW = power_req_base / (1000 * num_teus)

        logger.log_all()


def fully_foiling(num_teus, hydro_analysis, logger, speeds):
    """

    """
    # Operating profile
    ops_profile = LogObject()
    ops_profile.speed_kts = 0
    ops_profile.power_required_kW = 0
    ops_profile.power_per_TEU_kW = 0
    ops_profile.takeoff_power_per_TEU_kW = 0
    ops_profile.takeoff_speed_kts = 0

    logger.add_group('OperatingProfile', ops_profile)
    logger.add_channel_to_group('speed_kts', 'OperatingProfile', alias='Speed_kts')
    logger.add_channel_to_group('power_required_kW', 'OperatingProfile', alias='PowerRequired_kW')
    logger.add_channel_to_group('power_per_TEU_kW', 'OperatingProfile', alias='PowerPerTEU_kW')
    logger.add_channel_to_group('takeoff_power_per_TEU_kW', 'OperatingProfile', alias='TakeOffPowerPerTEU_kW')
    logger.add_channel_to_group('takeoff_speed_kts', 'OperatingProfile', alias='TakeOffSpeed_kts')

    # Define foils
    hull = hydro_analysis.get_hull()
    pos_xs = np.array([.25, .75]) * hull.length
    pos_z = -hull.height / 2  # below hull

    if num_teus < 10:
        aspect_ratio = 4.6
    elif num_teus < 25:
        aspect_ratio = 4.0
    else:
        aspect_ratio = 2.8

    if num_teus < 10:  # Account for container stacking foil size limitations at this size
        span = 1.2 * hull.beam
    else:
        span = hull.beam
    chord = span / aspect_ratio
    thickness_ratio = 0.1  # thickness / chord (this is quite thick)

    def generate_foil(pos_x):
        return HydroFoil(span, chord, Frame(hydro_analysis.get_hull().frame, pos_x, pos_z, 0),
                           thickness_ratio=thickness_ratio, end_plate_factor=1.2)  # struts act like end-plates
    foils = []
    for i in range(2):
        foil = generate_foil(pos_xs[i])
        foil.add_log_channels(logger, f"Foil{i}")
        foils.append(foil)

    # Add foils to the model (random AoA for now)
    for foil in foils:
        foil_mass = chord * span * 0.01 * 4 * SteelAISI1340.density
        print(f"{num_teus} TEU vessel Foil Mass = {foil_mass:.1f} kg")
        hydro_analysis.add_foil(foil, MassComponent(foil_mass, -chord / 4, 0))

    foil_split_fraction = 0.5  # 2 equal sized foils
    lift_target = constants.GRAVITY * hydro_analysis.total_mass() * foil_split_fraction
    aoa_equilib = np.deg2rad(1)  # initial guess

    area = chord * span
    foil_load_density = lift_target / area
    print(f"{num_teus} TEU Vessel Foil Area = {area:.2f} m^2")
    print(f"{num_teus} TEU Vessel Foil Load Density = {foil_load_density/1e3:.1f} kPa\n")
    if CAVITATION_CHECKS and foil_load_density > 6e4:
        print(f"\nWARNING: Foil Load Density exceeds cavitation limit (60 kPa) for {num_teus} TEU vessel."
              f" Try a larger foil area.")
        return

    for speed in speeds:
        # Compute foil AoA for full foiling equilib
        try:
            aoa_equilib = run_foil_aoa_vpp(foils[0], lift_target, speed, aoa_equilib, aoa_lb=-5, aoa_ub=5)
        except VPPSolverError as e:
            # print(e)
            continue

        except HydroFoil.FoilError as e:
            print("Foil Hydrodynamics Failed: ", e)
            continue

        # Set foil AoAs to compute equilib value
        for foil in foils:
            px, pz, ry = foil.get_location()
            foil.set_location(px, pz, -aoa_equilib)

        # Solve for power
        foil_fm = foils[0].force_moment(speed)
        foil_fm_B = ForceMoment(*hull.frame.vector_from_frame(*foil_fm.force(), foils[0].frame), foil_fm.moment())
        foiling_power = 2 * propulsive_power(speed, -foil_fm_B.force()[0])  # x2 for 2 foils

        ops_profile.speed_kts = mps_to_kts(speed)
        ops_profile.power_required_kW = foiling_power / 1000
        ops_profile.power_per_TEU_kW = foiling_power / (1000 * num_teus)

        # Solve for takeoff power (boat still in displacement mode, flaps at take-off state)
        # Simulate flaps by computing foil AoA for takeoff at 60 % max speed, then compute drag just below this speed
        speed_takeoff = speed * 0.6
        speed_takeoff_drag = 0.85 * speed_takeoff  # estimate this as point of max drag

        # Want any solver failure to throw here
        aoa_takeoff = run_foil_aoa_vpp(foils[0], lift_target, speed_takeoff, aoa_equilib, aoa_lb=-5, aoa_ub=15)
        for foil in foils:
            px, pz, ry = foil.get_location()
            foil.set_location(px, pz, -aoa_takeoff)

        _ = run_sink_vpp(hydro_analysis, speed_takeoff_drag, -1)
        equilib_forces = hydro_analysis.force_moment_waterplane(speed_takeoff_drag).force()
        takeoff_power = propulsive_power(speed_takeoff_drag, -equilib_forces[0])

        ops_profile.takeoff_power_per_TEU_kW = takeoff_power / (1000 * num_teus)
        ops_profile.takeoff_speed_kts = mps_to_kts(speed_takeoff)

        logger.log_all()


if __name__ == "__main__":
    main()
