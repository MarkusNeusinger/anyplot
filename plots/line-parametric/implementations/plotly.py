""" pyplots.ai
line-parametric: Parametric Curve Plot
Library: plotly 6.6.0 | Python 3.14.3
Quality: 88/100 | Created: 2026-03-20
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

# Custom colorscale from Python Blue (#306998) through teal to coral (#E4573A)
colorscale = [
    [0.0, "rgb(48,105,152)"],
    [0.15, "rgb(42,128,148)"],
    [0.35, "rgb(68,148,120)"],
    [0.55, "rgb(148,138,78)"],
    [0.75, "rgb(198,105,62)"],
    [1.0, "rgb(228,87,58)"],
]

# Plot
fig = make_subplots(
    rows=1,
    cols=2,
    subplot_titles=(
        "<b>Lissajous Figure</b><br><i>x = sin(3t), y = sin(2t) — closed, self-intersecting</i>",
        "<b>Archimedean Spiral</b><br><i>x = t·cos(t), y = t·sin(t) — open, expanding</i>",
    ),
    horizontal_spacing=0.14,
)

# Helper: create colored line segments for continuous curve with gradient
for curve_data, col_idx, t_vals, cb_x, cb_ticks, cb_labels, name in [
    (
        (x_lissajous, y_lissajous),
        1,
        t_lissajous,
        0.42,
        [0, np.pi / 2, np.pi, 3 * np.pi / 2, 2 * np.pi],
        ["0", "π/2", "π", "3π/2", "2π"],
        "Lissajous",
    ),
    (
        (x_spiral, y_spiral),
        2,
        t_spiral,
        1.0,
        [0, np.pi, 2 * np.pi, 3 * np.pi, 4 * np.pi],
        ["0", "π", "2π", "3π", "4π"],
        "Spiral",
    ),
]:
    xx, yy = curve_data
    # Continuous line with color gradient via markers on top of a thin line
    # Base line for continuity (thin, neutral)
    fig.add_trace(
        go.Scatter(
            x=xx,
            y=yy,
            mode="lines",
            line={"width": 1.5, "color": "rgba(120,120,120,0.15)"},
            showlegend=False,
            hoverinfo="skip",
        ),
        row=1,
        col=col_idx,
    )
    # Colored markers on top for gradient visualization
    fig.add_trace(
        go.Scatter(
            x=xx,
            y=yy,
            mode="markers",
            marker={
                "size": 6,
                "color": t_vals,
                "colorscale": colorscale,
                "showscale": True,
                "colorbar": {
                    "title": {"text": "Parameter <i>t</i>", "font": {"size": 18}, "side": "right"},
                    "tickvals": cb_ticks,
                    "ticktext": cb_labels,
                    "tickfont": {"size": 16},
                    "len": 0.75,
                    "x": cb_x,
                    "thickness": 18,
                    "outlinewidth": 0,
                },
            },
            hovertemplate=(
                "<b>%{customdata[1]}</b><br>"
                "t = %{customdata[0]:.3f}<br>"
                "x(t) = %{x:.3f}<br>"
                "y(t) = %{y:.3f}"
                "<extra></extra>"
            ),
            customdata=np.column_stack([t_vals, np.full(len(t_vals), name)]),
            showlegend=False,
        ),
        row=1,
        col=col_idx,
    )

# Start/end markers — Lissajous: both near origin, use annotation arrows to avoid overlap
fig.add_trace(
    go.Scatter(
        x=[x_lissajous[0]],
        y=[y_lissajous[0]],
        mode="markers",
        marker={"size": 16, "color": "#306998", "symbol": "circle", "line": {"color": "white", "width": 2.5}},
        showlegend=False,
        hovertemplate="<b>Start</b> (t = 0)<extra></extra>",
    ),
    row=1,
    col=1,
)
fig.add_annotation(
    x=x_lissajous[0],
    y=y_lissajous[0],
    text="<b>Start</b> (t = 0)",
    showarrow=True,
    arrowhead=0,
    arrowwidth=1.5,
    arrowcolor="#306998",
    ax=55,
    ay=-45,
    font={"size": 16, "color": "#306998"},
    bgcolor="rgba(255,255,255,0.85)",
    bordercolor="#306998",
    borderwidth=1,
    borderpad=4,
    xref="x",
    yref="y",
)

fig.add_trace(
    go.Scatter(
        x=[x_lissajous[-1]],
        y=[y_lissajous[-1]],
        mode="markers",
        marker={"size": 16, "color": "#E4573A", "symbol": "square", "line": {"color": "white", "width": 2.5}},
        showlegend=False,
        hovertemplate="<b>End</b> (t = 2π)<extra></extra>",
    ),
    row=1,
    col=1,
)
fig.add_annotation(
    x=x_lissajous[-1],
    y=y_lissajous[-1],
    text="<b>End</b> (t = 2π)",
    showarrow=True,
    arrowhead=0,
    arrowwidth=1.5,
    arrowcolor="#E4573A",
    ax=-55,
    ay=45,
    font={"size": 16, "color": "#E4573A"},
    bgcolor="rgba(255,255,255,0.85)",
    bordercolor="#E4573A",
    borderwidth=1,
    borderpad=4,
    xref="x",
    yref="y",
)

# Start/end markers — Spiral
fig.add_trace(
    go.Scatter(
        x=[x_spiral[0]],
        y=[y_spiral[0]],
        mode="markers",
        marker={"size": 16, "color": "#306998", "symbol": "circle", "line": {"color": "white", "width": 2.5}},
        showlegend=False,
        hovertemplate="<b>Start</b> (t = 0)<extra></extra>",
    ),
    row=1,
    col=2,
)
fig.add_annotation(
    x=x_spiral[0],
    y=y_spiral[0],
    text="<b>Start</b> (t = 0)",
    showarrow=True,
    arrowhead=0,
    arrowwidth=1.5,
    arrowcolor="#306998",
    ax=50,
    ay=-40,
    font={"size": 16, "color": "#306998"},
    bgcolor="rgba(255,255,255,0.85)",
    bordercolor="#306998",
    borderwidth=1,
    borderpad=4,
    xref="x2",
    yref="y2",
)

fig.add_trace(
    go.Scatter(
        x=[x_spiral[-1]],
        y=[y_spiral[-1]],
        mode="markers",
        marker={"size": 16, "color": "#E4573A", "symbol": "square", "line": {"color": "white", "width": 2.5}},
        showlegend=False,
        hovertemplate="<b>End</b> (t = 4π)<extra></extra>",
    ),
    row=1,
    col=2,
)
fig.add_annotation(
    x=x_spiral[-1],
    y=y_spiral[-1],
    text="<b>End</b> (t = 4π)",
    showarrow=True,
    arrowhead=0,
    arrowwidth=1.5,
    arrowcolor="#E4573A",
    ax=-60,
    ay=-35,
    font={"size": 16, "color": "#E4573A"},
    bgcolor="rgba(255,255,255,0.85)",
    bordercolor="#E4573A",
    borderwidth=1,
    borderpad=4,
    xref="x2",
    yref="y2",
)

# Style
fig.update_layout(
    title={
        "text": "line-parametric · plotly · pyplots.ai",
        "font": {"size": 28, "color": "#2a2a2a"},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.97,
    },
    template="plotly_white",
    plot_bgcolor="rgba(248,249,252,1)",
    paper_bgcolor="white",
    width=1200,
    height=600,
    margin={"l": 70, "r": 120, "t": 120, "b": 70},
)

# Style subplot titles
for annotation in fig.layout.annotations:
    if hasattr(annotation, "text") and ("<b>" in str(annotation.text)):
        annotation.font = {"size": 18, "color": "#2a2a2a"}

for col in [1, 2]:
    fig.update_xaxes(
        title={"text": "x(t)", "font": {"size": 22, "color": "#444"}, "standoff": 12},
        tickfont={"size": 18, "color": "#666"},
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(0,0,0,0.06)",
        zeroline=True,
        zerolinewidth=1.5,
        zerolinecolor="rgba(0,0,0,0.18)",
        showline=True,
        linewidth=1,
        linecolor="rgba(0,0,0,0.2)",
        scaleanchor="y" if col == 1 else "y2",
        scaleratio=1,
        row=1,
        col=col,
    )
    fig.update_yaxes(
        title={"text": "y(t)", "font": {"size": 22, "color": "#444"}, "standoff": 12},
        tickfont={"size": 18, "color": "#666"},
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(0,0,0,0.06)",
        zeroline=True,
        zerolinewidth=1.5,
        zerolinecolor="rgba(0,0,0,0.18)",
        showline=True,
        linewidth=1,
        linecolor="rgba(0,0,0,0.2)",
        row=1,
        col=col,
    )

# Plotly-specific: add range slider and update menus for interactivity
fig.update_layout(
    updatemenus=[
        {
            "type": "buttons",
            "showactive": True,
            "x": 0.5,
            "y": -0.12,
            "xanchor": "center",
            "buttons": [
                {
                    "label": "Reset View",
                    "method": "relayout",
                    "args": [
                        {
                            "xaxis.autorange": True,
                            "yaxis.autorange": True,
                            "xaxis2.autorange": True,
                            "yaxis2.autorange": True,
                        }
                    ],
                }
            ],
            "font": {"size": 14},
            "bgcolor": "rgba(48,105,152,0.08)",
            "bordercolor": "#306998",
            "borderwidth": 1,
        }
    ]
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
