import os
import matplotlib.pyplot as plt

SHOW_PLOTS = True      # True: window opens for every beam type. False: only save.


def plot_beam(table, beam_name, spans, mid_load, unit):
    plt.figure(figsize=(9, 5))

    for L in spans:
        part = table[(table["span_m"] == L) & (table["load_value"] == mid_load)]
        x = part["x_m"].values                     # metres
        y = part["deflection_m"].values * 1000     # metres to millimetres

        i = y.argmax()                             # index of the maximum
        line, = plt.plot(x, y, label=f"L = {L} m  (max {y[i]:.2f} mm)")
        plt.plot(x[i], y[i], "o", color=line.get_color())   # marker at the maximum

    plt.xlabel("Position x (m)")
    plt.ylabel("Deflection y (mm)")
    plt.title(f"{beam_name}, load = {mid_load} {unit}")
    plt.legend()
    plt.grid(True)
    plt.gca().invert_yaxis()                       # downward deflection plotted downward

    os.makedirs("outputs", exist_ok=True)
    plt.savefig(f"outputs/{beam_name}.png", dpi=150)   # save BEFORE show
    if SHOW_PLOTS:
        plt.show()
    plt.close()
