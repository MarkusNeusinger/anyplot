"""anyplot.ai
raincloud-basic: Basic Raincloud Plot
Library: altair 6.3.0 | Python 3.14.10
Quality: 85/100 | Updated: 2026-11-26
"""

import os
import sys


# Avoid shadowing the installed altair package with this file's directory
sys.path[:] = [p for p in sys.path if os.path.realpath(p or ".") != os.path.dirname(os.path.realpath(__file__))]

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette (positions 1-8)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
SEMANTIC_RED = "#AE3030"  # Imprint position 5 — median marker

# Constants
ROW_SPACING = 1.5  # distance between category baselines on the y scale
CLOUD_SCALE = 100  # density-to-height factor for the half violin
JITTER = (-0.22, -0.08)  # rain falls below the baseline

# Columns
CONDITION = "Condition"  # role: category
REACTION_TIME = "Reaction Time (ms)"  # role: value

# Data: reaction times (ms) across three experimental conditions
np.random.seed(42)
df = pd.DataFrame(
    {
        CONDITION: ["Control"] * 80 + ["Treatment A"] * 80 + ["Treatment B"] * 80,
        REACTION_TIME: np.concatenate(
            [
                np.random.normal(450, 60, 80),
                np.random.normal(380, 50, 80),
                np.concatenate([np.random.normal(340, 25, 50), np.random.normal(460, 35, 30)]),
            ]
        ),
    }
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
COND, RT = CONDITION.translate(ESCAPE), REACTION_TIME.translate(ESCAPE)

conditions = list(dict.fromkeys(df[CONDITION]))
palette = [IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] for i in range(len(conditions))]
baseline = {c: i * ROW_SPACING for i, c in enumerate(conditions)}
df["baseline"] = df[CONDITION].map(baseline)
df["rain_y"] = df["baseline"] + np.random.uniform(JITTER[0], JITTER[1], len(df))

stats = (
    df.groupby(CONDITION, sort=False)[REACTION_TIME]
    .agg(q1=lambda s: s.quantile(0.25), median="median", q3=lambda s: s.quantile(0.75), lo="min", hi="max")
    .reset_index()
)
iqr = stats["q3"] - stats["q1"]
stats["lower_w"] = np.maximum(stats["q1"] - 1.5 * iqr, stats["lo"])
stats["upper_w"] = np.minimum(stats["q3"] + 1.5 * iqr, stats["hi"])
stats["baseline"] = stats[CONDITION].map(baseline)

# Axis range reaches 3 standard deviations past each group, so every cloud tapers to near zero inside the axis
spread = df.groupby(CONDITION)[REACTION_TIME].agg(["mean", "std"])
x_lo = (spread["mean"] - 3 * spread["std"]).min()
x_hi = (spread["mean"] + 3 * spread["std"]).max()
x_domain = [float(np.floor(x_lo / 40) * 40), float(np.ceil(x_hi / 40) * 40)]
y_domain = [JITTER[0] - 0.3, baseline[conditions[-1]] + 1.2]

x_scale = alt.Scale(domain=x_domain)
y_scale = alt.Scale(domain=y_domain)
color = alt.Color(COND, type="nominal", scale=alt.Scale(domain=conditions, range=palette), legend=None)
x_enc = alt.X(RT, type="quantitative", title=REACTION_TIME, scale=x_scale, axis=alt.Axis(tickMinStep=40))

# Category labels sit on the baselines
label_expr = " : ".join(f"datum.value === {v} ? '{c}'" for c, v in baseline.items()) + " : ''"
y_axis = alt.Axis(
    values=list(baseline.values()),
    labelExpr=label_expr,
    title=None,
    labelFontSize=12,
    labelFontWeight="bold",
    labelColor=INK,
    labelPadding=8,
    domain=False,
    ticks=False,
    grid=False,
)

# Cloud: half violin rising above each baseline
cloud = (
    alt.Chart(df)
    .transform_density(RT, as_=[RT, "density"], groupby=[CONDITION.translate(ESCAPE), "baseline"], extent=x_domain)
    .transform_calculate(top=f"datum.baseline + 0.04 + datum.density * {CLOUD_SCALE}")
    .mark_area(orient="vertical", opacity=0.55, interpolate="monotone")
    .encode(
        x=x_enc,
        y=alt.Y("baseline:Q", axis=y_axis, scale=y_scale),
        y2="top:Q",
        color=color,
        tooltip=[
            alt.Tooltip(COND, type="nominal", title=CONDITION),
            alt.Tooltip(RT, type="quantitative", title=REACTION_TIME, format=".0f"),
        ],
    )
)

# Box: quartiles, median tick and whiskers on the baseline
y_base = alt.Y("baseline:Q", scale=y_scale)
whiskers = (
    alt.Chart(stats)
    .mark_rule(strokeWidth=1.2, color=INK_SOFT)
    .encode(x=alt.X("lower_w:Q", scale=x_scale), x2="upper_w:Q", y=y_base)
)
box = (
    alt.Chart(stats)
    .mark_bar(height=14, stroke=INK, strokeWidth=1.5, cornerRadius=2, fill=ELEVATED_BG, fillOpacity=0.95)
    .encode(x=alt.X("q1:Q", scale=x_scale), x2="q3:Q", y=y_base)
)
median = (
    alt.Chart(stats)
    .mark_tick(thickness=3, color=SEMANTIC_RED, orient="vertical", size=14)
    .encode(x=alt.X("median:Q", scale=x_scale), y=y_base)
)

# Rain: translucent jittered points below the baseline
rain = (
    alt.Chart(df)
    .mark_circle(size=40, opacity=0.55)
    .encode(
        x=x_enc,
        y=alt.Y("rain_y:Q", scale=y_scale),
        color=color,
        tooltip=[
            alt.Tooltip(COND, type="nominal", title=CONDITION),
            alt.Tooltip(RT, type="quantitative", title=REACTION_TIME, format=".1f"),
        ],
    )
)

chart = (
    alt.layer(cloud, whiskers, box, median, rain)
    .properties(
        width=800,
        height=450,
        autosize=alt.AutoSizeParams(type="fit", contains="padding"),
        padding=10,
        background=PAGE_BG,
        title=alt.Title("raincloud-basic · python · altair · anyplot.ai", fontSize=16, anchor="middle", color=INK),
    )
    .configure_view(fill=PAGE_BG, stroke=None)
    .configure_axis(
        labelFontSize=10,
        titleFontSize=12,
        titleFontWeight="bold",
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.15,
        labelColor=INK_SOFT,
        titleColor=INK,
    )
    .interactive()
)

# Save PNG, then fit to the canonical 3200×1800 canvas (no crop)
chart.save(f"plot-{THEME}.png", scale_factor=4.0)

TW, TH = 3200, 1800
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (TW, TH):
    _scale = min(1.0, TW / _img.width, TH / _img.height)
    _img = _img.resize((round(_img.width * _scale), round(_img.height * _scale)), Image.LANCZOS)
    _canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _img.width) // 2, (TH - _img.height) // 2))
    _canvas.save(f"plot-{THEME}.png")

# Save HTML (interactive)
chart.save(f"plot-{THEME}.html")
