""" pyplots.ai
histogram-epidemic: Epidemic Curve (Epi Curve)
Library: plotly 6.6.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-05
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Data - simulating a COVID-like outbreak with confirmed, probable, and suspect cases
np.random.seed(42)
dates = pd.date_range("2024-01-15", periods=120, freq="D")

# Wave 1: sharp rise and fall (point-source-like initial cluster)
wave1 = 45 * np.exp(-0.5 * ((np.arange(120) - 25) / 8) ** 2)
# Wave 2: broader propagated wave
wave2 = 80 * np.exp(-0.5 * ((np.arange(120) - 65) / 14) ** 2)
# Wave 3: smaller resurgence
wave3 = 30 * np.exp(-0.5 * ((np.arange(120) - 100) / 7) ** 2)

base_cases = wave1 + wave2 + wave3 + np.random.poisson(2, 120)

confirmed = np.round(base_cases * 0.65).astype(int)
probable = np.round(base_cases * 0.25).astype(int)
suspect = np.round(base_cases * 0.10).astype(int)

cumulative = np.cumsum(confirmed + probable + suspect)

# Plot
fig = go.Figure()

fig.add_trace(
    go.Bar(
        x=dates,
        y=confirmed,
        name="Confirmed",
        marker={"color": "#306998", "line": {"color": "rgba(255,255,255,0.4)", "width": 0.5}},
        hovertemplate="%{y} cases<extra></extra>",
    )
)

fig.add_trace(
    go.Bar(
        x=dates,
        y=probable,
        name="Probable",
        marker={"color": "#e8a838", "line": {"color": "rgba(255,255,255,0.5)", "width": 0.8}},
        hovertemplate="%{y} cases<extra></extra>",
    )
)

fig.add_trace(
    go.Bar(
        x=dates,
        y=suspect,
        name="Suspect",
        marker={"color": "#8cb4d5", "line": {"color": "rgba(255,255,255,0.5)", "width": 0.8}},
        hovertemplate="%{y} cases<extra></extra>",
    )
)

# Cumulative line on secondary y-axis
fig.add_trace(
    go.Scatter(
        x=dates,
        y=cumulative,
        name="Cumulative",
        yaxis="y2",
        mode="lines",
        line={"color": "#c44e52", "width": 3, "dash": "solid"},
        hovertemplate="%{y:,} total<extra></extra>",
    )
)

# Intervention lines
lockdown_date = dates[20]
vaccine_date = dates[75]

for evt_date, evt_text, evt_color in [
    (lockdown_date, "Lockdown imposed", "#8b0000"),
    (vaccine_date, "Vaccination campaign", "#2e7d32"),
]:
    fig.add_shape(
        type="line",
        x0=evt_date,
        x1=evt_date,
        y0=0,
        y1=0.82,
        yref="paper",
        line={"color": evt_color, "width": 2.5, "dash": "dashdot"},
    )
    fig.add_annotation(
        x=evt_date,
        y=0.88,
        yref="paper",
        text=f"<b>{evt_text}</b>",
        showarrow=True,
        arrowhead=0,
        arrowwidth=1.5,
        arrowcolor=evt_color,
        ax=0,
        ay=-20,
        font={"size": 13, "color": evt_color, "family": "Arial"},
        align="center",
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor=evt_color,
        borderwidth=1,
        borderpad=4,
    )

# Layout
fig.update_layout(
    title={
        "text": "histogram-epidemic · plotly · pyplots.ai",
        "font": {"size": 28, "color": "#1a1a2e"},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.96,
    },
    xaxis={
        "title": {"text": "Date of Symptom Onset", "font": {"size": 22, "color": "#333"}},
        "tickfont": {"size": 16, "color": "#555"},
        "tickformat": "%b %d, %Y",
        "dtick": 14 * 24 * 60 * 60 * 1000,
        "tickangle": -30,
        "showgrid": False,
        "zeroline": False,
        "showline": True,
        "linecolor": "#ccc",
        "linewidth": 1,
        "spikemode": "across",
        "spikethickness": 1,
        "spikecolor": "#999",
        "spikedash": "dot",
    },
    hovermode="x unified",
    yaxis={
        "title": {"text": "Daily New Cases", "font": {"size": 22, "color": "#333"}},
        "tickfont": {"size": 18, "color": "#555"},
        "showgrid": True,
        "gridcolor": "rgba(0,0,0,0.07)",
        "gridwidth": 1,
        "griddash": "dot",
        "zeroline": False,
        "showline": False,
        "rangemode": "tozero",
    },
    yaxis2={
        "title": {"text": "Cumulative Cases", "font": {"size": 22, "color": "#c44e52"}},
        "tickfont": {"size": 18, "color": "#c44e52"},
        "overlaying": "y",
        "side": "right",
        "showgrid": False,
        "zeroline": False,
        "rangemode": "tozero",
    },
    barmode="stack",
    bargap=0.1,
    template="plotly_white",
    plot_bgcolor="rgba(248,249,252,1)",
    paper_bgcolor="white",
    legend={
        "font": {"size": 16},
        "orientation": "h",
        "traceorder": "normal",
        "yanchor": "top",
        "y": 0.98,
        "xanchor": "center",
        "x": 0.4,
        "bgcolor": "rgba(255,255,255,0.9)",
        "bordercolor": "rgba(0,0,0,0.15)",
        "borderwidth": 1,
    },
    margin={"l": 75, "r": 80, "t": 70, "b": 75},
)

# Range slider for interactive exploration
fig.update_xaxes(rangeslider={"visible": True, "thickness": 0.06, "bgcolor": "rgba(248,249,252,0.8)"})

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs=True, full_html=True)
