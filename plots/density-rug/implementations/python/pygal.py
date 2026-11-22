"""anyplot.ai
density-rug: Density Plot with Rug Marks
Library: pygal 3.1.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-18
"""

import os

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style
from scipy.stats import gaussian_kde


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: position 1 is the KDE curve, position 2 the rug
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
MEASUREMENT = "Measurement value"  # role: values

# Data: replace this block with your own table, for example df = pd.read_csv("measurements.csv")
np.random.seed(42)
df = pd.DataFrame(
    {
        MEASUREMENT: np.concatenate(
            [np.random.normal(loc=35, scale=8, size=60), np.random.normal(loc=65, scale=10, size=90)]
        )
    }
)

# Plot: reads only df and the constants above
values = df[MEASUREMENT].dropna().to_numpy()
spread = values.max() - values.min()
x_range = np.linspace(values.min() - 0.15 * spread, values.max() + 0.15 * spread, 300)
density = gaussian_kde(values)(x_range)
tick_height = 0.06 * density.max()

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=tuple(IMPRINT_PALETTE),
    opacity=0.35,
    opacity_hover=0.5,
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=2.5,
    font_family="sans-serif",
    title_font_family="sans-serif",
    label_font_family="sans-serif",
    major_label_font_family="sans-serif",
    legend_font_family="sans-serif",
)

chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title="density-rug · python · pygal · anyplot.ai",
    x_title=MEASUREMENT,
    y_title="Density",
    show_legend=True,
    legend_at_bottom=True,
    show_dots=False,
    show_x_guides=False,
    show_y_guides=True,
    range=(0, density.max() * 1.1),
    include_x_axis=True,
    truncate_legend=-1,
    value_formatter=lambda v: f"{v:.3f}",
    x_value_formatter=lambda v: f"{v:.0f}",
    margin=40,
)

# Density curve with a semi-transparent fill that lets the rug and grid show through
chart.add(
    "Kernel density estimate",
    list(zip(x_range.tolist(), density.tolist(), strict=True)),
    fill=True,
    stroke_style={"width": 7},
)

# Rug: one short vertical tick per observation, each at its exact value; the path returns to the baseline after each tick
rug = []
for v in np.sort(values).tolist():
    rug += [(v, 0.0), (v, tick_height), (v, 0.0)]
chart.add(
    f"Observations (n = {len(values)})", rug, fill=False, show_dots=False, stroke_style={"width": 4, "linecap": "butt"}
)

# Save
chart.render_to_png(f"plot-{THEME}.png")
chart.render_to_file(f"plot-{THEME}.html")
