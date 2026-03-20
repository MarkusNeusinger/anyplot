""" pyplots.ai
line-parametric: Parametric Curve Plot
Library: plotly 6.6.0 | Python 3.14.3
Quality: 85/100 | Created: 2026-03-20
"""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Data
n_points = 2000

t_lissajous = np.linspace(0, 2 * np.pi, n_points)
x_lissajous = np.sin(3 * t_lissajous)
y_lissajous = np.sin(2 * t_lissajous)

t_spiral = np.linspace(0, 4 * np.pi, n_points)
x_spiral = t_spiral * np.cos(t_spiral)
y_spiral = t_spiral * np.sin(t_spiral)

# Custom colorscale from Python Blue (#306998) to coral (#E4573A)
colorscale = [
    [0.0, "rgb(48,105,152)"],
    [0.25, "rgb(78,108,140)"],
    [0.5, "rgb(138,96,105)"],
    [0.75, "rgb(193,91,73)"],
    [1.0, "rgb(228,87,58)"],
]

# Plot
fig = make_subplots(
    rows=1,
    cols=2,
    subplot_titles=("Lissajous Figure: x = sin(3t), y = sin(2t)", "Archimedean Spiral: x = t·cos(t), y = t·sin(t)"),
    horizontal_spacing=0.12,
)

# Lissajous curve using native colorscale with hover data
fig.add_trace(
    go.Scatter(
        x=x_lissajous,
        y=y_lissajous,
        mode="markers",
        marker={
            "size": 5,
            "color": t_lissajous,
            "colorscale": colorscale,
            "showscale": True,
            "colorbar": {
                "title": {"text": "Parameter t", "font": {"size": 16}},
                "tickvals": [0, np.pi / 2, np.pi, 3 * np.pi / 2, 2 * np.pi],
                "ticktext": ["0", "π/2", "π", "3π/2", "2π"],
                "tickfont": {"size": 14},
                "len": 0.8,
                "x": 0.44,
                "thickness": 15,
            },
        },
        hovertemplate="t = %{customdata:.3f}<br>x(t) = %{x:.3f}<br>y(t) = %{y:.3f}<extra>Lissajous</extra>",
        customdata=t_lissajous,
        showlegend=False,
    ),
    row=1,
    col=1,
)

# Spiral curve using native colorscale with hover data
fig.add_trace(
    go.Scatter(
        x=x_spiral,
        y=y_spiral,
        mode="markers",
        marker={
            "size": 5,
            "color": t_spiral,
            "colorscale": colorscale,
            "showscale": True,
            "colorbar": {
                "title": {"text": "Parameter t", "font": {"size": 16}},
                "tickvals": [0, np.pi, 2 * np.pi, 3 * np.pi, 4 * np.pi],
                "ticktext": ["0", "π", "2π", "3π", "4π"],
                "tickfont": {"size": 14},
                "len": 0.8,
                "x": 1.02,
                "thickness": 15,
            },
        },
        hovertemplate="t = %{customdata:.3f}<br>x(t) = %{x:.3f}<br>y(t) = %{y:.3f}<extra>Spiral</extra>",
        customdata=t_spiral,
        showlegend=False,
    ),
    row=1,
    col=2,
)

# Start/end markers for Lissajous (both at origin — offset labels to avoid overlap)
fig.add_trace(
    go.Scatter(
        x=[x_lissajous[0]],
        y=[y_lissajous[0]],
        mode="markers+text",
        marker={"size": 14, "color": "#306998", "line": {"color": "white", "width": 2}},
        text=["Start (t = 0)"],
        textposition="top right",
        textfont={"size": 16, "color": "#306998"},
        showlegend=False,
        hoverinfo="skip",
    ),
    row=1,
    col=1,
)

fig.add_trace(
    go.Scatter(
        x=[x_lissajous[-1]],
        y=[y_lissajous[-1]],
        mode="markers+text",
        marker={"size": 14, "color": "#E4573A", "symbol": "square", "line": {"color": "white", "width": 2}},
        text=["End (t = 2π)"],
        textposition="bottom left",
        textfont={"size": 16, "color": "#E4573A"},
        showlegend=False,
        hoverinfo="skip",
    ),
    row=1,
    col=1,
)

# Start/end markers for Spiral
fig.add_trace(
    go.Scatter(
        x=[x_spiral[0]],
        y=[y_spiral[0]],
        mode="markers+text",
        marker={"size": 14, "color": "#306998", "line": {"color": "white", "width": 2}},
        text=["Start (t = 0)"],
        textposition="top right",
        textfont={"size": 16, "color": "#306998"},
        showlegend=False,
        hoverinfo="skip",
    ),
    row=1,
    col=2,
)

fig.add_trace(
    go.Scatter(
        x=[x_spiral[-1]],
        y=[y_spiral[-1]],
        mode="markers+text",
        marker={"size": 14, "color": "#E4573A", "symbol": "square", "line": {"color": "white", "width": 2}},
        text=["End (t = 4π)"],
        textposition="bottom left",
        textfont={"size": 16, "color": "#E4573A"},
        showlegend=False,
        hoverinfo="skip",
    ),
    row=1,
    col=2,
)

# Style
fig.update_layout(
    title={"text": "line-parametric · plotly · pyplots.ai", "font": {"size": 28}, "x": 0.5, "xanchor": "center"},
    template="plotly_white",
    plot_bgcolor="white",
    paper_bgcolor="white",
    width=1200,
    height=600,
    margin={"l": 60, "r": 80, "t": 100, "b": 60},
)

fig.update_annotations(font={"size": 20})

for col in [1, 2]:
    fig.update_xaxes(
        title={"text": "x(t) — horizontal position", "font": {"size": 22}},
        tickfont={"size": 18},
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(0,0,0,0.08)",
        zeroline=True,
        zerolinewidth=1,
        zerolinecolor="rgba(0,0,0,0.15)",
        showline=True,
        linewidth=1,
        linecolor="rgba(0,0,0,0.3)",
        scaleanchor="y" if col == 1 else "y2",
        scaleratio=1,
        row=1,
        col=col,
    )
    fig.update_yaxes(
        title={"text": "y(t) — vertical position", "font": {"size": 22}},
        tickfont={"size": 18},
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(0,0,0,0.08)",
        zeroline=True,
        zerolinewidth=1,
        zerolinecolor="rgba(0,0,0,0.15)",
        showline=True,
        linewidth=1,
        linecolor="rgba(0,0,0,0.3)",
        row=1,
        col=col,
    )

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
