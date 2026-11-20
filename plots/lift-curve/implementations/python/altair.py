"""anyplot.ai
lift-curve: Model Lift Chart
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-10
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

# Imprint palette: first series is the brand green
BRAND = "#009E73"

# Constants
REFERENCE_LIFT = 1.0  # lift of random selection
REFERENCE_COLOR = INK_SOFT  # theme-adaptive neutral for the baseline

# Columns: set these to your table's column names
Y_TRUE = "Churned (0/1)"  # role: y_true
Y_SCORE = "Model score"  # role: y_score
POPULATION = "Population targeted (%)"  # role: extra
LIFT = "Cumulative lift"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
# Customer churn model: churners (20%) tend to receive higher scores, with overlap
np.random.seed(42)
df = pd.DataFrame(
    {
        Y_TRUE: np.concatenate([np.ones(200), np.zeros(800)]),
        Y_SCORE: np.concatenate([np.random.beta(5, 2, 200), np.random.beta(2, 5, 800)]),
    }
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})

ranked = df.sort_values(Y_SCORE, ascending=False)[Y_TRUE].to_numpy()
n_total = len(ranked)
baseline_rate = np.nanmean(ranked)
percentages = np.arange(1, 101)
n_selected = np.ceil(n_total * percentages / 100).astype(int)
captured = np.cumsum(ranked)[n_selected - 1]
lift = (captured / n_selected) / baseline_rate
curve = pd.DataFrame({POPULATION: percentages, LIFT: lift})
deciles = curve[curve[POPULATION] % 10 == 0]

x_axis = alt.X(POPULATION.translate(ESCAPE), type="quantitative", title=POPULATION, scale=alt.Scale(domain=[0, 100]))
y_axis = alt.Y(
    LIFT.translate(ESCAPE),
    type="quantitative",
    title=LIFT,
    scale=alt.Scale(domain=[0, max(curve[LIFT].max(), REFERENCE_LIFT) * 1.08]),
)

lift_line = alt.Chart(curve).mark_line(strokeWidth=3, color=BRAND).encode(x=x_axis, y=y_axis)

reference_line = (
    alt.Chart(pd.DataFrame({LIFT: [REFERENCE_LIFT]}))
    .mark_rule(strokeWidth=2, strokeDash=[8, 4], color=REFERENCE_COLOR)
    .encode(y=alt.Y(LIFT.translate(ESCAPE), type="quantitative", title=LIFT))
)

decile_points = (
    alt.Chart(deciles)
    .mark_point(size=60, filled=True, color=BRAND, stroke=PAGE_BG, strokeWidth=1)
    .encode(
        x=x_axis,
        y=y_axis,
        tooltip=[
            alt.Tooltip(POPULATION.translate(ESCAPE), type="quantitative", title=POPULATION, format=".0f"),
            alt.Tooltip(LIFT.translate(ESCAPE), type="quantitative", title=LIFT, format=".2f"),
        ],
    )
)

chart = (
    alt.layer(reference_line, lift_line, decile_points)
    .properties(
        width=620,
        height=320,
        background=PAGE_BG,
        title=alt.Title("lift-curve · python · altair · anyplot.ai", fontSize=16, anchor="middle"),
    )
    .configure_axis(
        labelFontSize=10,
        titleFontSize=12,
        labelColor=INK_SOFT,
        titleColor=INK,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT)
    .configure_title(color=INK)
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Pad (never crop) to the canonical landscape canvas
TARGET_W, TARGET_H = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
w, h = img.size
if w > TARGET_W or h > TARGET_H:
    raise SystemExit(f"altair produced {w}x{h}, exceeds {TARGET_W}x{TARGET_H}; shrink width/height")
if (w, h) != (TARGET_W, TARGET_H):
    canvas = Image.new("RGB", (TARGET_W, TARGET_H), PAGE_BG)
    canvas.paste(img, ((TARGET_W - w) // 2, (TARGET_H - h) // 2))
    canvas.save(f"plot-{THEME}.png")
