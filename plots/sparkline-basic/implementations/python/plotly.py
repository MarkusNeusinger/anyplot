""" anyplot.ai
sparkline-basic: Basic Sparkline
Library: plotly 6.8.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-06-16
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette
BRAND = "#009E73"  # position 1 — the single data series (always first)
PEAK = "#4467A3"  # position 3 — high / max marker
TROUGH = "#AE3030"  # position 5 — semantic red for low / min marker
AREA_FILL = "rgba(0,158,115,0.12)"  # brand green, soft area under the line

# Data — inline daily stock closing prices (a classic sparkline use case)
np.random.seed(42)
n_days = 60
daily_returns = np.random.randn(n_days) * 0.018
prices = 180 * np.cumprod(1 + daily_returns)
days = np.arange(n_days)

min_idx = int(np.argmin(prices))
max_idx = int(np.argmax(prices))

# Plot — a single clean sparkline compressed into a wide, short band
fig = go.Figure()

# Soft filled area beneath the line for the trend's shape
fig.add_trace(
    go.Scatter(
        x=days,
        y=prices,
        mode="lines",
        line={"color": BRAND, "width": 4, "shape": "spline", "smoothing": 0.6},
        fill="tozeroy",
        fillcolor=AREA_FILL,
        hovertemplate="Day %{x}<br>$%{y:.2f}<extra></extra>",
        name="Close",
    )
)

# Min point (trough) — semantic red
fig.add_trace(
    go.Scatter(
        x=[days[min_idx]],
        y=[prices[min_idx]],
        mode="markers",
        marker={"color": TROUGH, "size": 20, "line": {"color": PAGE_BG, "width": 3}},
        hovertemplate="Low $%{y:.2f}<extra></extra>",
        name="Low",
    )
)

# Max point (peak) — Imprint blue
fig.add_trace(
    go.Scatter(
        x=[days[max_idx]],
        y=[prices[max_idx]],
        mode="markers",
        marker={"color": PEAK, "size": 20, "line": {"color": PAGE_BG, "width": 3}},
        hovertemplate="High $%{y:.2f}<extra></extra>",
        name="High",
    )
)

# Current (last) value — emphasized endpoint in brand green with a value label
fig.add_trace(
    go.Scatter(
        x=[days[-1]],
        y=[prices[-1]],
        mode="markers+text",
        marker={"color": BRAND, "size": 22, "line": {"color": PAGE_BG, "width": 3}},
        text=[f"${prices[-1]:.0f}"],
        textposition="top center",
        textfont={"color": BRAND, "size": 18},
        hovertemplate="Current $%{y:.2f}<extra></extra>",
        name="Current",
    )
)

# Style — pure sparkline: no axes, gridlines, ticks, or legend
pad = (prices.max() - prices.min()) * 0.25
fig.update_layout(
    autosize=False,
    title={
        "text": "sparkline-basic · python · plotly · anyplot.ai",
        "font": {"size": 20, "color": INK},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.9,
    },
    xaxis={"visible": False, "showgrid": False, "zeroline": False, "showticklabels": False},
    yaxis={
        "visible": False,
        "showgrid": False,
        "zeroline": False,
        "showticklabels": False,
        "range": [prices.min() - pad, prices.max() + pad],
        "domain": [0.36, 0.72],  # compress the line into a wide, short sparkline band
    },
    showlegend=False,
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK_SOFT},
    margin={"l": 70, "r": 70, "t": 120, "b": 70},
)

# Save — hard target 3200 × 1800 (landscape)
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
