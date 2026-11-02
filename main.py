import csv
import json
import os
import sys
import numpy as np
import pandas as pd
import beams
import checks
import plotting

N_POINTS = 101
OUTPUT_DIR = "outputs"
DAY2_RESULTS = "day2_results.csv"


def load_config(filename):
    with open(filename) as f:
        return json.load(f)


def validate(cfg):
    def is_number(value):
        return type(value) in (int, float)

    if type(cfg) is not dict:
        raise ValueError("config must be a JSON object")
    for key in ["E", "I", "offcenter_fraction"]:
        if not is_number(cfg[key]):
            raise ValueError(f"{key} must be a number, got {cfg[key]!r}")
    for key in ["spans", "point_loads", "uniform_loads", "cases"]:
        if type(cfg[key]) is not list:
            raise ValueError(f"'{key}' must be a list, got {cfg[key]!r}")
    for key in ["spans", "point_loads", "uniform_loads"]:
        for value in cfg[key]:
            if not is_number(value):
                raise ValueError(f"every value in '{key}' must be a number, got {value!r}")
    for key in ["spans", "cases"]:
        if len(cfg[key]) == 0:
            raise ValueError(f"'{key}' must not be empty")
    for key in ["E", "I"]:
        if cfg[key] <= 0:
            raise ValueError(f"{key} must be positive, got {cfg[key]}")
    for key in ["spans", "point_loads", "uniform_loads"]:
        for value in cfg[key]:
            if value <= 0:
                raise ValueError(f"every value in '{key}' must be positive, got {value}")
    if not 0 < cfg["offcenter_fraction"] < 1:
        raise ValueError("offcenter_fraction must be between 0 and 1")
    for name in cfg["cases"]:
        if name not in beams.BEAM_FUNCTIONS:
            raise ValueError(f"unknown beam case '{name}'")


def run_cases(cfg):
    """Returns (tables, results).
    tables:  one DataFrame per beam type (all spans, loads, positions, deflections)
    results: one entry per span/load combination, used by the checks
    """
    tables = {}
    results = []
    for case in cfg["cases"]:
        func = beams.BEAM_FUNCTIONS[case]
        kind = beams.LOAD_KIND[case]
        loads = cfg["point_loads"] if kind == "point" else cfg["uniform_loads"]
        key = "P" if kind == "point" else "w"
        unit = "N" if kind == "point" else "N/m"
        pieces = []
        for L in cfg["spans"]:
            x = np.linspace(0, L, N_POINTS)          # 101 positions from 0 to L
            for load in loads:
                d = {"E": cfg["E"], "I": cfg["I"], "L": L, key: load,
                     "a": cfg["offcenter_fraction"] * L}
                y = func(x, d)                        # whole array at once
                pieces.append(pd.DataFrame({
                    "beam_type": case, "span_m": L,
                    "load_value": load, "load_unit": unit,
                    "x_m": x, "deflection_m": y}))
                results.append({"case": case, "d": d, "load": load,
                                "x": x, "y_all": y, "y": y.max()})
        tables[case] = pd.concat(pieces, ignore_index=True)
    return tables, results


def save_tables(tables):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for case, table in tables.items():
        table.to_csv(f"{OUTPUT_DIR}/{case}.csv", index=False)


def make_plots(tables, cfg):
    for case, table in tables.items():
        kind = beams.LOAD_KIND[case]
        loads = cfg["point_loads"] if kind == "point" else cfg["uniform_loads"]
        unit = "N" if kind == "point" else "N/m"
        mid_load = loads[len(loads) // 2]            # middle load
        plotting.plot_beam(table, case, cfg["spans"], mid_load, unit)


def save_csv(results, filename):
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["beam_type", "span_m", "load_value", "load_unit",
                         "max_deflection_m"])
        for r in results:
            unit = "N" if beams.LOAD_KIND[r["case"]] == "point" else "N/m"
            writer.writerow([r["case"], r["d"]["L"], r["load"], unit, r["y"]])


def read_csv(filename):
    with open(filename) as f:
        return list(csv.DictReader(f))


