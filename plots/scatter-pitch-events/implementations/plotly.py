"""pyplots.ai
scatter-pitch-events: Soccer Pitch Event Map
Library: plotly 6.6.0 | Python 3.14.3
Quality: 89/100 | Created: 2026-03-20
"""

import numpy as np
import plotly.graph_objects as go


# Data
np.random.seed(42)

n_passes = 70
n_shots = 16
n_tackles = 28
n_interceptions = 20

# Passes — distributed across the pitch, biased toward attacking half
pass_x = np.random.beta(2, 1.5, n_passes) * 105
pass_y = np.random.normal(34, 16, n_passes).clip(2, 66)
pass_end_x = pass_x + np.random.normal(15, 8, n_passes)
pass_end_y = pass_y + np.random.normal(0, 10, n_passes)
pass_end_x = pass_end_x.clip(0, 105)
pass_end_y = pass_end_y.clip(0, 68)
pass_success = np.random.choice([True, False], n_passes, p=[0.78, 0.22])

# Shots — concentrated in final third
shot_x = np.random.uniform(72, 98, n_shots)
shot_y = np.random.normal(34, 12, n_shots).clip(14, 54)
shot_end_x = np.full(n_shots, 105.0)
shot_end_y = np.random.normal(34, 4, n_shots).clip(27, 41)
shot_success = np.random.choice([True, False], n_shots, p=[0.33, 0.67])

# Tackles — midfield and defensive zones
tackle_x = np.random.beta(1.5, 2, n_tackles) * 80 + 10
tackle_y = np.random.uniform(5, 63, n_tackles)
tackle_success = np.random.choice([True, False], n_tackles, p=[0.65, 0.35])

# Interceptions — defensive and midfield zones
interception_x = np.random.beta(1.2, 2.5, n_interceptions) * 70 + 5
interception_y = np.random.uniform(8, 60, n_interceptions)
interception_success = np.random.choice([True, False], n_interceptions, p=[0.85, 0.15])

# Pitch
fig = go.Figure()

pitch_color = "#3A9D5C"
line_color = "rgba(255,255,255,0.85)"
lw = 2.5

# Pitch outline (layer="below" so traces render on top)
fig.add_shape(
    type="rect",
    x0=0,
    y0=0,
    x1=105,
    y1=68,
    line={"color": line_color, "width": lw},
    fillcolor=pitch_color,
    layer="below",
)

# Halfway line
fig.add_shape(type="line", x0=52.5, y0=0, x1=52.5, y1=68, line={"color": line_color, "width": lw}, layer="below")

# Penalty areas
fig.add_shape(type="rect", x0=0, y0=13.84, x1=16.5, y1=54.16, line={"color": line_color, "width": lw}, layer="below")
fig.add_shape(type="rect", x0=88.5, y0=13.84, x1=105, y1=54.16, line={"color": line_color, "width": lw}, layer="below")

# Goal areas
fig.add_shape(type="rect", x0=0, y0=24.84, x1=5.5, y1=43.16, line={"color": line_color, "width": lw}, layer="below")
fig.add_shape(type="rect", x0=99.5, y0=24.84, x1=105, y1=43.16, line={"color": line_color, "width": lw}, layer="below")

# Goal posts
fig.add_shape(
    type="rect",
    x0=-2,
    y0=30.34,
    x1=0,
    y1=37.66,
    line={"color": line_color, "width": 2},
    fillcolor="rgba(255,255,255,0.25)",
    layer="below",
)
fig.add_shape(
    type="rect",
    x0=105,
    y0=30.34,
    x1=107,
    y1=37.66,
    line={"color": line_color, "width": 2},
    fillcolor="rgba(255,255,255,0.25)",
    layer="below",
)

# Center circle
theta = np.linspace(0, 2 * np.pi, 100)
fig.add_trace(
    go.Scatter(
        x=52.5 + 9.15 * np.cos(theta),
        y=34 + 9.15 * np.sin(theta),
        mode="lines",
        line={"color": line_color, "width": lw},
        showlegend=False,
        hoverinfo="skip",
    )
)

# Center spot
fig.add_trace(
    go.Scatter(
        x=[52.5], y=[34], mode="markers", marker={"size": 5, "color": line_color}, showlegend=False, hoverinfo="skip"
    )
)

# Penalty spots
fig.add_trace(
    go.Scatter(
        x=[11, 94],
        y=[34, 34],
        mode="markers",
        marker={"size": 4, "color": line_color},
        showlegend=False,
        hoverinfo="skip",
    )
)

