""" pyplots.ai
line-parametric: Parametric Curve Plot
Library: plotly 6.6.0 | Python 3.14.3
Quality: 87/100 | Created: 2026-03-20
"""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Data
n_points = 2000
n_segments = 200

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


def interpolate_color(frac):
    """Interpolate RGB color from the custom colorscale at given fraction [0, 1]."""
    stops = [0.0, 0.15, 0.35, 0.55, 0.75, 1.0]
    colors = [(48, 105, 152), (42, 128, 148), (68, 148, 120), (148, 138, 78), (198, 105, 62), (228, 87, 58)]
    for i in range(len(stops) - 1):
        if frac <= stops[i + 1]:
            local = (frac - stops[i]) / (stops[i + 1] - stops[i])
            r = int(colors[i][0] + local * (colors[i + 1][0] - colors[i][0]))
            g = int(colors[i][1] + local * (colors[i + 1][1] - colors[i][1]))
            b = int(colors[i][2] + local * (colors[i + 1][2] - colors[i][2]))
            return f"rgb({r},{g},{b})"
    return f"rgb({colors[-1][0]},{colors[-1][1]},{colors[-1][2]})"


# Plot
fig = make_subplots(
    rows=1,
    cols=2,
    subplot_titles=(
        "<b>Lissajous Figure</b><br><i>x = sin(3t), y = sin(2t) — closed, self-intersecting curve</i>",
        "<b>Archimedean Spiral</b><br><i>x = t·cos(t), y = t·sin(t) — open, expanding outward</i>",
    ),
    horizontal_spacing=0.16,
)

# Draw smooth colored line segments for each curve
for xx, yy, t_vals, col_idx, cb_x, cb_ticks, cb_labels in [
    (
        x_lissajous,
        y_lissajous,
        t_lissajous,
        1,
        0.44,
        [0, np.pi / 2, np.pi, 3 * np.pi / 2, 2 * np.pi],
        ["0", "π/2", "π", "3π/2", "2π"],
    ),
    (x_spiral, y_spiral, t_spiral, 2, 1.02, [0, np.pi, 2 * np.pi, 3 * np.pi, 4 * np.pi], ["0", "π", "2π", "3π", "4π"]),
]:
    # Create smooth gradient by drawing overlapping line segments
    seg_size = n_points // n_segments
    for i in range(n_segments):
        start = i * seg_size
        end = min(start + seg_size + 1, n_points)
        frac = i / (n_segments - 1)
        color = interpolate_color(frac)
        fig.add_trace(
            go.Scatter(
                x=xx[start:end],
                y=yy[start:end],
                mode="lines",
                line={"width": 3.5, "color": color},
                showlegend=False,
                hoverinfo="skip",
            ),
            row=1,
            col=col_idx,
        )

    # Invisible scatter for colorbar and hover
    fig.add_trace(
        go.Scatter(
            x=xx[::10],
            y=yy[::10],
            mode="markers",
            marker={
                "size": 0.1,
                "opacity": 0,
                "color": t_vals[::10],
                "colorscale": colorscale,
                "showscale": True,
                "colorbar": {
                    "title": {"text": "Parameter <i>t</i> (rad)", "font": {"size": 18}, "side": "right"},
                    "tickvals": cb_ticks,
                    "ticktext": cb_labels,
                    "tickfont": {"size": 16},
                    "len": 0.75,
                    "x": cb_x,
                    "thickness": 16,
                    "outlinewidth": 0,
                },
            },
            hovertemplate=("t = %{customdata[0]:.3f} rad<br>x(t) = %{x:.3f}<br>y(t) = %{y:.3f}<extra></extra>"),
            customdata=np.column_stack([t_vals[::10]]),
            showlegend=False,
        ),
        row=1,
        col=col_idx,
    )

# Start/end markers and annotations for both curves
markers_config = [(x_lissajous, y_lissajous, 1, "x", "y", "0", "2π"), (x_spiral, y_spiral, 2, "x2", "y2", "0", "4π")]
for xx, yy, col_idx, xref, yref, t_start, t_end in markers_config:
    # Start marker
    fig.add_trace(
        go.Scatter(
            x=[xx[0]],
            y=[yy[0]],
            mode="markers",
            marker={"size": 16, "color": "#306998", "symbol": "circle", "line": {"color": "white", "width": 2.5}},
            showlegend=False,
            hovertemplate=f"<b>Start</b> (t = {t_start})<extra></extra>",
        ),
        row=1,
        col=col_idx,
    )
    fig.add_annotation(
        x=xx[0],
        y=yy[0],
        text=f"<b>Start</b> (t = {t_start})",
        showarrow=True,
        arrowhead=0,
        arrowwidth=1.5,
        arrowcolor="#306998",
        ax=55,
        ay=-45,
        font={"size": 16, "color": "#306998"},
        bgcolor="rgba(255,255,255,0.88)",
        bordercolor="#306998",
        borderwidth=1,
        borderpad=4,
        xref=xref,
        yref=yref,
    )
    # End marker
    fig.add_trace(
        go.Scatter(
            x=[xx[-1]],
            y=[yy[-1]],
            mode="markers",
            marker={"size": 16, "color": "#E4573A", "symbol": "square", "line": {"color": "white", "width": 2.5}},
            showlegend=False,
            hovertemplate=f"<b>End</b> (t = {t_end})<extra></extra>",
        ),
        row=1,
        col=col_idx,
    )
    ax_offset = -55 if col_idx == 1 else -60
    ay_offset = 45 if col_idx == 1 else -35
    fig.add_annotation(
        x=xx[-1],
        y=yy[-1],
        text=f"<b>End</b> (t = {t_end})",
        showarrow=True,
        arrowhead=0,
        arrowwidth=1.5,
        arrowcolor="#E4573A",
        ax=ax_offset,
        ay=ay_offset,
        font={"size": 16, "color": "#E4573A"},
        bgcolor="rgba(255,255,255,0.88)",
        bordercolor="#E4573A",
        borderwidth=1,
        borderpad=4,
        xref=xref,
        yref=yref,
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
    margin={"l": 70, "r": 70, "t": 120, "b": 70},
)

# Style subplot titles
for annotation in fig.layout.annotations:
    if hasattr(annotation, "text") and ("<b>" in str(annotation.text)):
        annotation.font = {"size": 18, "color": "#2a2a2a"}

for col in [1, 2]:
    fig.update_xaxes(
        title={"text": "Horizontal Position x(t)", "font": {"size": 22, "color": "#444"}, "standoff": 12},
        tickfont={"size": 18, "color": "#666"},
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(0,0,0,0.05)",
        zeroline=True,
        zerolinewidth=1.5,
        zerolinecolor="rgba(0,0,0,0.15)",
        showline=True,
        linewidth=1,
        linecolor="rgba(0,0,0,0.18)",
        scaleanchor="y" if col == 1 else "y2",
        scaleratio=1,
        row=1,
        col=col,
    )
    fig.update_yaxes(
        title={"text": "Vertical Position y(t)", "font": {"size": 22, "color": "#444"}, "standoff": 12},
        tickfont={"size": 18, "color": "#666"},
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(0,0,0,0.05)",
        zeroline=True,
        zerolinewidth=1.5,
        zerolinecolor="rgba(0,0,0,0.15)",
        showline=True,
        linewidth=1,
        linecolor="rgba(0,0,0,0.18)",
        row=1,
        col=col,
    )

# Plotly-specific: interactive reset button
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
