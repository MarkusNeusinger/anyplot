""" pyplots.ai
scatter-connected-temporal: Connected Scatter Plot with Temporal Path
Library: plotly 6.6.0 | Python 3.14.3
Quality: 91/100 | Created: 2026-03-13
"""

import numpy as np
import plotly.colors as pc
import plotly.graph_objects as go


# Data - US-style Phillips Curve: Unemployment vs Inflation (1990-2023)
np.random.seed(42)

years = np.arange(1990, 2024)
n = len(years)

# Realistic unemployment and inflation patterns
unemployment = np.array(
    [
        5.6,
        6.8,
        7.5,
        6.9,
        6.1,
        5.6,
        5.4,
        4.9,
        4.5,
        4.2,  # 1990s recovery
        4.0,
        4.7,
        5.8,
        6.0,
        5.5,
        5.1,
        4.6,
        4.6,
        5.8,
        9.3,  # 2000s + recession
        9.6,
        8.9,
        8.1,
        7.4,
        6.2,
        5.3,
        4.9,
        4.4,
        3.9,
        3.7,  # 2010s recovery
        8.1,
        5.4,
        3.6,
        3.6,  # 2020s pandemic
    ]
)

inflation = np.array(
    [
        5.4,
        4.2,
        3.0,
        3.0,
        2.6,
        2.8,
        3.0,
        2.3,
        1.6,
        2.2,  # 1990s
        3.4,
        2.8,
        1.6,
        2.3,
        2.7,
        3.4,
        3.2,
        2.8,
        3.8,
        -0.4,  # 2000s
        1.6,
        3.2,
        2.1,
        1.5,
        1.6,
        0.1,
        1.3,
        2.1,
        2.4,
        1.8,  # 2010s
        1.2,
        4.7,
        8.0,
        4.1,  # 2020s
    ]
)

# Temporal normalization for color mapping
t_norm = np.linspace(0, 1, n)

# Use Plotly's built-in viridis colorscale for consistent color sampling
viridis = pc.get_colorscale("viridis")

fig = go.Figure()

# Segment-by-segment colored lines using Plotly's sample_colorscale for consistency
seg_colors = pc.sample_colorscale("viridis", [t_norm[i] for i in range(n - 1)])

for i in range(n - 1):
    r, g, b = pc.unlabel_rgb(seg_colors[i])
    fig.add_trace(
        go.Scatter(
            x=unemployment[i : i + 2],
            y=inflation[i : i + 2],
            mode="lines",
            line={"color": f"rgba({r}, {g}, {b}, 0.6)", "width": 3.5},
            hoverinfo="skip",
            showlegend=False,
        )
    )

# Data points with viridis color gradient
fig.add_trace(
    go.Scatter(
        x=unemployment,
        y=inflation,
        mode="markers",
        marker={
            "size": 18,
            "color": t_norm,
            "colorscale": "viridis",
            "line": {"color": "white", "width": 2},
            "colorbar": {
                "title": {"text": "Year", "font": {"size": 18}},
                "tickvals": [0, 0.2, 0.4, 0.6, 0.8, 1],
                "ticktext": ["1990", "1997", "2003", "2010", "2017", "2023"],
                "tickfont": {"size": 16},
                "len": 0.75,
                "thickness": 22,
                "outlinewidth": 0,
                "x": 1.02,
            },
        },
        text=[str(y) for y in years],
        customdata=np.column_stack([years, unemployment, inflation]),
        hovertemplate=(
            "<b>%{customdata[0]:.0f}</b><br>"
            "Unemployment: %{customdata[1]:.1f}%<br>"
            "Inflation: %{customdata[2]:.1f}%"
            "<extra></extra>"
        ),
        showlegend=False,
    )
)

# Annotate key time points with improved positioning
key_points = {
    0: ("1990", 45, -35),
    9: ("1999", -50, -40),
    19: ("2009", 50, 30),
    30: ("2020", -55, 35),
    32: ("2022", -55, -35),
    33: ("2023", 50, -30),
}

for idx, (label, ax_off, ay_off) in key_points.items():
    fig.add_annotation(
        x=unemployment[idx],
        y=inflation[idx],
        text=f"<b>{label}</b>",
        showarrow=True,
        arrowhead=0,
        arrowcolor="rgba(80, 80, 80, 0.35)",
        arrowwidth=1.5,
        ax=ax_off,
        ay=ay_off,
        font={"size": 16, "color": "#2d2d2d"},
        bgcolor="rgba(255, 255, 255, 0.8)",
        borderpad=4,
    )

# Directional arrows showing temporal flow at two path points
for start_idx, end_idx, color in [
    (10, 13, "#3e4989"),  # Early 2000s path direction
    (27, 30, "#6ece58"),  # Late 2010s into pandemic
]:
    fig.add_annotation(
        x=unemployment[end_idx],
        y=inflation[end_idx],
        ax=unemployment[start_idx],
        ay=inflation[start_idx],
        xref="x",
        yref="y",
        axref="x",
        ayref="y",
        showarrow=True,
        arrowhead=3,
        arrowsize=2,
        arrowwidth=2.5,
        arrowcolor=color,
        opacity=0.5,
    )

# Decade shading to help distinguish dense regions
decade_labels = [
    {"x": 6.8, "y": 5.0, "text": "1990s", "color": "rgba(68,1,84,0.12)"},
    {"x": 7.8, "y": -0.1, "text": "2000s", "color": "rgba(49,104,142,0.10)"},
    {"x": 4.0, "y": 0.3, "text": "2010s", "color": "rgba(53,183,121,0.10)"},
    {"x": 5.8, "y": 7.5, "text": "2020s", "color": "rgba(253,231,37,0.12)"},
]

for dl in decade_labels:
    fig.add_annotation(
        x=dl["x"],
        y=dl["y"],
        text=f"<i>{dl['text']}</i>",
        showarrow=False,
        font={"size": 20, "color": "rgba(100,100,100,0.5)"},
    )

# Layout with refined styling
fig.update_layout(
    title={
        "text": "scatter-connected-temporal · plotly · pyplots.ai",
        "font": {"size": 28, "color": "#2d2d2d"},
        "x": 0.5,
        "y": 0.96,
    },
    xaxis={
        "title": {"text": "Unemployment Rate (%)", "font": {"size": 22, "color": "#3d3d3d"}},
        "tickfont": {"size": 18, "color": "#555"},
        "showgrid": True,
        "gridcolor": "rgba(0, 0, 0, 0.06)",
        "gridwidth": 1,
        "griddash": "dot",
        "zeroline": False,
        "showline": False,
    },
    yaxis={
        "title": {"text": "Inflation Rate (%)", "font": {"size": 22, "color": "#3d3d3d"}},
        "tickfont": {"size": 18, "color": "#555"},
        "showgrid": True,
        "gridcolor": "rgba(0, 0, 0, 0.06)",
        "gridwidth": 1,
        "griddash": "dot",
        "zeroline": False,
        "showline": False,
    },
    template="plotly_white",
    plot_bgcolor="rgba(250, 250, 252, 1)",
    paper_bgcolor="white",
    width=1600,
    height=900,
    margin={"l": 90, "r": 100, "t": 90, "b": 80},
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
