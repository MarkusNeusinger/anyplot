"""anyplot.ai
forest-basic: Meta-Analysis Forest Plot
Library: pygal 3.1.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-11
"""

import os

import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
NULL_EFFECT = 0  # no difference between treatment and control
Z_95 = 1.96  # 95% confidence interval

# Columns: set these to your table's column names
STUDY = "Study"  # role: study
EFFECT = "Mean Difference"  # role: effect_size
CI_LOWER = "CI lower"  # role: ci_lower
CI_UPPER = "CI upper"  # role: ci_upper
WEIGHT = "Weight (%)"  # role: weight

# Data: replace this block with your own table, for example df = pd.read_csv("studies.csv")
df = pd.DataFrame(
    {
        STUDY: [
            "Smith 2023",
            "Johnson 2023",
            "Williams 2022",
            "Brown 2022",
            "Davis 2022",
            "Miller 2021",
            "Wilson 2021",
            "Moore 2021",
            "Taylor 2020",
            "Anderson 2020",
        ],
        EFFECT: [-0.35, -0.52, -0.18, -0.67, -0.41, -0.29, -0.55, -0.38, -0.61, -0.44],
        CI_LOWER: [-0.72, -0.95, -0.58, -1.15, -0.78, -0.65, -0.98, -0.71, -1.08, -0.82],
        CI_UPPER: [0.02, -0.09, 0.22, -0.19, -0.04, 0.07, -0.12, -0.05, -0.14, -0.06],
        WEIGHT: [10.1, 12.5, 9.8, 10.3, 14.2, 11.7, 9.1, 13.8, 7.6, 12.8],
    }
)

# Plot: reads only df and the constants above
n = len(df)

# Pooled estimate by inverse-variance weighting
se = (df[CI_UPPER] - df[CI_LOWER]) / (2 * Z_95)
inv_var = 1 / se**2
pooled = (df[EFFECT] * inv_var).sum() / inv_var.sum()
pooled_se = inv_var.sum() ** -0.5
pooled_lo, pooled_hi = pooled - Z_95 * pooled_se, pooled + Z_95 * pooled_se

# Axis range with padding around every interval and the null line
span = max(df[CI_UPPER].max(), NULL_EFFECT) - min(df[CI_LOWER].min(), NULL_EFFECT)
x_min = min(df[CI_LOWER].min(), NULL_EFFECT) - 0.04 * span
x_max = max(df[CI_UPPER].max(), NULL_EFFECT) + 0.04 * span

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=(IMPRINT_PALETTE[0],) * (n + 1) + (INK_SOFT, IMPRINT_PALETTE[2]),
    title_font_size=66,
    label_font_size=40,
    major_label_font_size=40,
    legend_font_size=36,
    value_font_size=30,
    stroke_width=3,
)

chart = pygal.XY(
    width=3200,
    height=1800,
    title="forest-basic · python · pygal · anyplot.ai",
    x_title=f"{EFFECT} (95% CI)",
    style=custom_style,
    show_legend=False,
    stroke=False,
    show_y_guides=False,
    show_x_guides=True,
    range=(x_min, x_max),
    xrange=(x_min, x_max),
    margin=60,
)

# Study rows from the top; the pooled row sits at y = 0 below them
rows = [(n - i, row) for i, row in enumerate(df.itertuples(index=False))]

# Confidence intervals: one two-point series per study
for y, row in rows:
    chart.add(row[0], [(row[2], y), (row[3], y)], stroke=True, show_dots=False, stroke_style={"width": 6})

# Effect estimates: marker area proportional to study weight
max_weight = df[WEIGHT].max()
points = [{"value": (row[1], y), "node": {"r": 22 * (row[4] / max_weight) ** 0.5}} for y, row in rows]
chart.add("Effect", points, stroke=False)

# Null reference line through every row including the pooled one
chart.add(
    "Null",
    [(NULL_EFFECT, -0.7), (NULL_EFFECT, n + 0.7)],
    stroke=True,
    show_dots=False,
    stroke_style={"width": 4, "dasharray": "14, 8"},
)

# Pooled diamond
chart.add(
    "Pooled",
    [(pooled_lo, 0), (pooled, 0.4), (pooled_hi, 0), (pooled, -0.4), (pooled_lo, 0)],
    stroke=True,
    fill=True,
    show_dots=False,
    stroke_style={"width": 5},
)

chart.y_labels = [{"value": y, "label": f"{row[0]}  [{row[2]:.2f}, {row[3]:.2f}]"} for y, row in rows] + [
    {"value": 0, "label": f"Pooled  [{pooled_lo:.2f}, {pooled_hi:.2f}]"}
]

chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
