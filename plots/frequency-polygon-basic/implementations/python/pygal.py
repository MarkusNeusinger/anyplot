""" anyplot.ai
frequency-polygon-basic: Frequency Polygon for Distribution Comparison
Library: pygal 3.1.3 | Python 3.14.10
Quality: 79/100 | Updated: 2026-11-22
"""

import os

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
N_BINS = 14  # bins shared by every group

# Columns: set these to your table's column names
HEIGHT = "Plant Height (cm)"  # role: values
SOIL = "Soil type"  # role: group

# Data: replace this block with your own table, for example df = pd.read_csv("plants.csv")
np.random.seed(42)
df = pd.DataFrame(
    {
        HEIGHT: np.concatenate(
            [
                np.random.normal(loc=45, scale=8, size=200),
                np.random.normal(loc=55, scale=10, size=200),
                np.random.normal(loc=60, scale=6, size=200),
            ]
        ),
        SOIL: ["Sandy Soil"] * 200 + ["Loamy Soil"] * 200 + ["Clay Soil"] * 200,
    }
)

# Plot: reads only df and the constants above
edges = np.linspace(20, 85, N_BINS + 1)
midpoints = (edges[:-1] + edges[1:]) / 2
# Extend each polygon to zero at both ends so it closes on the baseline
xs = [float(edges[0])] + [float(m) for m in midpoints] + [float(edges[-1])]

series = {}
for group, values in df.groupby(SOIL, sort=False)[HEIGHT]:
    counts, _ = np.histogram(values.dropna(), bins=edges)
    series[group] = [0] + [int(c) for c in counts] + [0]
top = max(max(freqs) for freqs in series.values())

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT_PALETTE,
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    opacity=0.8,
    opacity_hover=1.0,
)

chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title="frequency-polygon-basic · python · pygal · anyplot.ai",
    x_title=HEIGHT,
    y_title="Frequency",
    show_x_guides=True,
    show_y_guides=True,
    dots_size=7,
    stroke_style={"width": 3},
    legend_at_bottom=True,
    show_dots=True,
    fill=True,
    x_label_rotation=0,
    range=(0, top + 5),
    xrange=(edges[0] - 5, edges[-1] + 5),
)

for group, freqs in series.items():
    chart.add(str(group), list(zip(xs, freqs, strict=True)))

chart.render_to_png(f"plot-{THEME}.png")
chart.render_to_file(f"plot-{THEME}.html")
