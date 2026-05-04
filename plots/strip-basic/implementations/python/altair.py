"""anyplot.ai
strip-basic: Basic Strip Plot
Library: altair | Python 3.13
Quality: pending | Created: 2026-05-04
"""

import os

import altair as alt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

BRAND = "#009E73"  # Okabe-Ito position 1 — always first series
ACCENT = "#D55E00"  # Okabe-Ito position 2 — mean markers

# Data — survey response scores by department
np.random.seed(42)

departments = ["Engineering", "Marketing", "Sales", "Support"]
distributions = {"Engineering": (75, 10), "Marketing": (68, 15), "Sales": (72, 12), "Support": (65, 18)}

rows = []
for dept in departments:
    mean, std = distributions[dept]
    n = np.random.randint(35, 50)
    scores = np.clip(np.random.normal(mean, std, n), 20, 100)
    for score in scores:
        rows.append({"Department": dept, "Response Score": score})

df = pd.DataFrame(rows)

means = df.groupby("Department")["Response Score"].mean().reset_index()
means.columns = ["Department", "Mean"]
means["Label"] = "Group Mean"

# Strip chart with Gaussian jitter via transform_calculate
strip = (
    alt.Chart(df)
    .mark_circle(size=200, opacity=0.6, color=BRAND)
    .encode(
        x=alt.X("Department:N", title="Department", axis=alt.Axis(labelAngle=0)),
        y=alt.Y("Response Score:Q", title="Response Score", scale=alt.Scale(domain=[20, 105])),
        xOffset="jitter:Q",
        tooltip=["Department:N", alt.Tooltip("Response Score:Q", format=".1f")],
    )
    .transform_calculate(jitter="sqrt(-2*log(random()))*cos(2*PI*random())*0.2")
)

# Mean reference ticks with legend entry
mean_ticks = (
    alt.Chart(means)
    .mark_tick(thickness=3, size=45)
    .encode(
        x=alt.X("Department:N"),
        y=alt.Y("Mean:Q"),
        color=alt.Color(
            "Label:N",
            scale=alt.Scale(domain=["Group Mean"], range=[ACCENT]),
            legend=alt.Legend(title="", labelFontSize=16, symbolType="stroke", symbolStrokeWidth=3, symbolSize=200),
        ),
        tooltip=[alt.Tooltip("Mean:Q", format=".1f", title="Group Mean")],
    )
)

# Combine and apply theme-adaptive chrome
chart = (
    alt.layer(strip, mean_ticks)
    .properties(
        width=1600, height=900, title=alt.Title("strip-basic · altair · anyplot.ai", fontSize=28), background=PAGE_BG
    )
    .configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=18,
        titleFontSize=22,
    )
    .configure_title(color=INK)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
