""" pyplots.ai
scatter-connected-temporal: Connected Scatter Plot with Temporal Path
Library: plotly 6.6.0 | Python 3.14.3
Quality: 82/100 | Created: 2026-03-13
"""

import numpy as np
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

# Viridis-inspired multi-hue colorscale for stronger temporal contrast
colorscale = [
    [0.0, "#440154"],
    [0.15, "#482878"],
    [0.3, "#3e4989"],
    [0.45, "#31688e"],
    [0.6, "#26828e"],
    [0.75, "#1f9e89"],
    [0.85, "#6ece58"],
    [1.0, "#fde725"],
]

fig = go.Figure()

# Segment-by-segment colored connecting lines for temporal gradient on path
for i in range(n - 1):
    seg_color_t = t_norm[i]
    # Sample the viridis scale for this segment
    r = int(68 + (253 - 68) * seg_color_t)
    g = int(1 + (231 - 1) * seg_color_t)
    b = int(84 + (37 - 84) * seg_color_t)
    fig.add_trace(
        go.Scatter(
            x=unemployment[i : i + 2],
            y=inflation[i : i + 2],
            mode="lines",
            line={"color": f"rgba({r}, {g}, {b}, 0.55)", "width": 3},
            hoverinfo="skip",
            showlegend=False,
        )
    )

# Data points with multi-hue color gradient
fig.add_trace(
    go.Scatter(
        x=unemployment,
        y=inflation,
        mode="markers",
        marker={
            "size": 18,
            "color": t_norm,
            "colorscale": colorscale,
            "line": {"color": "white", "width": 2},
            "colorbar": {
                "title": {"text": "Year", "font": {"size": 18}},
                "tickvals": [0, 0.25, 0.5, 0.75, 1],
                "ticktext": ["1990", "1998", "2006", "2015", "2023"],
                "tickfont": {"size": 16},
                "len": 0.55,
                "thickness": 18,
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
        bgcolor="rgba(255, 255, 255, 0.75)",
        borderpad=3,
    )

# Directional arrow at midpoint showing temporal flow
mid = n // 2
fig.add_annotation(
    x=unemployment[mid],
    y=inflation[mid],
    ax=unemployment[mid - 2],
    ay=inflation[mid - 2],
    xref="x",
    yref="y",
    axref="x",
    ayref="y",
    showarrow=True,
    arrowhead=3,
    arrowsize=2.5,
    arrowwidth=2.5,
    arrowcolor="#31688e",
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
    margin={"l": 90, "r": 120, "t": 90, "b": 90},
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
