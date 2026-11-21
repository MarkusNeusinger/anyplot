"""anyplot.ai
forest-basic: Meta-Analysis Forest Plot
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-11
"""

import os

import altair as alt
import pandas as pd
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
NULL_EFFECT = 0  # no difference between treatment and control (mean difference)
POOLED_LABEL = "Pooled estimate"
Z_95 = 1.96  # converts a 95% interval width into a standard error

# Columns: set these to your table's column names
STUDY = "Study"  # role: study
EFFECT_SIZE = "Standardized mean difference"  # role: effect_size
CI_LOWER = "CI lower"  # role: ci_lower
CI_UPPER = "CI upper"  # role: ci_upper
WEIGHT = "Weight (%)"  # role: weight

# Data: replace this block with your own table, for example df = pd.read_csv("studies.csv")
df = pd.DataFrame(
    {
        STUDY: [
            "Johnson 2018",
            "Smith 2019",
            "Garcia 2020",
            "Williams 2020",
            "Brown 2021",
            "Davis 2021",
            "Miller 2022",
            "Wilson 2022",
            "Anderson 2023",
            "Taylor 2023",
        ],
        EFFECT_SIZE: [-0.45, -0.32, -0.58, 0.12, -0.67, -0.38, -0.52, -0.29, -0.41, -0.55],
        CI_LOWER: [-0.78, -0.61, -0.95, -0.18, -1.02, -0.69, -0.88, -0.56, -0.72, -0.91],
        CI_UPPER: [-0.12, -0.03, -0.21, 0.42, -0.32, -0.07, -0.16, -0.02, -0.10, -0.19],
        WEIGHT: [8.5, 10.2, 7.8, 11.5, 6.9, 9.3, 8.1, 10.8, 9.7, 7.2],
    }
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
STUDY_F, EFFECT_F, LOWER_F, UPPER_F, WEIGHT_F = (
    c.translate(ESCAPE) for c in (STUDY, EFFECT_SIZE, CI_LOWER, CI_UPPER, WEIGHT)
)

# Pooled estimate: inverse-variance weighted mean of the studies, standard error from the interval widths
se = (df[CI_UPPER] - df[CI_LOWER]) / (2 * Z_95)
inv_var = 1 / se**2
pooled_effect = float((df[EFFECT_SIZE] * inv_var).sum() / inv_var.sum())
pooled_se = float(inv_var.sum() ** -0.5)
pooled = pd.DataFrame(
    {
        STUDY: [POOLED_LABEL],
        EFFECT_SIZE: [pooled_effect],
        CI_LOWER: [pooled_effect - Z_95 * pooled_se],
        CI_UPPER: [pooled_effect + Z_95 * pooled_se],
    }
)

row_order = [*df[STUDY], POOLED_LABEL]
span = max(df[CI_UPPER].max(), NULL_EFFECT) - min(df[CI_LOWER].min(), NULL_EFFECT)
x_scale = alt.Scale(
    domain=[min(df[CI_LOWER].min(), NULL_EFFECT) - 0.04 * span, max(df[CI_UPPER].max(), NULL_EFFECT) + 0.04 * span]
)
y_enc = alt.Y(STUDY_F, type="nominal", title=None, sort=row_order)


def tooltip(label):
    return [
        alt.Tooltip(STUDY_F, type="nominal", title=label),
        alt.Tooltip(EFFECT_F, type="quantitative", title=EFFECT_SIZE, format=".2f"),
        alt.Tooltip(LOWER_F, type="quantitative", title=CI_LOWER, format=".2f"),
        alt.Tooltip(UPPER_F, type="quantitative", title=CI_UPPER, format=".2f"),
    ]


reference_line = (
    alt.Chart(pd.DataFrame({"x": [NULL_EFFECT]}))
    .mark_rule(color=INK_SOFT, strokeDash=[4, 2], strokeWidth=1, opacity=0.8)
    .encode(x=alt.X("x:Q"))
)

ci_lines = (
    alt.Chart(pd.concat([df, pooled]))
    .mark_rule(color=IMPRINT_PALETTE[0], strokeWidth=1.5)
    .encode(
        x=alt.X(LOWER_F, type="quantitative", title="Standardized mean difference (95% CI)", scale=x_scale),
        x2=alt.X2(UPPER_F),
        y=y_enc,
    )
)

points = (
    alt.Chart(df)
    .mark_point(filled=True, color=IMPRINT_PALETTE[0], stroke=PAGE_BG, strokeWidth=1)
    .encode(
        x=alt.X(EFFECT_F, type="quantitative", scale=x_scale),
        y=y_enc,
        size=alt.Size(WEIGHT_F, type="quantitative", legend=None, scale=alt.Scale(range=[40, 170])),
        tooltip=[*tooltip(STUDY), alt.Tooltip(WEIGHT_F, type="quantitative", title=WEIGHT)],
    )
)

diamond = (
    alt.Chart(pooled)
    .mark_point(
        shape="diamond", filled=True, size=420, color=IMPRINT_PALETTE[4], stroke=IMPRINT_PALETTE[0], strokeWidth=1.5
    )
    .encode(x=alt.X(EFFECT_F, type="quantitative", scale=x_scale), y=y_enc, tooltip=tooltip("Estimate"))
)

TITLE = "forest-basic · python · altair · anyplot.ai"
chart = (
    alt.layer(reference_line, ci_lines, points, diamond)
    .properties(width=620, height=320, background=PAGE_BG, title=alt.Title(TITLE, fontSize=16, anchor="middle"))
    .configure_axis(
        labelFontSize=10,
        titleFontSize=12,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        gridColor=INK,
        gridOpacity=0.10,
    )
    .configure_axisY(grid=False, ticks=False, domain=False)
    .configure_title(color=INK)
    .configure_view(strokeWidth=0, fill=PAGE_BG)
)

# Save: render at 4x, then pad (never crop) to the 3200 x 1800 target
TARGET_W, TARGET_H = 3200, 1800
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TARGET_W or img.height > TARGET_H:
    raise SystemExit(f"altair rendered {img.width}x{img.height}, exceeds {TARGET_W}x{TARGET_H}; shrink width/height")
canvas = Image.new("RGB", (TARGET_W, TARGET_H), PAGE_BG)
canvas.paste(img, ((TARGET_W - img.width) // 2, (TARGET_H - img.height) // 2))
canvas.save(f"plot-{THEME}.png")
chart.save(f"plot-{THEME}.html")
