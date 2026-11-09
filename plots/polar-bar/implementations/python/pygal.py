""" anyplot.ai
polar-bar: Polar Bar Chart (Wind Rose)
Library: pygal 3.1.3 | Python 3.14.10
Quality: 75/100 | Updated: 2026-11-09
"""

import os

import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, first series always #009E73
IMPRINT_PALETTE = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Constants
STEPS_PER_SECTOR = 16  # angular samples per direction; pygal's Radar draws wedges as dense polygons
BAR_FILL = 0.8  # share of each direction's sector covered by its bar

# Columns: set these to your table's column names
DIRECTION = "Direction"  # role: direction
SPEED = "Wind speed"  # role: extra
FREQUENCY = "Frequency (%)"  # role: frequency

# Data: replace this block with your own table, for example df = pd.read_csv("wind.csv")
directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
speeds = {
    "Calm (0-5 km/h)": [8, 5, 4, 3, 5, 7, 12, 11],
    "Light (5-15 km/h)": [6, 4, 3, 2, 4, 7, 10, 9],
    "Moderate (15-25 km/h)": [3, 2, 2, 1, 2, 4, 7, 6],
    "Strong (25+ km/h)": [2, 1, 1, 1, 1, 2, 4, 3],
}
df = pd.DataFrame(
    [
        {DIRECTION: d, SPEED: speed, FREQUENCY: value}
        for speed, values in speeds.items()
        for d, value in zip(directions, values, strict=True)
    ]
)

# Plot: stack the speed classes per direction, then sample each bar as a wedge
table = df.pivot_table(index=DIRECTION, columns=SPEED, values=FREQUENCY, sort=False)
cumulative = table.cumsum(axis=1)
groups = list(table.columns)
n_dirs = len(table.index)
half_bar = BAR_FILL * STEPS_PER_SECTOR / 2

# Each direction owns STEPS_PER_SECTOR samples centred on its compass angle;
# samples outside the bar's half-width drop to zero so the wedge edges run radially
sample_dir = []
in_bar = []
for i in range(n_dirs * STEPS_PER_SECTOR):
    offset = (i + STEPS_PER_SECTOR // 2) % STEPS_PER_SECTOR - STEPS_PER_SECTOR // 2
    sample_dir.append(round(i / STEPS_PER_SECTOR) % n_dirs)
    in_bar.append(abs(offset) < half_bar)

# pygal's Radar runs counter-clockwise; reverse after the first sample for compass order
sample_dir = sample_dir[:1] + sample_dir[:0:-1]
in_bar = in_bar[:1] + in_bar[:0:-1]

top = float(cumulative.max().max())

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    # Outermost cumulative ring is drawn first, so the palette runs in reverse
    colors=tuple(IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] for i in reversed(range(len(groups)))),
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=56,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=1,
    opacity=1,
    opacity_hover=0.85,
    guide_stroke_color=INK_MUTED,
    major_guide_stroke_color=INK_MUTED,
)

chart = pygal.Radar(
    width=2400,
    height=2400,
    style=custom_style,
    title="polar-bar · python · pygal · anyplot.ai",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=2,
    legend_box_size=36,
    fill=True,
    stroke=True,
    show_dots=False,
    range=(0, top * 1.08),
    show_minor_x_labels=False,
    margin=60,
    spacing=40,
)

chart.x_labels = [str(table.index[d]) if i % STEPS_PER_SECTOR == 0 else "" for i, d in enumerate(sample_dir)]
chart.x_labels_major = [str(label) for label in table.index]

# Outer (cumulative) segments first so each inner class paints over its share
for group in reversed(groups):
    radii = [
        float(cumulative[group].iloc[d]) if bar and pd.notna(cumulative[group].iloc[d]) else 0
        for d, bar in zip(sample_dir, in_bar, strict=True)
    ]
    chart.add(str(group), radii)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
