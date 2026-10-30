import beams

TOL = 1e-9


def close(a, b, tol=TOL):
    return abs(a - b) <= tol * abs(b)


def closed_form_max(case, d):
    E, I, L = d["E"], d["I"], d["L"]
    if case == "ss_center":
        return d["P"] * L ** 3 / (48 * E * I)
    if case == "ss_udl":
        return 5 * d["w"] * L ** 4 / (384 * E * I)
    if case == "cant_end":
        return d["P"] * L ** 3 / (3 * E * I)
    if case == "cant_udl":
        return d["w"] * L ** 4 / (8 * E * I)
    return None


def continuity_ok(case, d):
    if case == "ss_center":
        xb = d["L"] / 2
        left, right = beams.ss_center_left(xb, d), beams.ss_center_right(xb, d)
    else:
        xb = d["a"]
        left, right = beams.ss_offcenter_left(xb, d), beams.ss_offcenter_right(xb, d)
    return close(left, right)


def boundary_ok(case, d, y_max):
    f = beams.BEAM_FUNCTIONS[case]
    return abs(f(0, d)) <= TOL * y_max and abs(f(d["L"], d)) <= TOL * y_max
