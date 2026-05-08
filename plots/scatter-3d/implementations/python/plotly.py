""" anyplot.ai
scatter-3d: 3D Scatter Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-08
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - Molecular compound properties (3D chemical space)
np.random.seed(42)

# Three distinct clusters representing different compound families
# X: Molecular Weight (g/mol), Y: LogP (lipophilicity), Z: Tpsa (polar surface area)
cluster1_x = np.random.normal(320, 40, 50)  # Heavy molecules
cluster1_y = np.random.normal(3.5, 0.8, 50)
cluster1_z = np.random.normal(60, 15, 50)

cluster2_x = np.random.normal(180, 30, 50)  # Light molecules
cluster2_y = np.random.normal(1.2, 0.6, 50)
cluster2_z = np.random.normal(40, 10, 50)

cluster3_x = np.random.normal(250, 35, 50)  # Medium molecules
cluster3_y = np.random.normal(2.8, 0.7, 50)
cluster3_z = np.random.normal(80, 12, 50)

x = np.concatenate([cluster1_x, cluster2_x, cluster3_x])
y = np.concatenate([cluster1_y, cluster2_y, cluster3_y])
z = np.concatenate([cluster1_z, cluster2_z, cluster3_z])

# Use molecular weight for color (continuous dimension)
color = x

# Create 3D scatter plot with turbo colormap for library differentiation
fig = go.Figure(
    data=[
        go.Scatter3d(
            x=x,
            y=y,
            z=z,
            mode="markers",
            marker=dict(
                size=12,
                color=color,
                colorscale="Turbo",
                opacity=0.8,
                colorbar=dict(
                    title=dict(text="Molecular Weight (g/mol)", font=dict(size=22)),
                    tickfont=dict(size=16),
                    thickness=25,
                    len=0.7,
                    x=1.02,
                    xpad=15,
                ),
            ),
            hovertemplate="<b>Compound Analysis</b><br>"
            "Molecular Weight: %{marker.color:.1f} g/mol<br>"
            "LogP (Lipophilicity): %{y:.2f}<br>"
            "Polar Surface Area: %{z:.1f} Ų<br>"
            "<extra></extra>",
        )
    ]
)

# Update layout with theme-adaptive styling
fig.update_layout(
    title=dict(text="scatter-3d · plotly · anyplot.ai", font=dict(size=32, color=INK), x=0.5, xanchor="center"),
    scene=dict(
        xaxis=dict(
            title=dict(text="Molecular Weight (g/mol)", font=dict(size=22, color=INK)),
            tickfont=dict(size=16, color=INK_SOFT),
            gridcolor="rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)",
            showbackground=True,
            backgroundcolor=PAGE_BG,
        ),
        yaxis=dict(
            title=dict(text="LogP (Lipophilicity)", font=dict(size=22, color=INK)),
            tickfont=dict(size=16, color=INK_SOFT),
            gridcolor="rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)",
            showbackground=True,
            backgroundcolor=PAGE_BG,
        ),
        zaxis=dict(
            title=dict(text="Polar Surface Area (Ų)", font=dict(size=22, color=INK)),
            tickfont=dict(size=16, color=INK_SOFT),
            gridcolor="rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)",
            showbackground=True,
            backgroundcolor=PAGE_BG,
        ),
        camera=dict(eye=dict(x=1.5, y=1.5, z=1.2)),
        bgcolor=PAGE_BG,
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(color=INK),
    margin=dict(l=60, r=100, t=120, b=60),
)

# Save outputs (theme-suffixed filenames)
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
