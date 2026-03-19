"""pyplots.ai
histogram-capability: Process Capability Plot with Specification Limits
Library: altair | Python 3.13
Quality: pending | Created: 2026-03-19
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

measurement_df = pd.DataFrame({"diameter": measurements})

# Normal curve data
bin_width = 0.004
x_curve = np.linspace(lsl - 0.005, usl + 0.005, 200)
y_curve = stats.norm.pdf(x_curve, mean, sigma) * n_measurements * bin_width

curve_df = pd.DataFrame({"diameter": x_curve, "density": y_curve})

# Plot - histogram using Altair's bin transform
x_domain = [lsl - 0.01, usl + 0.01]

histogram = (
    alt.Chart(measurement_df)
    .mark_bar(color="#306998", opacity=0.8, stroke="white", strokeWidth=0.5)
    .encode(
        x=alt.X(
            "diameter:Q",
            bin=alt.Bin(step=bin_width, extent=[lsl - 0.005, usl + 0.005]),
            title="Shaft Diameter (mm)",
            scale=alt.Scale(domain=x_domain),
        ),
        y=alt.Y("count():Q", title="Frequency"),
    )
)

# Normal curve overlay
curve = alt.Chart(curve_df).mark_line(color="#1F4E79", strokeWidth=3, opacity=0.9).encode(x="diameter:Q", y="density:Q")

# LSL and USL lines
lsl_usl_df = pd.DataFrame({"value": [lsl, usl]})
spec_rules = alt.Chart(lsl_usl_df).mark_rule(color="#D62728", strokeWidth=3, strokeDash=[8, 6]).encode(x="value:Q")

# Target line
target_df = pd.DataFrame({"value": [target]})
target_rule = alt.Chart(target_df).mark_rule(color="#2CA02C", strokeWidth=3, strokeDash=[8, 6]).encode(x="value:Q")

# Spec line labels at top
label_lsl_usl = pd.DataFrame({"value": [lsl, usl], "label": ["LSL (9.95)", "USL (10.05)"]})
label_target = pd.DataFrame({"value": [target], "label": ["Target (10.00)"]})

lsl_usl_labels = (
    alt.Chart(label_lsl_usl)
    .mark_text(align="center", baseline="bottom", dy=-10, fontSize=16, fontWeight="bold", color="#D62728")
    .encode(x="value:Q", y=alt.value(10), text="label:N")
)

target_label = (
    alt.Chart(label_target)
    .mark_text(align="center", baseline="bottom", dy=-10, fontSize=16, fontWeight="bold", color="#2CA02C")
    .encode(x="value:Q", y=alt.value(10), text="label:N")
)

# Capability indices annotation
annotation_df = pd.DataFrame({"x": [usl - 0.003], "y": [1], "text": [f"Cp = {cp:.2f}  |  Cpk = {cpk:.2f}"]})

annotation = (
    alt.Chart(annotation_df)
    .mark_text(align="right", fontSize=20, fontWeight="bold", color="#333333")
    .encode(x="x:Q", y=alt.value(30), text="text:N")
)

# Combine all layers
chart = (
    (histogram + curve + spec_rules + target_rule + lsl_usl_labels + target_label + annotation)
    .properties(
        width=1600,
        height=900,
        title=alt.Title("histogram-capability · altair · pyplots.ai", fontSize=28, fontWeight="bold"),
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, grid=False)
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
