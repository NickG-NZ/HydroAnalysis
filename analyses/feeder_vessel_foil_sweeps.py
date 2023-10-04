"""
Small 150 and 300 TEU feeder vessel sweeps over speed

No Foils drag vs Speed
    +
Foil assist drag vs. Speed
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
STRUCTURAL_CHECKS = False
CAVITATION_CHECKS = False


def main():
    speeds_kts = np.arange(20, 50, 1)
    speeds = [kts_to_mps(s_kts) for s_kts in speeds_kts]

    pw_app = PlotWindowApplication()
    pw = PlotWindow("Feeder Comparisons")
    logs150 = run_150(speeds, pw)
    logs300 = run_300(speeds, pw)

    # Compare the 150 and 300 TEU vessels (in all 3 configurations)
    for i, k in enumerate(logs150.keys()):
        fig, ax = plt.subplots()

        # The results arrays may be different sizes since the solver rejects invalid structural foils and cavitation
        res_speeds_150 = logs150[k].get_channel_log("OperatingProfile", "Speed_kts")
        power_per_TEU_150 = logs150[k].get_channel_log("OperatingProfile", "PowerPerTEU_kW")

        res_speeds_300 = logs300[k].get_channel_log("OperatingProfile", "Speed_kts")
        power_per_TEU_300 = logs300[k].get_channel_log("OperatingProfile", "PowerPerTEU_kW")

        ax.scatter(res_speeds_150, power_per_TEU_150, label=f"150-{k}")
        ax.scatter(res_speeds_300, power_per_TEU_300, label=f"300-{k}")
        ax.set(xlabel="Speed_kts", ylabel="Power per TEU [kW]")
        ax.grid(True)
        ax.legend()
        pw.add_plot(f"150 v 300 - {k}", fig)

    # Plot takeoff power for fully foiling case
    fig, ax = plt.subplots()
    logs = [logs150, logs300]
    keys = ['150', '300']
    for i in range(2):
        res_speeds = logs[i]['foiling'].get_channel_log("OperatingProfile", "TakeOffSpeed_kts")
        ax.scatter(res_speeds, logs[i]['foiling'].get_channel_log("OperatingProfile", "TakeOffPowerPerTEU_kW"), label=keys[i])
    ax.set(xlabel="TakeOffSpeed_kts", ylabel="TakeOffPowerPerTEU_kW")
    ax.grid(True)
    ax.legend()
    pw.add_plot("TakeOffPower (per TEU)", fig)

    pw_app.run()


def run_150(speeds, pw):
    """

    """
    num_teus = 150
    vessel_mass = 2750e3
    length = 79.9  # [m]
    beam = 16  # [m]
    height = 2 * ft_to_m(13.1)  # [m]
    bow_fraction = 0.25
    chine_fraction = 0.3  # near flat bottom

    hull = Hull(length, beam, height, bow_fraction, chine_fraction)

    return configuration_comparison(speeds, pw, hull, num_teus, vessel_mass)


def run_300(speeds, pw):
    """

    """
    # Vessel definition
    num_teus = 300
    vessel_mass = 4081e3
    length = 93.6  # [m]
    beam = 16  # [m]
    height = 12  # [m]
    bow_fraction = 0.25
    chine_fraction = 0.3  # near flat bottom

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

    # Foil Assist
    assist_results = Logger(f"Assist{num_teus}")
    hull.add_log_channels(assist_results, "Hull")
    foil_assist(num_teus, hydro_analysis, assist_results, speeds)

    # Fully foiling
    foiling_results = Logger(f"Foiling{num_teus}")
    hull.add_log_channels(foiling_results, "Hull")
    hydro_analysis = HydroAnalysis(hull)  # reset to remove old foils
    hydro_analysis.add_mass_component(MassComponent(vessel_mass, *hull.mass_reference_point()))
    fully_foiling(num_teus, hydro_analysis, foiling_results, speeds)

    # Overlay all 3 results sets
    results = {'base': base_results, 'assist': assist_results,'foiling': foiling_results}

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
    pw.add_plot(f"HullDraft ({num_teus})", fig2)

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


def foil_assist(num_teus, hydro_analysis, logger, speeds):
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

    # Define foils
    hull = hydro_analysis.get_hull()
    pos_xs = np.array([.25, .25, .75, .75]) * hull.length
    pos_z = hull.height / 5
    aoa = np.deg2rad(3)  # [deg] Tuned manually
    aspect_ratio = 4
    span = hull.beam * 0.2
    chord = span / aspect_ratio
    thickness_ratio = 0.1  # thickness / chord (this is quite thick)

    def generate_foil(pos_x):
        return HydroFoil(span, chord, Frame(hydro_analysis.get_hull().frame, pos_x, pos_z, -aoa),
                           thickness_ratio=thickness_ratio, end_plate_factor=2)  # Foils mounted to side of hull
    foils = []
    for i in range(4):
        foils.append(generate_foil(pos_xs[i]))
        foils[i].add_log_channels(logger, f"Foil{i}")

    for speed in speeds:
        skip_speed = False

        # compute foil structural mass
        for foil in foils:
            try:
                foil_mass = foil.structural_mass(aoa, speed, SteelAISI1340, fos=1.3,
                                                 scaling_factor=1.5, share_frac=0.2)
            except HydroFoil.FoilError as e:
                if STRUCTURAL_CHECKS:
                    print("Foil Structure Failed: ", e)
                    skip_speed = True
                    continue
                else:
                    foil_mass_num = 4 * span * chord * 20e-3 * SteelAISI1340.density
                    foil_mass = MassComponent(foil_mass_num, -chord / 4, 0)

            hydro_analysis.add_foil(foil, foil_mass)

        if skip_speed:
            continue

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
    pos_z = -hull.height / 3  # below hull

    aspect_ratio = 10
    span = hull.beam
    chord = span / aspect_ratio
    thickness_ratio = 0.1  # thickness / chord (this is quite thick)

    def generate_foil(pos_x):
        return HydroFoil(span, chord, Frame(hydro_analysis.get_hull().frame, pos_x, pos_z, 0),
                           thickness_ratio=thickness_ratio, end_plate_factor=1.2)  # foil struts act like end-plates

    foils = []
    for i in range(2):
        foil = generate_foil(pos_xs[i])
        foil.add_log_channels(logger, f"Foil{i}")
        foils.append(foil)

    # Add foils to the model (random AoA for now)
    for foil in foils:
        hydro_analysis.add_foil(foil, MassComponent(10e3, -chord / 4, 0))

    foil_split_fraction = 0.5  # 2 equal sized foils
    lift_target = constants.GRAVITY * hydro_analysis.total_mass() * foil_split_fraction
    aoa_equilib = np.deg2rad(1)  # initial guess

    for speed in speeds:
        # Compute foil AoA for full foiling equilib
        try:
            aoa_equilib = run_foil_aoa_vpp(foils[0], lift_target, speed, aoa_equilib)
        except VPPSolverError as e:
            print(e)
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

        # Solve for takeoff power (boat still in displacement mode)
        speed_takeoff = speed * 0.6
        _ = run_sink_vpp(hydro_analysis, speed_takeoff, -1)
        equilib_forces = hydro_analysis.force_moment_waterplane(speed_takeoff).force()
        takeoff_power = propulsive_power(speed, -equilib_forces[0])

        ops_profile.takeoff_power_per_TEU_kW = takeoff_power / (1000 * num_teus)
        ops_profile.takeoff_speed_kts = mps_to_kts(speed_takeoff)

        logger.log_all()


if __name__ == "__main__":
    main()
