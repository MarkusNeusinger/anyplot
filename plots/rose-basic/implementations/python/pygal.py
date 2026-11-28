"""anyplot.ai
rose-basic: Basic Rose Chart
Library: pygal 3.1.3 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-27
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

# Imprint palette: all eight positions, first is the brand green
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
STEPS = 24  # radar points per wedge: sets the angular resolution of the outer arc (even)
HEADROOM = 1.03  # share of the largest value kept free beyond the longest wedge

# Columns: set these to your table's column names
MONTH = "Month"  # role: category
RAINFALL = "Rainfall (mm)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("rainfall.csv")
df = pd.DataFrame(
    {
        MONTH: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        RAINFALL: [145, 115, 95, 65, 45, 35, 20, 25, 50, 90, 135, 155],
    }
)


# Plot
# A Radar chart with STEPS points per category: each month is its own series that holds its value
# across the points of its wedge and zero elsewhere, so the filled series reads as a pie-slice wedge.
# pygal's radar runs counter-clockwise, so month m is centred at point -m * STEPS to read clockwise.
n_cat = len(df)
n_points = n_cat * STEPS
half = STEPS // 2
x_labels = [""] * n_points
for m, name in enumerate(df[MONTH]):
    x_labels[(-m * STEPS) % n_points] = name

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    guide_stroke_color=INK_MUTED,
    major_guide_stroke_color=INK_MUTED,
    colors=[IMPRINT_PALETTE[0]] * len(df),  # one brand-green wedge per category
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=56,
    stroke_width=3,
    opacity=0.5,
    opacity_hover=0.88,
)

chart = pygal.Radar(
    width=2400,
    height=2400,
    style=custom_style,
    title="rose-basic · python · pygal · anyplot.ai",
    fill=True,
    stroke=True,
    show_dots=False,
    show_legend=False,
    show_x_guides=True,
    show_minor_x_labels=False,
    show_y_guides=True,
    range=(0, df[RAINFALL].max() * HEADROOM),
    margin=70,
    value_formatter=lambda v: f"{v:.0f} mm",
)

chart.x_labels = x_labels
chart.x_labels_major = df[MONTH].tolist()
for m, (name, value) in enumerate(zip(df[MONTH], df[RAINFALL], strict=True)):
    wedge = [0] * n_points
    for k in range(-half, half + 1):
        wedge[(-m * STEPS + k) % n_points] = value
    chart.add(name, wedge)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
