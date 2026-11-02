# Beam Deflection Toolkit

Computes the deflection of five beam types over a range of spans and loads
using NumPy arrays. For every beam type it writes a CSV table with all
positions and deflections and a plot of the deflection curves. It also writes
the largest deflection of every case to `results.csv` and checks the results
against closed-form solutions and against the earlier loop based version.

## Beam types

Set in `config.json` under `cases`. `x` is measured from the left end.

| Name | Beam |
|---|---|
| `ss_center` | simply supported, point load at midspan |
| `ss_offcenter` | simply supported, point load at distance a = offcenter_fraction * L from the left support |
| `ss_udl` | simply supported, uniform load over the whole span |
| `cant_end` | cantilever fixed at x = 0, point load at the free end |
| `cant_udl` | cantilever fixed at x = 0, uniform load over the whole span |

## Requirements

- Python 3 (developed on 3.13)
- NumPy, pandas and Matplotlib (versions are listed in `requirements.txt`)

## Installation

Clone this repository, open a terminal in the project folder, create a
virtual environment and install the packages:

    python -m venv .venv
    source .venv/Scripts/activate
    pip install -r requirements.txt

The `activate` line is for Git Bash on Windows. In Command Prompt or PowerShell
use `.venv\Scripts\activate`. On Linux or macOS use `source .venv/bin/activate`.
Activate the environment again in every new terminal.

## Usage

Run with the default configuration:

    python main.py

Run with another configuration file:

    python main.py path/to/other_config.json

Every plot opens in its own window; close it to continue to the next one. To
only save the figures, set `SHOW_PLOTS = False` at the top of `plotting.py`.

On Windows, if `python` is not found, use `py` instead.

## Configuration

`config.json` has these keys. All numbers must be positive.

| Key | Meaning | Unit |
|---|---|---|
| `E` | Young's modulus | Pa |
| `I` | second moment of area | m^4 |
| `spans` | list of beam spans L | m |
| `point_loads` | list of point loads P | N |
| `uniform_loads` | list of uniform loads w | N/m |
| `offcenter_fraction` | load position for `ss_offcenter`, between 0 and 1 | none |
| `cases` | list of beam types to run | none |

Every case is run for every span and every load of its kind, so the default
configuration gives 5 cases x 3 spans x 3 loads = 45 rows in `results.csv`.
Each span is divided into 101 equally spaced positions with
`np.linspace(0, L, 101)`.

## Output

Everything below is regenerated on every run and is not stored in the
repository.

- `outputs/<beam_type>.csv`: one table per beam type with the columns
  `beam_type`, `span_m`, `load_value`, `load_unit`, `x_m` and `deflection_m`.
  The default configuration gives 3 spans x 3 loads x 101 positions = 909 rows.
- `outputs/<beam_type>.png`: one plot per beam type. It shows the three spans
  under the middle load, with the maximum of each span marked. The y axis is
  inverted, so downward deflection is drawn downward. Deflection is in mm.
- `results.csv`: one row per case, with the columns `beam_type`, `span_m`,
  `load_value`, `load_unit` and `max_deflection_m`.

The console also prints the largest deflection for each beam type and a
self-check table:

- closed-form maximum (for `ss_offcenter` the maximum lies between two grid
  points, so a looser tolerance of 1e-4 is used there)
- continuity of the deflection at the load point (`ss_center`, `ss_offcenter`)
- zero deflection at both supports (`ss_center`, `ss_offcenter`)
- hand-calculated value at L/4 and 3L/4 (`ss_center`)
- symmetry about midspan (`ss_center`, `ss_udl`)
- NumPy result equals the loop version at every point (all cases)

Finally the maxima are compared with `day2_results.csv`, the saved results of
the first version of this toolkit.

## Invalid input

A bad configuration is rejected with a one-line error message. Examples are in
`broken_configs/`:

    python main.py broken_configs/negative_I.json

If an output file cannot be written, for example because it is open in Excel,
the program prints an error and stops.

## Speed comparison

    python benchmark.py

Times the loop version (`beams_loop.py`) against the NumPy version (`beams.py`)
on one million positions and checks that both give the same values.

## Files

- `main.py`: reads the config, validates it, runs all cases, writes the tables, plots and CSV
- `beams.py`: the deflection function for each beam type, using NumPy arrays
- `beams_loop.py`: the earlier loop based version, kept for comparison
- `checks.py`: the closed-form and array checks used in the self-check table
- `plotting.py`: one plot per beam type
- `benchmark.py`: speed comparison of loop and NumPy versions
- `config.json`: default input
- `day2_results.csv`: results of the first version, used as a reference
- `requirements.txt`: package versions
- `broken_configs/`: deliberately invalid inputs for testing error handling
- `test_validation.py`: tests for config validation

## Tests

    python test_validation.py

Runs every file in `broken_configs/` through `validate()` and checks that each
one is rejected with a clear error, and that `config.json` is still
accepted. Prints `all checks passed` on success.
