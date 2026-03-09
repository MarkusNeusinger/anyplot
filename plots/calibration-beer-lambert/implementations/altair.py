""" pyplots.ai
calibration-beer-lambert: Beer-Lambert Calibration Curve
Library: altair 6.0.0 | Python 3.14.3
Quality: 93/100 | Created: 2026-03-09
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Calibration standards for UV-Vis spectrophotometry
np.random.seed(42)
concentrations = np.array([0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0])
epsilon_l = 0.045
true_absorbance = epsilon_l * concentrations
measured_absorbance = true_absorbance + np.random.normal(0, 0.008, len(concentrations))
measured_absorbance[0] = max(measured_absorbance[0], 0.002)

# Regression stats for annotation and prediction interval
n = len(concentrations)
x_mean = np.mean(concentrations)
y_mean = np.mean(measured_absorbance)
ss_xx = np.sum((concentrations - x_mean) ** 2)
ss_xy = np.sum((concentrations - x_mean) * (measured_absorbance - y_mean))
slope = ss_xy / ss_xx
intercept = y_mean - slope * x_mean
residuals = measured_absorbance - (slope * concentrations + intercept)
ss_res = np.sum(residuals**2)
ss_tot = np.sum((measured_absorbance - y_mean) ** 2)
r_squared = 1 - ss_res / ss_tot

# Prediction interval
x_fit = np.linspace(0, 15, 200)
y_fit = slope * x_fit + intercept
mse = ss_res / (n - 2)
se_pred = np.sqrt(mse * (1 + 1 / n + (x_fit - x_mean) ** 2 / ss_xx))
t_val = 2.447  # t-value for 95% PI, df=6
upper = y_fit + t_val * se_pred
lower = y_fit - t_val * se_pred

# Unknown sample
unknown_absorbance = 0.38
unknown_concentration = (unknown_absorbance - intercept) / slope

# DataFrames
standards_df = pd.DataFrame({"Concentration (mg/L)": concentrations, "Absorbance": measured_absorbance})

fit_df = pd.DataFrame({"Concentration (mg/L)": x_fit, "Absorbance": y_fit, "Upper": upper, "Lower": lower})

unknown_point_df = pd.DataFrame({"Concentration (mg/L)": [unknown_concentration], "Absorbance": [unknown_absorbance]})

unknown_hline_df = pd.DataFrame(
    {"Concentration (mg/L)": [0, unknown_concentration], "Absorbance": [unknown_absorbance, unknown_absorbance]}
)

unknown_vline_df = pd.DataFrame(
    {"Concentration (mg/L)": [unknown_concentration, unknown_concentration], "Absorbance": [0, unknown_absorbance]}
)

# Shared scales with tighter axis ranges
x_scale = alt.Scale(domain=[0, 15.5], nice=False)
y_scale = alt.Scale(domain=[0, 0.68])

# Prediction interval band
band = (
    alt.Chart(fit_df)
    .mark_area(opacity=0.12, color="#306998")
    .encode(x=alt.X("Concentration (mg/L):Q", scale=x_scale), y=alt.Y("Lower:Q", scale=y_scale), y2="Upper:Q")
)

# Regression line using transform_regression (idiomatic Altair)
reg_line = (
    alt.Chart(standards_df)
    .mark_line(color="#306998", strokeWidth=3)
    .transform_regression("Concentration (mg/L)", "Absorbance")
    .encode(x=alt.X("Concentration (mg/L):Q", scale=x_scale), y=alt.Y("Absorbance:Q", scale=y_scale))
)

# Calibration standard points with selection for interactive highlighting
highlight = alt.selection_point(on="pointerover", nearest=True, empty=False)

points = (
    alt.Chart(standards_df)
    .mark_point(filled=True, color="#306998", stroke="white", strokeWidth=1.5)
    .encode(
        x=alt.X(
            "Concentration (mg/L):Q",
            scale=x_scale,
            title="Concentration (mg/L)",
            axis=alt.Axis(values=[0, 2, 4, 6, 8, 10, 12, 14]),
        ),
        y=alt.Y("Absorbance:Q", scale=y_scale, title="Absorbance"),
        size=alt.condition(highlight, alt.value(500), alt.value(350)),
        tooltip=[alt.Tooltip("Concentration (mg/L):Q", format=".1f"), alt.Tooltip("Absorbance:Q", format=".4f")],
    )
    .add_params(highlight)
)

# Unknown sample dashed lines - dark orange for accessibility
unknown_color = "#C46210"

h_line = (
    alt.Chart(unknown_hline_df)
    .mark_line(color=unknown_color, strokeWidth=2, strokeDash=[8, 6])
    .encode(x=alt.X("Concentration (mg/L):Q", scale=x_scale), y=alt.Y("Absorbance:Q", scale=y_scale))
)

v_line = (
    alt.Chart(unknown_vline_df)
    .mark_line(color=unknown_color, strokeWidth=2, strokeDash=[8, 6])
    .encode(x=alt.X("Concentration (mg/L):Q", scale=x_scale), y=alt.Y("Absorbance:Q", scale=y_scale))
)

# Unknown sample point
unknown_pt = (
    alt.Chart(unknown_point_df)
    .mark_point(size=400, filled=True, color=unknown_color, stroke="white", strokeWidth=1.5, shape="diamond")
    .encode(
        x=alt.X("Concentration (mg/L):Q", scale=x_scale),
        y=alt.Y("Absorbance:Q", scale=y_scale),
        tooltip=[
            alt.Tooltip("Concentration (mg/L):Q", title="Predicted Conc.", format=".2f"),
            alt.Tooltip("Absorbance:Q", title="Measured Abs.", format=".4f"),
        ],
    )
)

# Annotation - regression equation and R²
eq_text = f"y = {slope:.4f}x + {intercept:.4f}    R\u00b2 = {r_squared:.4f}"
annotation_df = pd.DataFrame({"Concentration (mg/L)": [9.5], "Absorbance": [0.12], "text": [eq_text]})

eq_label = (
    alt.Chart(annotation_df)
    .mark_text(fontSize=20, align="left", fontWeight="bold", color="#306998")
    .encode(x=alt.X("Concentration (mg/L):Q", scale=x_scale), y=alt.Y("Absorbance:Q", scale=y_scale), text="text:N")
)

# Unknown label
unknown_label_df = pd.DataFrame(
    {
        "Concentration (mg/L)": [unknown_concentration + 0.4],
        "Absorbance": [unknown_absorbance + 0.03],
        "text": [f"Unknown ({unknown_concentration:.1f} mg/L)"],
    }
)

unknown_label = (
    alt.Chart(unknown_label_df)
    .mark_text(fontSize=18, align="left", fontWeight="bold", color=unknown_color)
    .encode(x=alt.X("Concentration (mg/L):Q", scale=x_scale), y=alt.Y("Absorbance:Q", scale=y_scale), text="text:N")
)

# Combine all layers
chart = (
    alt.layer(band, reg_line, points, h_line, v_line, unknown_pt, eq_label, unknown_label)
    .properties(
        width=1600, height=900, title=alt.Title("calibration-beer-lambert \u00b7 altair \u00b7 pyplots.ai", fontSize=28)
    )
    .configure_axis(
        labelFontSize=18,
        titleFontSize=22,
        titleFont="Helvetica Neue, Arial, sans-serif",
        labelFont="Helvetica Neue, Arial, sans-serif",
        titleColor="#333333",
        labelColor="#555555",
        grid=False,
        domainColor="#aaaaaa",
        domainWidth=0.6,
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
