""" pyplots.ai
spc-xbar-r: Statistical Process Control Chart (X-bar/R)
Library: altair 6.0.0 | Python 3.14.3
Quality: 83/100 | Created: 2026-03-19
"""

import altair as alt
import numpy as np
import pandas as pd


# Data: CNC shaft diameter measurements, subgroups of n=5
np.random.seed(42)
n_samples = 30
n_per_sample = 5
target_diameter = 25.0  # mm
process_std = 0.05  # mm

# Generate measurements with a few out-of-control points
measurements = np.random.normal(target_diameter, process_std, (n_samples, n_per_sample))

# Inject out-of-control shifts at samples 8, 17, 24
measurements[7] += 0.15  # Upward shift
measurements[16] -= 0.18  # Downward shift
measurements[23] += 0.20  # Upward shift

# Compute sample means (X-bar) and ranges (R)
sample_means = measurements.mean(axis=1)
sample_ranges = measurements.max(axis=1) - measurements.min(axis=1)

# Control chart constants for n=5
A2 = 0.577
D3 = 0.0
D4 = 2.114

# X-bar chart limits
xbar_bar = sample_means.mean()
r_bar = sample_ranges.mean()
xbar_ucl = xbar_bar + A2 * r_bar
xbar_lcl = xbar_bar - A2 * r_bar
xbar_upper_warn = xbar_bar + (2 / 3) * A2 * r_bar
xbar_lower_warn = xbar_bar - (2 / 3) * A2 * r_bar

# R chart limits
r_ucl = D4 * r_bar
r_lcl = D3 * r_bar
r_upper_warn = r_bar + (2 / 3) * (r_ucl - r_bar)
r_lower_warn = r_bar - (2 / 3) * (r_bar - r_lcl)

# Build dataframe
df_xbar = pd.DataFrame(
    {
        "sample": np.arange(1, n_samples + 1),
        "value": sample_means,
        "ucl": xbar_ucl,
        "lcl": xbar_lcl,
        "center": xbar_bar,
        "upper_warn": xbar_upper_warn,
        "lower_warn": xbar_lower_warn,
    }
)
df_xbar["out_of_control"] = (df_xbar["value"] > xbar_ucl) | (df_xbar["value"] < xbar_lcl)

df_range = pd.DataFrame(
    {
        "sample": np.arange(1, n_samples + 1),
        "value": sample_ranges,
        "ucl": r_ucl,
        "lcl": r_lcl,
        "center": r_bar,
        "upper_warn": r_upper_warn,
        "lower_warn": r_lower_warn,
    }
)
df_range["out_of_control"] = (df_range["value"] > r_ucl) | (df_range["value"] < r_lcl)

# Colors
blue = "#306998"
red = "#D62728"
warn_color = "#E8A838"

# --- X-bar Chart ---
xbar_x = alt.X("sample:Q", axis=alt.Axis(title="", labelFontSize=16, titleFontSize=20, tickMinStep=1))

xbar_line = (
    alt.Chart(df_xbar)
    .mark_line(color=blue, strokeWidth=2)
    .encode(
        x=xbar_x,
        y=alt.Y(
            "value:Q",
            scale=alt.Scale(zero=False),
            axis=alt.Axis(title="X-bar (mm)", labelFontSize=16, titleFontSize=20),
        ),
    )
)

xbar_points_normal = (
    alt.Chart(df_xbar[~df_xbar["out_of_control"]])
    .mark_point(color=blue, size=120, filled=True, stroke="white", strokeWidth=1)
    .encode(
        x="sample:Q",
        y="value:Q",
        tooltip=[alt.Tooltip("sample:Q", title="Sample"), alt.Tooltip("value:Q", title="X-bar", format=".4f")],
    )
)

xbar_points_ooc = (
    alt.Chart(df_xbar[df_xbar["out_of_control"]])
    .mark_point(color=red, size=200, filled=True, stroke="white", strokeWidth=1.5, shape="diamond")
    .encode(
        x="sample:Q",
        y="value:Q",
        tooltip=[alt.Tooltip("sample:Q", title="Sample"), alt.Tooltip("value:Q", title="X-bar (OOC)", format=".4f")],
    )
)

# Limit lines for X-bar
xbar_ucl_rule = alt.Chart(df_xbar).mark_rule(color=red, strokeDash=[8, 4], strokeWidth=2).encode(y="ucl:Q")

xbar_lcl_rule = alt.Chart(df_xbar).mark_rule(color=red, strokeDash=[8, 4], strokeWidth=2).encode(y="lcl:Q")

xbar_center_rule = alt.Chart(df_xbar).mark_rule(color="#333333", strokeWidth=2).encode(y="center:Q")

xbar_uwarn_rule = (
    alt.Chart(df_xbar)
    .mark_rule(color=warn_color, strokeDash=[4, 4], strokeWidth=1.5, opacity=0.7)
    .encode(y="upper_warn:Q")
)

