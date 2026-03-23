""" pyplots.ai
histogram-capability: Process Capability Plot with Specification Limits
Library: plotly 6.6.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-19
"""

import numpy as np
import plotly.graph_objects as go
from scipy import stats


# Data - shaft diameter measurements (mm)
np.random.seed(42)
measurements = np.random.normal(loc=10.002, scale=0.012, size=200)

lsl = 9.95
usl = 10.05
target = 10.00

mean_val = np.mean(measurements)
sigma = np.std(measurements, ddof=1)

# Capability indices
cp = (usl - lsl) / (6 * sigma)
cpk = min((usl - mean_val) / (3 * sigma), (mean_val - lsl) / (3 * sigma))

# Normal distribution curve
x_curve = np.linspace(mean_val - 4 * sigma, mean_val + 4 * sigma, 300)
y_curve = stats.norm.pdf(x_curve, mean_val, sigma)

# Scale the normal curve to match histogram area
bin_width = (measurements.max() - measurements.min()) / 25
scale_factor = len(measurements) * bin_width
y_scaled = y_curve * scale_factor
y_peak = y_scaled.max()

# Colorblind-safe palette: blue for limits, dark amber for target
limit_color = "#d45800"
target_color = "#306998"

# Plot
fig = go.Figure()

# Shaded rejection regions (outside spec limits) — Plotly-distinctive filled area
x_left = x_curve[x_curve <= lsl]
y_left = y_scaled[x_curve <= lsl]
if len(x_left) > 0:
    fig.add_trace(
        go.Scatter(
            x=np.concatenate([[x_left[0]], x_left, [x_left[-1]]]),
            y=np.concatenate([[0], y_left, [0]]),
            fill="toself",
            fillcolor="rgba(212, 88, 0, 0.12)",
            line={"width": 0},
            showlegend=False,
            hoverinfo="skip",
        )
    )

x_right = x_curve[x_curve >= usl]
y_right = y_scaled[x_curve >= usl]
if len(x_right) > 0:
    fig.add_trace(
        go.Scatter(
            x=np.concatenate([[x_right[0]], x_right, [x_right[-1]]]),
            y=np.concatenate([[0], y_right, [0]]),
            fill="toself",
            fillcolor="rgba(212, 88, 0, 0.12)",
            line={"width": 0},
            showlegend=False,
            hoverinfo="skip",
        )
    )

# Histogram
fig.add_trace(
    go.Histogram(
        x=measurements,
        nbinsx=25,
        marker={"color": "rgba(48, 105, 152, 0.75)", "line": {"color": "rgba(255,255,255,0.7)", "width": 1.2}},
        name="Measurements",
        hovertemplate="Diameter: %{x:.4f} mm<br>Count: %{y}<extra></extra>",
    )
)

# Normal distribution curve
fig.add_trace(
    go.Scatter(
        x=x_curve,
        y=y_scaled,
        mode="lines",
        line={"color": "#0f2440", "width": 3.5, "shape": "spline"},
        name="Normal Fit",
        hoverinfo="skip",
    )
)

# LSL line
fig.add_shape(
    type="line", x0=lsl, x1=lsl, y0=0, y1=0.90, yref="paper", line={"color": limit_color, "width": 2.5, "dash": "dash"}
)
fig.add_annotation(
    x=lsl,
    y=0.93,
    yref="paper",
    text=f"<b>LSL</b><br>{lsl}",
    showarrow=False,
    font={"size": 15, "color": limit_color, "family": "Arial"},
    align="center",
)

# USL line
fig.add_shape(
    type="line", x0=usl, x1=usl, y0=0, y1=0.90, yref="paper", line={"color": limit_color, "width": 2.5, "dash": "dash"}
)
fig.add_annotation(
    x=usl,
    y=0.93,
    yref="paper",
    text=f"<b>USL</b><br>{usl}",
    showarrow=False,
    font={"size": 15, "color": limit_color, "family": "Arial"},
    align="center",
)

# Target line — distinct style: solid, different color
fig.add_shape(
    type="line",
    x0=target,
    x1=target,
    y0=0,
    y1=0.90,
    yref="paper",
    line={"color": target_color, "width": 2.5, "dash": "dashdot"},
)
fig.add_annotation(
    x=target,
    y=0.93,
    yref="paper",
    text=f"<b>Target</b><br>{target}",
    showarrow=False,
    font={"size": 15, "color": target_color, "family": "Arial"},
    align="center",
)

# Cpk interpretation
cpk_status = "Capable" if cpk >= 1.33 else "Marginal" if cpk >= 1.0 else "Not Capable"
cpk_emoji = "PASS" if cpk >= 1.33 else "WARN" if cpk >= 1.0 else "FAIL"

# Capability indices annotation — styled card
fig.add_annotation(
    x=0.98,
    y=0.85,
    xref="paper",
    yref="paper",
    text=(
        f"<b>Process Capability</b><br>"
        f"<span style='font-size:13px;color:#666'>─────────────</span><br>"
        f"Cp = {cp:.2f}    Cpk = {cpk:.2f}<br>"
        f"<br>"
        f"μ = {mean_val:.4f} mm<br>"
        f"σ = {sigma:.4f} mm<br>"
        f"<br>"
        f"<b>{cpk_status}</b> (Cpk ≥ 1.33 = {cpk_emoji})"
    ),
    showarrow=False,
    font={"size": 15, "color": "#1a1a2e", "family": "Arial"},
    align="left",
    xanchor="right",
    yanchor="top",
    bgcolor="rgba(255,255,255,0.95)",
    bordercolor="rgba(48,105,152,0.3)",
    borderwidth=1.5,
    borderpad=12,
)

# Layout
fig.update_layout(
    title={
        "text": (
            "<b>Shaft Diameter Process Capability</b>"
            "<br><span style='font-size:16px;color:#666'>"
            "histogram-capability · plotly · pyplots.ai</span>"
        ),
        "font": {"size": 26, "color": "#1a1a2e", "family": "Arial"},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.97,
    },
    xaxis={
        "title": {"text": "Shaft Diameter (mm)", "font": {"size": 22, "color": "#333", "family": "Arial"}},
        "tickfont": {"size": 18, "color": "#555"},
        "showgrid": False,
        "zeroline": False,
        "showline": True,
        "linecolor": "rgba(0,0,0,0.15)",
        "linewidth": 1,
        "range": [9.935, 10.065],
        "dtick": 0.01,
        "tickformat": ".2f",
    },
    yaxis={
        "title": {"text": "Frequency", "font": {"size": 22, "color": "#333", "family": "Arial"}},
        "tickfont": {"size": 18, "color": "#555"},
        "showgrid": True,
        "gridcolor": "rgba(0,0,0,0.06)",
        "gridwidth": 0.5,
        "griddash": "dot",
        "zeroline": False,
        "showline": False,
        "rangemode": "tozero",
    },
    template="plotly_white",
    bargap=0,
    plot_bgcolor="rgba(250,251,254,1)",
    paper_bgcolor="white",
    margin={"l": 80, "r": 45, "t": 85, "b": 70},
    showlegend=True,
    legend={
        "font": {"size": 16, "family": "Arial"},
        "x": 0.02,
        "y": 0.78,
        "bgcolor": "rgba(255,255,255,0.92)",
        "bordercolor": "rgba(0,0,0,0.08)",
        "borderwidth": 1,
    },
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs=True, full_html=True)
