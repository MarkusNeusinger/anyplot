""" pyplots.ai
line-arrhenius: Arrhenius Plot for Reaction Kinetics
Library: altair 6.0.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-21
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - First-order decomposition reaction rate constants at various temperatures
np.random.seed(42)
temperature_K = np.array([300, 325, 350, 375, 400, 425, 450, 475, 500, 525, 550, 600])
R = 8.314  # J/(mol·K)
Ea_true = 75000  # J/mol (75 kJ/mol)
A_true = 1.5e12  # Pre-exponential factor (s⁻¹)

# Arrhenius equation: k = A * exp(-Ea / (R*T))
ln_k_true = np.log(A_true) - Ea_true / (R * temperature_K)
ln_k_measured = ln_k_true + np.random.normal(0, 0.15, len(temperature_K))

inv_T = 1.0 / temperature_K  # 1/T in K⁻¹

# Compute regression parameters for annotations
coeffs = np.polyfit(inv_T, ln_k_measured, 1)
slope_fit, intercept_fit = coeffs
y_pred = slope_fit * inv_T + intercept_fit
ss_res = np.sum((ln_k_measured - y_pred) ** 2)
ss_tot = np.sum((ln_k_measured - np.mean(ln_k_measured)) ** 2)
r_squared = 1 - ss_res / ss_tot
Ea_fit = -slope_fit * R  # Activation energy in J/mol

# DataFrame
data_df = pd.DataFrame({"inv_T": inv_T, "ln_k": ln_k_measured, "T_K": temperature_K})

# Shared scales
x_scale = alt.Scale(domain=[inv_T.min() - 0.0001, inv_T.max() + 0.0001], nice=False)
y_scale = alt.Scale(domain=[ln_k_measured.min() - 1.2, ln_k_measured.max() + 1.2])

# Regression line using Altair's native transform_regression
reg_line = (
    alt.Chart(data_df)
    .mark_line(strokeWidth=3, color="#306998")
    .transform_regression("inv_T", "ln_k", extent=[inv_T.min() - 0.00005, inv_T.max() + 0.00005])
    .encode(x=alt.X("inv_T:Q", scale=x_scale), y=alt.Y("ln_k:Q", scale=y_scale))
)

# Data points with interactive highlight
highlight = alt.selection_point(on="pointerover", nearest=True, empty=False)

points = (
    alt.Chart(data_df)
    .mark_point(filled=True, color="#306998", stroke="white", strokeWidth=1.5)
    .encode(
        x=alt.X("inv_T:Q", scale=x_scale, title="1/T (K⁻¹)"),
        y=alt.Y("ln_k:Q", scale=y_scale, title="ln(k)"),
        size=alt.condition(highlight, alt.value(500), alt.value(350)),
        tooltip=[
            alt.Tooltip("T_K:Q", title="Temperature", format=".0f"),
            alt.Tooltip("inv_T:Q", title="1/T", format=".5f"),
            alt.Tooltip("ln_k:Q", title="ln(k)", format=".2f"),
        ],
    )
    .add_params(highlight)
)

# Annotation: Ea and R² value
ea_kj = Ea_fit / 1000
annotation_text = f"Eₐ = {ea_kj:.1f} kJ/mol   R² = {r_squared:.4f}"
slope_text = f"slope = −Eₐ/R = {slope_fit:.0f} K"

annotation_df = pd.DataFrame(
    {"inv_T": [inv_T.min() + 0.0002], "ln_k": [ln_k_measured.max() + 0.7], "text": [annotation_text]}
)

slope_ann_df = pd.DataFrame(
    {"inv_T": [inv_T.min() + 0.0002], "ln_k": [ln_k_measured.max() + 0.15], "text": [slope_text]}
)

ea_label = (
    alt.Chart(annotation_df)
    .mark_text(fontSize=20, align="left", fontWeight="bold", color="#306998")
    .encode(x=alt.X("inv_T:Q", scale=x_scale), y=alt.Y("ln_k:Q", scale=y_scale), text="text:N")
)

slope_label = (
    alt.Chart(slope_ann_df)
    .mark_text(fontSize=17, align="left", fontStyle="italic", color="#666666")
    .encode(x=alt.X("inv_T:Q", scale=x_scale), y=alt.Y("ln_k:Q", scale=y_scale), text="text:N")
)

# Secondary x-axis: temperature labels at data point positions
temp_labels_df = pd.DataFrame(
    {
        "inv_T": inv_T[::2],
        "ln_k": [ln_k_measured.min() - 0.5] * len(inv_T[::2]),
        "text": [f"{int(t)} K" for t in temperature_K[::2]],
    }
)

temp_tick_labels = (
    alt.Chart(temp_labels_df)
    .mark_text(fontSize=14, color="#888888", angle=0)
    .encode(x=alt.X("inv_T:Q", scale=x_scale), y=alt.Y("ln_k:Q", scale=y_scale), text="text:N")
)

# Temperature axis label
temp_axis_label_df = pd.DataFrame(
    {"inv_T": [(inv_T.min() + inv_T.max()) / 2], "ln_k": [ln_k_measured.min() - 0.9], "text": ["Temperature (K)"]}
)

temp_axis_label = (
    alt.Chart(temp_axis_label_df)
    .mark_text(fontSize=16, color="#888888", fontStyle="italic")
    .encode(x=alt.X("inv_T:Q", scale=x_scale), y=alt.Y("ln_k:Q", scale=y_scale), text="text:N")
)

# Combine all layers
chart = (
    alt.layer(reg_line, points, ea_label, slope_label, temp_tick_labels, temp_axis_label)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "line-arrhenius · altair · pyplots.ai",
            fontSize=28,
            anchor="middle",
            color="#2C3E50",
            subtitle="First-Order Decomposition · Rate Constants vs Inverse Temperature",
            subtitleFontSize=18,
            subtitleColor="#7f8c8d",
            subtitlePadding=8,
        ),
    )
    .configure_axis(
        labelFontSize=18,
        titleFontSize=22,
        titleFont="Helvetica Neue, Arial, sans-serif",
        labelFont="Helvetica Neue, Arial, sans-serif",
        titleColor="#333333",
        labelColor="#555555",
        grid=False,
        domain=False,
        tickColor="#aaaaaa",
        tickSize=5,
        tickWidth=0.6,
    )
    .configure_title(font="Helvetica Neue, Arial, sans-serif", color="#222222")
    .configure_view(strokeWidth=0)
    .interactive()
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