def print_largest_per_beam(rows):
    print("\nLargest deflection for each beam type (read back from CSV):")
    for case in beams.BEAM_FUNCTIONS:
        best = None
        best_value = 0.0
        for row in rows:
            if row["beam_type"] == case:
                value = float(row["max_deflection_m"])
                if best is None or value > best_value:
                    best = row
                    best_value = value
        if best is None:       # no rows of this beam type in the file
            continue
        print(f"  {case:13s} span={best['span_m']} m  load={best['load_value']} "
              f"{best['load_unit']}  max deflection={best_value:.6e} m")


def compare_with_day2(new_file, old_file):
    """True/False: do new maxima equal Day 2 maxima? None if no Day 2 file."""
    if not os.path.exists(old_file):
        return None
    new = pd.read_csv(new_file)
    old = pd.read_csv(old_file)
    if len(new) != len(old):
        return False
    same_rows = (new["beam_type"] == old["beam_type"]).all() and \
                np.allclose(new["span_m"], old["span_m"]) and \
                np.allclose(new["load_value"], old["load_value"])
    same_values = np.allclose(new["max_deflection_m"], old["max_deflection_m"],
                              rtol=checks.TOL, atol=0)
    return bool(same_rows and same_values)


def print_check_table(results):
    table = {}

    def record(name, ok):
        table.setdefault(name, [0, 0])
        table[name][1] += 1
        if ok:
            table[name][0] += 1

    for r in results:
        case, d, y = r["case"], r["d"], r["y"]
        expected, tol = checks.closed_form_max(case, d)
        if expected is not None:
            label = "closed-form maximum"
            if case == "ss_offcenter":
                label = "closed-form maximum (grid tol)"
            record(f"{case}: {label}", checks.close(y, expected, tol))
        if case in ("ss_center", "ss_offcenter"):
            record(f"{case}: continuity at break", checks.continuity_ok(case, d))
            record(f"{case}: zero at both supports", checks.boundary_ok(r["y_all"], y))
        if case == "ss_center":
            record("ss_center: value at L/4 and 3L/4", checks.quarter_point_ok(d, r["y_all"]))
        if case in ("ss_center", "ss_udl"):
            record(f"{case}: symmetric about L/2", checks.symmetric_ok(r["y_all"]))
        record(f"{case}: array equals Day 2 loop code", checks.matches_loop(case, d, r["x"], r["y_all"]))

    print("\nSelf-check table:")
    print(f"  {'check':42s} {'passed':>7s}  result")
    for name, (passed, total) in table.items():
        result = "PASS" if passed == total else "FAIL"
        print(f"  {name:42s} {passed:>3d}/{total:<3d}  {result}")


def main():
    config_file = sys.argv[1] if len(sys.argv) > 1 else "config.json"
    try:
        cfg = load_config(config_file)
        validate(cfg)
        tables, results = run_cases(cfg)
    except FileNotFoundError:
        print(f"Error: config file '{config_file}' not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: '{config_file}' is not valid JSON.")
        return
    except KeyError as e:
        print(f"Error: config is missing the key {e}.")
        return
    except ValueError as e:
        print(f"Error: {e}")
        return

    try:
        save_csv(results, "results.csv")
        save_tables(tables)
    except PermissionError as e:
        print(f"Error: cannot write '{e.filename}'. Is it open in Excel?")
        return
    print(f"{len(results)} cases written to results.csv")
    print(f"{len(tables)} tables written to {OUTPUT_DIR}/ (one CSV per beam type)")

    rows = read_csv("results.csv")
    print_largest_per_beam(rows)
    print_check_table(results)

    same = compare_with_day2("results.csv", DAY2_RESULTS)
    if same is None:
        print(f"\nDay 2 comparison skipped: '{DAY2_RESULTS}' not found.")
    else:
        print("\nMaxima match Day 2 results.csv (np.allclose):", "PASS" if same else "FAIL")

    make_plots(tables, cfg)
    print(f"{len(tables)} plots saved to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
