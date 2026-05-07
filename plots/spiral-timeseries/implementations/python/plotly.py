"""anyplot.ai
Daily Temperatures · spiral-timeseries: Spiral Time Series Chart
Library: plotly | Python 3.13
Quality: pending | Created: 2026-05-07
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Data: Daily average temperatures 2019–2023 (temperate northern hemisphere)
np.random.seed(42)
dates = pd.date_range("2019-01-01", "2023-12-31", freq="D")
n = len(dates)

doy = dates.day_of_year.values.astype(float)
yr_num = (dates.year - 2019).values.astype(float)

seasonal = -12.0 * np.cos(2 * np.pi * doy / 365.25)  # cold Jan, warm Jul
trend = yr_num * 0.4  # gradual multi-year warming signal
noise = np.random.normal(0, 1.8, n)
temperature = 10.0 + seasonal + trend + noise  # °C, roughly −4 to +26

TMIN, TMAX = -5.0, 28.0

# Archimedean spiral geometry (clockwise from top = Jan 1)
SPACING = 2.0
R0 = 1.2
frac = (doy - 1.0) / 365.25
theta = np.pi / 2.0 - 2 * np.pi * frac
r = R0 + (yr_num + frac) * SPACING
x_sp = r * np.cos(theta)
y_sp = r * np.sin(theta)

r_outer = R0 + 5.0 * SPACING  # outer boundary (end of 2023)
r_label = r_outer + 0.55  # month-label ring

# Figure
fig = go.Figure()

# 1. Circular ring guides at each year boundary
arc_t = np.linspace(0, 2 * np.pi, 361)
for k in range(6):
    arc_r = R0 + k * SPACING
    fig.add_trace(
        go.Scatter(
            x=arc_r * np.cos(arc_t),
            y=arc_r * np.sin(arc_t),
            mode="lines",
            line=dict(color=GRID, width=1),
            hoverinfo="skip",
            showlegend=False,
        )
    )

# 2. Radial month dividers and labels
month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
for m, mname in enumerate(month_names):
    mt = np.pi / 2.0 - 2 * np.pi * (m / 12.0)
    fig.add_trace(
        go.Scatter(
            x=[0, (r_outer + 0.1) * np.cos(mt)],
            y=[0, (r_outer + 0.1) * np.sin(mt)],
            mode="lines",
            line=dict(color=GRID, width=1),
            hoverinfo="skip",
            showlegend=False,
        )
    )
    fig.add_annotation(
        x=r_label * np.cos(mt),
        y=r_label * np.sin(mt),
        text=mname,
        showarrow=False,
        font=dict(size=20, color=INK, family="Arial, sans-serif"),
        xanchor="center",
        yanchor="middle",
    )

# 3. Thin connector line (shows spiral path beneath colored markers)
fig.add_trace(
    go.Scatter(
        x=x_sp,
        y=y_sp,
        mode="lines",
        line=dict(color=INK_SOFT, width=1.0),
        opacity=0.35,
        hoverinfo="skip",
        showlegend=False,
    )
)

# 4. Temperature-colored markers (daily resolution, Viridis scale)
fig.add_trace(
    go.Scatter(
        x=x_sp,
        y=y_sp,
        mode="markers",
        marker=dict(
            size=10,
            color=temperature,
            colorscale="Viridis",
            cmin=TMIN,
            cmax=TMAX,
            showscale=True,
            colorbar=dict(
                title=dict(text="Temp (°C)", font=dict(size=20, color=INK)),
                tickfont=dict(size=17, color=INK_SOFT),
                tickvals=[-5, 0, 5, 10, 15, 20, 25],
                bgcolor=ELEVATED_BG,
                bordercolor=INK_SOFT,
                borderwidth=1,
                thickness=24,
                len=0.65,
                x=1.03,
            ),
            line=dict(width=0),
        ),
        text=[f"{d.strftime('%b %d, %Y')}: {t:.1f}°C" for d, t in zip(dates, temperature)],
        hovertemplate="%{text}<extra></extra>",
        showlegend=False,
    )
)

# 5. Year labels at Jan 1 position (top of each ring)
for k, yr in enumerate(range(2019, 2024)):
    yr_r = R0 + k * SPACING + 0.12
    fig.add_annotation(
        x=0.0,
        y=yr_r,
        text=f"<b>{yr}</b>",
        showarrow=False,
        font=dict(size=17, color=INK_MUTED, family="Arial, sans-serif"),
        xanchor="center",
        yanchor="bottom",
        bgcolor=PAGE_BG,
        borderpad=3,
    )

# Layout (square canvas for circular chart)
ax_lim = r_label + 0.5
fig.update_layout(
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    width=1200,
    height=1200,
    title=dict(
        text="Daily Temperatures · spiral-timeseries · plotly · anyplot.ai",
        font=dict(size=26, color=INK, family="Arial, sans-serif"),
        x=0.5,
        xanchor="center",
        y=0.98,
        yanchor="top",
    ),
    xaxis=dict(range=[-ax_lim, ax_lim], scaleanchor="y", scaleratio=1, visible=False),
    yaxis=dict(range=[-ax_lim, ax_lim], visible=False),
    margin=dict(l=20, r=120, t=55, b=20),
    showlegend=False,
)

# Save
fig.write_image(f"plot-{THEME}.png", width=1200, height=1200, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
