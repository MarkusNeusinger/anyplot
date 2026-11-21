""" anyplot.ai
errorbar-asymmetric: Asymmetric Error Bars Plot
Library: pygal 3.1.3 | Python 3.14.10
Quality: 78/100 | Updated: 2026-11-21
"""

import os

import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: a single series uses position 1
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]

# Constants
CAP_HALF_WIDTH = 0.3  # half the cap length, in category-slot units
BOUNDS_LABEL = "Median (10th-90th percentile)"

# Columns: set these to your table's column names
MATERIAL = "Material"  # role: x
STRENGTH = "Tensile Strength (MPa)"  # role: y
ERROR_LOWER = "Lower error (MPa)"  # role: error_lower
ERROR_UPPER = "Upper error (MPa)"  # role: error_upper

# Data: replace this block with your own table, for example df = pd.read_csv("strength.csv")
df = pd.DataFrame(
    {
        MATERIAL: ["Steel", "Aluminum", "Titanium", "Copper", "Brass", "Bronze"],
        STRENGTH: [250, 150, 450, 200, 180, 220],
        ERROR_LOWER: [35, 12, 20, 25, 8, 18],
        ERROR_UPPER: [20, 28, 50, 15, 22, 30],
    }
)

# Plot
n = len(df)
low = df[STRENGTH] - df[ERROR_LOWER]
high = df[STRENGTH] + df[ERROR_UPPER]
span = high.max() - low.min()

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=(BRAND,) * (1 + 3 * n),  # one color for the points, bars and caps
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=2.5,
)

chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title="errorbar-asymmetric · python · pygal · anyplot.ai",
    x_title=MATERIAL,
    y_title=STRENGTH,
    show_legend=True,
    legend_at_bottom=True,
    show_y_guides=True,
    show_x_guides=False,
    print_values=False,
    margin=40,
    stroke=True,
    dots_size=12,
    range=(float(low.min() - 0.1 * span), float(high.max() + 0.1 * span)),
    xrange=(0, n + 1),
    x_labels=["", *df[MATERIAL]],
    x_labels_major_every=1,
    show_minor_x_labels=False,
    truncate_legend=-1,
    truncate_label=-1,
)

# Central values: markers only
points = [(i + 1, float(v)) for i, v in enumerate(df[STRENGTH])]
chart.add(BOUNDS_LABEL, points, stroke=False, dots_size=16)

# Error bars and caps: unnamed line series, kept out of the legend
for i in range(n):
    x = i + 1
    chart.add(None, [(x, float(low[i])), (x, float(high[i]))], show_dots=False, stroke_style={"width": 5})
    for y in (low[i], high[i]):
        chart.add(
            None,
            [(x - CAP_HALF_WIDTH, float(y)), (x + CAP_HALF_WIDTH, float(y))],
            show_dots=False,
            stroke_style={"width": 8},
        )

chart.render_to_file(f"plot-{THEME}.html")
chart.render_to_png(f"plot-{THEME}.png")
