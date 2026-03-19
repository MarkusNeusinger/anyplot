""" pyplots.ai
spc-xbar-r: Statistical Process Control Chart (X-bar/R)
Library: altair 6.0.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-19
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

measurements = np.random.normal(target_diameter, process_std, (n_samples, n_per_sample))

# Inject out-of-control shifts at samples 8, 17, 24
measurements[7] += 0.15
measurements[16] -= 0.18
measurements[23] += 0.20

sample_means = measurements.mean(axis=1)
sample_ranges = measurements.max(axis=1) - measurements.min(axis=1)

# Control chart constants for n=5
A2, D3, D4 = 0.577, 0.0, 2.114

# X-bar chart limits
xbar_bar = sample_means.mean()
r_bar = sample_ranges.mean()
xbar_ucl = xbar_bar + A2 * r_bar
xbar_lcl = xbar_bar - A2 * r_bar
xbar_uwarn = xbar_bar + (2 / 3) * A2 * r_bar
xbar_lwarn = xbar_bar - (2 / 3) * A2 * r_bar

# R chart limits
r_ucl = D4 * r_bar
r_lcl = D3 * r_bar
r_uwarn = r_bar + (2 / 3) * (r_ucl - r_bar)
r_lwarn = r_bar - (2 / 3) * (r_bar - r_lcl)

# Build dataframes
samples = np.arange(1, n_samples + 1)

df_xbar = pd.DataFrame(
    {
        "sample": samples,
        "value": sample_means,
        "ucl": xbar_ucl,
        "lcl": xbar_lcl,
        "center": xbar_bar,
        "uwarn": xbar_uwarn,
        "lwarn": xbar_lwarn,
    }
)
df_xbar["ooc"] = (df_xbar["value"] > xbar_ucl) | (df_xbar["value"] < xbar_lcl)

df_range = pd.DataFrame(
    {
        "sample": samples,
        "value": sample_ranges,
        "ucl": r_ucl,
        "lcl": r_lcl,
        "center": r_bar,
        "uwarn": r_uwarn,
        "lwarn": r_lwarn,
    }
)
df_range["ooc"] = (df_range["value"] > r_ucl) | (df_range["value"] < r_lcl)

# Colors — teal/vermillion for better colorblind accessibility
teal = "#306998"
vermillion = "#C03030"
amber = "#B8860B"
zone_fill = "#F0F4F8"

x_domain = [0, n_samples + 1]

# Zone shading data (±1σ, ±2σ bands) for X-bar
xbar_zone_1s = pd.DataFrame({"y": [xbar_bar - (1 / 3) * A2 * r_bar], "y2": [xbar_bar + (1 / 3) * A2 * r_bar]})
xbar_zone_2s = pd.DataFrame({"y": [xbar_lwarn], "y2": [xbar_uwarn]})

# Zone shading for R chart
r_zone_1s = pd.DataFrame({"y": [r_bar - (1 / 3) * (r_bar - r_lcl)], "y2": [r_bar + (1 / 3) * (r_ucl - r_bar)]})
r_zone_2s = pd.DataFrame({"y": [r_lwarn], "y2": [r_uwarn]})

# Label data for X-bar (inline, no helper function)
xbar_labels_df = pd.DataFrame(
    {
        "sample": [2] * 5,
        "y": [xbar_ucl, xbar_uwarn, xbar_bar, xbar_lwarn, xbar_lcl],
        "label": ["UCL", "+2σ", "CL", "−2σ", "LCL"],
        "ltype": ["limit", "warn", "center", "warn", "limit"],
    }
)

r_labels_df = pd.DataFrame(
    {
        "sample": [2] * 5,
        "y": [r_ucl, r_uwarn, r_bar, r_lwarn, r_lcl],
        "label": ["UCL", "+2σ", "CL", "−2σ", "LCL"],
        "ltype": ["limit", "warn", "center", "warn", "limit"],
    }
)

label_color_scale = alt.Scale(domain=["limit", "warn", "center"], range=[vermillion, amber, "#333333"])

# --- X-bar Chart ---
xbar_x = alt.X(
    "sample:Q",
    scale=alt.Scale(domain=x_domain, nice=False),
    axis=alt.Axis(title="", labelFontSize=16, titleFontSize=20, tickMinStep=1, grid=False),
)
xbar_y = alt.Y(
    "value:Q",
    scale=alt.Scale(zero=False),
    axis=alt.Axis(
        title="X̄  (mm)", labelFontSize=16, titleFontSize=20, gridColor="#E0E0E0", gridDash=[2, 4], gridOpacity=0.4
    ),
)

xbar_zone2 = alt.Chart(xbar_zone_2s).mark_rect(color=zone_fill, opacity=0.5).encode(y="y:Q", y2="y2:Q")
xbar_zone1 = alt.Chart(xbar_zone_1s).mark_rect(color=zone_fill, opacity=0.8).encode(y="y:Q", y2="y2:Q")

xbar_line = alt.Chart(df_xbar).mark_line(color=teal, strokeWidth=2).encode(x=xbar_x, y=xbar_y)

xbar_pts_normal = (
    alt.Chart(df_xbar[~df_xbar["ooc"]])
    .mark_point(color=teal, size=120, filled=True, stroke="white", strokeWidth=1)
    .encode(
        x="sample:Q",
        y="value:Q",
        tooltip=[alt.Tooltip("sample:Q", title="Sample"), alt.Tooltip("value:Q", title="X̄", format=".4f")],
    )
)

xbar_pts_ooc = (
    alt.Chart(df_xbar[df_xbar["ooc"]])
    .mark_point(color=vermillion, size=220, filled=True, stroke="white", strokeWidth=1.5, shape="diamond")
    .encode(
        x="sample:Q",
        y="value:Q",
        tooltip=[alt.Tooltip("sample:Q", title="Sample"), alt.Tooltip("value:Q", title="X̄ (OOC)", format=".4f")],
    )
)

xbar_ucl_rule = alt.Chart(df_xbar).mark_rule(color=vermillion, strokeDash=[8, 4], strokeWidth=2).encode(y="ucl:Q")
xbar_lcl_rule = alt.Chart(df_xbar).mark_rule(color=vermillion, strokeDash=[8, 4], strokeWidth=2).encode(y="lcl:Q")
xbar_center_rule = alt.Chart(df_xbar).mark_rule(color="#333333", strokeWidth=2.5).encode(y="center:Q")
xbar_uwarn_rule = (
    alt.Chart(df_xbar).mark_rule(color=amber, strokeDash=[4, 4], strokeWidth=1.5, opacity=0.7).encode(y="uwarn:Q")
)
xbar_lwarn_rule = (
    alt.Chart(df_xbar).mark_rule(color=amber, strokeDash=[4, 4], strokeWidth=1.5, opacity=0.7).encode(y="lwarn:Q")
)

xbar_labels = (
    alt.Chart(xbar_labels_df)
    .mark_text(align="left", dx=5, dy=-10, fontSize=16, fontWeight="bold")
    .encode(x="sample:Q", y="y:Q", text="label:N", color=alt.Color("ltype:N", scale=label_color_scale, legend=None))
)

xbar_chart = (
    xbar_zone2
    + xbar_zone1
    + xbar_line
    + xbar_pts_normal
    + xbar_pts_ooc
    + xbar_ucl_rule
    + xbar_lcl_rule
    + xbar_center_rule
    + xbar_uwarn_rule
    + xbar_lwarn_rule
    + xbar_labels
).properties(width=1600, height=420)

# --- R Chart ---
r_x = alt.X(
    "sample:Q",
    scale=alt.Scale(domain=x_domain, nice=False),
    axis=alt.Axis(title="Sample Number", labelFontSize=16, titleFontSize=20, tickMinStep=1, grid=False),
)
r_y = alt.Y(
    "value:Q",
    scale=alt.Scale(zero=False),
    axis=alt.Axis(
        title="Range R (mm)", labelFontSize=16, titleFontSize=20, gridColor="#E0E0E0", gridDash=[2, 4], gridOpacity=0.4
    ),
)

r_zone2 = alt.Chart(r_zone_2s).mark_rect(color=zone_fill, opacity=0.5).encode(y="y:Q", y2="y2:Q")
r_zone1 = alt.Chart(r_zone_1s).mark_rect(color=zone_fill, opacity=0.8).encode(y="y:Q", y2="y2:Q")

r_line = alt.Chart(df_range).mark_line(color=teal, strokeWidth=2).encode(x=r_x, y=r_y)

r_pts_normal = (
    alt.Chart(df_range[~df_range["ooc"]])
    .mark_point(color=teal, size=120, filled=True, stroke="white", strokeWidth=1)
    .encode(
        x="sample:Q",
        y="value:Q",
        tooltip=[alt.Tooltip("sample:Q", title="Sample"), alt.Tooltip("value:Q", title="Range", format=".4f")],
    )
)

r_pts_ooc = (
    alt.Chart(df_range[df_range["ooc"]])
    .mark_point(color=vermillion, size=220, filled=True, stroke="white", strokeWidth=1.5, shape="diamond")
    .encode(
        x="sample:Q",
        y="value:Q",
        tooltip=[alt.Tooltip("sample:Q", title="Sample"), alt.Tooltip("value:Q", title="Range (OOC)", format=".4f")],
    )
)

r_ucl_rule = alt.Chart(df_range).mark_rule(color=vermillion, strokeDash=[8, 4], strokeWidth=2).encode(y="ucl:Q")
r_lcl_rule = (
    alt.Chart(df_range).mark_rule(color=vermillion, strokeDash=[4, 4], strokeWidth=1.5, opacity=0.5).encode(y="lcl:Q")
)
r_center_rule = alt.Chart(df_range).mark_rule(color="#333333", strokeWidth=2.5).encode(y="center:Q")
r_uwarn_rule = (
    alt.Chart(df_range).mark_rule(color=amber, strokeDash=[4, 4], strokeWidth=1.5, opacity=0.7).encode(y="uwarn:Q")
)
r_lwarn_rule = (
    alt.Chart(df_range).mark_rule(color=amber, strokeDash=[4, 4], strokeWidth=1.5, opacity=0.7).encode(y="lwarn:Q")
)

r_labels = (
    alt.Chart(r_labels_df)
    .mark_text(align="left", dx=5, dy=-10, fontSize=16, fontWeight="bold")
    .encode(x="sample:Q", y="y:Q", text="label:N", color=alt.Color("ltype:N", scale=label_color_scale, legend=None))
)

r_chart = (
    r_zone2
    + r_zone1
    + r_line
    + r_pts_normal
    + r_pts_ooc
    + r_ucl_rule
    + r_lcl_rule
    + r_center_rule
    + r_uwarn_rule
    + r_lwarn_rule
    + r_labels
).properties(width=1600, height=420)

# Combine
combined = alt.vconcat(xbar_chart, r_chart, spacing=15).properties(
    title=alt.Title(
        "CNC Shaft Diameter Monitoring · spc-xbar-r · altair · pyplots.ai",
        fontSize=28,
        anchor="middle",
        offset=15,
        fontWeight="bold",
        color="#222222",
    )
)

chart = combined.configure_axis(labelFontSize=16, titleFontSize=20).configure_view(strokeWidth=0)

chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
