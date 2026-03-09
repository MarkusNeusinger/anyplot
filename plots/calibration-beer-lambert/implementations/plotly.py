""" pyplots.ai
calibration-beer-lambert: Beer-Lambert Calibration Curve
Library: plotly 6.6.0 | Python 3.14.3
Quality: 89/100 | Created: 2026-03-09
"""

import numpy as np
import plotly.graph_objects as go


# Data - calibration standards for UV-Vis spectrophotometry
np.random.seed(42)
concentration = np.array([0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0])
molar_absorptivity = 0.045
absorbance_true = molar_absorptivity * concentration
absorbance = absorbance_true + np.random.normal(0, 0.008, len(concentration))
absorbance[0] = 0.003

# Linear regression using numpy
slope, intercept = np.polyfit(concentration, absorbance, 1)
absorbance_pred = slope * concentration + intercept
ss_res = np.sum((absorbance - absorbance_pred) ** 2)
ss_tot = np.sum((absorbance - np.mean(absorbance)) ** 2)
r_squared = 1 - ss_res / ss_tot

# Regression line and 95% prediction interval
conc_fit = np.linspace(-0.5, 15.5, 200)
abs_fit = slope * conc_fit + intercept
n = len(concentration)
conc_mean = np.mean(concentration)
mse = ss_res / (n - 2)
se_pred = np.sqrt(mse * (1 + 1 / n + (conc_fit - conc_mean) ** 2 / np.sum((concentration - conc_mean) ** 2)))
# t-critical value for 95% two-sided, df=6 (pre-computed)
t_crit = 2.447
pred_upper = abs_fit + t_crit * se_pred
pred_lower = abs_fit - t_crit * se_pred

# Unknown sample
unknown_absorbance = 0.38
unknown_concentration = (unknown_absorbance - intercept) / slope

# Plot
fig = go.Figure()

# Prediction interval band
fig.add_trace(
    go.Scatter(
        x=np.concatenate([conc_fit, conc_fit[::-1]]),
        y=np.concatenate([pred_upper, pred_lower[::-1]]),
        fill="toself",
        fillcolor="rgba(48, 105, 152, 0.12)",
        line={"color": "rgba(0,0,0,0)"},
        name="95% Prediction Interval",
        showlegend=True,
        hoverinfo="skip",
    )
)

# Regression line
fig.add_trace(
    go.Scatter(
        x=conc_fit,
        y=abs_fit,
        mode="lines",
        name=f"Fit: y = {slope:.4f}x + {intercept:.4f}",
        line={"color": "#306998", "width": 3},
    )
)

# Calibration standards
fig.add_trace(
    go.Scatter(
        x=concentration,
        y=absorbance,
        mode="markers",
        name="Calibration Standards",
        marker={"size": 14, "color": "#306998", "line": {"color": "white", "width": 2}, "symbol": "circle"},
    )
)

# Unknown sample point
fig.add_trace(
    go.Scatter(
        x=[unknown_concentration],
        y=[unknown_absorbance],
        mode="markers",
        name=f"Unknown ({unknown_concentration:.1f} mg/L)",
        marker={"size": 16, "color": "#E8453C", "line": {"color": "white", "width": 2}, "symbol": "diamond"},
    )
)

# Dashed lines from unknown to axes
fig.add_shape(
    type="line",
    x0=unknown_concentration,
    y0=0,
    x1=unknown_concentration,
    y1=unknown_absorbance,
    line={"color": "#E8453C", "width": 2, "dash": "dash"},
)
fig.add_shape(
    type="line",
    x0=0,
    y0=unknown_absorbance,
    x1=unknown_concentration,
    y1=unknown_absorbance,
    line={"color": "#E8453C", "width": 2, "dash": "dash"},
)

# Equation and R² annotation
fig.add_annotation(
    x=3.0,
    y=0.55,
    text=f"y = {slope:.4f}x + {intercept:.4f}<br>R² = {r_squared:.5f}",
    showarrow=False,
    font={"size": 20, "color": "#306998"},
    bgcolor="rgba(255,255,255,0.8)",
    bordercolor="#306998",
    borderwidth=1,
    borderpad=6,
    align="left",
)

# Layout
fig.update_layout(
    title={"text": "calibration-beer-lambert · plotly · pyplots.ai", "font": {"size": 28}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": "Concentration (mg/L)", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "range": [-0.5, 15.5],
        "gridcolor": "rgba(0,0,0,0.08)",
        "gridwidth": 1,
        "zeroline": False,
    },
    yaxis={
        "title": {"text": "Absorbance", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "range": [-0.05, 0.75],
        "gridcolor": "rgba(0,0,0,0.08)",
        "gridwidth": 1,
        "zeroline": False,
    },
    template="plotly_white",
    legend={
        "font": {"size": 16},
        "x": 0.02,
        "y": 0.98,
        "xanchor": "left",
        "yanchor": "top",
        "bgcolor": "rgba(255,255,255,0.85)",
        "bordercolor": "#cccccc",
        "borderwidth": 1,
    },
    margin={"l": 100, "r": 80, "t": 100, "b": 80},
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
