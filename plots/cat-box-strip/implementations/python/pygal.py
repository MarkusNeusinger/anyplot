"""anyplot.ai
cat-box-strip: Box Plot with Strip Overlay
Library: pygal 3.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-13
"""

import os

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens from environment
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, one per category in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
EDUCATION = "Education Level"  # role: category
TEST_SCORE = "Test Score"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
np.random.seed(42)
groups = {
    "High School": np.random.normal(68, 12, 45),
    "Bachelor's": np.random.normal(78, 10, 50),
    "Master's": np.random.normal(82, 8, 38),
    "PhD": np.random.normal(85, 7, 42),
}
outliers = {"High School": [95, 48], "Bachelor's": [58, 98], "Master's": [62, 95], "PhD": [65, 100]}
df = pd.DataFrame(
    [(name, float(np.clip(v, 0, 100))) for name, draws in groups.items() for v in np.append(draws, outliers[name])],
    columns=[EDUCATION, TEST_SCORE],
)

# Plot: reads only df and the constants above
categories = list(df[EDUCATION].unique())
n_cat = len(categories)
BOX_WIDTH = 0.25
CAP_WIDTH = 0.15
JITTER = 0.12

# Six box elements per category (box, median, two whiskers, two caps), then one strip series per category
palette = [IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] for i in range(n_cat)]
color_sequence = [color for color in palette for _ in range(6)] + palette

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=tuple(color_sequence),
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    opacity=0.7,
)

low, high = df[TEST_SCORE].min(), df[TEST_SCORE].max()
pad = (high - low) * 0.05

chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title="cat-box-strip · python · pygal · anyplot.ai",
    x_title=EDUCATION,
    y_title=TEST_SCORE,
    show_legend=False,
    stroke=True,
    fill=True,
    dots_size=0,
    show_x_guides=True,
    show_y_guides=True,
    xrange=(0, n_cat + 1),
    range=(float(low - pad), float(high + pad)),
    margin=60,
    explicit_size=True,
)

box_data = []
strip_data = []
for i, category in enumerate(categories):
    center_x = i + 1
    values = df.loc[df[EDUCATION] == category, TEST_SCORE].dropna().to_numpy(dtype=float)
    if values.size == 0:
        continue

    q1, median, q3 = (float(np.percentile(values, p)) for p in (25, 50, 75))
    iqr = q3 - q1
    whisker_low = float(values[values >= q1 - 1.5 * iqr].min())
    whisker_high = float(values[values <= q3 + 1.5 * iqr].max())
    box_data.append((center_x, median, q1, q3, whisker_low, whisker_high))

    np.random.seed(42 + i)
    jitter = np.random.uniform(-JITTER, JITTER, len(values))
    strip_data.append([(center_x + j, float(v)) for j, v in zip(jitter, values, strict=True)])

# Boxes first so the strip points sit on top
for center_x, median, q1, q3, whisker_low, whisker_high in box_data:
    quartile_box = [
        (center_x - BOX_WIDTH, q1),
        (center_x - BOX_WIDTH, q3),
        (center_x + BOX_WIDTH, q3),
        (center_x + BOX_WIDTH, q1),
        (center_x - BOX_WIDTH, q1),
    ]
    chart.add("", quartile_box, stroke=True, fill=True, show_dots=False, stroke_style={"width": 4})
    chart.add(
        "",
        [(center_x - BOX_WIDTH * 1.1, median), (center_x + BOX_WIDTH * 1.1, median)],
        fill=False,
        show_dots=False,
        stroke_style={"width": 7},
    )
    for whisker in ([(center_x, q1), (center_x, whisker_low)], [(center_x, q3), (center_x, whisker_high)]):
        chart.add("", whisker, fill=False, show_dots=False, stroke_style={"width": 4})
    for cap_y in (whisker_low, whisker_high):
        chart.add(
            "",
            [(center_x - CAP_WIDTH, cap_y), (center_x + CAP_WIDTH, cap_y)],
            fill=False,
            show_dots=False,
            stroke_style={"width": 4},
        )

for strip_points in strip_data:
    chart.add("", strip_points, stroke=False, fill=False, dots_size=9)

chart.x_labels = [{"value": 0, "label": ""}]
chart.x_labels += [{"value": i + 1, "label": c} for i, c in enumerate(categories)]
chart.x_labels += [{"value": n_cat + 1, "label": ""}]

chart.render_to_file(f"plot-{THEME}.html")
chart.render_to_png(f"plot-{THEME}.png")
