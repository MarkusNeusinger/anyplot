"""anyplot.ai
survival-kaplan-meier: Kaplan-Meier Survival Plot
Library: altair 6.1.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-11
"""

import os

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

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
Z_95 = 1.96  # normal quantile for the 95% confidence interval
SURVIVAL = "Survival Probability"  # derived by the Kaplan-Meier estimate below

# Columns: set these to your table's column names
TIME = "Time (Months)"  # role: time
EVENT = "Event observed"  # role: event
GROUP = "Treatment group"  # role: group

# Data: replace this block with your own table, for example df = pd.read_csv("trial.csv")
# (EVENT: 1 = event occurred, 0 = censored)
np.random.seed(42)
n_per_group = 80

# Treatment A (better survival)
time_a = np.clip(np.random.exponential(scale=24, size=n_per_group), 1, 36)
event_a = np.random.binomial(1, 0.65, size=n_per_group)

# Treatment B (standard)
time_b = np.clip(np.random.exponential(scale=16, size=n_per_group), 1, 36)
event_b = np.random.binomial(1, 0.75, size=n_per_group)

df = pd.DataFrame(
    {
        TIME: np.concatenate([time_a, time_b]),
        EVENT: np.concatenate([event_a, event_b]),
        GROUP: ["Treatment A"] * n_per_group + ["Treatment B"] * n_per_group,
    }
)

# Plot: reads only df and the constants above
LOWER, UPPER = "CI lower", "CI upper"
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
groups = list(df[GROUP].unique())

# Kaplan-Meier estimate per group, with Greenwood confidence bands
km_rows = []
censor_rows = []
for group_name in groups:
    sub = df[df[GROUP] == group_name].dropna(subset=[TIME, EVENT])
    order = np.argsort(sub[TIME].to_numpy())
    time = sub[TIME].to_numpy()[order]
    event = sub[EVENT].to_numpy()[order]

    survival = 1.0
    var_sum = 0.0
    steps = [(0.0, 1.0, 1.0, 1.0)]
    for t in np.unique(time[event == 1]):
        at_risk = np.sum(time >= t)
        events = np.sum((time == t) & (event == 1))
        survival *= (at_risk - events) / at_risk
        if at_risk > events:
            var_sum += events / (at_risk * (at_risk - events))
        se = survival * np.sqrt(var_sum)
        steps.append((t, survival, max(0.0, survival - Z_95 * se), min(1.0, survival + Z_95 * se)))
    # Extend the last step to the end of follow-up
    steps.append((time.max(), *steps[-1][1:]))

    for t, s, lo, hi in steps:
        km_rows.append({TIME: t, SURVIVAL: s, LOWER: lo, UPPER: hi, GROUP: group_name})

    # Censored observations sit on the curve at their censoring time
    step_times = np.array([s[0] for s in steps])
    step_surv = np.array([s[1] for s in steps])
    for t in time[event == 0]:
        censor_rows.append(
            {TIME: t, SURVIVAL: step_surv[np.searchsorted(step_times, t, side="right") - 1], GROUP: group_name}
        )

km_df = pd.DataFrame(km_rows)
censored_df = pd.DataFrame(censor_rows, columns=[TIME, SURVIVAL, GROUP])

group_scale = alt.Scale(domain=groups, range=IMPRINT_PALETTE)
color = alt.Color(GROUP.translate(ESCAPE), type="nominal", title=GROUP, sort=None, scale=group_scale)
x_axis = alt.X(
    TIME.translate(ESCAPE),
    type="quantitative",
    title=TIME,
    scale=alt.Scale(domain=[0, df[TIME].max() * 1.05], nice=False),
)

# Confidence interval bands, stepping with their curves
ci_band = (
    alt.Chart(km_df)
    .mark_area(interpolate="step-after", opacity=0.25)
    .encode(x=x_axis, y=alt.Y(LOWER.translate(ESCAPE), type="quantitative", title=SURVIVAL), y2=UPPER, color=color)
)

# Survival step curves
survival_line = (
    alt.Chart(km_df)
    .mark_line(interpolate="step-after", strokeWidth=3)
    .encode(
        x=x_axis,
        y=alt.Y(SURVIVAL.translate(ESCAPE), type="quantitative", title=SURVIVAL, scale=alt.Scale(domain=[0, 1])),
        color=color,
    )
)

# Censored observations as tick marks on the curve
censor_marks = (
    alt.Chart(censored_df)
    .mark_tick(thickness=2, size=12)
    .encode(x=x_axis, y=alt.Y(SURVIVAL.translate(ESCAPE), type="quantitative", title=SURVIVAL), color=color)
)

# Style
chart = (
    (ci_band + survival_line + censor_marks)
    .properties(
        width=555,
        height=360,
        background=PAGE_BG,
        title=alt.Title(
            "survival-kaplan-meier · python · altair · anyplot.ai", fontSize=18, anchor="middle", offset=12
        ),
    )
    .configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelFontSize=12,
        titleFontSize=14,
        labelColor=INK_SOFT,
        titleColor=INK,
    )
    .configure_title(color=INK)
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        titleFontSize=13,
        labelFontSize=12,
        strokeWidth=1,
        padding=8,
    )
)

# Output: render, then pad (never crop) to the 3200 x 1800 target canvas
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

TARGET_W, TARGET_H = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
w, h = img.size
if w > TARGET_W or h > TARGET_H:
    raise SystemExit(f"altair rendered {w}x{h}, exceeds {TARGET_W}x{TARGET_H}; shrink width/height")
if (w, h) != (TARGET_W, TARGET_H):
    canvas = Image.new("RGB", (TARGET_W, TARGET_H), PAGE_BG)
    canvas.paste(img, ((TARGET_W - w) // 2, (TARGET_H - h) // 2))
    canvas.save(f"plot-{THEME}.png")
