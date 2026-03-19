""" pyplots.ai
line-growth-percentile: Pediatric Growth Chart with Percentile Curves
Library: altair 6.0.0 | Python 3.14.3
Quality: 89/100 | Created: 2026-03-19
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - WHO-style weight-for-age reference for boys, 0-36 months
np.random.seed(42)
age_months = np.arange(0, 37, 1)

# Approximate WHO weight-for-age percentiles for boys (kg)
# Based on realistic growth curves using logistic-like growth
median = 3.3 + 7.5 * (1 - np.exp(-0.08 * age_months)) + 0.12 * age_months
sd_base = 0.35 + 0.03 * age_months

percentile_values = {
    "P3": median - 1.88 * sd_base,
    "P10": median - 1.28 * sd_base,
    "P25": median - 0.67 * sd_base,
    "P50": median,
    "P75": median + 0.67 * sd_base,
    "P90": median + 1.28 * sd_base,
    "P97": median + 1.88 * sd_base,
}

# Build reference DataFrame
ref_df = pd.DataFrame({"age_months": age_months})
for label, vals in percentile_values.items():
    ref_df[label] = vals

# Individual patient data - a healthy boy tracked at well-child visits
patient_ages = np.array([0, 1, 2, 4, 6, 9, 12, 15, 18, 24, 30, 36])
# Tracking around 60th-75th percentile with some variation
patient_weights = np.array([3.5, 4.6, 5.7, 7.2, 8.3, 9.5, 10.4, 11.2, 12.0, 13.1, 14.3, 15.6])
patient_df = pd.DataFrame({"age_months": patient_ages, "weight": patient_weights})

# Percentile bands - create area layers between adjacent percentiles
band_pairs = [
    ("P3", "P10", "rgba(48, 105, 152, 0.12)"),
    ("P10", "P25", "rgba(48, 105, 152, 0.18)"),
    ("P25", "P75", "rgba(48, 105, 152, 0.25)"),
    ("P75", "P90", "rgba(48, 105, 152, 0.18)"),
    ("P90", "P97", "rgba(48, 105, 152, 0.12)"),
]

# Build long-form data for bands
band_layers = []
for lower, upper, fill_color in band_pairs:
    band = (
        alt.Chart(ref_df)
        .mark_area(opacity=1, color=fill_color)
        .encode(x=alt.X("age_months:Q"), y=alt.Y(f"{lower}:Q"), y2=alt.Y2(f"{upper}:Q"))
    )
    band_layers.append(band)

# Percentile lines - thin reference lines for each percentile
line_layers = []
percentile_labels_list = ["P3", "P10", "P25", "P50", "P75", "P90", "P97"]
line_opacities = [0.55, 0.6, 0.7, 1.0, 0.7, 0.6, 0.55]
line_widths = [1.0, 1.0, 1.0, 2.5, 1.0, 1.0, 1.0]

for pct, opacity, width in zip(percentile_labels_list, line_opacities, line_widths, strict=True):
    line = (
        alt.Chart(ref_df)
        .mark_line(color="#306998", strokeWidth=width, opacity=opacity)
        .encode(x=alt.X("age_months:Q"), y=alt.Y(f"{pct}:Q"))
    )
    line_layers.append(line)

# Percentile labels on the right margin
label_df = pd.DataFrame(
    {
        "age_months": [36.5] * 7,
        "value": [ref_df[p].iloc[-1] for p in percentile_labels_list],
        "label": percentile_labels_list,
    }
)

percentile_text = (
    alt.Chart(label_df)
    .mark_text(align="left", dx=6, fontSize=16, fontWeight="bold", color="#306998")
    .encode(x=alt.X("age_months:Q"), y=alt.Y("value:Q"), text="label:N")
)

# Patient trajectory line
patient_line = (
    alt.Chart(patient_df)
    .mark_line(color="#E74C3C", strokeWidth=2.5, point=False)
    .encode(x=alt.X("age_months:Q"), y=alt.Y("weight:Q"))
)

# Patient data points
patient_points = (
    alt.Chart(patient_df)
    .mark_circle(size=120, color="#E74C3C", stroke="white", strokeWidth=1.5)
    .encode(
        x=alt.X("age_months:Q"),
        y=alt.Y("weight:Q"),
        tooltip=[
            alt.Tooltip("age_months:Q", title="Age (months)"),
            alt.Tooltip("weight:Q", title="Weight (kg)", format=".1f"),
        ],
    )
)

# Compose all layers
chart = (
    alt.layer(*band_layers, *line_layers, percentile_text, patient_line, patient_points)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "line-growth-percentile · altair · pyplots.ai",
            fontSize=28,
            subtitle="Boys Weight-for-Age (0–36 months)",
            subtitleFontSize=18,
            subtitleColor="#666666",
        ),
    )
    .configure_axis(
        labelFontSize=18,
        titleFontSize=22,
        gridColor="#e0e0e0",
        gridOpacity=0.5,
        gridDash=[3, 3],
        domainColor="#888888",
        tickColor="#888888",
    )
    .configure_axisX(grid=False)
    .configure_axisY(grid=True)
    .configure_view(strokeWidth=0, fill="#f8fafc")
    .resolve_scale(y="shared")
    .encode(
        x=alt.X("age_months:Q", title="Age (months)", scale=alt.Scale(domain=[0, 38])), y=alt.Y(title="Weight (kg)")
    )
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.interactive().save("plot.html")
