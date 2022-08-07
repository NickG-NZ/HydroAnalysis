import numpy as np
from scipy import optimize

import constants


def reynolds_number(speed, kinematic_viscosity, reference_length):
    """
    """
    return speed * reference_length / kinematic_viscosity


def froude_number(speed, reference_length):
    """
    """
    return speed / np.sqrt(constants.GRAVITY * reference_length)


def schoenherr_drag_coeff(Re, initial_guess):
    """
    Solve the non-linear equation defining the Schoenherr drag equation
    :param Re:
    :param initial_guess:
    """
    def schoenherr_error(x, Re):
        return 0.242 / np.sqrt(x) - np.log10(Re * x)

    cd_skin_friction = optimize.newton(schoenherr_error, initial_guess, args=(Re,))

    return cd_skin_friction


def propulsive_power(speed, drag, prop_efficiency=1.0):
    """
    Compute the propulsive power required
    Assumes speed and drag are both defined parallel to the waterplane

    Typical prop efficiencies are in the range 0.6-0.8
    """
    return speed * drag * prop_efficiency


def kts_to_mps(speed_kts):
    return speed_kts / 1.94384


def mps_to_kts(speed_mps):
    return speed_mps * 1.94384


def ft_to_m(ft):
    return ft * 0.3048
