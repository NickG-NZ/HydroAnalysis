"""
Basic lifting line analysis to capture trends
"""
import numpy as np
import matplotlib.pyplot as plt


def main():

    angle_of_attack = np.deg2rad(5)
    e = 0.8  # Oswald efficiency

    # Run aspect ratio sweep
    aspect_ratios = np.arange(1, 15, 0.5)

    ld_ratios = []
    cls = []
    cdis = []
    a_s = []
    for AR in aspect_ratios:

        # Lift slope
        a0 = dcl_dalpha_2d_plate()
        a = dcl_dalpha_finite(a0, AR, e)

        # Cl and Cdi
        cl = a * angle_of_attack
        cdi = cd_induced(cl, AR, e)

        ld = cl / cdi
        ld_ratios.append(ld)
        cls.append(cl)
        a_s.append(a)
        cdis.append(cdi)

    # Plot Cl, Cdi, L/D vs aspect ratio
    fig, ax = plt.subplots(3, 1)
    ax[0].scatter(aspect_ratios, a_s)
    ax[1].scatter(aspect_ratios, cdis)
    ax[2].scatter(aspect_ratios, ld_ratios)
    ylabels = ["dCL_dalpha", "CDi", "L/D"]
    for i in range(3):
        ax[i].set(xlabel="Aspect Ratio", ylabel=ylabels[i])
        ax[i].grid(True)

    plt.show()


def dcl_dalpha_finite(a0, aspect_ratio, e):
    """
    """
    if aspect_ratio < 4:
        return dcl_dalpha_helmbold(a0, aspect_ratio, e)
    else:
        return dcl_dalpha_prandtl(a0, aspect_ratio, e)


def dcl_dalpha_prandtl(a0, aspect_ratio, e):
    """
    Standard lifting line finite wing relationship
    """
    ratio = a0 / (np.pi * aspect_ratio * e)
    a = a0 / (1 + ratio)

    return a


def dcl_dalpha_helmbold(a0, aspect_ratio, e):
    """
    Corrects for low aspect ratios
    """
    ratio = a0 / (np.pi * aspect_ratio)
    a = a0 / (np.sqrt(1 + ratio ** 2) + ratio)

    return a


def dcl_dalpha_2d_plate():
    return 2 * np.pi


def cd_induced(cl, aspect_ratio, e):
    """
    """
    return (cl ** 2) / (np.pi * aspect_ratio * e)


if __name__ == "__main__":
    main()
