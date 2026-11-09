"""anyplot.ai
histogram-stacked: Stacked Histogram
Library: pygal 3.1.3 | Python 3.14.10
Quality: 81/100 | Updated: 2026-11-09
"""

import os

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Constants
BIN_COUNT = 12  # shared bin boundaries for every group

# Columns: set these to your table's column names
PLANT_HEIGHT = "Plant Height (cm)"  # role: values
LIGHT_CONDITION = "Light condition"  # role: group

# Data: replace this block with your own table, for example df = pd.read_csv("plants.csv")
np.random.seed(42)
df = pd.DataFrame(
    {
        PLANT_HEIGHT: np.concatenate(
            [np.random.normal(25, 5, 150), np.random.normal(35, 7, 180), np.random.normal(45, 6, 120)]
        ),
        LIGHT_CONDITION: ["Shade-grown"] * 150 + ["Partial-sun"] * 180 + ["Full-sun"] * 120,
    }
)

# Plot: reads only df and the constants above
observed = df.dropna(subset=[PLANT_HEIGHT, LIGHT_CONDITION])
bin_edges = np.histogram_bin_edges(observed[PLANT_HEIGHT], bins=BIN_COUNT)
bin_labels = [f"{lo:.0f}–{hi:.0f}" for lo, hi in zip(bin_edges[:-1], bin_edges[1:], strict=True)]
tallest_total = np.histogram(observed[PLANT_HEIGHT], bins=bin_edges)[0].max()

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT_PALETTE,
    title_font_size=66,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    tooltip_font_size=36,
    stroke_width=2.5,
    opacity=1.0,
    opacity_hover=0.8,
)


class ContiguousStackedBar(pygal.StackedBar):
    # Histogram bins touch, as in pygal's own Histogram: no margin inside each bin slot
    _series_margin = 0


chart = ContiguousStackedBar(
    width=3200,
    height=1800,
    style=custom_style,
    title="histogram-stacked · python · pygal · anyplot.ai",
    x_title=PLANT_HEIGHT,
    y_title="Frequency (plants)",
    show_y_guides=True,
    show_x_guides=False,
    legend_at_bottom=True,
    legend_at_bottom_columns=observed[LIGHT_CONDITION].nunique(),
    legend_box_size=36,
    margin=60,
    spacing=0,
    truncate_legend=-1,
    range=(0, tallest_total * 1.1),
)
chart.x_labels = bin_labels

# Segments: one per group, stacked in the data's group order in every bin
for group, heights in observed.groupby(LIGHT_CONDITION, sort=False)[PLANT_HEIGHT]:
    counts, _ = np.histogram(heights, bins=bin_edges)
    chart.add(str(group), counts.tolist())

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
