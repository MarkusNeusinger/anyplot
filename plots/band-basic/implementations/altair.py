""" pyplots.ai
band-basic: Basic Band Plot
Library: altair 6.0.0 | Python 3.14
Quality: 94/100 | Updated: 2026-02-23
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Oscilloscope voltage measurement with growing uncertainty
np.random.seed(42)
x = np.linspace(0, 10, 100)
y_center = 2 * np.sin(x) + 0.5 * x  # Central trend (sinusoidal + linear growth)

# Confidence band widens over time (realistic sensor drift uncertainty)
uncertainty = 0.5 + 0.15 * x
y_lower = y_center - 1.96 * uncertainty
y_upper = y_center + 1.96 * uncertainty
y_inner_lower = y_center - 0.674 * uncertainty  # 50% CI inner band
y_inner_upper = y_center + 0.674 * uncertainty

df = pd.DataFrame(
    {
        "x": x,
        "y_center": y_center,
        "y_lower": y_lower,
        "y_upper": y_upper,
        "y_inner_lower": y_inner_lower,
        "y_inner_upper": y_inner_upper,
    }
)

# Annotation data — callout at x≈9.0 s where uncertainty is wide and clearly visible
ann_row = df.iloc[90]  # x ≈ 9.09
ann_df = pd.DataFrame(
    {
        "x": [ann_row["x"]],
        "y_upper": [ann_row["y_upper"]],
        "y_lower": [ann_row["y_lower"]],
        "y_mid": [(ann_row["y_upper"] + ann_row["y_lower"]) / 2],
        "label": [f"95% CI: ±{(ann_row['y_upper'] - ann_row['y_lower']) / 2:.1f} mV"],
    }
)

# Nearest-point selection for interactive HTML export
nearest = alt.selection_point(nearest=True, on="pointerover", fields=["x"], empty=False)

# 95% confidence band (outer) — teal-shifted blue for visual depth against inner band
band_outer = (
    alt.Chart(df)
    .mark_area(opacity=0.25, color="#4a8db7", interpolate="monotone")
    .encode(
        x=alt.X("x:Q", title="Time (s)"), y=alt.Y("y_lower:Q", title="Oscilloscope Signal (mV)"), y2=alt.Y2("y_upper:Q")
    )
)

# 50% confidence band (inner) — deeper saturated blue for layered contrast
band_inner = (
    alt.Chart(df)
    .mark_area(opacity=0.3, color="#306998", interpolate="monotone")
    .encode(x="x:Q", y="y_inner_lower:Q", y2="y_inner_upper:Q")
)

# Central trend line (dark navy for strong focal contrast)
line = alt.Chart(df).mark_line(strokeWidth=2.5, color="#1a3a5c", interpolate="monotone").encode(x="x:Q", y="y_center:Q")

# Annotation: vertical bracket showing uncertainty span
ann_rule = (
    alt.Chart(ann_df)
    .mark_rule(color="#c0392b", strokeWidth=1.5, strokeDash=[6, 3])
    .encode(x="x:Q", y="y_lower:Q", y2="y_upper:Q")
)

ann_text = (
    alt.Chart(ann_df)
    .mark_text(align="left", dx=10, fontSize=16, fontWeight="bold", color="#c0392b")
    .encode(x="x:Q", y="y_mid:Q", text="label:N")
)

# Interactive tooltip points (visible only on hover in HTML)
tooltip_points = (
    alt.Chart(df)
    .mark_point(color="#1a3a5c", size=80)
    .encode(
        x="x:Q",
        y="y_center:Q",
        opacity=alt.condition(nearest, alt.value(1), alt.value(0)),
        tooltip=[
            alt.Tooltip("x:Q", title="Time (s)", format=".1f"),
            alt.Tooltip("y_center:Q", title="Signal (mV)", format=".2f"),
            alt.Tooltip("y_lower:Q", title="95% CI Lower", format=".2f"),
            alt.Tooltip("y_upper:Q", title="95% CI Upper", format=".2f"),
        ],
    )
    .add_params(nearest)
)

# Vertical guide rule (visible only on hover in HTML)
guide_rule = (
    alt.Chart(df)
    .mark_rule(color="#999999", strokeDash=[4, 4])
    .encode(x="x:Q", opacity=alt.condition(nearest, alt.value(0.5), alt.value(0)))
)

# Combine layers
chart = (
    (band_outer + band_inner + line + ann_rule + ann_text + tooltip_points + guide_rule)
    .properties(width=1600, height=900, title=alt.Title("band-basic · altair · pyplots.ai", fontSize=28))
    .configure_axis(labelFontSize=18, titleFontSize=22, gridOpacity=0.15, gridColor="#cccccc")
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