xbar_lwarn_rule = (
    alt.Chart(df_xbar)
    .mark_rule(color=warn_color, strokeDash=[4, 4], strokeWidth=1.5, opacity=0.7)
    .encode(y="lower_warn:Q")
)

# Label data for X-bar limits
label_color_scale = alt.Scale(
    domain=["UCL", "LCL", "CL", "+2σ", "-2σ"], range=[red, red, "#333333", warn_color, warn_color]
)

xbar_labels_data = pd.DataFrame(
    {
        "sample": [n_samples + 0.5] * 5,
        "y": [xbar_ucl, xbar_lcl, xbar_bar, xbar_upper_warn, xbar_lower_warn],
        "label": ["UCL", "LCL", "CL", "+2σ", "-2σ"],
    }
)

xbar_labels = (
    alt.Chart(xbar_labels_data)
    .mark_text(align="left", dx=5, fontSize=14, fontWeight="bold")
    .encode(x="sample:Q", y="y:Q", text="label:N", color=alt.Color("label:N", scale=label_color_scale, legend=None))
)

xbar_chart = (
    xbar_line
    + xbar_points_normal
    + xbar_points_ooc
    + xbar_ucl_rule
    + xbar_lcl_rule
    + xbar_center_rule
    + xbar_uwarn_rule
    + xbar_lwarn_rule
    + xbar_labels
).properties(width=1600, height=400)

# --- R Chart ---
r_x = alt.X("sample:Q", axis=alt.Axis(title="Sample Number", labelFontSize=16, titleFontSize=20, tickMinStep=1))

r_line = (
    alt.Chart(df_range)
    .mark_line(color=blue, strokeWidth=2)
    .encode(
        x=r_x,
        y=alt.Y(
            "value:Q",
            scale=alt.Scale(zero=False),
            axis=alt.Axis(title="Range R (mm)", labelFontSize=16, titleFontSize=20),
        ),
    )
)

r_points_normal = (
    alt.Chart(df_range[~df_range["out_of_control"]])
    .mark_point(color=blue, size=120, filled=True, stroke="white", strokeWidth=1)
    .encode(
        x="sample:Q",
        y="value:Q",
        tooltip=[alt.Tooltip("sample:Q", title="Sample"), alt.Tooltip("value:Q", title="Range", format=".4f")],
    )
)

r_points_ooc = (
    alt.Chart(df_range[df_range["out_of_control"]])
    .mark_point(color=red, size=200, filled=True, stroke="white", strokeWidth=1.5, shape="diamond")
    .encode(
        x="sample:Q",
        y="value:Q",
        tooltip=[alt.Tooltip("sample:Q", title="Sample"), alt.Tooltip("value:Q", title="Range (OOC)", format=".4f")],
    )
)

# Limit lines for R chart
r_ucl_rule = alt.Chart(df_range).mark_rule(color=red, strokeDash=[8, 4], strokeWidth=2).encode(y="ucl:Q")

r_lcl_rule = alt.Chart(df_range).mark_rule(color=red, strokeDash=[4, 4], strokeWidth=1.5, opacity=0.5).encode(y="lcl:Q")

r_center_rule = alt.Chart(df_range).mark_rule(color="#333333", strokeWidth=2).encode(y="center:Q")

r_uwarn_rule = (
    alt.Chart(df_range)
    .mark_rule(color=warn_color, strokeDash=[4, 4], strokeWidth=1.5, opacity=0.7)
    .encode(y="upper_warn:Q")
)

r_lwarn_rule = (
    alt.Chart(df_range)
    .mark_rule(color=warn_color, strokeDash=[4, 4], strokeWidth=1.5, opacity=0.7)
    .encode(y="lower_warn:Q")
)

# Label data for R limits
r_labels_data = pd.DataFrame(
    {
        "sample": [n_samples + 0.5] * 5,
        "y": [r_ucl, r_lcl, r_bar, r_upper_warn, r_lower_warn],
        "label": ["UCL", "LCL", "CL", "+2σ", "-2σ"],
    }
)

r_labels = (
    alt.Chart(r_labels_data)
    .mark_text(align="left", dx=5, fontSize=14, fontWeight="bold")
    .encode(x="sample:Q", y="y:Q", text="label:N", color=alt.Color("label:N", scale=label_color_scale, legend=None))
)

r_chart = (
    r_line
    + r_points_normal
    + r_points_ooc
    + r_ucl_rule
    + r_lcl_rule
    + r_center_rule
    + r_uwarn_rule
    + r_lwarn_rule
    + r_labels
).properties(width=1600, height=400)

# Combine vertically
combined = alt.vconcat(xbar_chart, r_chart, spacing=20).properties(
    title=alt.Title("CNC Shaft Diameter Monitoring · spc-xbar-r · altair · pyplots.ai", fontSize=28, anchor="middle")
)

chart = combined.configure_axis(labelFontSize=16, titleFontSize=20).configure_view(strokeWidth=0)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
