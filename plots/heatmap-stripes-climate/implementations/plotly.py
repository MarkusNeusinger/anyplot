""" pyplots.ai
heatmap-stripes-climate: Climate Warming Stripes
Library: plotly 6.6.0 | Python 3.14.3
Quality: 84/100 | Created: 2026-03-06
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


def anomaly_to_color(val, vmin, vmax_val):
    """Map anomaly value to color using the colorscale."""
    t = (val - vmin) / (vmax_val - vmin)
    t = max(0.0, min(1.0, t))
    for i in range(len(colorscale) - 1):
        t0, c0 = colorscale[i]
        t1, c1 = colorscale[i + 1]
        if t0 <= t <= t1:
            f = (t - t0) / (t1 - t0)
            r0, g0, b0 = int(c0[1:3], 16), int(c0[3:5], 16), int(c0[5:7], 16)
            r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
            r = int(r0 + f * (r1 - r0))
            g = int(g0 + f * (g1 - g0))
            b = int(b0 + f * (b1 - b0))
            return f"rgb({r},{g},{b})"
    return colorscale[-1][1]


bar_colors = [anomaly_to_color(a, -vmax, vmax) for a in anomalies]

# Plot using go.Bar for seamless stripes (no gap artifacts)
fig = go.Figure(
    data=go.Bar(
        x=years, y=[1] * n_years, marker={"color": bar_colors, "line": {"width": 0}}, width=1.0, hoverinfo="skip"
    )
)

# Subtle decade markers as thin semi-transparent lines
decade_years = [1900, 1950, 2000]
for dy in decade_years:
    fig.add_shape(type="line", x0=dy, x1=dy, y0=0, y1=1, line={"color": "rgba(255,255,255,0.35)", "width": 1.5})

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
    yaxis={
        "showgrid": False,
        "showticklabels": False,
        "zeroline": False,
        "showline": False,
        "range": [0, 1],
        "fixedrange": True,
    },
    margin={"l": 0, "r": 0, "t": 70, "b": 30},
    bargap=0,
    bargroupgap=0,
    showlegend=False,
)

# Save with ~3:1 aspect ratio (wide and short, per spec)
fig.write_image("plot.png", width=1600, height=533, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
