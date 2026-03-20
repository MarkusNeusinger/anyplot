""" pyplots.ai
line-parametric: Parametric Curve Plot
Library: plotly 6.6.0 | Python 3.14.3
Quality: 80/100 | Created: 2026-03-20
"""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Data
n_points = 1000
n_segments = 80

t_lissajous = np.linspace(0, 2 * np.pi, n_points)
x_lissajous = np.sin(3 * t_lissajous)
y_lissajous = np.sin(2 * t_lissajous)

t_spiral = np.linspace(0, 4 * np.pi, n_points)
x_spiral = t_spiral * np.cos(t_spiral)
y_spiral = t_spiral * np.sin(t_spiral)

# Color gradient from Python Blue to warm coral
segment_indices = np.linspace(0, n_points - 1, n_segments + 1, dtype=int)
colors_r = np.linspace(48, 228, n_segments, dtype=int)
colors_g = np.linspace(105, 87, n_segments, dtype=int)
colors_b = np.linspace(152, 58, n_segments, dtype=int)

# Plot
fig = make_subplots(
    rows=1,
    cols=2,
    subplot_titles=("Lissajous Figure: x = sin(3t), y = sin(2t)", "Archimedean Spiral: x = t·cos(t), y = t·sin(t)"),
    horizontal_spacing=0.12,
)

# Draw curves as colored segments
for curve_idx, (x_data, y_data) in enumerate([(x_lissajous, y_lissajous), (x_spiral, y_spiral)]):
    col = curve_idx + 1
    for i in range(n_segments):
        start, end = segment_indices[i], segment_indices[i + 1] + 1
        fig.add_trace(
            go.Scatter(
                x=x_data[start:end],
                y=y_data[start:end],
                mode="lines",
                line={"color": f"rgb({colors_r[i]},{colors_g[i]},{colors_b[i]})", "width": 3.5},
                showlegend=False,
                hoverinfo="skip",
            ),
            row=1,
            col=col,
        )

# Start/end markers for Lissajous
fig.add_trace(
    go.Scatter(
        x=[x_lissajous[0]],
        y=[y_lissajous[0]],
        mode="markers+text",
        marker={"size": 14, "color": "#306998", "line": {"color": "white", "width": 2}},
        text=["t = 0"],
        textposition="top right",
        textfont={"size": 16, "color": "#306998"},
        showlegend=False,
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
        text=["t = 2π"],
        textposition="bottom left",
        textfont={"size": 16, "color": "#E4573A"},
        showlegend=False,
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
        text=["t = 0"],
        textposition="top right",
        textfont={"size": 16, "color": "#306998"},
        showlegend=False,
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
        text=["t = 4π"],
        textposition="bottom left",
        textfont={"size": 16, "color": "#E4573A"},
        showlegend=False,
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
    margin={"l": 60, "r": 60, "t": 100, "b": 60},
)

fig.update_annotations(font={"size": 20})

for col in [1, 2]:
    fig.update_xaxes(
        title={"text": "x(t)", "font": {"size": 22}},
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
        title={"text": "y(t)", "font": {"size": 22}},
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
