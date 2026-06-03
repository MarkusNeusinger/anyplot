""" anyplot.ai
calibration-beer-lambert: Beer-Lambert Calibration Curve
Library: altair 6.1.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-06-03
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette — position 1 (brand green) for calibration series, position 4 (ochre) for unknown
BRAND = "#009E73"
UNKNOWN_COLOR = "#BD8233"

# Data — UV-Vis spectrophotometry calibration standards
np.random.seed(42)
concentrations = np.array([0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0])
epsilon_l = 0.045
true_absorbance = epsilon_l * concentrations
measured_absorbance = true_absorbance + np.random.normal(0, 0.008, len(concentrations))
measured_absorbance[0] = max(measured_absorbance[0], 0.002)

# Regression stats for prediction interval and annotation
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

# Prediction interval (95%, df=6)
x_fit = np.linspace(0, 15, 200)
y_fit = slope * x_fit + intercept
mse = ss_res / (n - 2)
se_pred = np.sqrt(mse * (1 + 1 / n + (x_fit - x_mean) ** 2 / ss_xx))
t_val = 2.447
upper = y_fit + t_val * se_pred
lower = y_fit - t_val * se_pred

# Unknown sample determination
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

# Shared scales
x_scale = alt.Scale(domain=[0, 15.5], nice=False)
y_scale = alt.Scale(domain=[0, 0.68])

# Prediction interval band (muted brand green)
band = (
    alt.Chart(fit_df)
    .mark_area(opacity=0.12, color=BRAND)
    .encode(x=alt.X("Concentration (mg/L):Q", scale=x_scale), y=alt.Y("Lower:Q", scale=y_scale), y2="Upper:Q")
)

# Regression line — idiomatic Altair transform_regression
reg_line = (
    alt.Chart(standards_df)
    .mark_line(color=BRAND, strokeWidth=2.5)
    .transform_regression("Concentration (mg/L)", "Absorbance")
    .encode(x=alt.X("Concentration (mg/L):Q", scale=x_scale), y=alt.Y("Absorbance:Q", scale=y_scale))
)

# Calibration standard points with hover highlighting
highlight = alt.selection_point(on="pointerover", nearest=True, empty=False)

points = (
    alt.Chart(standards_df)
    .mark_point(filled=True, color=BRAND, stroke=PAGE_BG, strokeWidth=1.5)
    .encode(
        x=alt.X(
            "Concentration (mg/L):Q",
            scale=x_scale,
            title="Concentration (mg/L)",
            axis=alt.Axis(values=[0, 2, 4, 6, 8, 10, 12, 14]),
        ),
        y=alt.Y(
            "Absorbance:Q",
            scale=y_scale,
            title="Absorbance",
            axis=alt.Axis(values=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6], format=".1f"),
        ),
        size=alt.condition(highlight, alt.value(280), alt.value(200)),
        tooltip=[alt.Tooltip("Concentration (mg/L):Q", format=".1f"), alt.Tooltip("Absorbance:Q", format=".4f")],
    )
    .add_params(highlight)
)

# Unknown sample dashed projection lines
h_line = (
    alt.Chart(unknown_hline_df)
    .mark_line(color=UNKNOWN_COLOR, strokeWidth=1.8, strokeDash=[8, 6])
    .encode(x=alt.X("Concentration (mg/L):Q", scale=x_scale), y=alt.Y("Absorbance:Q", scale=y_scale))
)

v_line = (
    alt.Chart(unknown_vline_df)
    .mark_line(color=UNKNOWN_COLOR, strokeWidth=1.8, strokeDash=[8, 6])
    .encode(x=alt.X("Concentration (mg/L):Q", scale=x_scale), y=alt.Y("Absorbance:Q", scale=y_scale))
)

# Unknown sample point (diamond marker)
unknown_pt = (
    alt.Chart(unknown_point_df)
    .mark_point(size=220, filled=True, color=UNKNOWN_COLOR, stroke=PAGE_BG, strokeWidth=1.5, shape="diamond")
    .encode(
        x=alt.X("Concentration (mg/L):Q", scale=x_scale),
        y=alt.Y("Absorbance:Q", scale=y_scale),
        tooltip=[
            alt.Tooltip("Concentration (mg/L):Q", title="Predicted Conc.", format=".2f"),
            alt.Tooltip("Absorbance:Q", title="Measured Abs.", format=".4f"),
        ],
    )
)

# Regression equation annotation — lighter weight for secondary info
eq_text = f"y = {slope:.4f}x + {intercept:.4f}    R² = {r_squared:.4f}"
annotation_df = pd.DataFrame({"Concentration (mg/L)": [1.0], "Absorbance": [0.055], "text": [eq_text]})

eq_label = (
    alt.Chart(annotation_df)
    .mark_text(fontSize=10, align="left", fontWeight="normal", color=INK_SOFT)
    .encode(x=alt.X("Concentration (mg/L):Q", scale=x_scale), y=alt.Y("Absorbance:Q", scale=y_scale), text="text:N")
)

# Unknown sample label
unknown_label_df = pd.DataFrame(
    {
        "Concentration (mg/L)": [unknown_concentration + 0.4],
        "Absorbance": [unknown_absorbance + 0.028],
        "text": [f"Unknown ({unknown_concentration:.1f} mg/L)"],
    }
)

unknown_label = (
    alt.Chart(unknown_label_df)
    .mark_text(fontSize=10, align="left", fontWeight="bold", color=UNKNOWN_COLOR)
    .encode(x=alt.X("Concentration (mg/L):Q", scale=x_scale), y=alt.Y("Absorbance:Q", scale=y_scale), text="text:N")
)

# Title with scaled font size for length
title_str = "calibration-beer-lambert · python · altair · anyplot.ai"
title_fs = round(16 * min(1.0, 67 / len(title_str)))

# Compose layers and configure theme-adaptive chrome
chart = (
    alt.layer(band, reg_line, points, h_line, v_line, unknown_pt, eq_label, unknown_label)
    .properties(
        width=620, height=320, background=PAGE_BG, title=alt.Title(title_str, fontSize=title_fs, fontWeight="bold")
    )
    .configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_axis(
        labelFontSize=10,
        titleFontSize=12,
        titleColor=INK,
        labelColor=INK_SOFT,
        grid=False,
        domainColor=INK_SOFT,
        domainWidth=0.6,
        tickColor=INK_SOFT,
        tickSize=5,
        tickWidth=0.6,
    )
    .configure_title(color=INK)
    .interactive()
)

# Save PNG
chart.save(f"plot-{THEME}.png", scale_factor=4.0)

# Pad to exactly 3200 × 1800 (landscape target)
TW, TH = 3200, 1800
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
_w, _h = _img.size
if _w > TW or _h > TH:
    raise SystemExit(
        f"altair vl-convert produced {_w}×{_h}, exceeds target {TW}×{TH}. "
        f"Shrink chart .properties(width=, height=) values and re-render."
    )
if _w < TW or _h < TH:
    _canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _w) // 2, (TH - _h) // 2))
    _canvas.save(f"plot-{THEME}.png")

# Save HTML
chart.save(f"plot-{THEME}.html")
