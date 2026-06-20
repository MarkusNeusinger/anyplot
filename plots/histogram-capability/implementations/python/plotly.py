"""anyplot.ai
histogram-capability: Process Capability Plot with Specification Limits
Library: plotly 6.6.0 | Python 3.14.3
Quality: 90/100 | Updated: 2026-06-20
"""

import os

import numpy as np
import plotly.graph_objects as go
from scipy import stats


# Theme tokens — Imprint palette (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

BRAND = "#009E73"  # Imprint position 1 — histogram bars (first series)
LIMIT_COLOR = "#AE3030"  # matte red — spec limit boundaries (semantic: bad/rejection)
TARGET_COLOR = "#DDCC77"  # amber — target nominal reference line

# Data — shaft diameter measurements (mm), slightly off-center to contrast Cp vs Cpk
np.random.seed(42)
measurements = np.random.normal(loc=10.010, scale=0.012, size=200)

lsl = 9.95
usl = 10.05
target = 10.00

mean_val = np.mean(measurements)
sigma = np.std(measurements, ddof=1)

# Capability indices
cp = (usl - lsl) / (6 * sigma)
cpk = min((usl - mean_val) / (3 * sigma), (mean_val - lsl) / (3 * sigma))

# Normal distribution curve (fitted to sample mean and sigma)
x_min, x_max = 9.925, 10.075
x_curve = np.linspace(mean_val - 4 * sigma, mean_val + 4 * sigma, 300)
y_curve = stats.norm.pdf(x_curve, mean_val, sigma)

# Scale curve to match histogram area (count scale)
bin_width = (measurements.max() - measurements.min()) / 25
y_scaled = y_curve * len(measurements) * bin_width

# Plot
fig = go.Figure()

# Rejection zone shading via vrect — clearly visible background, below all traces
fig.add_vrect(x0=x_min, x1=lsl, fillcolor="rgba(174,48,48,0.10)", line_width=0, layer="below")
fig.add_vrect(x0=usl, x1=x_max, fillcolor="rgba(174,48,48,0.10)", line_width=0, layer="below")

# Histogram bars (Imprint brand green — first categorical series)
fig.add_trace(
    go.Histogram(
        x=measurements,
        nbinsx=25,
        marker={"color": "rgba(0,158,115,0.75)", "line": {"color": PAGE_BG, "width": 1.2}},
        name="Measurements",
        hovertemplate="Diameter: %{x:.4f} mm<br>Count: %{y}<extra></extra>",
    )
)

# Normal distribution curve (INK — analytical/structural layer)
fig.add_trace(
    go.Scatter(
        x=x_curve,
        y=y_scaled,
        mode="lines",
        line={"color": INK, "width": 3.0, "shape": "spline"},
        name="Normal Fit",
        hoverinfo="skip",
    )
)

# LSL vertical line (matte red — rejection boundary)
fig.add_shape(
    type="line", x0=lsl, x1=lsl, y0=0, y1=0.90, yref="paper", line={"color": LIMIT_COLOR, "width": 2.5, "dash": "dash"}
)
fig.add_annotation(
    x=lsl,
    y=0.93,
    yref="paper",
    text=f"<b>LSL</b><br>{lsl}",
    showarrow=False,
    font={"size": 11, "color": LIMIT_COLOR},
    align="center",
)

# USL vertical line (matte red — rejection boundary)
fig.add_shape(
    type="line", x0=usl, x1=usl, y0=0, y1=0.90, yref="paper", line={"color": LIMIT_COLOR, "width": 2.5, "dash": "dash"}
)
fig.add_annotation(
    x=usl,
    y=0.93,
    yref="paper",
    text=f"<b>USL</b><br>{usl}",
    showarrow=False,
    font={"size": 11, "color": LIMIT_COLOR},
    align="center",
)

# Target line (amber — nominal reference point)
fig.add_shape(
    type="line",
    x0=target,
    x1=target,
    y0=0,
    y1=0.90,
    yref="paper",
    line={"color": TARGET_COLOR, "width": 2.5, "dash": "dashdot"},
)
fig.add_annotation(
    x=target,
    y=0.93,
    yref="paper",
    text=f"<b>Target</b><br>{target:.2f}",
    showarrow=False,
    font={"size": 11, "color": TARGET_COLOR},
    align="center",
)

# Capability status
cpk_status = "Capable" if cpk >= 1.33 else "Marginal" if cpk >= 1.0 else "Not Capable"
cpk_flag = "PASS" if cpk >= 1.33 else "WARN" if cpk >= 1.0 else "FAIL"

# Process capability annotation card
fig.add_annotation(
    x=0.98,
    y=0.86,
    xref="paper",
    yref="paper",
    text=(
        f"<b>Process Capability</b><br>"
        f"Cp = {cp:.2f}    Cpk = {cpk:.2f}<br>"
        f"<br>"
        f"μ = {mean_val:.4f} mm<br>"
        f"σ = {sigma:.4f} mm<br>"
        f"<br>"
        f"<b>{cpk_status}</b> [{cpk_flag}]"
    ),
    showarrow=False,
    font={"size": 11, "color": INK},
    align="left",
    xanchor="right",
    yanchor="top",
    bgcolor=ELEVATED_BG,
    bordercolor=INK_SOFT,
    borderwidth=1.5,
    borderpad=10,
)

# Layout
fig.update_layout(
    autosize=False,
    title={
        "text": (
            "<b>Shaft Diameter Process Capability</b>"
            f"<br><span style='font-size:12px;color:{INK_MUTED}'>"
            "histogram-capability · python · plotly · anyplot.ai</span>"
        ),
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.97,
        "yanchor": "top",
    },
    xaxis={
        "title": {"text": "Shaft Diameter (mm)", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "showgrid": False,
        "zeroline": False,
        "showline": True,
        "linecolor": INK_SOFT,
        "linewidth": 1,
        "range": [x_min, x_max],
        "dtick": 0.01,
        "tickformat": ".2f",
        "gridcolor": GRID,
        "zerolinecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": "Frequency", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "showgrid": True,
        "gridcolor": GRID,
        "gridwidth": 0.5,
        "zeroline": False,
        "showline": False,
        "rangemode": "tozero",
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    template="plotly_white",
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    bargap=0,
    margin={"l": 80, "r": 50, "t": 80, "b": 60},
    showlegend=True,
    legend={
        "font": {"size": 10, "color": INK_SOFT},
        "x": 0.02,
        "y": 0.78,
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
    },
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
