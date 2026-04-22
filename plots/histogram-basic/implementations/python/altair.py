""" pyplots.ai
histogram-basic: Basic Histogram
Library: altair 6.0.0 | Python 3.14.0
Quality: 95/100 | Created: 2025-12-23
"""

import altair as alt
import numpy as np
import pandas as pd


# Data
np.random.seed(42)
primary = np.random.normal(loc=170, scale=7, size=350)
taller = np.random.normal(loc=186, scale=4.5, size=150)
values = np.concatenate([primary, taller])  # Heights in cm — bimodal distribution

df = pd.DataFrame({"height": values})

# Compute peak locations for annotations
primary_peak = np.median(primary)
taller_peak = np.median(taller)

# Histogram bars
bars = (
    alt.Chart(df)
    .mark_bar(color="#306998", stroke="#1e4a6e", strokeWidth=0.6, cornerRadiusTopLeft=2, cornerRadiusTopRight=2)
    .encode(
        alt.X("height:Q", bin=alt.Bin(maxbins=30), title="Height (cm)"),
        alt.Y("count()", title="Frequency"),
        tooltip=[
            alt.Tooltip("height:Q", bin=alt.Bin(maxbins=30), title="Height Range"),
            alt.Tooltip("count()", title="Count"),
        ],
    )
)

# Annotation data for the two peaks
peaks_df = pd.DataFrame(
    {
        "x": [primary_peak, taller_peak],
        "label": [
            f"Primary group (\u03bc \u2248 {primary_peak:.0f} cm, n=350)",
            f"Taller subgroup (\u03bc \u2248 {taller_peak:.0f} cm, n=150)",
        ],
        "y_offset": [50, 32],
    }
)

# Vertical rule lines at peak locations
rules = (
    alt.Chart(peaks_df)
    .mark_rule(strokeDash=[6, 4], strokeWidth=1.5, opacity=0.7)
    .encode(x="x:Q", color=alt.value("#8B4513"))
)

# Peak labels — primary on left side, taller on right side of their respective lines
primary_label = (
    alt.Chart(peaks_df.iloc[[0]])
    .mark_text(align="left", dx=10, fontSize=16, fontWeight="bold")
    .encode(x="x:Q", y="y_offset:Q", text="label:N", color=alt.value("#5a3010"))
)

taller_label = (
    alt.Chart(peaks_df.iloc[[1]])
    .mark_text(align="right", dx=-10, fontSize=16, fontWeight="bold")
    .encode(x="x:Q", y="y_offset:Q", text="label:N", color=alt.value("#5a3010"))
)

# Mean line
mean_val = df["height"].mean()
mean_df = pd.DataFrame({"x": [mean_val], "label": [f"Mean: {mean_val:.1f} cm"]})

mean_rule = (
    alt.Chart(mean_df)
    .mark_rule(strokeDash=[2, 2], strokeWidth=1.2, opacity=0.5)
    .encode(x="x:Q", color=alt.value("#333333"))
)

mean_label = (
    alt.Chart(mean_df)
    .mark_text(align="left", dx=8, dy=0, fontSize=14, fontStyle="italic")
    .encode(x="x:Q", y=alt.datum(42), text="label:N", color=alt.value("#666666"))
)

# Layer all elements
chart = (
    (bars + rules + primary_label + taller_label + mean_rule + mean_label)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "histogram-basic \u00b7 altair \u00b7 pyplots.ai",
            fontSize=28,
            subtitle="Distribution of human heights — bimodal pattern with primary and taller subgroups",
            subtitleFontSize=16,
            subtitleColor="#666666",
            anchor="start",
            offset=12,
        ),
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, titleColor="#333333", labelColor="#555555", grid=False)
    .configure_axisY(grid=True, gridColor="#dddddd", gridOpacity=0.4, gridDash=[4, 4])
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
