"""anyplot.ai
polar-bar: Polar Bar Chart (Wind Rose)
Library: pygal 3.1.3 | Python 3.14.10
Quality: 75/100 | Updated: 2026-11-09
"""

import copy
import math
import os

import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions; the ordered speed classes use imprint_seq steps instead
IMPRINT_PALETTE = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314")
SEQ_START, SEQ_END = "#009E73", "#4467A3"  # imprint_seq endpoints

# Constants
STEPS_PER_SECTOR = 16  # angular samples per direction; pygal's Radar draws wedges as dense polygons
BAR_FILL = 0.8  # share of each direction's sector covered by its bar
MARGIN = 60

# Columns: set these to your table's column names
DIRECTION = "Direction"  # role: direction
SPEED = "Wind speed"  # role: extra
FREQUENCY = "Frequency (%)"  # role: frequency

# Data: replace this block with your own table, for example df = pd.read_csv("wind.csv")
directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
speeds = {
    "Calm (0-5 km/h)": [6, 4, 3, 2, 4, 5, 8, 7],
    "Light (5-15 km/h)": [4, 3, 2, 2, 3, 5, 7, 6],
    "Moderate (15-25 km/h)": [2, 1, 1, 1, 1, 3, 5, 4],
    "Strong (25+ km/h)": [1.5, 0.5, 0.5, 0.5, 0.5, 1.5, 3.5, 2.5],
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

# Ordered speed classes: imprint_seq steps from the first class to the last
seq_colors = []
for i in range(len(groups)):
    t = i / max(len(groups) - 1, 1)
    rgb = [round(int(SEQ_START[k : k + 2], 16) * (1 - t) + int(SEQ_END[k : k + 2], 16) * t) for k in (1, 3, 5)]
    seq_colors.append("#{:02X}{:02X}{:02X}".format(*rgb))

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    # Outermost cumulative ring is drawn first, so the steps run in reverse
    colors=tuple(reversed(seq_colors)),
    title_font_size=66,
    label_font_size=48,
    major_label_font_size=48,
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
    x_title=f"Rings: {FREQUENCY} of all observations",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=2,
    legend_box_size=36,
    fill=True,
    stroke=True,
    show_dots=False,
    range=(0, top * 1.08),
    value_formatter=lambda v: f"{v:g}%",
    show_minor_x_labels=False,
    margin=MARGIN,
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

# Radar stretches its polar box to the plot box; widen the side margins until the box is square
plot_box = chart.render_tree().find(".//*[@class='plot']/*[@class='background']")
excess = float(plot_box.get("width")) - float(plot_box.get("height"))
chart.margin_left = chart.margin_right = MARGIN + max(excess, 0) / 2
chart.margin_top = chart.margin_bottom = MARGIN + max(-excess, 0) / 2

# Radar puts the ring labels on the N spoke, under the N bar; turn them into the gap
# before N and drop the centre label, which the wedge tips cover
gap = math.pi / n_dirs


def move_ring_labels(svg):
    plot = svg.find(".//*[@class='plot']")
    box = plot.find("*[@class='background']")
    cx, cy = float(box.get("width")) / 2, float(box.get("height")) / 2
    axis = plot.find("*[@class='axis y web']")
    for guides in axis.findall("*"):
        for text in guides.findall("{*}text"):
            dx, dy = float(text.get("x")) - cx, float(text.get("y")) - cy
            guides.remove(text)
            if math.hypot(dx, dy) < 10:
                continue
            text.set("x", f"{cx + dy * math.sin(gap):.1f}")
            text.set("y", f"{cy + dy * math.cos(gap):.1f}")
            text.set("style", "text-anchor: middle")
            # A page-coloured halo keeps each label legible where it crosses a bar
            halo = copy.deepcopy(text)
            halo.set("style", f"text-anchor: middle; fill: {PAGE_BG}; stroke: {PAGE_BG}; stroke-width: 12px")
            guides.extend([halo, text])
    # Draw the axis after the series so the labels sit on top of the bars
    plot.remove(axis)
    plot.append(axis)
    return svg


chart.add_xml_filter(move_ring_labels)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
