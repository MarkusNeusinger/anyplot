""" pyplots.ai
histogram-capability: Process Capability Plot with Specification Limits
Library: altair 6.0.0 | Python 3.14.3
Quality: 89/100 | Created: 2026-03-19
"""

import altair as alt
import numpy as np
import pandas as pd
from scipy import stats


# Data
np.random.seed(42)
n_measurements = 200
target = 10.00
lsl = 9.95
usl = 10.05
measurements = np.random.normal(loc=10.002, scale=0.012, size=n_measurements)

mean = measurements.mean()
sigma = measurements.std(ddof=1)
cp = (usl - lsl) / (6 * sigma)
cpk = min((usl - mean) / (3 * sigma), (mean - lsl) / (3 * sigma))

# Colorblind-safe palette (orange + purple instead of red + green)
COLOR_BAR = "#306998"
COLOR_CURVE = "#1F4E79"
COLOR_SPEC = "#D4760A"  # Orange for LSL/USL
COLOR_TARGET = "#7B4F9D"  # Purple for target

# Pre-bin histogram data to avoid scale conflicts with other layers
bin_width = 0.004
bin_extent = [lsl - 0.005, usl + 0.005]
bin_edges = np.arange(bin_extent[0], bin_extent[1] + bin_width, bin_width)
counts, edges = np.histogram(measurements, bins=bin_edges)
hist_df = pd.DataFrame({"bin_start": edges[:-1], "bin_end": edges[1:], "count": counts})

# Normal curve data
x_curve = np.linspace(bin_extent[0], bin_extent[1], 200)
y_curve = stats.norm.pdf(x_curve, mean, sigma) * n_measurements * bin_width
curve_df = pd.DataFrame({"diameter": x_curve, "density": y_curve})

# Shared x-axis scale
x_scale = alt.Scale(domain=[lsl - 0.012, usl + 0.012])

# Background shaded zones (in-spec / out-of-spec)
zone_df = pd.DataFrame(
    {"x": [lsl - 0.012, lsl, usl], "x2": [lsl, usl, usl + 0.012], "fill": ["#FDE8E0", "#E6F0E6", "#FDE8E0"]}
)
zones = (
    alt.Chart(zone_df)
    .mark_rect(opacity=0.35)
    .encode(x=alt.X("x:Q", scale=x_scale), x2="x2:Q", color=alt.Color("fill:N", scale=None))
)

# Histogram using pre-binned data (rect marks)
histogram = (
    alt.Chart(hist_df)
    .mark_rect(
        color=COLOR_BAR, opacity=0.82, stroke="white", strokeWidth=0.8, cornerRadiusTopLeft=2, cornerRadiusTopRight=2
    )
    .encode(
        x=alt.X("bin_start:Q", title="Shaft Diameter (mm)", scale=x_scale),
        x2="bin_end:Q",
        y=alt.Y("count:Q", title="Frequency"),
        tooltip=[
            alt.Tooltip("bin_start:Q", title="Bin start", format=".3f"),
            alt.Tooltip("bin_end:Q", title="Bin end", format=".3f"),
            alt.Tooltip("count:Q", title="Count"),
        ],
    )
)

# Normal curve overlay
curve = (
    alt.Chart(curve_df)
    .mark_line(color=COLOR_CURVE, strokeWidth=3, opacity=0.9, interpolate="monotone")
    .encode(x=alt.X("diameter:Q", scale=x_scale), y="density:Q")
)

# LSL and USL lines
spec_df = pd.DataFrame({"value": [lsl, usl]})
spec_rules = (
    alt.Chart(spec_df)
    .mark_rule(color=COLOR_SPEC, strokeWidth=3, strokeDash=[10, 5])
    .encode(x=alt.X("value:Q", scale=x_scale))
)

# Target line
target_df = pd.DataFrame({"value": [target]})
target_rule = (
    alt.Chart(target_df)
    .mark_rule(color=COLOR_TARGET, strokeWidth=2.5, strokeDash=[4, 3])
    .encode(x=alt.X("value:Q", scale=x_scale))
)

# LSL / USL labels — offset outward to avoid overlap
lsl_label_df = pd.DataFrame({"value": [lsl], "label": ["LSL 9.950"]})
usl_label_df = pd.DataFrame({"value": [usl], "label": ["USL 10.050"]})

lsl_labels = (
    alt.Chart(lsl_label_df)
    .mark_text(align="right", dx=-8, fontSize=17, fontWeight="bold", color=COLOR_SPEC)
    .encode(x=alt.X("value:Q", scale=x_scale), y=alt.value(14), text="label:N")
)

usl_labels = (
    alt.Chart(usl_label_df)
    .mark_text(align="left", dx=8, fontSize=17, fontWeight="bold", color=COLOR_SPEC)
    .encode(x=alt.X("value:Q", scale=x_scale), y=alt.value(14), text="label:N")
)

target_label = (
    alt.Chart(pd.DataFrame({"value": [target], "label": ["Target 10.000"]}))
    .mark_text(align="center", fontSize=17, fontWeight="bold", color=COLOR_TARGET)
    .encode(x=alt.X("value:Q", scale=x_scale), y=alt.value(14), text="label:N")
)

# Capability indices annotation
status = "CAPABLE" if cpk >= 1.33 else "NOT CAPABLE"
cap_df = pd.DataFrame({"x": [usl + 0.010], "line1": [f"Cp = {cp:.2f}   Cpk = {cpk:.2f}"], "line2": [status]})

cap_annotation = (
    alt.Chart(cap_df)
    .mark_text(align="right", fontSize=21, fontWeight="bold", color="#1a1a2e")
    .encode(x=alt.X("x:Q", scale=x_scale), y=alt.value(34), text="line1:N")
)

status_color = "#2E7D32" if cpk >= 1.33 else "#C62828"
status_annotation = (
    alt.Chart(cap_df)
    .mark_text(align="right", fontSize=17, fontWeight="bold", color=status_color)
    .encode(x=alt.X("x:Q", scale=x_scale), y=alt.value(56), text="line2:N")
)

# Mean indicator
mean_df = pd.DataFrame({"value": [mean], "label": [f"x\u0304={mean:.3f}"]})
mean_rule = (
    alt.Chart(mean_df)
    .mark_rule(color="#666666", strokeWidth=1.5, strokeDash=[2, 2])
    .encode(x=alt.X("value:Q", scale=x_scale))
)
mean_label = (
    alt.Chart(mean_df)
    .mark_text(align="center", baseline="top", dy=5, fontSize=14, fontStyle="italic", color="#666666")
    .encode(x=alt.X("value:Q", scale=x_scale), y=alt.value(870), text="label:N")
)

# Combine all layers
chart = (
    alt.layer(
        zones,
        histogram,
        curve,
        spec_rules,
        target_rule,
        mean_rule,
        lsl_labels,
        usl_labels,
        target_label,
        cap_annotation,
        status_annotation,
        mean_label,
    )
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "histogram-capability \u00b7 altair \u00b7 pyplots.ai",
            fontSize=28,
            fontWeight="bold",
            anchor="start",
            offset=16,
            subtitle=f"n={n_measurements}   \u03c3={sigma:.4f} mm   Process centered at {mean:.3f} mm",
            subtitleFontSize=16,
            subtitleColor="#666666",
        ),
    )
    .configure_axis(
        labelFontSize=18,
        titleFontSize=22,
        titleColor="#333333",
        labelColor="#555555",
        grid=False,
        domainColor="#999999",
        tickColor="#999999",
    )
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
