"""anyplot.ai
violin-box: Violin Plot with Embedded Box Plot
Library: pygal 3.1.0 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-12
"""

import os
import sys

import numpy as np
import pandas as pd


sys.path = [p for p in sys.path if not p.endswith("/python")]
import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
WHISKER_IQR = 1.5  # whiskers reach the farthest value within this many IQRs of the box
VIOLIN_HALF_WIDTH = 0.38  # widest half-width of a violin, in x units (groups sit 1 apart)
BOX_HALF_WIDTH = 0.09  # half-width of the embedded box, in x units

# Columns: set these to your table's column names
DEPARTMENT = "Department"  # role: group
SCORE = "Performance score (0-100)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
rng = np.random.default_rng(42)
departments = {"Engineering": (75, 10), "Marketing": (62, 12), "Sales": (68, 14), "Operations": (55, 8)}
df = pd.DataFrame(
    {
        DEPARTMENT: np.repeat(list(departments), 200),
        SCORE: np.clip(np.concatenate([rng.normal(mu, sd, 200) for mu, sd in departments.values()]), 0, 100),
    }
)

# Plot: reads only df and the constants above
groups = list(dict.fromkeys(df[DEPARTMENT]))
values_by_group = {g: df.loc[df[DEPARTMENT] == g, SCORE].dropna().to_numpy() for g in groups}
lo, hi = df[SCORE].min(), df[SCORE].max()
pad = (hi - lo) * 0.06

# Series are added in this order; pygal hands out colors by series index
series_colors = []


def add_line(chart, points, color, fill=False, stroke=True, show_dots=False, dots_size=0, width=4, dash="none"):
    series_colors.append(color)
    chart.add(
        None,
        points,
        fill=fill,
        stroke=stroke,
        show_dots=show_dots,
        dots_size=dots_size,
        stroke_style={"width": width, "dasharray": dash},
    )


def add_shape(chart, points, color):
    # pygal fills a line down to the baseline and strokes that closing edge too, so the fill
    # goes in as an unstroked series and the outline as a separate, unfilled one
    add_line(chart, points, color, fill=True, stroke=True, dash="0 100000")
    add_line(chart, points, color)


chart = pygal.XY(
    width=3200,
    height=1800,
    title="violin-box · python · pygal · anyplot.ai",
    x_title=DEPARTMENT,
    y_title=SCORE,
    show_legend=False,
    stroke=True,
    fill=True,
    dots_size=0,
    show_x_guides=False,
    show_y_guides=True,
    range=(lo - pad, hi + pad),
    xrange=(0.4, len(groups) + 0.6),
    margin=60,
    x_labels=[{"label": str(g), "value": i + 1} for i, g in enumerate(groups)],
    x_labels_major_count=len(groups),
    show_minor_x_labels=True,
)

for i, group in enumerate(groups):
    values = values_by_group[group]
    cx = i + 1
    color = IMPRINT_PALETTE[i]

    # Gaussian KDE (Silverman bandwidth) limited to the data range, so tails end near the data
    n = len(values)
    q1, median, q3 = (float(q) for q in np.percentile(values, [25, 50, 75]))
    bandwidth = 0.9 * min(values.std(), (q3 - q1) / 1.34) * n ** (-0.2)
    grid = np.linspace(values.min(), values.max(), 120)
    density = np.exp(-0.5 * ((grid[:, None] - values[None, :]) / bandwidth) ** 2).sum(axis=1)
    half = density / density.max() * VIOLIN_HALF_WIDTH

    outline = [(cx - h, y) for y, h in zip(grid, half, strict=True)]
    outline += [(cx + h, y) for y, h in zip(grid[::-1], half[::-1], strict=True)]
    add_shape(chart, outline + outline[:1], color)

    # Box statistics
    iqr = q3 - q1
    inside = values[(values >= q1 - WHISKER_IQR * iqr) & (values <= q3 + WHISKER_IQR * iqr)]
    low_whisker, high_whisker = float(inside.min()), float(inside.max())
    outliers = values[(values < low_whisker) | (values > high_whisker)]

    # Box, whiskers and caps in ink so they stand out against the violin fill
    box = [(cx - BOX_HALF_WIDTH, q1), (cx - BOX_HALF_WIDTH, q3), (cx + BOX_HALF_WIDTH, q3), (cx + BOX_HALF_WIDTH, q1)]
    add_shape(chart, box + box[:1], INK)
    cap = BOX_HALF_WIDTH * 0.7
    for a, b in ((q1, low_whisker), (q3, high_whisker)):
        add_line(chart, [(cx, a), (cx, b)], INK, fill=False)
        add_line(chart, [(cx - cap, b), (cx + cap, b)], INK, fill=False)

    # Median in the page color so it reads on the ink box
    add_line(chart, [(cx - BOX_HALF_WIDTH, median), (cx + BOX_HALF_WIDTH, median)], PAGE_BG, width=7)

    # Outliers as individual points at their values
    if len(outliers) > 0:
        add_line(chart, [(cx, float(o)) for o in outliers], INK, fill=False, stroke=False, show_dots=True, dots_size=11)

chart.config.style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=tuple(series_colors),
    opacity=0.55,
    opacity_hover=0.55,
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=3,
)

# Save
chart.render_to_file(f"plot-{THEME}.html")
chart.render_to_png(f"plot-{THEME}.png")
