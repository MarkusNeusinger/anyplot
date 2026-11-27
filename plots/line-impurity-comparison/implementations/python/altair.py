"""anyplot.ai
line-impurity-comparison: Gini Impurity vs Entropy Comparison
Library: altair 6.1.0 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-29
"""

import os

import altair as alt
import numpy as np
import pandas as pd


# Theme tokens (Imprint palette — see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
P = "Probability p"  # role: p
GINI = "Gini: 2p(1−p)"  # role: extra
ENTROPY = "Entropy: −p·log₂p − (1−p)·log₂(1−p)"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("impurity.csv")
p = np.linspace(0, 1, 200)
with np.errstate(divide="ignore", invalid="ignore"):
    entropy_raw = -p * np.log2(p) - (1 - p) * np.log2(1 - p)
entropy_raw = np.nan_to_num(entropy_raw, nan=0.0)  # entropy is defined as 0 at p = 0 and p = 1
df = pd.DataFrame({P: p, GINI: 2 * p * (1 - p), ENTROPY: entropy_raw / entropy_raw.max()})

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
MEASURE = "Measure"
IMPURITY = "Impurity measure (normalized)"
measures = [GINI, ENTROPY]
long_df = df.melt(id_vars=P, value_vars=measures, var_name=MEASURE, value_name=IMPURITY)

# Peaks, found by a rule over df
peaks = pd.DataFrame(
    {
        P: [df.loc[df[m].idxmax(), P] for m in measures],
        IMPURITY: [df[m].max() for m in measures],
        "label": [f"{m.split(':')[0]} max = {df[m].max():.1f}" for m in measures],
    }
)
top = df[measures].to_numpy().max()

title_text = "line-impurity-comparison · python · altair · anyplot.ai"
title_fontsize = max(11, round(16 * (67 / len(title_text) if len(title_text) > 67 else 1.0)))

color_scale = alt.Scale(domain=measures, range=IMPRINT_PALETTE[: len(measures)])
dash_scale = alt.Scale(domain=measures, range=[[1, 0], [8, 4]])
x_enc = alt.X(
    P.translate(ESCAPE),
    type="quantitative",
    title=P,
    scale=alt.Scale(domain=[df[P].min(), df[P].max()]),
    axis=alt.Axis(tickCount=10, labelFontSize=10, titleFontSize=12),
)

# Shaded band between the two curves
area_fill = (
    alt.Chart(df)
    .mark_area(opacity=0.12, color=IMPRINT_PALETTE[1])
    .encode(x=x_enc, y=alt.Y(GINI.translate(ESCAPE), type="quantitative"), y2=alt.Y2(ENTROPY.translate(ESCAPE)))
)

lines = (
    alt.Chart(long_df)
    .mark_line(strokeWidth=4)
    .encode(
        x=x_enc,
        y=alt.Y(
            IMPURITY.translate(ESCAPE),
            type="quantitative",
            title=IMPURITY,
            scale=alt.Scale(domain=[0, top * 1.12]),
            axis=alt.Axis(labelFontSize=10, titleFontSize=12),
        ),
        color=alt.Color(
            MEASURE,
            type="nominal",
            scale=color_scale,
            legend=alt.Legend(
                title=None, labelFontSize=10, orient="top-right", offset=10, symbolStrokeWidth=4, symbolSize=300
            ),
        ),
        strokeDash=alt.StrokeDash(MEASURE, type="nominal", scale=dash_scale, legend=None),
    )
)

vertical_rule = (
    alt.Chart(peaks.head(1))
    .mark_rule(strokeDash=[6, 4], strokeWidth=1.5, color=INK_MUTED)
    .encode(x=alt.X(P.translate(ESCAPE), type="quantitative"))
)

annotation_point = (
    alt.Chart(peaks)
    .mark_point(size=150, filled=True, color=INK, opacity=0.75)
    .encode(x=alt.X(P.translate(ESCAPE), type="quantitative"), y=alt.Y(IMPURITY.translate(ESCAPE), type="quantitative"))
)

annotation_text = [
    alt.Chart(peaks.iloc[[i]])
    .mark_text(fontSize=10, dx=10, dy=dy, align="left", fontWeight="bold", color=INK)
    .encode(
        x=alt.X(P.translate(ESCAPE), type="quantitative"),
        y=alt.Y(IMPURITY.translate(ESCAPE), type="quantitative"),
        text="label:N",
    )
    for i, dy in enumerate([30, -16])
]

chart = (
    alt.layer(area_fill, lines, vertical_rule, annotation_point, *annotation_text)
    .properties(
        width=800,
        height=450,
        autosize=alt.AutoSizeParams(type="fit", contains="padding"),
        padding=10,
        background=PAGE_BG,
        title=alt.Title(title_text, fontSize=title_fontsize, color=INK),
    )
    .configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.13,
        labelColor=INK_SOFT,
        titleColor=INK,
        domain=False,
    )
    .configure_legend(
        fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK, labelFontSize=10, padding=8
    )
    .configure_title(color=INK, fontSize=title_fontsize)
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")
