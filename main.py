import csv
import json
import sys
import beams
import checks

N_POINTS = 101


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


#I am just trying this two times, one with normal loop and next with list comprehension which is just below this
def max_deflection_loop(func, d):
    values = []
    for i in range(N_POINTS):
        x = i * d["L"] / (N_POINTS - 1)
        values.append(func(x, d))
    return max(values)


def max_deflection(func, d):
    #Just for fun, using list comprehension for same result
    return max([func(i * d["L"] / (N_POINTS - 1), d) for i in range(N_POINTS)])


def run_cases(cfg):
    results = []
    for case in cfg["cases"]:
        func = beams.BEAM_FUNCTIONS[case]
        kind = beams.LOAD_KIND[case]
        loads = cfg["point_loads"] if kind == "point" else cfg["uniform_loads"]
        key = "P" if kind == "point" else "w"
        for L in cfg["spans"]:
            for load in loads:
                d = {"E": cfg["E"], "I": cfg["I"], "L": L, key: load,
                     "a": cfg["offcenter_fraction"] * L}
                y_loop = max_deflection_loop(func, d)
                y = max_deflection(func, d)
                if y_loop != y:
                    raise ValueError("loop and list comprehension disagree")
                results.append({"case": case, "d": d, "y": y, "load": load})
    return results


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


def print_check_table(results):
    table = {}

    def record(name, ok):
        table.setdefault(name, [0, 0])
        table[name][1] += 1
        if ok:
            table[name][0] += 1

    for r in results:
        case, d, y = r["case"], r["d"], r["y"]
        expected = checks.closed_form_max(case, d)
        if expected is not None:
            record(f"{case}: closed-form maximum", checks.close(y, expected))
        if case in ("ss_center", "ss_offcenter"):
            record(f"{case}: continuity at break", checks.continuity_ok(case, d))
            record(f"{case}: zero at both supports", checks.boundary_ok(case, d, y))

    print("\nSelf-check table:")
    print(f"  {'check':38s} {'passed':>7s}  result")
    for name, (passed, total) in table.items():
        result = "PASS" if passed == total else "FAIL"
        print(f"  {name:38s} {passed:>3d}/{total:<3d}  {result}")


def main():
    config_file = sys.argv[1] if len(sys.argv) > 1 else "config.json"
    try:
        cfg = load_config(config_file)
        validate(cfg)
        results = run_cases(cfg)
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

    save_csv(results, "results.csv")
    print(f"{len(results)} cases written to results.csv")
    rows = read_csv("results.csv")
    print_largest_per_beam(rows)
    print_check_table(results)


if __name__ == "__main__":
    main()
