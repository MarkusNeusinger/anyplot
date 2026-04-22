""" pyplots.ai
line-growth-percentile: Pediatric Growth Chart with Percentile Curves
Library: altair 6.0.0 | Python 3.14.3
Quality: 91/100 | Created: 2026-03-19
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - WHO-style weight-for-age reference for boys, 0-36 months
np.random.seed(42)
age_months = np.arange(0, 37, 1)

# Approximate WHO weight-for-age percentiles for boys (kg)
median = 3.3 + 7.5 * (1 - np.exp(-0.08 * age_months)) + 0.12 * age_months
sd_base = 0.35 + 0.03 * age_months

percentile_names = ["P3", "P10", "P25", "P50", "P75", "P90", "P97"]
z_scores = [-1.88, -1.28, -0.67, 0.0, 0.67, 1.28, 1.88]

ref_df = pd.DataFrame({"age_months": age_months})
for name, z in zip(percentile_names, z_scores, strict=True):
    ref_df[name] = median + z * sd_base

# Individual patient data - a healthy boy tracked at well-child visits
patient_ages = np.array([0, 1, 2, 4, 6, 9, 12, 15, 18, 24, 30, 36])
patient_weights = np.array([3.5, 4.6, 5.7, 7.2, 8.3, 9.5, 10.4, 11.2, 12.0, 13.1, 14.3, 15.6])
patient_df = pd.DataFrame({"age_months": patient_ages, "weight": patient_weights})

# --- Percentile bands as separate area layers with graduated opacity ---
band_defs = [
    ("P3", "P10", 0.15),
    ("P10", "P25", 0.24),
    ("P25", "P75", 0.38),
    ("P75", "P90", 0.24),
    ("P90", "P97", 0.15),
]

band_layers = []
for lower, upper, opacity in band_defs:
    band = (
        alt.Chart(ref_df)
        .mark_area(opacity=opacity, color="#306998")
        .encode(x=alt.X("age_months:Q"), y=alt.Y(f"{lower}:Q"), y2=alt.Y2(f"{upper}:Q"))
    )
    band_layers.append(band)

# --- Percentile lines using transform_fold (idiomatic Altair) ---
line_base = alt.Chart(ref_df).transform_fold(fold=percentile_names, as_=["percentile", "weight"])

# P50 emphasized line
p50_line = (
    line_base.transform_filter(alt.datum.percentile == "P50")
    .mark_line(strokeWidth=3.0, opacity=1.0)
    .encode(x=alt.X("age_months:Q"), y=alt.Y("weight:Q"), color=alt.value("#1a4971"))
)

# Other percentile lines
other_lines = (
    line_base.transform_filter(alt.datum.percentile != "P50")
    .mark_line(strokeWidth=1.0, opacity=0.5)
    .encode(x=alt.X("age_months:Q"), y=alt.Y("weight:Q"), color=alt.value("#306998"), detail="percentile:N")
)

# --- Right-margin percentile labels with vertical nudging to avoid crowding ---
label_values = {p: ref_df[p].iloc[-1] for p in percentile_names}

# Nudge labels apart where P25/P50/P75 cluster together
nudge = {"P3": 0, "P10": 0, "P25": -0.3, "P50": 0.05, "P75": 0.35, "P90": 0, "P97": 0}
label_df = pd.DataFrame(
    {
        "age_months": [37.2] * 7,
        "value": [label_values[p] + nudge[p] for p in percentile_names],
        "label": percentile_names,
    }
)

percentile_text = (
    alt.Chart(label_df)
    .mark_text(
        align="left", dx=4, fontSize=15, fontWeight="bold", color="#1a4971", font="Helvetica Neue, Arial, sans-serif"
    )
    .encode(x=alt.X("age_months:Q"), y=alt.Y("value:Q"), text="label:N")
)

# --- Patient trajectory with selection highlight (distinctive Altair feature) ---
nearest = alt.selection_point(nearest=True, on="pointerover", fields=["age_months"], empty=False)

patient_line = (
    alt.Chart(patient_df)
    .mark_line(color="#D64541", strokeWidth=2.5, interpolate="monotone")
    .encode(x=alt.X("age_months:Q"), y=alt.Y("weight:Q"))
)

patient_points = (
    alt.Chart(patient_df)
    .mark_circle(color="#D64541", stroke="white", strokeWidth=2)
    .encode(
        x=alt.X("age_months:Q"),
        y=alt.Y("weight:Q"),
        size=alt.condition(nearest, alt.value(200), alt.value(100)),
        tooltip=[
            alt.Tooltip("age_months:Q", title="Age (months)"),
            alt.Tooltip("weight:Q", title="Weight (kg)", format=".1f"),
        ],
    )
    .add_params(nearest)
)

# Patient label positioned above the last point to avoid overlap with P75
patient_label = (
    alt.Chart(pd.DataFrame({"age_months": [33], "weight": [15.3], "label": ["Patient A"]}))
    .mark_text(
        align="left",
        dx=4,
        dy=-14,
        fontSize=14,
        fontWeight="bold",
        color="#D64541",
        font="Helvetica Neue, Arial, sans-serif",
    )
    .encode(x=alt.X("age_months:Q"), y=alt.Y("weight:Q"), text="label:N")
)

# --- Compose all layers ---
chart = (
    alt.layer(*band_layers, other_lines, p50_line, percentile_text, patient_line, patient_points, patient_label)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "line-growth-percentile · altair · pyplots.ai",
            fontSize=28,
            font="Helvetica Neue, Arial, sans-serif",
            subtitle=["Boys Weight-for-Age (0–36 months)", "WHO Reference Standard · Individual Patient Overlay"],
            subtitleFontSize=16,
            subtitleColor="#7f8c8d",
            anchor="start",
            offset=12,
        ),
    )
    .configure_axis(
        labelFontSize=18,
        titleFontSize=22,
        titleColor="#2c3e50",
        labelColor="#555555",
        gridColor="#e8e8e8",
        gridOpacity=0.6,
        gridDash=[4, 4],
        domainColor="#aaaaaa",
        tickColor="#aaaaaa",
        titlePadding=12,
    )
    .configure_axisX(grid=False, tickCount=12)
    .configure_axisY(grid=True, tickCount=8)
    .configure_view(strokeWidth=0, fill="#f7f9fb")
    .resolve_scale(y="shared")
    .encode(
        x=alt.X("age_months:Q", title="Age (months)", scale=alt.Scale(domain=[0, 39])),
        y=alt.Y(title="Weight (kg)", scale=alt.Scale(domain=[0, 19])),
    )
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.interactive().save("plot.html")
