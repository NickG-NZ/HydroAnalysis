"""
Compute the relative efficiency of real Container vessels of different sizes
"""
import sys, os

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir))

from HydroAnalysis import HydroAnalysis
from ForceMoment import MassComponent
from Logger import Logger, LogObject
from PlotWindow import *
from Hull import Hull
from VPP import *
from utils import *


def main():
    pwApp = PlotWindowApplication()
    pw = PlotWindow("CompareVessels")

    # Existing vessel comparisons
    compare_at_same_speeds(pw)
    compare_at_operating_speeds(pw)

    pwApp.run()


def run_hull_equilib(hydro_analysis, log, speed, num_teus):
    """
    Adds 'Equilib' log group to the log and runs a VPP to solve for the
    equilibrium (saving relevant data in the group)
    """
    # Equilib data log
    equilib = LogObject()
    equilib.power_required_kW = 0
    equilib.power_per_TEU_kW = 0
    equilib.speed_kts = mps_to_kts(speed)

    log.add_group('Equilib', equilib)
    log.add_channel_to_group('power_required_kW', 'Equilib', alias='PowerRequired_kW')
    log.add_channel_to_group('power_per_TEU_kW', 'Equilib', alias='PowerPerTEU_kW')
    log.add_channel_to_group('speed_kts', 'Equilib', alias='Speed_kts')

    # Solve for equilib
    equilib_sink = run_sink_vpp(hydro_analysis, speed, -3)
    equilib_forces = hydro_analysis.force_moment_waterplane(speed).force()
    drag_power = propulsive_power(speed, -equilib_forces[0])

    equilib.power_required_kW = drag_power / 1e3
    equilib.power_per_TEU_kW = drag_power / (num_teus * 1e3)

    log.log_all()


def compare_at_same_speeds(pw):
    """
    Compare the drag of the vessels with them all operating at the same
    speed. In reality the smaller vesssels tend to operate at lower speed
    """
    stats = {}  # dict of results logs

    speed_kts = 23

    # FEEDER
    stats.update({150: c150_teu(speed=kts_to_mps(speed_kts))})
    stats.update({300: c300_teu(speed=kts_to_mps(speed_kts))})
    stats.update({537: c537_teu(speed=kts_to_mps(speed_kts))})

    # HANDY
    stats.update({1005: c1005_teu(speed=kts_to_mps(speed_kts))})
    stats.update({1338: c1338_teu(speed=kts_to_mps(speed_kts))})
    stats.update({1732: c1732_teu(speed=kts_to_mps(speed_kts))})
    stats.update({1970: c1970_teu(speed=kts_to_mps(speed_kts))})

    # PANAMAX
    stats.update({3078: c3078_teu(speed=kts_to_mps(speed_kts))})
    stats.update({3534: c3534_teu(speed=kts_to_mps(speed_kts))})
    stats.update({4178: c4178_teu(speed=kts_to_mps(speed_kts))})
    stats.update({4578: c4578_teu(speed=kts_to_mps(speed_kts))})
    stats.update({5089: c5089_teu(speed=kts_to_mps(speed_kts))})

    # POST PANAMAX
    stats.update({3650: c3650_teu(speed=kts_to_mps(speed_kts))})
    stats.update({4432: c4432_teu(speed=kts_to_mps(speed_kts))})
    stats.update({5301: c5301_teu(speed=kts_to_mps(speed_kts))})

    num_teus = []
    power_per_teus = []
    for k, v in stats.items():
        num_teus.append(k)
        power_per_teus.append(v.get_channel_log('Equilib', 'PowerPerTEU_kW'))

    # Plot power per TEU against num teus
    pw.create_and_add_scatter(num_teus, power_per_teus, "TEUs", "Power/TEU [kW]", f"Power per TEU ({speed_kts} kts)")


