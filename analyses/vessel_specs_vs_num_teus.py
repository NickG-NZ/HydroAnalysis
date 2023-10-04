"""
Fit plots to vessel size specs vs num teus
"""
import sys, os

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir))

import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

from utils import *

TEU_LENGTH = ft_to_m(20)
TEU_WIDTH = ft_to_m(8)
TEU_HEIGHT = ft_to_m(8)
TEU_MASS = 18  # [T]

PLOT = True

def main():
    lookup_size = 40  # TEUs

    vessel_mass(lookup_size, plot=PLOT)
    vessel_length(lookup_size, plot=PLOT)
    vesel_aspect_ratio(lookup_size, plot=PLOT)
    vessel_draft(lookup_size, plot=PLOT)


def vessel_mass(lookup_size, plot=True):
    num_teus = np.array([150, 300, 365, 442, 537, 608, 803, 957, 1338])
    masses = [2750, 4081, 7000, 7000, 8100, 8150, 10500, 11768, 17230]  # [T]

    # linear fit
    fit = stats.linregress(num_teus, masses)
    line = fit.slope * num_teus + fit.intercept

    if plot:
        fig, ax = plt.subplots()
        ax.scatter(num_teus, masses)
        ax.plot(num_teus, line)
        ax.set(xlabel="Num Teu", ylabel="Mass [T]")
        ax.grid(True)

        plt.show()

    print(f"Mass from fit for {lookup_size} TEUs = {fit.slope * lookup_size + fit.intercept:.0f} T")

    if lookup_size == 4:
        print(f"Mass from containers {TEU_MASS * lookup_size * 2.5:.1f} T")

    elif lookup_size == 18:
        print(f"Mass from containers {TEU_MASS * lookup_size * 1.8:.1f} T")

    elif lookup_size == 40:
        print(f"Mass from containers {TEU_MASS * lookup_size * 1.2:.1f} T")


def vessel_length(lookup_size, plot=True):
    num_teus = np.array([150, 300, 365, 442, 537, 608, 803, 1005])

    lengths_ft = [262.5, 307.7, 328.1, 331.8, 393.4, 379.6, 461.9, 508.2]
    lengths = ft_to_m(np.array(lengths_ft))

    # linear fit
    fit = stats.linregress(num_teus, lengths)
    line = fit.slope * num_teus + fit.intercept

    if plot:
        fig, ax = plt.subplots()
        ax.scatter(num_teus, lengths)
        ax.plot(num_teus, line)
        ax.set(xlabel="Num Teu", ylabel="Length [m]")
        ax.grid(True)

        plt.show()

    print(f"Length from fit for {lookup_size} TEUs = {fit.slope * lookup_size + fit.intercept:.0f} m")

    if lookup_size == 4:
        N_longways = 2
        print(f"Length from container sizing = {N_longways * TEU_LENGTH * 1.4:.0f} m")

    elif lookup_size == 18:
        N_longways = 3
        print(f"Length from container sizing = {N_longways * TEU_LENGTH * 1.4:.0f} m")

    elif lookup_size == 40:
        N_longways = 4
        print(f"Length from container sizing = {N_longways * TEU_LENGTH * 1.4:.0f} m")


def vesel_aspect_ratio(lookup_size, plot=True):
    """
    Length / Beam
    """
    num_teus = np.array([150, 300, 365, 442, 537, 803, 1005])

    lengths_ft = [262.5, 307.7, 328.1, 331.8, 393.4, 461.9, 508.2]
    beams_ft = [52.5, 51.2, 52.2, 61.7, 71.5, 71.5, 70.5]

    aspect_ratios = np.array(lengths_ft) / np.array(beams_ft)

    # linear fit
    fit = stats.linregress(num_teus, aspect_ratios)
    line = fit.slope * num_teus + fit.intercept

    if plot:
        fig, ax = plt.subplots()
        ax.scatter(num_teus, aspect_ratios)
        ax.plot(num_teus, line)
        ax.set(xlabel="Num Teu", ylabel="Aspect Ratio")
        ax.grid(True)

        plt.show()

    print(f"AR from fit for {lookup_size} TEUs = {fit.slope * lookup_size + fit.intercept:.1f}")

    if lookup_size == 4:
        print(f"AR from container sizing = {1.4 * TEU_LENGTH / TEU_WIDTH:.1f}")

    elif lookup_size == 18:
        print(f"AR from container sizing = {1.4 * 3 * TEU_LENGTH / (3 * TEU_WIDTH):.1f}")

    elif lookup_size == 40:
        print(f"AR from container sizing = {1.4 * 4 * TEU_LENGTH / (5 * TEU_WIDTH):.1f}")


def vessel_draft(lookup_size, plot=True):
    num_teus = np.array([150, 300, 365, 442, 537, 608, 803, 957])

    drafts_ft = [13.1, 17.4, 16.4, 24, 17.1, 21.3, 24, 28.9]
    drafts = ft_to_m(np.array(drafts_ft))

    # linear fit
    fit = stats.linregress(num_teus, drafts)
    line = fit.slope * num_teus + fit.intercept

    if plot:
        fig, ax = plt.subplots()
        ax.scatter(num_teus, drafts)
        ax.plot(num_teus, line)
        ax.set(xlabel="Num Teu", ylabel="Draft [m]")
        ax.grid(True)

        plt.show()

    print(f"Draft from fit for {lookup_size} TEUs = {fit.slope * lookup_size + fit.intercept:.1f}")

    if lookup_size == 4:
        print(f"Draft from container sizing = {TEU_HEIGHT:.1f}")

    elif lookup_size == 18:
        print(f"Draft from container sizing = {1.4 * TEU_HEIGHT:.1f}")

    elif lookup_size == 40:
        print(f"Draft from container sizing = {1.8 * TEU_HEIGHT:.1f}")



if __name__ == "__main__":
    main()
