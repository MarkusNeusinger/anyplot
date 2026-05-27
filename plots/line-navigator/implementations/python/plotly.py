"""anyplot.ai
line-navigator: Line Chart with Mini Navigator
Library: plotly 6.7.0 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-27
"""

import os
import sys


# Prevent this file from shadowing the installed plotly package
_script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path if p and os.path.abspath(p) != _script_dir]

import numpy as np
import pandas as pd
import plotly.graph_objects as go


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"
BRAND = "#009E73"
FILL_COLOR = "rgba(0,158,115,0.12)" if THEME == "light" else "rgba(0,158,115,0.15)"

# Data - Daily temperature sensor data over 3 years (~1100 data points)
np.random.seed(42)
dates = pd.date_range("2022-01-01", periods=1100, freq="D")
days_of_year = np.arange(1100) % 365
seasonal = 15 * np.sin(2 * np.pi * days_of_year / 365)
trend = np.linspace(0, 3, 1100)
noise = np.random.randn(1100) * 2
values = 20 + seasonal + trend + noise

df = pd.DataFrame({"date": dates, "value": values})

title = "Temperature Sensor Data · line-navigator · python · plotly · anyplot.ai"
n = len(title)
ratio = 67 / n if n > 67 else 1.0
title_fontsize = max(11, round(16 * ratio))

# Plot
fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=df["date"],
        y=df["value"],
        mode="lines",
        name="Temperature",
        line={"color": BRAND, "width": 2},
        fill="tozeroy",
        fillcolor=FILL_COLOR,
        hovertemplate="%{x|%Y-%m-%d}<br>%{y:.1f}°C<extra></extra>",
        showlegend=False,
    )
)

fig.update_layout(
    autosize=False,
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    title={"text": title, "font": {"size": title_fontsize, "color": INK}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": "Date", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "showgrid": False,
        "showline": False,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
        "showspikes": True,
        "spikemode": "across",
        "spikesnap": "cursor",
        "spikethickness": 1,
        "spikecolor": INK_SOFT,
        "spikedash": "dot",
        "rangeslider": {
            "visible": True,
            "thickness": 0.15,
            "bgcolor": ELEVATED_BG,
            "bordercolor": INK_SOFT,
            "borderwidth": 1,
        },
        "rangeselector": {
            "buttons": [
                {"count": 1, "label": "1M", "step": "month", "stepmode": "backward"},
                {"count": 3, "label": "3M", "step": "month", "stepmode": "backward"},
                {"count": 6, "label": "6M", "step": "month", "stepmode": "backward"},
                {"count": 1, "label": "1Y", "step": "year", "stepmode": "backward"},
                {"step": "all", "label": "All"},
            ],
            "font": {"size": 10, "color": INK},
            "bgcolor": ELEVATED_BG,
            "activecolor": BRAND,
            "bordercolor": INK_SOFT,
            "borderwidth": 1,
            "x": 0,
            "y": 1.08,
        },
        "type": "date",
    },
    yaxis={
        "title": {"text": "Temperature (°C)", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "showline": False,
        "zeroline": False,
        "showspikes": True,
        "spikemode": "across",
        "spikesnap": "cursor",
        "spikethickness": 1,
        "spikecolor": INK_SOFT,
        "spikedash": "dot",
    },
    hovermode="x unified",
    margin={"l": 80, "r": 40, "t": 100, "b": 60},
)

fig.add_hline(
    y=0,
    line_dash="dot",
    line_color=INK_SOFT,
    line_width=1,
    annotation_text="Freezing Point",
    annotation_font_size=9,
    annotation_font_color=INK_SOFT,
    annotation_position="bottom right",
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