def compare_at_operating_speeds(pw):
    """
    Compare the vessels with them operating at their designated speeds
    """
    stats = {}  # dict of results logs

    stats.update({150: c150_teu(speed=kts_to_mps(10))})
    stats.update({300: c300_teu(speed=kts_to_mps(12))})
    stats.update({537: c537_teu(speed=kts_to_mps(13))})

    # HANDY
    stats.update({1005: c1005_teu(speed=kts_to_mps(18))})
    stats.update({1338: c1338_teu(speed=kts_to_mps(19.3))})
    stats.update({1732: c1732_teu(speed=kts_to_mps(20.6))})
    stats.update({1970: c1970_teu(speed=kts_to_mps(21.0))})

    # PANAMAX
    stats.update({3078: c3078_teu(speed=kts_to_mps(22))})
    stats.update({3534: c3534_teu(speed=kts_to_mps(22.9))})
    stats.update({4178: c4178_teu(speed=kts_to_mps(24.5))})
    stats.update({4578: c4578_teu(speed=kts_to_mps(24))})
    stats.update({5089: c5089_teu(speed=kts_to_mps(26))})

    # # POST PANAMAX
    stats.update({3650: c3650_teu(speed=kts_to_mps(21.6))})
    stats.update({4432: c4432_teu(speed=kts_to_mps(24.1))})
    stats.update({5301: c5301_teu(speed=kts_to_mps(24.6))})

    num_teus = []
    power_per_teus = []
    for k, v in stats.items():
        num_teus.append(k)
        power_per_teus.append(v.get_channel_log('Equilib', 'PowerPerTEU_kW'))

    # Plot power per TEU against num teus
    pw.create_and_add_scatter(num_teus, power_per_teus, "TEUs", "Power/TEU [kW]", "Power per TEU (diff. speeds)")


def c150_teu(speed):
    """
    NP Suratthani 3
    """
    log = Logger("C150")

    num_teus = 150
    vessel_mass = 2750e3
    length = 79.9  # [m]
    beam = 16  # [m]
    height = 2 * ft_to_m(13.1)  # [m]
    bow_fraction = 0.25
    chine_fraction = 0.3  # near flat bottom

    hull = Hull(length, beam, height, bow_fraction, chine_fraction)
    hull.add_log_channels(log, "Hull")
    hydro_analysis = HydroAnalysis(hull)
    hydro_analysis.add_mass_component(MassComponent(vessel_mass, *hull.mass_reference_point()))

    run_hull_equilib(hydro_analysis, log, speed, num_teus)

    return log


def c300_teu(speed):
    """
    Sheng An Da 12
    """
    log = Logger("C300")

    num_teus = 300
    vessel_mass = 4081e3
    length = 93.6  # [m]
    beam = 16  # [m]
    height = 12  # [m]
    bow_fraction = 0.25
    chine_fraction = 0.3  # near flat bottom

    hull = Hull(length, beam, height, bow_fraction, chine_fraction)
    hull.add_log_channels(log, "Hull")
    hydro_analysis = HydroAnalysis(hull)
    hydro_analysis.add_mass_component(MassComponent(vessel_mass, *hull.mass_reference_point()))

    run_hull_equilib(hydro_analysis, log, speed, num_teus)

    return log


def c537_teu(speed):
    """
    Loagoa Mas
    """
    log = Logger("C537")

    num_teus = 537
    vessel_mass = 8100e3
    length = ft_to_m(393.4)  # [m]
    beam = ft_to_m(71.5)  # [m]
    height = 2 * ft_to_m(17.1)  # [m]
    bow_fraction = 0.25
    chine_fraction = 0.3  # near flat bottom

    hull = Hull(length, beam, height, bow_fraction, chine_fraction)
    hull.add_log_channels(log, "Hull")
    hydro_analysis = HydroAnalysis(hull)
    hydro_analysis.add_mass_component(MassComponent(vessel_mass, *hull.mass_reference_point()))

    run_hull_equilib(hydro_analysis, log, speed, num_teus)

    return log


def c1005_teu(speed):
    """

    """
    log = Logger("C1005")

    num_teus = 1005
    vessel_mass = 10600e3
    length = ft_to_m(508.2)  # [m]
    beam = ft_to_m(70.5)  # [m]
    height = 2 * ft_to_m(23.0)  # [m]
    bow_fraction = 0.25
    chine_fraction = 0.3  # near flat bottom

    hull = Hull(length, beam, height, bow_fraction, chine_fraction)
    hull.add_log_channels(log, "Hull")
    hydro_analysis = HydroAnalysis(hull)
    hydro_analysis.add_mass_component(MassComponent(vessel_mass, *hull.mass_reference_point()))

    run_hull_equilib(hydro_analysis, log, speed, num_teus)

    return log


