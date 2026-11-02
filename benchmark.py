"""Speed of the loop version (beams_loop) against the NumPy version (beams)."""
import json
import time
import numpy as np
import beams
import beams_loop

N = 1_000_000

with open("config.json") as f:
    cfg = json.load(f)

L = cfg["spans"][0]
d = {"E": cfg["E"], "I": cfg["I"], "L": L, "P": cfg["point_loads"][0],
     "a": cfg["offcenter_fraction"] * L}

x = np.linspace(0, L, N)
x_list = x.tolist()            # plain Python floats for the loop version

for case in ["ss_center", "ss_offcenter"]:
    loop_func = beams_loop.BEAM_FUNCTIONS[case]
    numpy_func = beams.BEAM_FUNCTIONS[case]

    t0 = time.perf_counter()
    y_loop = [loop_func(xi, d) for xi in x_list]
    t_loop = time.perf_counter() - t0

    t_numpy = 1e9
    for _ in range(5):                       # NumPy is fast, so take the best of 5
        t0 = time.perf_counter()
        y_numpy = numpy_func(x, d)
        t_numpy = min(t_numpy, time.perf_counter() - t0)

    same = np.allclose(y_numpy, y_loop, rtol=1e-9, atol=1e-12 * y_numpy.max())
    print(f"{case}: {N} points")
    print(f"  loop  : {t_loop:.3f} s")
    print(f"  numpy : {t_numpy * 1000:.1f} ms")
    print(f"  speed-up: {t_loop / t_numpy:.0f} times,  results equal: {same}")
