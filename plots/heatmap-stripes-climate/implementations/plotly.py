""" pyplots.ai
heatmap-stripes-climate: Climate Warming Stripes
Library: plotly 6.6.0 | Python 3.14.3
Quality: 92/100 | Created: 2026-03-06
"""

import numpy as np
import plotly.graph_objects as go


# Data
np.random.seed(42)
years = np.arange(1850, 2025)
n_years = len(years)

trend = np.linspace(-0.35, 0.85, n_years)
noise = np.random.normal(0, 0.12, n_years)

volcanic_events = {1883: -0.25, 1912: -0.15, 1942: -0.20, 1991: -0.15}
volcanic_dips = np.zeros(n_years)
for year, dip in volcanic_events.items():
    volcanic_dips[year - years[0]] = dip

anomalies = trend + noise + volcanic_dips
vmax = max(abs(anomalies.min()), abs(anomalies.max()))

# Colorscale (blue to white to red, symmetric around 0)
colorscale = [
    [0.0, "#08306b"],
    [0.25, "#2171b5"],
    [0.45, "#6baed6"],
    [0.5, "#ffffff"],
    [0.55, "#fb6a4a"],
    [0.75, "#cb181d"],
    [1.0, "#67000d"],
]

# Classify each year's anomaly for hover display
labels = np.where(
    anomalies > 0.3,
    "Strong warming",
    np.where(anomalies > 0, "Warm", np.where(anomalies > -0.3, "Cool", "Strong cooling")),
)

# Plot using go.Heatmap with native colorscale and custom hovertemplate
fig = go.Figure(
    data=go.Heatmap(
        z=[anomalies],
        x=years,
        y=[""],
        colorscale=colorscale,
        zmin=-vmax,
        zmax=vmax,
        showscale=False,
        xgap=0,
        ygap=0,
        customdata=[np.column_stack([labels])],
        hovertemplate="<b>%{x}</b><br>Anomaly: %{z:+.2f} °C<br>%{customdata[0]}<extra></extra>",
    )
)

# Subtle decade markers as thin semi-transparent lines
for dy in [1900, 1950, 2000]:
    fig.add_shape(type="line", x0=dy, x1=dy, y0=-0.5, y1=0.5, line={"color": "rgba(255,255,255,0.35)", "width": 1.5})

# Subtle start/end year annotations
fig.add_annotation(
    x=0.01,
    y=-0.02,
    text="1850",
    showarrow=False,
    font={"size": 16, "color": "rgba(80,80,80,0.7)"},
    xanchor="left",
    yanchor="top",
    xref="paper",
    yref="paper",
)
fig.add_annotation(
    x=0.99,
    y=-0.02,
    text="2024",
    showarrow=False,
    font={"size": 16, "color": "rgba(80,80,80,0.7)"},
    xanchor="right",
    yanchor="top",
    xref="paper",
    yref="paper",
)

fig.update_layout(
    title={
        "text": "heatmap-stripes-climate · plotly · pyplots.ai",
        "font": {"size": 28, "color": "#333333"},
        "x": 0.5,
        "y": 0.95,
    },
    paper_bgcolor="white",
    plot_bgcolor="white",
    xaxis={"showgrid": False, "showticklabels": False, "zeroline": False, "showline": False, "range": [1849.5, 2024.5]},
    yaxis={"showgrid": False, "showticklabels": False, "zeroline": False, "showline": False, "fixedrange": True},
    margin={"l": 0, "r": 0, "t": 70, "b": 30},
    showlegend=False,
)

# Save with ~3:1 aspect ratio (wide and short, per spec)
fig.write_image("plot.png", width=1600, height=533, scale=3)
fig.write_html(
    "plot.html", include_plotlyjs="cdn", config={"displayModeBar": False, "scrollZoom": False, "staticPlot": False}
)