# Penalty arcs
la = np.linspace(-0.65, 0.65, 50)
fig.add_trace(
    go.Scatter(
        x=11 + 9.15 * np.cos(la),
        y=34 + 9.15 * np.sin(la),
        mode="lines",
        line={"color": line_color, "width": lw},
        showlegend=False,
        hoverinfo="skip",
    )
)
ra = np.linspace(np.pi - 0.65, np.pi + 0.65, 50)
fig.add_trace(
    go.Scatter(
        x=94 + 9.15 * np.cos(ra),
        y=34 + 9.15 * np.sin(ra),
        mode="lines",
        line={"color": line_color, "width": lw},
        showlegend=False,
        hoverinfo="skip",
    )
)

# Corner arcs
for cx_pos, cy_pos in [(0, 0), (0, 68), (105, 0), (105, 68)]:
    start = (
        0
        if cx_pos == 0 and cy_pos == 0
        else (
            np.pi * 1.5 if cx_pos == 0 and cy_pos == 68 else (np.pi * 0.5 if cx_pos == 105 and cy_pos == 0 else np.pi)
        )
    )
    ct = np.linspace(start, start + np.pi / 2, 25)
    fig.add_trace(
        go.Scatter(
            x=cx_pos + 1.5 * np.cos(ct),
            y=cy_pos + 1.5 * np.sin(ct),
            mode="lines",
            line={"color": line_color, "width": lw},
            showlegend=False,
            hoverinfo="skip",
        )
    )

# Event colors
pass_color = "#4FC3F7"
shot_color = "#FF7043"
tackle_color = "#FFEE58"
intercept_color = "#CE93D8"

# Batch direction lines using None separators for efficiency
# Successful pass lines
pass_s_xs, pass_s_ys = [], []
for i in np.where(pass_success)[0]:
    pass_s_xs.extend([pass_x[i], pass_end_x[i], None])
    pass_s_ys.extend([pass_y[i], pass_end_y[i], None])
fig.add_trace(
    go.Scatter(
        x=pass_s_xs,
        y=pass_s_ys,
        mode="lines",
        line={"color": "rgba(79,195,247,0.18)", "width": 1},
        showlegend=False,
        hoverinfo="skip",
    )
)

# Unsuccessful pass lines
pass_u_xs, pass_u_ys = [], []
for i in np.where(~pass_success)[0]:
    pass_u_xs.extend([pass_x[i], pass_end_x[i], None])
    pass_u_ys.extend([pass_y[i], pass_end_y[i], None])
fig.add_trace(
    go.Scatter(
        x=pass_u_xs,
        y=pass_u_ys,
        mode="lines",
        line={"color": "rgba(79,195,247,0.08)", "width": 0.8, "dash": "dot"},
        showlegend=False,
        hoverinfo="skip",
    )
)

# Successful shot lines
shot_s_xs, shot_s_ys = [], []
for i in np.where(shot_success)[0]:
    shot_s_xs.extend([shot_x[i], shot_end_x[i], None])
    shot_s_ys.extend([shot_y[i], shot_end_y[i], None])
fig.add_trace(
    go.Scatter(
        x=shot_s_xs,
        y=shot_s_ys,
        mode="lines",
        line={"color": "rgba(255,112,67,0.8)", "width": 2.5},
        showlegend=False,
        hoverinfo="skip",
    )
)

# Unsuccessful shot lines
shot_u_xs, shot_u_ys = [], []
for i in np.where(~shot_success)[0]:
    shot_u_xs.extend([shot_x[i], shot_end_x[i], None])
    shot_u_ys.extend([shot_y[i], shot_end_y[i], None])
fig.add_trace(
    go.Scatter(
        x=shot_u_xs,
        y=shot_u_ys,
        mode="lines",
        line={"color": "rgba(255,112,67,0.3)", "width": 2, "dash": "dot"},
        showlegend=False,
        hoverinfo="skip",
    )
)

# Pass markers — circles
fig.add_trace(
    go.Scatter(
        x=pass_x[pass_success],
        y=pass_y[pass_success],
        mode="markers",
        marker={
            "size": 11,
            "color": pass_color,
            "opacity": 0.9,
            "symbol": "circle",
            "line": {"width": 1.5, "color": "white"},
        },
        name="Pass (successful)",
        hovertemplate="<b>Pass</b><br>x: %{x:.0f}m, y: %{y:.0f}m<extra></extra>",
    )
)

fig.add_trace(
    go.Scatter(
        x=pass_x[~pass_success],
        y=pass_y[~pass_success],
        mode="markers",
        marker={
            "size": 11,
            "color": pass_color,
            "opacity": 0.55,
            "symbol": "circle-open",
            "line": {"width": 2, "color": pass_color},
        },
        name="Pass (unsuccessful)",
        hovertemplate="<b>Pass (missed)</b><br>x: %{x:.0f}m, y: %{y:.0f}m<extra></extra>",
    )
)

