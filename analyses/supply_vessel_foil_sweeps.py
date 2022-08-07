"""
Parameter sweeps to investigate the effects of foil assist and fully hydrofoiling configurations
applied to existing supply vessels
"""
import sys, os

sys.path.append(os.path.join(os.path.abspath(__file__), os.pardir))

from HydroAnalysis import HydroAnalysis
from Logger import Logger, LogObject
from ResultsViewer import ResultsViewer
from Hull import Hull
from HydroFoil import HydroFoil
from Frame import Frame
from ForceMoment import MassComponent

from Material import SteelAISI1340
from VPP import *
from utils import *
from ForceMoment import ForceMoment


def main():
    foil_size_sweep_supply_vessel()
    fully_foiling_supply_vessel()


def foil_size_sweep_supply_vessel():
    """
    Sweep over foil angle-of-attack and aspect ratio with fixed span
    """
    # Logging
    results_log = Logger("FoilSweep")

    # hull definition
    num_teus = 14
    vessel_mass = 490e3  # [kg] DWT + LWT
    length = 35.5  # [m]
    beam = 7.9  # [m]
    height = 4  # [m]
    bow_fraction = 0.22
    chine_fraction = 0.2
    hull = Hull(length, beam, height, bow_fraction, chine_fraction)

    # Add logging
    hull.add_log_channels(results_log, "Hull")

    # operation
    speed_kts = 26
    speed = kts_to_mps(speed_kts)
    ops_profile = LogObject()
    ops_profile.speed_kts = speed_kts
    ops_profile.power_required_kW = 0
    ops_profile.power_per_TEU_kW = 0
    results_log.add_group('OperatingProfile', ops_profile)
    results_log.add_channel_to_group('speed_kts', 'OperatingProfile', alias='Speed_kts')
    results_log.add_channel_to_group('power_required_kW', 'OperatingProfile', alias='PowerRequired_kW')
    results_log.add_channel_to_group('power_per_TEU_kW', 'OperatingProfile', alias='PowerPerTEU_kW')

    print(f"Running HydroAnalysis of Supply Vessel operating at {speed_kts:.1f} kts")

    # Solve for equilib with no foils first
    hydro_analysis = HydroAnalysis(hull)
    hydro_analysis.add_mass_component(MassComponent(vessel_mass, *hull.mass_reference_point()))

    equilib_sink = run_sink_vpp(hydro_analysis, speed, -1)
    equilib_forces = hydro_analysis.force_moment_waterplane(speed).force()
    power_req_base = propulsive_power(speed, -equilib_forces[0])
    print(f"Equilibrium Draft (no foils): {-equilib_sink:.3f} m")
    print(f"Equilibrium Power: {power_req_base / 1000:.2f} kW")
    print(f"Power per TEU: {power_req_base / (1000 * num_teus):.2f} kW")
    print(f"Wave Drag: {hull._wave_drag_N / 1e6:.1f} MN")

    # main foil definitions
    aspect_ratio = 2.5  # [m] per foil
    thickness_ratio = 0.15  # thickness / chord
    max_angle_of_attack = np.deg2rad(8)
    max_speed = kts_to_mps(26)

    foil_pos_x = length / 2
    foil_pos_y = height / 4
    foil_port = HydroFoil(1, 1, Frame(hull.frame, foil_pos_x, foil_pos_y, 0), thickness_ratio=thickness_ratio,
                         end_plate_factor=2)
    foil_stbd = HydroFoil(1, 1, Frame(hull.frame, foil_pos_x, foil_pos_y, 0), thickness_ratio=thickness_ratio,
                          end_plate_factor=2)  # factor of 2 accounts for single sided wing mounted to side of hull

    # Sweeps
    angles_of_attack = np.deg2rad(np.arange(3, 26, 1))
    foil_areas = np.arange(4, 16, 2)

    # Add logging
    foil_port.add_log_channels(results_log, "FoilPort")
    foil_stbd.add_log_channels(results_log, "FoilStbd")
    results_log.run()

    for area in foil_areas:
        span = np.sqrt(aspect_ratio * area)
        chord = span / aspect_ratio

        for idx in range(len(angles_of_attack)):
            aoa = angles_of_attack[idx]

            hydro_analysis = HydroAnalysis(hull)
            hydro_analysis.add_mass_component(MassComponent(vessel_mass, *hull.mass_reference_point()))

            foil_port.set_location(foil_pos_x, foil_pos_y, -aoa)
            foil_stbd.set_location(foil_pos_x, foil_pos_y, -aoa)
            foil_port.resize(span, chord, thickness_ratio)
            foil_stbd.resize(span, chord, thickness_ratio)

            # compute structural mass
            try:
                foil_mass = foil_port.structural_mass(max_angle_of_attack, max_speed, SteelAISI1340, fos=1.3,
                                                      scaling_factor=1.5, share_frac=0.2)
            except HydroFoil.FoilError as e:
                print("Foil Structure Failed: ", e)
                continue

            # add foils
            hydro_analysis.add_foil(foil_port, MassComponent(foil_mass, -chord / 4, 0))
            hydro_analysis.add_foil(foil_stbd, MassComponent(foil_mass, -chord / 4, 0))

            # Solve for equilibriums
            try:
                equilib_draft = -run_sink_vpp(hydro_analysis, speed, -1.0)
                equilib_forces = hydro_analysis.force_moment_waterplane(speed).force()
                power_required = propulsive_power(speed, -equilib_forces[0])
                ops_profile.power_required_kW = power_required / 1000
                ops_profile.power_per_TEU_kW = power_required / (1000 * num_teus)
            except HydroFoil.FoilError as e:
                print("Foil Hydrodynamics Failed: ", e)
                continue

            # Log the VPP solution
            results_log.log_all()

    results_vis = ResultsViewer(results_log)
    # results_vis.compare_channels("FoilPort.AoA_rad", "FoilPort.Drag_N")
    results_vis.compare_channels("FoilPort.Span_m", "OperatingProfile.PowerRequired_kW", sort_by="FoilPort.AoA_rad")
    results_vis.compare_channels("FoilPort.Span_m", "OperatingProfile.PowerPerTEU_kW", sort_by="FoilPort.AoA_rad")
    results_vis.compare_channels("FoilStbd.AoA_rad", "OperatingProfile.PowerRequired_kW", sort_by="FoilStbd.Span_m")
    results_vis.compare_channels("FoilPort.Span_m", "Hull.FrictionDrag_N", sort_by="FoilPort.AoA_rad")
    results_vis.compare_channels("FoilPort.Span_m", "Hull.WaveDrag_N", sort_by="FoilPort.AoA_rad")

    results_vis.run()


