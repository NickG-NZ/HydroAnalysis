"""
Velocity and Pointing Program (VPP)
Solves for the equilibrium state of the given vessel configuration

Currently only 1D (sink)
"""
import numpy as np
from scipy import optimize


class VPPSolverError(Exception):
    def __init__(self, message):
        super().__init__(message)


def run_sink_vpp(hydro_model, speed, x0):
    """
    Solve for equiibirum vessel sink

    :param hydro_model: An instance of HydroAnalysis
    :param speed:
    :param x0: iterable, initial guess for the solution
    """
    bounds = optimize.Bounds([-15], [-0.01])  # sink limits

    res = optimize.minimize(objective_sink, [x0], args=(hydro_model, speed), method='SLSQP', jac='2-point', bounds=bounds)

    if not res.success:
        raise VPPSolverError("VPP Sink Failed to converge")

    return res.x[0]


def objective_sink(x, hydro_model, speed):
    """
    Solve for force equilibrium in the waterplane vertical axis
    """
    hydro_model.set_state(x[0], 0)
    cost = (hydro_model.force_moment_waterplane(speed).force()[1] / 1e7) ** 2

    return cost


def run_foil_aoa_vpp(hydrofoil, lift_target, speed, x0, aoa_lb=-25, aoa_ub=25):
    """
    Solve for angle of attack on a foil to achieve a desired force
    """
    bounds = optimize.Bounds([np.deg2rad(aoa_lb)], [np.deg2rad(aoa_ub)])  # sink limits

    res = optimize.minimize(objective_foil_aoa, [x0], args=(hydrofoil, speed, lift_target), method='SLSQP', jac='2-point',
                            bounds=bounds, options={'ftol': 1e-12})

    if not res.success:
        raise VPPSolverError("VPP Foil AoA Failed to converge")

    cost = objective_foil_aoa(res.x, hydrofoil, speed, lift_target)
    if cost > 0.1:  # [kN]
        raise VPPSolverError(f"VPP Foil AoA Failed to achieve Lift target {lift_target / 1000:.2f} kN")

    return res.x[0]


def objective_foil_aoa(x, hydrofoil, speed, lift_desired):
    """
    """
    px, pz, ry = hydrofoil.get_location()

    # Set foil angle-of attack (decision var x0)
    hydrofoil.set_location(px, pz, -x[0])

    fx, fz = hydrofoil.force_moment(speed).force()

    lift = fx * np.sin(x[0]) + fz * np.cos(x[0])

    cost = abs(lift - lift_desired) / 1e3  # lift error in kN

    return cost

