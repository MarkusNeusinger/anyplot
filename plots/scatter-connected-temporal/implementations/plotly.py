"""pyplots.ai
scatter-connected-temporal: Connected Scatter Plot with Temporal Path
Library: plotly | Python 3.13
Quality: pending | Created: 2026-03-13
"""

import numpy as np
import plotly.graph_objects as go


# Data - US-style Phillips Curve: Unemployment vs Inflation (1990-2023)
np.random.seed(42)

years = np.arange(1990, 2024)
n = len(years)

# Simulate realistic unemployment and inflation patterns
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

# Color gradient: light to dark blue for temporal progression
t_norm = np.linspace(0, 1, n)
colors = [f"rgba(48, 105, 152, {0.3 + 0.7 * t})" for t in t_norm]

# Plot
fig = go.Figure()

# Connecting line path
fig.add_trace(
    go.Scatter(
        x=unemployment,
        y=inflation,
        mode="lines",
        line=dict(color="rgba(48, 105, 152, 0.25)", width=2),
        hoverinfo="skip",
        showlegend=False,
    )
)

# Data points with color gradient
fig.add_trace(
    go.Scatter(
        x=unemployment,
        y=inflation,
        mode="markers",
        marker=dict(
            size=14,
            color=t_norm,
            colorscale=[[0, "#a8c4d8"], [0.5, "#306998"], [1, "#1a3a5c"]],
            line=dict(color="white", width=1.5),
            colorbar=dict(
                title=dict(text="Year", font=dict(size=18)),
                tickvals=[0, 0.5, 1],
                ticktext=["1990", "2006", "2023"],
                tickfont=dict(size=16),
                len=0.5,
                thickness=15,
            ),
        ),
        text=[str(y) for y in years],
        hovertemplate="Year: %{text}<br>Unemployment: %{x:.1f}%<br>Inflation: %{y:.1f}%<extra></extra>",
        showlegend=False,
    )
)

# Annotate key time points
annotations = {0: "1990", 9: "1999", 19: "2009", 30: "2020", 32: "2022", 33: "2023"}

for idx, label in annotations.items():
    x_off = 0.3 if unemployment[idx] < 6 else -0.3
    y_off = 0.4 if inflation[idx] < 5 else -0.4
    fig.add_annotation(
        x=unemployment[idx],
        y=inflation[idx],
        text=f"<b>{label}</b>",
        showarrow=True,
        arrowhead=0,
        arrowcolor="rgba(48, 105, 152, 0.4)",
        arrowwidth=1.5,
        ax=x_off * 60,
        ay=-y_off * 40,
        font=dict(size=16, color="#1a3a5c"),
    )

# Arrow showing direction at midpoint
mid = n // 2
fig.add_annotation(
    x=unemployment[mid],
    y=inflation[mid],
    ax=unemployment[mid - 1],
    ay=inflation[mid - 1],
    xref="x",
    yref="y",
    axref="x",
    ayref="y",
    showarrow=True,
    arrowhead=3,
    arrowsize=2,
    arrowwidth=2,
    arrowcolor="#306998",
)

# Style
fig.update_layout(
    title=dict(text="scatter-connected-temporal · plotly · pyplots.ai", font=dict(size=28), x=0.5),
    xaxis=dict(
        title=dict(text="Unemployment Rate (%)", font=dict(size=22)),
        tickfont=dict(size=18),
        showgrid=True,
        gridcolor="rgba(0, 0, 0, 0.08)",
        gridwidth=1,
        zeroline=False,
        showline=True,
        linecolor="rgba(0, 0, 0, 0.3)",
    ),
    yaxis=dict(
        title=dict(text="Inflation Rate (%)", font=dict(size=22)),
        tickfont=dict(size=18),
        showgrid=True,
        gridcolor="rgba(0, 0, 0, 0.08)",
        gridwidth=1,
        zeroline=False,
        showline=True,
        linecolor="rgba(0, 0, 0, 0.3)",
    ),
    template="plotly_white",
    plot_bgcolor="white",
    width=1600,
    height=900,
    margin=dict(l=80, r=100, t=80, b=80),
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
