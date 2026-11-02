# Beam Deflection Toolkit

Computes the deflection of five beam types over a range of spans and loads,
writes the largest deflection of every case to a CSV file, and checks the
results against closed-form solutions.

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
- No third-party packages; only the standard library (`csv`, `json`, `sys`)

## Installation

Download or clone this repository and open a terminal in the project folder.
There is nothing to install.

## Usage

Run with the default configuration:

    python main.py

Run with another configuration file:

    python main.py path/to/other_config.json

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
configuration gives 5 cases x 3 spans x 3 loads = 45 rows.

## Output

`results.csv` has one row per case, with the columns `beam_type`, `span_m`,
`load_value`, `load_unit` and `max_deflection_m`. The maximum is the largest
deflection found at 101 equally spaced points along the span.

The console also prints the largest deflection for each beam type and a
self-check table:

- closed-form maximum (not available for `ss_offcenter`)
- continuity of the deflection at the load point (`ss_center`, `ss_offcenter`)
- zero deflection at both supports (`ss_center`, `ss_offcenter`)

`results.csv` is regenerated on every run and is not stored in the repository.

## Invalid input

A bad configuration is rejected with a one-line error message. Examples are in
`broken_configs/`:

    python main.py broken_configs/negative_I.json

## Files

- `main.py`: reads the config, validates it, runs all cases, writes the CSV
- `beams.py`: the deflection function for each beam type
- `checks.py`: the closed-form checks used in the self-check table
- `config.json`: default input
- `broken_configs/`: deliberately invalid inputs for testing error handling

## Tests

    python test_validation.py

Runs every file in `broken_configs/` through `validate()` and checks that each
one is rejected with a clear error, and that `config.json` is still
accepted. Prints `all checks passed` on success.
