""" pyplots.ai
scatter-ashby-material: Ashby Material Selection Chart
Library: plotly 6.6.0 | Python 3.14.3
Quality: 85/100 | Created: 2026-03-11
"""

import numpy as np
import plotly.graph_objects as go
from scipy.spatial import ConvexHull


# Data - Density (kg/m^3) vs Young's Modulus (GPa) for material families
np.random.seed(42)

families = {
    "Metals": {"density": (4500, 11000), "modulus": (40, 250), "n": 30, "color": "#306998"},
    "Ceramics": {"density": (2200, 4200), "modulus": (150, 500), "n": 25, "color": "#D4513D"},
    "Polymers": {"density": (900, 1500), "modulus": (0.2, 4), "n": 25, "color": "#2CA02C"},
    "Composites": {"density": (1400, 2200), "modulus": (10, 200), "n": 22, "color": "#1B9E77"},
    "Elastomers": {"density": (900, 1300), "modulus": (0.001, 0.1), "n": 20, "color": "#E6932E"},
    "Foams": {"density": (20, 300), "modulus": (0.001, 1), "n": 20, "color": "#17BECF"},
    "Natural Materials": {"density": (150, 1300), "modulus": (0.5, 20), "n": 18, "color": "#8C564B"},
}

# Generate realistic log-uniform data for each family
data = {}
for family, props in families.items():
    log_d_min, log_d_max = np.log10(props["density"][0]), np.log10(props["density"][1])
    log_m_min, log_m_max = np.log10(props["modulus"][0]), np.log10(props["modulus"][1])
    n = props["n"]
    log_density = np.random.uniform(log_d_min, log_d_max, n)
    log_modulus = np.random.uniform(log_m_min, log_m_max, n)
    data[family] = {"density": 10**log_density, "modulus": 10**log_modulus}

# Plot
fig = go.Figure()

for family, props in families.items():
    d = data[family]["density"]
    m = data[family]["modulus"]
    color = props["color"]

    # Draw convex hull envelope for each family
    log_pts = np.column_stack([np.log10(d), np.log10(m)])
    if len(log_pts) >= 3:
        hull = ConvexHull(log_pts)
        hull_indices = np.append(hull.vertices, hull.vertices[0])
        hull_d = 10 ** log_pts[hull_indices, 0]
        hull_m = 10 ** log_pts[hull_indices, 1]
        fig.add_trace(
            go.Scatter(
                x=hull_d,
                y=hull_m,
                mode="lines",
                line={"color": color, "width": 2},
                fill="toself",
                fillcolor=color.replace(")", ", 0.15)")
                if "rgba" in color
                else f"rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.15)",
                showlegend=False,
                hoverinfo="skip",
            )
        )

    # Scatter points
    fig.add_trace(
        go.Scatter(
            x=d,
            y=m,
            mode="markers",
            name=family,
            marker={"size": 13, "color": color, "line": {"width": 1, "color": "white"}, "opacity": 0.85},
            hovertemplate=f"<b>{family}</b><br>Density: %{{x:.0f}} kg/m³<br>Modulus: %{{y:.3g}} GPa<extra></extra>",
        )
    )

    # Family label at centroid
    centroid_d = 10 ** np.mean(np.log10(d))
    centroid_m = 10 ** np.mean(np.log10(m))
    fig.add_annotation(
        x=np.log10(centroid_d),
        y=np.log10(centroid_m),
        xref="x",
        yref="y",
        text=f"<b>{family}</b>",
        showarrow=False,
        font={"size": 15, "color": "#222222"},
        bgcolor="rgba(255, 255, 255, 0.8)",
        borderpad=4,
    )

# Performance index guide lines: E/rho = constant (lightweight stiffness)
guide_values = [0.001, 0.01, 0.1, 1, 10]
density_range = np.array([10, 20000])
for gv in guide_values:
    modulus_line = gv * density_range
    mask = (modulus_line >= 0.0005) & (modulus_line <= 1000)
    if mask.any():
        fig.add_trace(
            go.Scatter(
                x=density_range[mask],
                y=modulus_line[mask],
                mode="lines",
                line={"color": "rgba(0, 0, 0, 0.12)", "width": 1, "dash": "dot"},
                showlegend=False,
                hoverinfo="skip",
            )
        )

# Guide line label
fig.add_annotation(
    x=np.log10(18000),
    y=np.log10(18000 * 0.01),
    xref="x",
    yref="y",
    text="E/ρ = const",
    showarrow=False,
    font={"size": 14, "color": "rgba(0, 0, 0, 0.55)"},
    textangle=-38,
)

# Layout
fig.update_layout(
    title={
        "text": "scatter-ashby-material · plotly · pyplots.ai",
        "font": {"size": 28, "color": "#222222"},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Density (kg/m³)", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "type": "log",
        "showgrid": True,
        "gridcolor": "rgba(0, 0, 0, 0.06)",
        "gridwidth": 1,
        "showline": True,
        "linecolor": "#333333",
        "linewidth": 1,
        "mirror": False,
        "range": [np.log10(10), np.log10(20000)],
    },
    yaxis={
        "title": {"text": "Young's Modulus (GPa)", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "type": "log",
        "showgrid": True,
        "gridcolor": "rgba(0, 0, 0, 0.06)",
        "gridwidth": 1,
        "showline": True,
        "linecolor": "#333333",
        "linewidth": 1,
        "mirror": False,
        "range": [np.log10(0.0005), np.log10(1000)],
    },
    template="plotly_white",
    plot_bgcolor="#FAFAFA",
    paper_bgcolor="#FFFFFF",
    legend={
        "title": {"text": "Material Family", "font": {"size": 18}},
        "font": {"size": 16},
        "bgcolor": "rgba(255, 255, 255, 0.92)",
        "bordercolor": "rgba(0, 0, 0, 0.15)",
        "borderwidth": 1,
        "x": 0.98,
        "y": 0.02,
        "xanchor": "right",
        "yanchor": "bottom",
    },
    width=1600,
    height=900,
    margin={"l": 80, "r": 60, "t": 100, "b": 80},
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
