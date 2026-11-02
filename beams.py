"""Beam deflection formulas, NumPy version.

Every function takes x as a NumPy array (or a single number) and a dictionary d.
It returns deflection with the same shape as x. Downward deflection is positive.

The old loop version is kept in beams_loop.py for comparison.
"""
import numpy as np


def ss_center_left(x, d):
    return d["P"] * x * (3 * d["L"] ** 2 - 4 * x ** 2) / (48 * d["E"] * d["I"])


def ss_center_right(x, d):
    return ss_center_left(d["L"] - x, d)


def ss_center(x, d):
    # np.where(condition, value_if_true, value_if_false), decided point by point
    return np.where(x <= d["L"] / 2, ss_center_left(x, d), ss_center_right(x, d))


def ss_offcenter_left(x, d):
    L = d["L"]
    b = L - d["a"]
    return d["P"] * b * x * (L ** 2 - b ** 2 - x ** 2) / (6 * L * d["E"] * d["I"])


def ss_offcenter_right(x, d):
    L = d["L"]
    a = d["a"]
    return d["P"] * a * (L - x) * (2 * L * x - x ** 2 - a ** 2) / (6 * L * d["E"] * d["I"])


def ss_offcenter(x, d):
    return np.where(x <= d["a"], ss_offcenter_left(x, d), ss_offcenter_right(x, d))


def ss_udl(x, d):
    L = d["L"]
    return d["w"] * x * (L ** 3 - 2 * L * x ** 2 + x ** 3) / (24 * d["E"] * d["I"])


def cant_end(x, d):
    return d["P"] * x ** 2 * (3 * d["L"] - x) / (6 * d["E"] * d["I"])


def cant_udl(x, d):
    L = d["L"]
    return d["w"] * x ** 2 * (6 * L ** 2 - 4 * L * x + x ** 2) / (24 * d["E"] * d["I"])


BEAM_FUNCTIONS = {
    "ss_center": ss_center,
    "ss_offcenter": ss_offcenter,
    "ss_udl": ss_udl,
    "cant_end": cant_end,
    "cant_udl": cant_udl,
}

LOAD_KIND = {
    "ss_center": "point",
    "ss_offcenter": "point",
    "ss_udl": "uniform",
    "cant_end": "point",
    "cant_udl": "uniform",
}