def fully_foiling_supply_vessel():
    """
    Fully foiling vessel analysis.
    Consider a vessel design with two main lifting foils (rather than one lifting foil and one stabilizer)
    The forward lifting foil takes a specified fraction of the total load

    Sweep over aspect ratios
    """
    results_log = Logger("FullyFoiling")

    # hull definition
    num_teus = 14
    vessel_mass = 490e3  # [kg] DWT + LWT
    length = 35.5  # [m]
    beam = 7.9  # [m]
    height = 4  # [m]
    bow_fraction = 0.22
    chine_fraction = 0.2
    hull = Hull(length, beam, height, bow_fraction, chine_fraction)

    # Add logging
    hull.add_log_channels(results_log, "Hull")

    # operation
    ops_profile = LogObject()
    results_log.add_group('OperatingProfile', ops_profile)
    speed_kts = 30
    speed = kts_to_mps(speed_kts)
    ops_profile.speed_kts = speed_kts
    ops_profile.power_required_kW = 0
    ops_profile.power_per_TEU_kW = 0
    results_log.add_channel_to_group('speed_kts', 'OperatingProfile', alias='Speed_kts')
    results_log.add_channel_to_group('power_required_kW', 'OperatingProfile', alias='PowerRequired_kW')
    results_log.add_channel_to_group('power_per_TEU_kW', 'OperatingProfile', alias='PowerPerTEU_kW')

    print(f"\nRunning HydroAnalysis of Fully Foiling Supply Vessel")

    # Main foil sweep
    foil_split_fraction_to_front = 0.6  # Percentage of total lift provided by front foil
    span = beam * 1.2
    aspect_ratios = np.arange(3, 20, 0.5)
    chords = span / aspect_ratios
    foil = HydroFoil(span, chords[0], Frame(hull.frame, length / 2, height / 4, 0), thickness_ratio=0.15,
                     end_plate_factor=1.2)  # struts end-plate the foil

    foil.add_log_channels(results_log, "Foil")
    lift_target = constants.GRAVITY * vessel_mass * foil_split_fraction_to_front
    aoa_equilib = np.deg2rad(4)  # initial guess

    for idx, AR in enumerate(aspect_ratios):
        foil_loading = foil_split_fraction_to_front * vessel_mass * constants.GRAVITY / (span * chords[idx])
        print(f"\nFoil Loading {foil_loading / 1000:.1f} kPa")

        foil.resize(span, chords[idx], thickness_ratio=0.15)
        try:
            aoa_equilib = run_foil_aoa_vpp(foil, lift_target, speed, aoa_equilib)
        except VPPSolverError as e:
            print(f"{e}. Foil Aspect Ratio (b/c) =", AR)
            continue

        except HydroFoil.FoilError as e:
            print("Foil Hydrodynamics Failed: ", e)
            continue

        # Compute foil forces
        foil_fm = foil.force_moment(speed)
        foil_fm_B = ForceMoment(*hull.frame.vector_from_frame(*foil_fm.force(), foil.frame), foil_fm.moment())

        drag_power = propulsive_power(speed, -foil_fm_B.force()[0])
        ops_profile.power_required_kW = drag_power / 1000
        ops_profile.power_per_TEU_kW = drag_power / (1000 * num_teus)

        # Log the VPP solution
        results_log.log_all()

    results_vis = ResultsViewer(results_log)
    results_vis.compare_channels("Foil.AspectRatioEffective", "Foil.LD")
    results_vis.compare_channels("Foil.AspectRatioEffective", "OperatingProfile.PowerPerTEU_kW")
    results_vis.compare_channels("Foil.AspectRatioEffective", "Foil.LoadDensity_Pa")
    results_vis.compare_channels("Foil.AspectRatioEffective", "Foil.AoA_rad")
    results_vis.compare_channels("Foil.`AspectRatio`Effective", "Foil.Lift_N")
    results_vis.compare_channels("Foil.AoA_rad", "Foil.CL")

    results_vis.run()


if __name__ == "__main__":
    main()
