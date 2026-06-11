# PlotDrop

PlotDrop is a small Python desktop application for Linux and macOS. Drop numeric data files onto the window and PlotDrop draws the curves with Matplotlib.

## Features

- drag and drop local `.txt`, `.dat`, `.csv`, and `.tsv` files;
- plot multiple datasets in one Matplotlib figure;
- show loaded datasets with point counts and load status;
- switch axis scale between `linear`, `logx`, `logy`, and `loglog`;
- toggle a plot grid;
- use the native Matplotlib toolbar for zoom, pan, reset, and quick save;
- export the current figure as PNG, PDF, or SVG.

## Development install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Run

```bash
plotdrop
```

You can also open files from the File menu if drag and drop is inconvenient.

## Data format

Supported file extensions are `.txt`, `.dat`, `.csv`, and `.tsv`.

Rules:

- empty lines are ignored;
- anything after `#` is ignored, including inline comments;
- separators can be spaces, tabs, commas, or semicolons;
- decimal values must use a dot;
- one non-numeric header line is tolerated before the data starts;
- after numeric data starts, non-numeric lines are errors;
- `nan`, `inf`, and `-inf` are rejected.

With one numeric column, values are read as `y` and `x` is generated as `0, 1, 2, ...`.

```text
# one-column data
1.0
2.5
3.0
```

With two or more numeric columns, the first two columns are read as `x` and `y`.

```text
# x y
0.0 1.0
1.0 0.8
2.0 0.6
```

Example files are available in `examples/`.

## Export

The Export button saves the current figure exactly as displayed, including the current scale and grid setting. PNG is exported at 300 dpi. PDF and SVG are exported as vector formats.

## Tests

```bash
pytest
```