# Tackle markers — triangles
fig.add_trace(
    go.Scatter(
        x=tackle_x[tackle_success],
        y=tackle_y[tackle_success],
        mode="markers",
        marker={
            "size": 16,
            "color": tackle_color,
            "opacity": 0.95,
            "symbol": "triangle-up",
            "line": {"width": 1.5, "color": "white"},
        },
        name="Tackle (successful)",
        hovertemplate="<b>Tackle</b><br>x: %{x:.0f}m, y: %{y:.0f}m<extra></extra>",
    )
)

fig.add_trace(
    go.Scatter(
        x=tackle_x[~tackle_success],
        y=tackle_y[~tackle_success],
        mode="markers",
        marker={
            "size": 16,
            "color": tackle_color,
            "opacity": 0.55,
            "symbol": "triangle-up-open",
            "line": {"width": 2.5, "color": tackle_color},
        },
        name="Tackle (unsuccessful)",
        hovertemplate="<b>Tackle (missed)</b><br>x: %{x:.0f}m, y: %{y:.0f}m<extra></extra>",
    )
)

# Interception markers — diamonds
fig.add_trace(
    go.Scatter(
        x=interception_x[interception_success],
        y=interception_y[interception_success],
        mode="markers",
        marker={
            "size": 15,
            "color": intercept_color,
            "opacity": 0.95,
            "symbol": "diamond",
            "line": {"width": 1.5, "color": "white"},
        },
        name="Interception (successful)",
        hovertemplate="<b>Interception</b><br>x: %{x:.0f}m, y: %{y:.0f}m<extra></extra>",
    )
)

fig.add_trace(
    go.Scatter(
        x=interception_x[~interception_success],
        y=interception_y[~interception_success],
        mode="markers",
        marker={
            "size": 15,
            "color": intercept_color,
            "opacity": 0.55,
            "symbol": "diamond-open",
            "line": {"width": 2.5, "color": intercept_color},
        },
        name="Interception (unsuccessful)",
        hovertemplate="<b>Interception (missed)</b><br>x: %{x:.0f}m, y: %{y:.0f}m<extra></extra>",
    )
)

# Shot markers — stars (drawn last, top layer)
fig.add_trace(
    go.Scatter(
        x=shot_x[shot_success],
        y=shot_y[shot_success],
        mode="markers",
        marker={
            "size": 22,
            "color": shot_color,
            "opacity": 0.95,
            "symbol": "star",
            "line": {"width": 2, "color": "white"},
        },
        name="Shot (on target)",
        hovertemplate="<b>Shot (on target)</b><br>x: %{x:.0f}m, y: %{y:.0f}m<extra></extra>",
    )
)

fig.add_trace(
    go.Scatter(
        x=shot_x[~shot_success],
        y=shot_y[~shot_success],
        mode="markers",
        marker={
            "size": 22,
            "color": shot_color,
            "opacity": 0.55,
            "symbol": "star-open",
            "line": {"width": 2.5, "color": shot_color},
        },
        name="Shot (off target)",
        hovertemplate="<b>Shot (off target)</b><br>x: %{x:.0f}m, y: %{y:.0f}m<extra></extra>",
    )
)

# Tactical annotation — highlight the shot-dense zone
fig.add_annotation(
    x=85,
    y=62,
    text="<b>Danger Zone</b><br>Shots cluster in<br>the final third",
    showarrow=True,
    arrowhead=2,
    arrowsize=1,
    arrowwidth=1.5,
    arrowcolor="rgba(255,255,255,0.7)",
    ax=0,
    ay=40,
    font={"size": 14, "color": "white", "family": "Arial, sans-serif"},
    bgcolor="rgba(0,0,0,0.45)",
    bordercolor="rgba(255,255,255,0.4)",
    borderwidth=1,
    borderpad=6,
)

# Layout
fig.update_layout(
    title={
        "text": "scatter-pitch-events · plotly · pyplots.ai",
        "font": {"size": 28, "color": "white", "family": "Arial Black, Arial, sans-serif"},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.97,
    },
    xaxis={
        "range": [-4, 109],
        "showgrid": False,
        "zeroline": False,
        "showticklabels": False,
        "showline": False,
        "fixedrange": True,
    },
    yaxis={
        "range": [-4, 72],
        "showgrid": False,
        "zeroline": False,
        "showticklabels": False,
        "showline": False,
        "fixedrange": True,
        "scaleanchor": "x",
        "scaleratio": 1,
    },
    plot_bgcolor="#1B5E20",
    paper_bgcolor="#1B5E20",
    margin={"l": 20, "r": 20, "t": 60, "b": 20},
    legend={
        "font": {"size": 18, "color": "white"},
        "bgcolor": "rgba(0,0,0,0.5)",
        "bordercolor": "rgba(255,255,255,0.3)",
        "borderwidth": 1,
        "x": 0.005,
        "y": 0.99,
        "xanchor": "left",
        "yanchor": "top",
        "itemsizing": "constant",
        "tracegroupgap": 4,
    },
    hoverlabel={"bgcolor": "white", "font_size": 14},
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs=True)
