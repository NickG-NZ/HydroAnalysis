"""
Velocity and Pointing Program (VPP)
Solves for the equilibrium state of the given vessel configuration

Currently only 1D (sink)
"""
from scipy import optimize


class VPPSolverError(Exception):
    def __init__(self, message):
        super().__init__(message)


def run_vpp(hydro_model, speed, x0):
    """
    :param hydro_model: An instance of HydroAnalysis
    :param speed:
    :param x0: iterable, initial guess for the solution
    """
    bounds = optimize.Bounds([-15], [-0.01])  # sink limits

    res = optimize.minimize(objective, x0, args=(hydro_model, speed), method='SLSQP', jac='2-point', bounds=bounds)

    if not res.success:
        raise VPPSolverError("VPP Failed to converge")

    return res.x[0]


def objective(x, hydro_model, speed):
    """
    Solve for force equilibrium in the waterplane vertical axis
    """
    hydro_model.set_state(x[0], 0)
    cost = (hydro_model.force_moment_waterplane(speed).force()[1] / 1e7) ** 2

    return cost