def c1338_teu(speed):
    """

    """
    log = Logger("C1338")

    num_teus = 1338
    vessel_mass = 17230e3
    length = ft_to_m(529.2)  # [m]
    beam = ft_to_m(82.0)  # [m]
    height = 2 * ft_to_m(31.2)  # [m]
    bow_fraction = 0.25
    chine_fraction = 0.3  # near flat bottom

    hull = Hull(length, beam, height, bow_fraction, chine_fraction)
    hull.add_log_channels(log, "Hull")
    hydro_analysis = HydroAnalysis(hull)
    hydro_analysis.add_mass_component(MassComponent(vessel_mass, *hull.mass_reference_point()))

    run_hull_equilib(hydro_analysis, log, speed, num_teus)

    return log


def c1732_teu(speed):
    """

    """
    log = Logger("C1732")

    num_teus = 1732
    vessel_mass = 23550e3
    length = ft_to_m(575.5)  # [m]
    beam = ft_to_m(89.0)  # [m]
    height = 2 * ft_to_m(35.8)  # [m]
    bow_fraction = 0.25
    chine_fraction = 0.3  # near flat bottom

    hull = Hull(length, beam, height, bow_fraction, chine_fraction)
    hull.add_log_channels(log, "Hull")
    hydro_analysis = HydroAnalysis(hull)
    hydro_analysis.add_mass_component(MassComponent(vessel_mass, *hull.mass_reference_point()))

    run_hull_equilib(hydro_analysis, log, speed, num_teus)

    return log


def c1970_teu(speed):
    """

    """
    log = Logger("C1970")

    num_teus = 1970
    vessel_mass = 28632e3
    length = ft_to_m(621.8)  # [m]
    beam = ft_to_m(90.6)  # [m]
    height = 2 * ft_to_m(37.4)  # [m]
    bow_fraction = 0.25
    chine_fraction = 0.3  # near flat bottom

    hull = Hull(length, beam, height, bow_fraction, chine_fraction)
    hull.add_log_channels(log, "Hull")
    hydro_analysis = HydroAnalysis(hull)
    hydro_analysis.add_mass_component(MassComponent(vessel_mass, *hull.mass_reference_point()))

    run_hull_equilib(hydro_analysis, log, speed, num_teus)

    return log


def c3078_teu(speed):
    """
    Safamarine Bayete
    """
    log = Logger("C3078")

    num_teus = 3078
    vessel_mass = 43127e3
    length = ft_to_m(721.8)  # [m]
    beam = ft_to_m(105.7)  # [m]
    height = 2 * ft_to_m(39.4)  # [m]
    bow_fraction = 0.25
    chine_fraction = 0.3  # near flat bottom

    hull = Hull(length, beam, height, bow_fraction, chine_fraction)
    hull.add_log_channels(log, "Hull")
    hydro_analysis = HydroAnalysis(hull)
    hydro_analysis.add_mass_component(MassComponent(vessel_mass, *hull.mass_reference_point()))

    run_hull_equilib(hydro_analysis, log, speed, num_teus)

    return log


def c3534_teu(speed):
    """

    """
    log = Logger("C3534")

    num_teus = 3534
    vessel_mass = 41975e3
    length = ft_to_m(757.9)  # [m]
    beam = ft_to_m(106)  # [m]
    height = 2 * ft_to_m(39.4)  # [m]
    bow_fraction = 0.25
    chine_fraction = 0.3  # near flat bottom

    hull = Hull(length, beam, height, bow_fraction, chine_fraction)
    hull.add_log_channels(log, "Hull")
    hydro_analysis = HydroAnalysis(hull)
    hydro_analysis.add_mass_component(MassComponent(vessel_mass, *hull.mass_reference_point()))

    run_hull_equilib(hydro_analysis, log, speed, num_teus)

    return log


