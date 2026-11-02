import numpy as np
import beams
import beams_loop

TOL = 1e-9
GRID_TOL = 1e-4   # for maxima that fall between grid points (see closed_form_max)


def close(a, b, tol=TOL):
    return bool(np.isclose(a, b, rtol=tol, atol=0))


def closed_form_max(case, d):
    """Returns (theoretical maximum, tolerance to use on a 101 point grid)."""
    E, I, L = d["E"], d["I"], d["L"]
    if case == "ss_center":
        return d["P"] * L ** 3 / (48 * E * I), TOL
    if case == "ss_udl":
        return 5 * d["w"] * L ** 4 / (384 * E * I), TOL
    if case == "cant_end":
        return d["P"] * L ** 3 / (3 * E * I), TOL
    if case == "cant_udl":
        return d["w"] * L ** 4 / (8 * E * I), TOL
    if case == "ss_offcenter":
        # Maximum lies in the longer segment, at x = sqrt((L^2 - c^2)/3) from the
        # far support, where c is the shorter distance from the load to a support.
        # That x is not a grid point, so the grid maximum is slightly smaller.
        c = min(d["a"], L - d["a"])
        y = d["P"] * c * (L ** 2 - c ** 2) ** 1.5 / (9 * 3 ** 0.5 * L * E * I)
        return y, GRID_TOL
    return None, TOL


def continuity_ok(case, d):
    if case == "ss_center":
        xb = d["L"] / 2
        left, right = beams.ss_center_left(xb, d), beams.ss_center_right(xb, d)
    else:
        xb = d["a"]
        left, right = beams.ss_offcenter_left(xb, d), beams.ss_offcenter_right(xb, d)
    return close(left, right)


def boundary_ok(y_all, y_max):
    # first and last element of the array are x = 0 and x = L
    return abs(y_all[0]) <= TOL * y_max and abs(y_all[-1]) <= TOL * y_max


def symmetric_ok(y_all):
    # y_all[::-1] is the array read backwards; a symmetric beam equals its mirror
    return bool(np.allclose(y_all, y_all[::-1], rtol=TOL, atol=0))


def quarter_point_ok(d, y_all):
    # Hand value for ss_center: y(L/4) = 11 P L^3 / (768 E I). Index 25 of 101 points.
    expected = 11 * d["P"] * d["L"] ** 3 / (768 * d["E"] * d["I"])
    return close(y_all[25], expected) and close(y_all[75], expected)


def matches_loop(case, d, x, y_all):
    """New array result against the Day 2 loop code, point by point."""
    old_func = beams_loop.BEAM_FUNCTIONS[case]
    y_old = np.array([old_func(xi, d) for xi in x])
    # atol is needed because values at the supports are 0 or almost 0
    return bool(np.allclose(y_all, y_old, rtol=TOL, atol=1e-12 * y_all.max()))
