"""
Parameter sweeps to investigate the effects of hydrofoils
on ship efficiency
"""
import sys, os
import matplotlib.pyplot as plt

sys.path.append(os.path.join(os.path.abspath(__file__), os.pardir))

from HydroAnalysis import HydroAnalysis, MassComponent
from Logger import Logger, LogObject
from ResultsViewer import ResultsViewer
from Hull import Hull
from HydroFoil import HydroFoil
from Frame import Frame
from Material import Steel, SteelAISI1340
from VPP import *
from utils import *
from ForceMoment import ForceMoment


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
    ops_profile = LogObject()
    results_log.add_group('OperatingProfile', ops_profile)
    speed_kts = 26
    speed = kts_to_mps(speed_kts)
    ops_profile.speed_kts = speed_kts
    ops_profile.power_required_kW = 0
    ops_profile.power_per_TEU_kW = 0
    results_log.add_channel_to_group('speed_kts', 'OperatingProfile', alias='Speed_kts')
    results_log.add_channel_to_group('power_required_kW', 'OperatingProfile', alias='PowerRequired_kW')
    results_log.add_channel_to_group('power_per_TEU_kW', 'OperatingProfile', alias='PowerPerTEU_kW')

    print(f"Running HydroAnalysis of Supply Vessel operating at {speed_kts:.1f} kts")

    # Solve for equilib with no foils first
    hydro_analysis = HydroAnalysis(hull)
    hydro_analysis.add_mass_component(MassComponent(vessel_mass, *hull.mass_reference_point()))

    equilib_sink = run_vpp(hydro_analysis, speed, [-1])
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
    foil_port = HydroFoil(1, 1, Frame(hull.frame, foil_pos_x, foil_pos_y, 0), thickness_ratio=thickness_ratio, end_plated=True)
    foil_stbd = HydroFoil(1, 1, Frame(hull.frame, foil_pos_x, foil_pos_y, 0), thickness_ratio=thickness_ratio, end_plated=True)

    # Sweeps
    angles_of_attack = np.deg2rad(np.arange(3, 7, 0.2))
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
                continue

            # add foils
            hydro_analysis.add_foil(foil_port, MassComponent(foil_mass, -chord / 4, 0))
            hydro_analysis.add_foil(foil_stbd, MassComponent(foil_mass, -chord / 4, 0))

            # Solve for equilibriums
            equilib_draft = -run_vpp(hydro_analysis, speed, [-1.0])
            equilib_forces = hydro_analysis.force_moment_waterplane(speed).force()
            power_required = propulsive_power(speed, -equilib_forces[0])
            ops_profile.power_required_kW = power_required / 1000
            ops_profile.power_per_TEU_kW = power_required / (1000 * num_teus)

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
    Fully foiling vessel analysis
    """
    # hull definition
    num_teus = 14
    vessel_mass = 490e3  # [kg] DWT + LWT
    length = 35.5  # [m]
    beam = 7.9  # [m]
    height = 4  # [m]
    bow_fraction = 0.22
    chine_fraction = 0.2
    hull = Hull(length, beam, height, bow_fraction, chine_fraction)

    # operation
    speed_kts = 26
    speed = kts_to_mps(speed_kts)
    print(f"\nRunning HydroAnalysis of Fully Foiling Supply Vessel")

    # Add hull model (to compute take-off power)
    hydro_analysis = HydroAnalysis(hull)
    hydro_analysis.add_mass_component(MassComponent(vessel_mass, *hull.mass_reference_point()))

    # Add main foil
    span = beam
    aspect_ratio = 10
    chord = span / aspect_ratio
    aoa = 1.7
    foil = HydroFoil(span, chord, Frame(hull.frame, length / 2, height / 4, -aoa), thickness_ratio=0.2, end_plated=False)

    # Compute foil force
    foil_fm = foil.force_moment(speed)
    foil_fm_B = ForceMoment(*hull.frame.vector_from_frame(*foil_fm.force(), foil.frame), foil_fm.moment())

    drag_power = propulsive_power(speed, -foil_fm_B.force()[0]) / 1000
    print(f"L/D: {-foil_fm.force()[1] / foil_fm_B.force()[0]}")
    print(f"Foil Lift: {foil_fm_B.force()[1] / constants.GRAVITY / 1e3:.2f} T")
    print(f"Foil Drag Power: {drag_power:.2f} kW")
    print(f"Power per TEU: {drag_power / num_teus:.2f} kW")


def feeder_150_teu():
    """
    Vessel: NP Suratthani 3
    """
    num_teus = 150
    vessel_mass = 2750e3
    length = 79.9  # [m]
    beam = 16  # [m]
    height = 10  # [m]
    bow_fraction = 0.25
    chine_fraction = 0.3  # near flat bottom
    hull = Hull(length, beam, height, bow_fraction, chine_fraction)

    # operation
    speed_kts = 26  # (Vessel actually sails at 10 kts)
    speed = kts_to_mps(speed_kts)
    print(f"\nRunning HydroAnalysis of NP Suranthi 3 ({num_teus} TEU) Vessel operating at {speed_kts:.1f} kts")

    # Solve for equilib
    hydro_analysis = HydroAnalysis(hull)
    hydro_analysis.add_mass_component(MassComponent(vessel_mass, *hull.mass_reference_point()))

    equilib_sink = run_vpp(hydro_analysis, speed, [-3])
    equilib_forces = hydro_analysis.force_moment_waterplane(speed).force()
    power_req_base = propulsive_power(speed, -equilib_forces[0])
    print(f"Equilibrium Draft: {-equilib_sink:.3f} m")
    print(f"Equilibrium Power: {power_req_base / 1000:.2f} kW")
    print(f"Power per TEU: {power_req_base / (1000 * num_teus):.2f} kW")
    print(f"Wave Drag: {hull._wave_drag_N / 1e6:.1f} MN")


def feeder_300_teu():
    """
    Sheng An Da 12
    """
    num_teus = 300
    vessel_mass = 4081e3
    length = 93.6  # [m]
    beam = 16  # [m]
    height = 12  # [m]
    bow_fraction = 0.25
    chine_fraction = 0.3  # near flat bottom
    hull = Hull(length, beam, height, bow_fraction, chine_fraction)

    # operation
    speed_kts = 26  # (vessel actually sails at 12 kts)
    speed = kts_to_mps(speed_kts)
    print(f"\nRunning HydroAnalysis of Sheng An Da 12 ({num_teus} TEU) Vessel operating at {speed_kts:.1f} kts")

    # Solve for equilib
    hydro_analysis = HydroAnalysis(hull)
    hydro_analysis.add_mass_component(MassComponent(vessel_mass, *hull.mass_reference_point()))

    equilib_sink = run_vpp(hydro_analysis, speed, [-3.5])
    equilib_forces = hydro_analysis.force_moment_waterplane(speed).force()
    power_req_base = propulsive_power(speed, -equilib_forces[0])
    print(f"Equilibrium Draft [m]: {-equilib_sink:.3f} m")
    print(f"Equilibrium Power [kW]: {power_req_base / 1000:.2f}")
    print(f"Power per TEU [kW]: {power_req_base / (1000 * num_teus):.2f}")


def panamax_5000_teu():
    """
    Compute the propulsion power per teu for a 5000 TEU (PANAMX) container ship

    Vessel: Tian Fyu He (PANAMX)
    """
    num_teus = 5000
    vessel_mass = 63143e3
    length = 300  # [m]
    beam = 35  # [m]
    height = 25  # [m]
    bow_fraction = 0.25
    chine_fraction = 0.3  # near flat bottom (currently higher to account for stern)
    hull = Hull(length, beam, height, bow_fraction, chine_fraction)

    # operation
    speed_kts = 26  # this is specified for this vessel
    speed = kts_to_mps(speed_kts)
    print(f"\nRunning HydroAnalysis of Tian Fyu He ({num_teus} TEU) Vessel operating at {speed_kts:.1f} kts")

    # Solve for equilib
    hydro_analysis = HydroAnalysis(hull)
    hydro_analysis.add_mass_component(MassComponent(vessel_mass, *hull.mass_reference_point()))

    equilib_sink = run_vpp(hydro_analysis, speed, [-10.44])
    equilib_forces = hydro_analysis.force_moment_waterplane(speed).force()
    power_req_base = propulsive_power(speed, -equilib_forces[0])
    print(f"Equilibrium Draft [m]: {-equilib_sink:.3f} m")
    print(f"Equilibrium Power [kW]: {power_req_base / 1000:.2f}")
    print(f"Power per TEU [kW]: {power_req_base / (1000 * num_teus):.2f}")


if __name__ == "__main__":
    foil_size_sweep_supply_vessel()
    # fully_foiling_supply_vessel()
    feeder_150_teu()
    # feeder_300_teu()
    # panamax_5000_teu()


