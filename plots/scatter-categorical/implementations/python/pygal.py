""" anyplot.ai
scatter-categorical: Categorical Scatter Plot
Library: pygal 3.1.3 | Python 3.14.10
Quality: 80/100 | Updated: 2026-11-21
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
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
CPU_SCORE = "Multi-core benchmark score"  # role: x
BATTERY = "Battery life (hours)"  # role: y
LAPTOP_CLASS = "Laptop class"  # role: category

# Data: replace this block with your own table, for example df = pd.read_csv("laptops.csv")
np.random.seed(42)
classes = {
    # name: (n, mean score, sd score, mean battery, sd battery)
    "Ultrabook": (40, 8500, 1300, 14.5, 2.0),
    "Gaming": (35, 17500, 2600, 5.5, 1.2),
    "Workstation": (30, 21000, 3200, 8.5, 1.6),
}
df = pd.concat(
    [
        pd.DataFrame(
            {
                CPU_SCORE: np.random.normal(mx, sx, n).round(0),
                BATTERY: np.random.normal(my, sy, n).round(1).clip(min=1.5),
                LAPTOP_CLASS: name,
            }
        )
        for name, (n, mx, sx, my, sy) in classes.items()
    ],
    ignore_index=True,
)

# Plot
style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_SOFT,
    colors=IMPRINT_PALETTE,
    title_font_size=66,
    label_font_size=52,
    major_label_font_size=42,
    legend_font_size=46,
    value_font_size=36,
    opacity=0.7,
    opacity_hover=0.95,
    stroke_width=2.5,
)

chart = pygal.XY(
    width=3200,
    height=1800,
    style=style,
    title="scatter-categorical · python · pygal · anyplot.ai",
    x_title=CPU_SCORE,
    y_title=BATTERY,
    stroke=False,
    dots_size=11,
    show_x_guides=True,
    show_y_guides=True,
    legend_at_bottom=True,
    legend_box_size=30,
    truncate_legend=-1,
    margin=40,
)

for name, group in df.groupby(LAPTOP_CLASS, sort=False):
    chart.add(str(name), list(zip(group[CPU_SCORE], group[BATTERY], strict=True)))

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
