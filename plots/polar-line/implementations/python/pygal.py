"""anyplot.ai
polar-line: Polar Line Plot
Library: pygal 3.1.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-12
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

# Imprint palette: all eight positions, one per series in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
HOUR = "Hour of day"  # role: theta
DAY_TYPE = "Day type"  # role: series
CUSTOMERS = ["Customers per hour"]  # role: radius

# Data: replace this block with your own table, for example df = pd.read_csv("traffic.csv")
rng = np.random.default_rng(42)
hours = np.arange(24)


def _bump(center, width, height):
    return height * np.exp(-0.5 * ((hours - center) / width) ** 2)


weekday = 4 + _bump(8, 1.2, 55) + _bump(12.5, 1.4, 70) + _bump(17, 1.5, 38)
weekend = 3 + _bump(11, 2.2, 62) + _bump(15, 2.0, 50)
weekday[:6] = weekday[:6] * 0.05  # closed overnight
weekend[:7] = weekend[:7] * 0.05
weekday[20:] = weekday[20:] * 0.1
weekend[21:] = weekend[21:] * 0.1
df = pd.DataFrame(
    {
        HOUR: [f"{h:02d}:00" for h in hours] * 2,
        DAY_TYPE: ["Weekday"] * 24 + ["Weekend"] * 24,
        CUSTOMERS[0]: np.round(np.concatenate([weekday, weekend]) + rng.normal(0, 1.5, 48).clip(0), 1),
    }
)

# Plot: pygal takes plain lists, built from df
table = df.pivot_table(index=HOUR, columns=DAY_TYPE, values=CUSTOMERS[0], sort=False)

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=tuple(IMPRINT_PALETTE),
    title_font_size=60,
    label_font_size=44,
    major_label_font_size=40,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=5,
    opacity=0.95,
    opacity_hover=1.0,
)

chart = pygal.Radar(
    width=2400,
    height=2400,
    style=custom_style,
    title="Café Foot Traffic · polar-line · python · pygal · anyplot.ai",
    show_legend=True,
    legend_at_bottom=True,
    legend_box_size=36,
    dots_size=8,
    fill=False,
    show_dots=True,
    inner_radius=0.1,
    margin=60,
    margin_top=120,
    margin_bottom=60,
)
chart.x_labels = table.index.tolist()
for day_type in table.columns:
    chart.add(str(day_type), table[day_type].tolist())

chart.render_to_file(f"plot-{THEME}.html")
chart.render_to_png(f"plot-{THEME}.png")
