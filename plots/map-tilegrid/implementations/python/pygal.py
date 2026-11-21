"""anyplot.ai
map-tilegrid: Tile Grid Map for Equal-Area Geographic Comparison
Library: pygal 3.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-11-21
"""

import os
import sys


sys.path.pop(0)  # remove script dir so "import pygal" finds the installed package, not this file

import matplotlib.colors as mcolors
import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: sequential ramp for unipolar data (brand green -> blue)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
imprint_seq = mcolors.LinearSegmentedColormap.from_list("imprint_seq", ["#009E73", "#4467A3"])

# Constants
N_BINS = 5  # value classes in the colour key

# Column constants
REGION = "State"  # role: region
VALUE = "Renewable share of electricity (%)"  # role: value
ROW = "Grid row"  # role: row
COL = "Grid column"  # role: col

# Data: replace this block with your own table, for example df = pd.read_csv("tiles.csv")
# US state tile grid positions (row, col), a geographic approximation
state_grid = {
    "AK": (0, 0),
    "ME": (0, 10),
    "WA": (1, 1),
    "MT": (1, 2),
    "ND": (1, 3),
    "MN": (1, 4),
    "WI": (1, 5),
    "VT": (1, 9),
    "NH": (1, 10),
    "OR": (2, 1),
    "ID": (2, 2),
    "WY": (2, 3),
    "SD": (2, 4),
    "IA": (2, 5),
    "MI": (2, 6),
    "NY": (2, 7),
    "MA": (2, 9),
    "RI": (2, 10),
    "CA": (3, 1),
    "NV": (3, 2),
    "CO": (3, 3),
    "NE": (3, 4),
    "IL": (3, 5),
    "IN": (3, 6),
    "OH": (3, 7),
    "PA": (3, 8),
    "NJ": (3, 9),
    "CT": (3, 10),
    "AZ": (4, 2),
    "UT": (4, 3),
    "KS": (4, 4),
    "MO": (4, 5),
    "KY": (4, 6),
    "WV": (4, 7),
    "VA": (4, 8),
    "MD": (4, 9),
    "DE": (4, 10),
    "NM": (5, 3),
    "OK": (5, 4),
    "AR": (5, 5),
    "TN": (5, 6),
    "NC": (5, 7),
    "SC": (5, 8),
    "TX": (6, 4),
    "LA": (6, 5),
    "MS": (6, 6),
    "AL": (6, 7),
    "GA": (6, 8),
    "HI": (7, 1),
    "FL": (7, 9),
}
# Synthetic renewable energy share of electricity generation, with real-world anchors
np.random.seed(42)
state_values = {s: round(float(np.random.uniform(18, 78)), 1) for s in state_grid}
state_values.update(
    {
        "WA": 88.2,  # Pacific Northwest hydropower
        "OR": 72.1,
        "ID": 81.5,
        "MT": 65.3,
        "WY": 18.5,  # coal-heavy states
        "WV": 12.3,
        "KY": 15.7,
        "TX": 24.8,
        "LA": 20.4,
        "MS": 18.9,
        "CA": 52.3,
        "ND": 41.8,
        "SD": 76.4,  # high hydro + wind
    }
)
df = pd.DataFrame(
    {
        REGION: list(state_grid),
        VALUE: [state_values[s] for s in state_grid],
        ROW: [rc[0] for rc in state_grid.values()],
        COL: [rc[1] for rc in state_grid.values()],
    }
)

# Plot
# Quintile classes: five steps of the sequential ramp, low to high
edges = np.percentile(df[VALUE], np.linspace(0, 100, N_BINS + 1)[1:-1])
df["bin"] = np.digitize(df[VALUE], edges)
bin_hex = [mcolors.to_hex(imprint_seq(t)).upper() for t in np.linspace(0, 1, N_BINS)]
bin_labels = (
    [f"< {edges[0]:.0f}%"]
    + [f"{lo:.0f}–{hi:.0f}%" for lo, hi in zip(edges[:-1], edges[1:], strict=True)]
    + [f"> {edges[-1]:.0f}%"]
)

# One stacked-bar series per grid row (bottom row first); every cell has height 1,
# so each column stacks equally sized square tiles. Empty cells are page-coloured.
n_rows = int(df[ROW].max()) + 1
n_cols = int(df[COL].max()) + 1
cells = {}
for _, rec in df.iterrows():
    cells[(int(rec[ROW]), int(rec[COL]))] = (rec[REGION], int(rec["bin"]), rec[VALUE])

style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=tuple([PAGE_BG] * n_rows + bin_hex),
    title_font_size=66,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=48,
    value_font_size=62,
    value_label_font_size=62,
    value_colors=tuple(["#FFFFFF"] * n_rows),
    opacity=1,
    opacity_hover=1,
    stroke_width=0,
)

chart = pygal.StackedBar(
    width=3200,
    height=1800,
    title="map-tilegrid · python · pygal · anyplot.ai",
    print_labels=True,
    show_x_labels=False,
    show_y_labels=False,
    show_x_guides=False,
    show_y_guides=False,
    legend_at_bottom=True,
    legend_at_bottom_columns=N_BINS,
    legend_box_size=44,
    margin=40,
    margin_left=460,
    margin_right=460,
    spacing=24,
    css=[
        "file://style.css",
        "file://graph.css",
        f"inline:.bar{{stroke:{PAGE_BG};stroke-width:10px}} text.label{{text-anchor:middle;font-weight:bold}}",
    ],
    style=style,
)
chart.x_labels = list(range(n_cols))

for r in range(n_rows - 1, -1, -1):
    points = []
    for c in range(n_cols):
        if (r, c) in cells:
            name, b, val = cells[(r, c)]
            points.append({"value": 1, "color": bin_hex[b], "label": name})
        else:
            points.append({"value": 1, "color": PAGE_BG, "label": ""})
    chart.add(None, points)

# Colour key: the legend entries are empty series, one per value class
for lab in bin_labels:
    chart.add(lab, [None] * n_cols)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
