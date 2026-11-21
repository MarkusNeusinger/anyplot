"""anyplot.ai
andrews-curves: Andrews Curves for Multivariate Data
Library: pygal 3.1.3 | Python 3.14.10
Quality: pending | Updated: 2026-11-21
"""

import os
import sys

import numpy as np
import pandas as pd


# This file is named pygal.py: keep its own directory off sys.path so the real package imports
sys.path = [p for p in sys.path if p not in ("", ".")]

import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
CURVE_ALPHA = 0.7  # transparency so bundles of similar observations read as darker bands
CURVES_PER_GROUP = 15  # curves drawn per category, for clarity
T_POINTS = 200  # samples along t, dense enough that no corners show

# Columns: set these to your table's column names
SPECIES = "Species"  # role: category
VARIABLES = ["Sepal length (cm)", "Sepal width (cm)", "Petal length (cm)", "Petal width (cm)"]  # role: variable_

# Data: replace this block with your own table, for example df = pd.read_csv("iris.csv")
np.random.seed(42)
means = {"Setosa": (5.0, 3.4, 1.5, 0.2), "Versicolor": (5.9, 2.8, 4.3, 1.3), "Virginica": (6.6, 3.0, 5.5, 2.0)}
spreads = {
    "Setosa": (0.35, 0.38, 0.17, 0.10),
    "Versicolor": (0.52, 0.31, 0.47, 0.20),
    "Virginica": (0.64, 0.32, 0.55, 0.27),
}
frames = []
for name in means:
    columns = {
        col: np.random.normal(mu, sd, 50) for col, mu, sd in zip(VARIABLES, means[name], spreads[name], strict=True)
    }
    frames.append(pd.DataFrame({SPECIES: name, **columns}))
df = pd.concat(frames, ignore_index=True)

# Plot: reads only df and the constants above
# z-score each variable so none dominates the Fourier series
scaled = (df[VARIABLES] - df[VARIABLES].mean()) / df[VARIABLES].std(ddof=0)
t = np.linspace(-np.pi, np.pi, T_POINTS)


def andrews(row):
    """Andrews transform: f(t) = x1/sqrt(2) + x2 sin t + x3 cos t + x4 sin 2t + x5 cos 2t + ..."""
    values = np.full_like(t, row[0] / np.sqrt(2))
    for k, x in enumerate(row[1:]):
        harmonic = k // 2 + 1
        values += x * (np.sin(harmonic * t) if k % 2 == 0 else np.cos(harmonic * t))
    return values


def with_alpha(hex_color, alpha):
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (1, 3, 5))
    return f"rgba({r},{g},{b},{alpha})"


groups = list(dict.fromkeys(df[SPECIES]))

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=tuple(with_alpha(IMPRINT_PALETTE[i], CURVE_ALPHA) for i in range(len(groups))),
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=4,
)

chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title="andrews-curves · python · pygal · anyplot.ai",
    x_title="t (radians)",
    y_title="f(t), standardized variables",
    show_dots=False,
    stroke_style={"width": 4},
    show_x_guides=True,
    show_y_guides=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=len(groups),
    legend_box_size=36,
    truncate_legend=-1,
    margin=40,
)
chart.x_labels = [-np.pi, -np.pi / 2, 0, np.pi / 2, np.pi]
chart.x_value_formatter = lambda v: f"{v:.2f}"

for group in groups:
    members = scaled[(df[SPECIES] == group).fillna(False).to_numpy(dtype=bool)].dropna().to_numpy(dtype=float)
    picks = np.random.choice(len(members), min(CURVES_PER_GROUP, len(members)), replace=False)
    points = []
    for n, idx in enumerate(picks):
        if n:
            points.append(None)  # break between curves
        points.extend(zip(t.tolist(), andrews(members[idx]).tolist(), strict=True))
    chart.add(str(group), points, show_dots=False)

# Output
chart.render_to_file(f"plot-{THEME}.html")
chart.render_to_png(f"plot-{THEME}.png")
