""" anyplot.ai
gain-curve: Cumulative Gains Chart
Library: altair 6.3.0 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-21
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette
BRAND = "#009E73"  # Model curve (position 1)

# Setup
TARGET_W, TARGET_H = 3200, 1800
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})

# Column constants
Y_TRUE = "y_true"  # role: y_true
Y_SCORE = "y_score"  # role: y_score

# Data: simulated fraud-detection scores and outcomes
rng = np.random.default_rng(42)
n_samples = 1500
base_score = rng.beta(2, 5, n_samples)
score = np.clip(base_score + rng.normal(0, 0.1, n_samples), 0, 1)
outcome = (rng.random(n_samples) < 0.5 * score + 0.02).astype(int)
df = pd.DataFrame({Y_TRUE: outcome, Y_SCORE: score})

# Plot: cumulative gains, ranked by score descending
POPULATION = "Population Targeted (%)"
GAIN = "Positive Cases Captured (%)"
SERIES = "Series"
ranked = df.sort_values(Y_SCORE, ascending=False)[Y_TRUE].to_numpy()
n_rows = len(ranked)
gains = pd.concat(
    [
        pd.DataFrame(
            {
                POPULATION: np.arange(0, n_rows + 1) / n_rows * 100,
                GAIN: np.concatenate([[0], np.nancumsum(ranked)]) / np.nansum(ranked) * 100,
                SERIES: "Model",
            }
        ),
        pd.DataFrame({POPULATION: [0.0, 100.0], GAIN: [0.0, 100.0], SERIES: "Random baseline"}),
    ],
    ignore_index=True,
)

series_order = list(gains[SERIES].unique())
x_enc = alt.X(
    POPULATION.translate(ESCAPE),
    type="quantitative",
    title=POPULATION,
    scale=alt.Scale(domain=[0, gains[POPULATION].max()], nice=False),
    axis=alt.Axis(tickCount=10),
)
y_enc = alt.Y(
    GAIN.translate(ESCAPE),
    type="quantitative",
    title=GAIN,
    scale=alt.Scale(domain=[0, gains[GAIN].max()], nice=False),
    axis=alt.Axis(tickCount=10),
)

area = (
    alt.Chart(gains)
    .transform_filter(alt.datum[SERIES] == series_order[0])
    .mark_area(opacity=0.15, color=BRAND)
    .encode(x=x_enc, y=y_enc)
)

lines = (
    alt.Chart(gains)
    .mark_line(strokeWidth=4)
    .encode(
        x=x_enc,
        y=y_enc,
        color=alt.Color(
            SERIES,
            type="nominal",
            title=None,
            sort=None,
            scale=alt.Scale(domain=series_order, range=[BRAND, INK_SOFT]),
            legend=alt.Legend(orient="bottom-right", direction="vertical", symbolStrokeWidth=4),
        ),
        strokeDash=alt.StrokeDash(
            SERIES,
            type="nominal",
            sort=None,
            scale=alt.Scale(domain=series_order, range=[[1, 0], [10, 6]]),
            legend=None,
        ),
        order=alt.value(0),
    )
)

chart = (
    alt.layer(area, lines)
    .properties(
        width=620,
        height=320,
        background=PAGE_BG,
        title=alt.Title("gain-curve · python · altair · anyplot.ai", fontSize=16, anchor="middle", color=INK),
    )
    .configure_axis(
        gridColor=INK,
        gridOpacity=0.12,
        gridDash=[2, 2],
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=12,
        titleFontSize=14,
    )
    .configure_legend(labelColor=INK, labelFontSize=12, symbolSize=600, rowPadding=6)
    .configure_view(strokeWidth=0, fill=PAGE_BG)
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TARGET_W or img.height > TARGET_H:
    scale = min(TARGET_W / img.width, TARGET_H / img.height)
    img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
canvas = Image.new("RGB", (TARGET_W, TARGET_H), PAGE_BG)
canvas.paste(img, ((TARGET_W - img.width) // 2, (TARGET_H - img.height) // 2))
canvas.save(f"plot-{THEME}.png")