def c4178_teu(speed):
    """

    """
    log = Logger("C4178")

    num_teus = 4178
    vessel_mass = 52788e3
    length = ft_to_m(767.7)  # [m]
    beam = ft_to_m(105.7)  # [m]
    height = 2 * ft_to_m(41.0)  # [m]
    bow_fraction = 0.25
    chine_fraction = 0.3  # near flat bottom

    hull = Hull(length, beam, height, bow_fraction, chine_fraction)
    hull.add_log_channels(log, "Hull")
    hydro_analysis = HydroAnalysis(hull)
    hydro_analysis.add_mass_component(MassComponent(vessel_mass, *hull.mass_reference_point()))

    run_hull_equilib(hydro_analysis, log, speed, num_teus)

    return log


def c4578_teu(speed):
    """

    """
    log = Logger("C4578")

    num_teus = 4578
    vessel_mass = 50575e3
    length = ft_to_m(855.4)  # [m]
    beam = ft_to_m(105.7)  # [m]
    height = 2 * ft_to_m(41.3)  # [m]
    bow_fraction = 0.25
    chine_fraction = 0.3  # near flat bottom

    hull = Hull(length, beam, height, bow_fraction, chine_fraction)
    hull.add_log_channels(log, "Hull")
    hydro_analysis = HydroAnalysis(hull)
    hydro_analysis.add_mass_component(MassComponent(vessel_mass, *hull.mass_reference_point()))

    run_hull_equilib(hydro_analysis, log, speed, num_teus)

    return log


def c5089_teu(speed):
    """

    """
    log = Logger("C5089")

    num_teus = 5089
    vessel_mass = 63143e3
    length = ft_to_m(964.6)  # [m]
    beam = ft_to_m(105.7)  # [m]
    height = 2 * ft_to_m(39.4)  # [m]
    bow_fraction = 0.25
    chine_fraction = 0.3  # near flat bottom

    hull = Hull(length, beam, height, bow_fraction, chine_fraction)
    hull.add_log_channels(log, "Hull")
    hydro_analysis = HydroAnalysis(hull)
    hydro_analysis.add_mass_component(MassComponent(vessel_mass, *hull.mass_reference_point()))

    run_hull_equilib(hydro_analysis, log, speed, num_teus)

    return log


def c3650_teu(speed):
    """

    """
    log = Logger("C3650")

    num_teus = 3650
    vessel_mass = 51604e3
    length = ft_to_m(748.1)  # [m]
    beam = ft_to_m(122.37)  # [m]
    height = 2 * ft_to_m(41.0)  # [m]
    bow_fraction = 0.25
    chine_fraction = 0.3  # near flat bottom

    hull = Hull(length, beam, height, bow_fraction, chine_fraction)
    hull.add_log_channels(log, "Hull")
    hydro_analysis = HydroAnalysis(hull)
    hydro_analysis.add_mass_component(MassComponent(vessel_mass, *hull.mass_reference_point()))

    run_hull_equilib(hydro_analysis, log, speed, num_teus)

    return log


def c4432_teu(speed):
    """

    """
    log = Logger("C4432")

    num_teus = 4432
    vessel_mass = 52055e3
    length = ft_to_m(875.0)  # [m]
    beam = ft_to_m(116.2)  # [m]
    height = 2 * ft_to_m(41.3)  # [m]
    bow_fraction = 0.25
    chine_fraction = 0.3  # near flat bottom

    hull = Hull(length, beam, height, bow_fraction, chine_fraction)
    hull.add_log_channels(log, "Hull")
    hydro_analysis = HydroAnalysis(hull)
    hydro_analysis.add_mass_component(MassComponent(vessel_mass, *hull.mass_reference_point()))

    run_hull_equilib(hydro_analysis, log, speed, num_teus)

    return log


def c5301_teu(speed):
    """

    """
    log = Logger("C5301")

    num_teus = 5301
    vessel_mass = 65700e3
    length = ft_to_m(964.9)  # [m]
    beam = ft_to_m(105.7)  # [m]
    height = 2 * ft_to_m(44.3)  # [m]
    bow_fraction = 0.25
    chine_fraction = 0.3  # near flat bottom

    hull = Hull(length, beam, height, bow_fraction, chine_fraction)
    hull.add_log_channels(log, "Hull")
    hydro_analysis = HydroAnalysis(hull)
    hydro_analysis.add_mass_component(MassComponent(vessel_mass, *hull.mass_reference_point()))

    run_hull_equilib(hydro_analysis, log, speed, num_teus)

    return log


if __name__ == "__main__":
    main()
