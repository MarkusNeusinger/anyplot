"""anyplot.ai
density-basic: Basic Density Plot
Library: pygal 3.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-30
"""

import sys


# Remove script directory from sys.path so "import pygal" resolves to the installed package,
# not this file itself (which would cause a circular import on the script's own name).
if sys.path and sys.path[0]:
    sys.path.pop(0)

import os

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens — Imprint palette, theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint categorical palette — first series always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set this to your table's column name
RENT = "Monthly rent (EUR)"  # role: values

# Data: replace this block with your own table, for example df = pd.read_csv("rents.csv")
# Apartment asking rents in one city: right-skewed, most flats cheap, a long thin tail of expensive ones
rng = np.random.default_rng(42)
df = pd.DataFrame({RENT: np.round(rng.lognormal(mean=6.9, sigma=0.35, size=260))})

# Plot: KDE with Gaussian kernel and Scott's rule bandwidth
rents = df[RENT].dropna().to_numpy(dtype=float)
n = len(rents)
bandwidth = n ** (-1 / 5) * np.std(rents, ddof=1)
x_grid = np.linspace(rents.min() - 2 * bandwidth, rents.max() + 2 * bandwidth, 400)
density = np.exp(-0.5 * ((x_grid[:, None] - rents[None, :]) / bandwidth) ** 2).sum(axis=1)
density /= n * bandwidth * np.sqrt(2 * np.pi)

# Imprint palette style — theme-adaptive chrome
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    guide_stroke_color=INK_MUTED,
    major_guide_stroke_color=INK_MUTED,
    colors=IMPRINT_PALETTE,
    title_font_size=66,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=4,
    opacity=0.45,
    opacity_hover=0.7,
    font_family="'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
)

# Theme-adaptive CSS overrides for spine removal and chrome
css_rules = [
    "file://style.css",
    f"inline:.plot .background {{fill: {PAGE_BG} !important; stroke: none !important; stroke-width: 0 !important;}}",
    f"inline:.graph > .background {{fill: {PAGE_BG} !important; stroke: none !important;}}",
    f"inline:.axis .guides .line {{stroke: {INK_MUTED} !important; stroke-width: 0.8px; opacity: 0.15;}}",
    "inline:.axis.x > path.line {stroke: none !important; stroke-width: 0 !important;}",
    "inline:.axis.y > path.line {stroke: none !important; stroke-width: 0 !important;}",
    f"inline:.axis .guides text {{fill: {INK_MUTED} !important;}}",
    f"inline:text.title {{font-weight: 600 !important; fill: {INK} !important;}}",
    "inline:.axis text {font-weight: 400 !important;}",
    f"inline:.legends text {{font-weight: 400 !important; fill: {INK} !important; opacity: 1 !important;}}",
    "inline:.legends .legend {opacity: 1 !important;}",
]

# Chart — 3200×1800 landscape canvas
chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title="density-basic · python · pygal · anyplot.ai",
    x_title=RENT,
    y_title="Density",
    show_dots=False,
    fill=True,
    show_legend=True,
    legend_at_bottom=True,
    legend_box_size=28,
    show_y_guides=True,
    show_x_guides=False,
    stroke_style={"width": 5, "linecap": "round"},
    truncate_label=-1,
    range=(0, float(density.max()) * 1.08),
    margin_top=40,
    margin_right=40,
    margin_bottom=30,
    margin_left=20,
    x_value_formatter=lambda x: f"{x:,.0f}",
    y_value_formatter=lambda y: f"{y:.4f}",
    css=css_rules,
    js=[],
)

# Density curve — Imprint green with a translucent fill
chart.add("Density estimate", list(zip(x_grid.tolist(), density.tolist(), strict=True)))

# Rug plot — one thin tick per observation, drawn up and back down so the line stays on the ticks
rug_height = float(density.max()) * 0.06
rug = []
for value in np.sort(rents).tolist():
    rug += [(value, 0.0), (value, rug_height), (value, 0.0)]
chart.add("Individual rents", rug, stroke_style={"width": 2.5, "linecap": "butt"}, fill=False)

# Save outputs
chart.render_to_png(f"plot-{THEME}.png")
chart.render_to_file(f"plot-{THEME}.html")
