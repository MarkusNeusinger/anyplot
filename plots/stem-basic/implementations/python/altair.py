""" anyplot.ai
stem-basic: Basic Stem Plot
Library: altair 6.1.0 | Python 3.13.13
Quality: 89/100 | Updated: 2026-04-30
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
BRAND = "#009E73"  # Okabe-Ito position 1

# Data — acoustic impulse response samples
np.random.seed(42)
n_samples = 30
sample_index = np.arange(n_samples)
amplitude = np.exp(-sample_index / 8) * np.cos(sample_index * 0.9) + np.random.randn(n_samples) * 0.03

df = pd.DataFrame({"n": sample_index, "amplitude": amplitude, "baseline": 0.0})

# Decay envelope — highlights the exponential decay story
n_env = np.linspace(0, n_samples - 1, 200)
env_df = pd.DataFrame({"n": n_env, "upper": np.exp(-n_env / 8), "lower": -np.exp(-n_env / 8)})

# Shaded decay region (subtle background emphasis)
envelope_area = (
    alt.Chart(env_df)
    .mark_area(color=BRAND, opacity=0.07)
    .encode(x=alt.X("n:Q"), y=alt.Y("upper:Q"), y2=alt.Y2("lower:Q"))
)

# Dashed bounds of the decay envelope
envelope_upper = (
    alt.Chart(env_df)
    .mark_line(color=INK_SOFT, strokeWidth=1.5, strokeDash=[5, 4], opacity=0.45)
    .encode(x=alt.X("n:Q"), y=alt.Y("upper:Q"))
)

envelope_lower = (
    alt.Chart(env_df)
    .mark_line(color=INK_SOFT, strokeWidth=1.5, strokeDash=[5, 4], opacity=0.45)
    .encode(x=alt.X("n:Q"), y=alt.Y("lower:Q"))
)

# Baseline rule at y=0
baseline_rule = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(color=INK_SOFT, strokeWidth=1.5).encode(y=alt.Y("y:Q"))

# Stems: vertical rules from baseline to each data point
stems = (
    alt.Chart(df)
    .mark_rule(color=BRAND, strokeWidth=2.5, opacity=0.85)
    .encode(
        x=alt.X("n:Q", title="Sample Index (n)", axis=alt.Axis(labelFontSize=18, titleFontSize=22)),
        y=alt.Y("baseline:Q"),
        y2=alt.Y2("amplitude:Q"),
    )
)

# Markers at the tip of each stem
markers = (
    alt.Chart(df)
    .mark_circle(color=BRAND, size=300, stroke=PAGE_BG, strokeWidth=2)
    .encode(
        x=alt.X("n:Q"),
        y=alt.Y("amplitude:Q", title="Amplitude (a.u.)", axis=alt.Axis(labelFontSize=18, titleFontSize=22)),
        tooltip=[
            alt.Tooltip("n:Q", title="Sample (n)"),
            alt.Tooltip("amplitude:Q", title="Amplitude (a.u.)", format=".3f"),
        ],
    )
)

# Compose and apply theme-adaptive chrome
chart = (
    (envelope_area + envelope_upper + envelope_lower + baseline_rule + stems + markers)
    .properties(
        width=1600,
        height=900,
        background=PAGE_BG,
        title=alt.Title("stem-basic · altair · anyplot.ai", fontSize=28, anchor="middle", color=INK),
    )
    .configure_view(fill=PAGE_BG, stroke=None)
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
    .configure_axisX(grid=False)
    .configure_title(color=INK, fontSize=28)
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
