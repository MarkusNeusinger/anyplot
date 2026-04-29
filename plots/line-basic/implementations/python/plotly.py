""" anyplot.ai
line-basic: Basic Line Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-04-29
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
BRAND = "#009E73"
BRAND_FILL = "rgba(0,158,115,0.12)"

# Data - Monthly temperature readings (seasonal pattern)
np.random.seed(42)
months = np.arange(1, 13)
month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
temperature = 15 + 12 * np.sin((months - 4) * np.pi / 6) + np.random.randn(12) * 1.5

peak_idx = int(np.argmax(temperature))

# Plot
fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=months,
        y=temperature,
        mode="lines+markers",
        line={"color": BRAND, "width": 5},
        marker={"size": 18, "color": BRAND},
        fill="tozeroy",
        fillcolor=BRAND_FILL,
        hovertemplate="%{customdata}<br>%{y:.1f}°C<extra></extra>",
        customdata=month_labels,
    )
)

# Peak annotation for visual storytelling
fig.add_annotation(
    x=months[peak_idx],
    y=temperature[peak_idx],
    text=f"Peak: {temperature[peak_idx]:.1f}°C",
    showarrow=True,
    arrowhead=2,
    arrowcolor=INK_SOFT,
    arrowwidth=2,
    ax=40,
    ay=-50,
    font={"size": 20, "color": INK},
    bgcolor=ELEVATED_BG,
    bordercolor=INK_SOFT,
    borderwidth=1,
    borderpad=6,
)

fig.update_layout(
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    title={
        "text": "line-basic · plotly · anyplot.ai",
        "font": {"size": 36, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Month", "font": {"size": 28, "color": INK}},
        "tickfont": {"size": 22, "color": INK_SOFT},
        "tickmode": "array",
        "tickvals": months,
        "ticktext": month_labels,
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": GRID,
        "showline": True,
        "linecolor": INK_SOFT,
        "mirror": False,
        "zerolinecolor": GRID,
        "showspikes": True,
        "spikemode": "across",
        "spikethickness": 1,
        "spikedash": "dot",
        "spikecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": "Temperature (°C)", "font": {"size": 28, "color": INK}},
        "tickfont": {"size": 22, "color": INK_SOFT},
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": GRID,
        "showline": True,
        "linecolor": INK_SOFT,
        "mirror": False,
        "zerolinecolor": GRID,
        "rangemode": "tozero",
        "showspikes": True,
        "spikemode": "across",
        "spikethickness": 1,
        "spikedash": "dot",
        "spikecolor": INK_SOFT,
    },
    hovermode="x",
    margin={"t": 120, "b": 100, "l": 120, "r": 60},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
