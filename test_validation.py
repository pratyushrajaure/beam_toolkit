import json
import os
import sys
import main


def result_for(path):
    with open(path) as f:
        cfg = json.load(f)
    try:
        main.validate(cfg)
    except ValueError:
        return "rejected"
    except Exception as e:
        return "CRASH " + type(e).__name__
    return "accepted"


def check(label, result, expected):
    ok = result == expected
    print(f"  {label:22s} {result:14s} {'PASS' if ok else 'FAIL'}")
    return ok


def run_tests():
    failures = 0
    for name in sorted(os.listdir("broken_configs")):
        result = result_for("broken_configs/" + name)
        if not check(name, result, "rejected"):
            failures += 1
    if not check("config.json", result_for("config.json"), "accepted"):
        failures += 1
    return failures


failures = run_tests()
if failures > 0:
    print(f"{failures} check(s) failed")
    sys.exit(1)
print("all checks passed")
