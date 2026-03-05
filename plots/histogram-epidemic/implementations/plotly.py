"""pyplots.ai
histogram-epidemic: Epidemic Curve (Epi Curve)
Library: plotly | Python 3.13
Quality: pending | Created: 2026-03-05
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
        hovertemplate="Date: %{x|%b %d}<br>Confirmed: %{y}<extra></extra>",
    )
)

fig.add_trace(
    go.Bar(
        x=dates,
        y=probable,
        name="Probable",
        marker={"color": "#e8a838", "line": {"color": "rgba(255,255,255,0.4)", "width": 0.5}},
        hovertemplate="Date: %{x|%b %d}<br>Probable: %{y}<extra></extra>",
    )
)

fig.add_trace(
    go.Bar(
        x=dates,
        y=suspect,
        name="Suspect",
        marker={"color": "#8cb4d5", "line": {"color": "rgba(255,255,255,0.4)", "width": 0.5}},
        hovertemplate="Date: %{x|%b %d}<br>Suspect: %{y}<extra></extra>",
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
        hovertemplate="Date: %{x|%b %d}<br>Cumulative: %{y:,}<extra></extra>",
    )
)

# Intervention lines
lockdown_date = dates[20]
vaccine_date = dates[75]

fig.add_shape(
    type="line",
    x0=lockdown_date,
    x1=lockdown_date,
    y0=0,
    y1=0.85,
    yref="paper",
    line={"color": "#555", "width": 2, "dash": "dash"},
)

fig.add_annotation(
    x=lockdown_date,
    y=0.87,
    yref="paper",
    text="Lockdown<br>imposed",
    showarrow=False,
    font={"size": 13, "color": "#333"},
    align="center",
)

fig.add_shape(
    type="line",
    x0=vaccine_date,
    x1=vaccine_date,
    y0=0,
    y1=0.85,
    yref="paper",
    line={"color": "#555", "width": 2, "dash": "dash"},
)

fig.add_annotation(
    x=vaccine_date,
    y=0.87,
    yref="paper",
    text="Vaccination<br>campaign",
    showarrow=False,
    font={"size": 13, "color": "#333"},
    align="center",
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
        "tickformat": "%b %d",
        "dtick": 14 * 24 * 60 * 60 * 1000,
        "tickangle": -30,
        "showgrid": False,
        "zeroline": False,
        "showline": True,
        "linecolor": "#ccc",
        "linewidth": 1,
    },
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
        "yanchor": "top",
        "y": 0.98,
        "xanchor": "right",
        "x": 0.65,
        "bgcolor": "rgba(255,255,255,0.85)",
        "bordercolor": "rgba(0,0,0,0.1)",
        "borderwidth": 1,
    },
    margin={"l": 75, "r": 80, "t": 70, "b": 75},
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs=True, full_html=True)
