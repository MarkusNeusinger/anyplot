""" pyplots.ai
scatter-ashby-material: Ashby Material Selection Chart
Library: plotly 6.6.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-11
"""

import numpy as np
import plotly.graph_objects as go
from scipy.spatial import ConvexHull


# Data - Density (kg/m^3) vs Young's Modulus (GPa) for material families
np.random.seed(42)

# Colorblind-safe palette avoiding red-green confusion
families = {
    "Metals": {"density": (5000, 11000), "modulus": (50, 220), "n": 30, "color": "#306998", "corr": 0.4},
    "Ceramics": {"density": (2200, 4000), "modulus": (180, 500), "n": 25, "color": "#C44E52", "corr": 0.3},
    "Polymers": {"density": (900, 1500), "modulus": (0.2, 4), "n": 25, "color": "#8172B3", "corr": 0.5},
    "Composites": {"density": (1400, 2200), "modulus": (10, 180), "n": 22, "color": "#17BECF", "corr": 0.6},
    "Elastomers": {"density": (900, 1300), "modulus": (0.001, 0.1), "n": 20, "color": "#E5A94F", "corr": 0.3},
    "Foams": {"density": (20, 300), "modulus": (0.001, 1), "n": 20, "color": "#A1A832", "corr": 0.7},
    "Natural Materials": {"density": (150, 1300), "modulus": (0.5, 20), "n": 18, "color": "#8C564B", "corr": 0.5},
}

# Generate log-uniform data with realistic intra-family correlations
data = {}
for family, props in families.items():
    log_d_min, log_d_max = np.log10(props["density"][0]), np.log10(props["density"][1])
    log_m_min, log_m_max = np.log10(props["modulus"][0]), np.log10(props["modulus"][1])
    n = props["n"]
    r = props["corr"]
    # Correlated bivariate normal in log-space, then clip to range
    mean = [0.5 * (log_d_min + log_d_max), 0.5 * (log_m_min + log_m_max)]
    std_d = (log_d_max - log_d_min) / 4
    std_m = (log_m_max - log_m_min) / 4
    cov = [[std_d**2, r * std_d * std_m], [r * std_d * std_m, std_m**2]]
    pts = np.random.multivariate_normal(mean, cov, n)
    log_density = np.clip(pts[:, 0], log_d_min, log_d_max)
    log_modulus = np.clip(pts[:, 1], log_m_min, log_m_max)
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

    # Scatter points with E/rho performance index in hover
    e_over_rho = m / (d / 1000)  # GPa per (Mg/m³)
    fig.add_trace(
        go.Scatter(
            x=d,
            y=m,
            mode="markers",
            name=family,
            legendgroup=family,
            marker={"size": 12, "color": color, "line": {"width": 1.5, "color": "white"}, "opacity": 0.82},
            customdata=np.column_stack([e_over_rho]),
            hovertemplate=(
                f"<b>{family}</b><br>"
                "Density: %{x:.0f} kg/m³<br>"
                "Modulus: %{y:.3g} GPa<br>"
                "E/ρ: %{customdata[0]:.3g} GPa·m³/Mg"
                "<extra></extra>"
            ),
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
        font={"size": 18, "color": "#333333", "family": "Arial, Helvetica, sans-serif"},
        bgcolor="rgba(255, 255, 255, 0.85)",
        borderpad=5,
        bordercolor="rgba(0, 0, 0, 0.08)",
        borderwidth=1,
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
                line={"color": "rgba(0, 0, 0, 0.18)", "width": 1.2, "dash": "dot"},
                showlegend=False,
                hoverinfo="skip",
            )
        )

# Guide line label
fig.add_annotation(
    x=np.log10(40),
    y=np.log10(40 * 1),
    xref="x",
    yref="y",
    text="<i>E/ρ = const</i>",
    showarrow=False,
    font={"size": 16, "color": "#666666", "family": "Arial, Helvetica, sans-serif"},
    bgcolor="rgba(255, 255, 255, 0.85)",
    borderpad=4,
    textangle=-38,
)

# Layout
fig.update_layout(
    title={
        "text": "scatter-ashby-material · plotly · pyplots.ai",
        "font": {"size": 28, "color": "#2B2B2B", "family": "Arial, Helvetica, sans-serif"},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.96,
    },
    xaxis={
        "title": {"text": "Density (kg/m³)", "font": {"size": 22, "color": "#444444"}},
        "tickfont": {"size": 18, "color": "#555555"},
        "type": "log",
        "showgrid": True,
        "gridcolor": "rgba(0, 0, 0, 0.04)",
        "gridwidth": 1,
        "showline": True,
        "linecolor": "#AAAAAA",
        "linewidth": 1,
        "mirror": False,
        "range": [np.log10(10), np.log10(20000)],
        "dtick": 1,
        "minor": {"showgrid": True, "gridcolor": "rgba(0, 0, 0, 0.02)"},
    },
    yaxis={
        "title": {"text": "Young's Modulus (GPa)", "font": {"size": 22, "color": "#444444"}},
        "tickfont": {"size": 18, "color": "#555555"},
        "type": "log",
        "showgrid": True,
        "gridcolor": "rgba(0, 0, 0, 0.04)",
        "gridwidth": 1,
        "showline": True,
        "linecolor": "#AAAAAA",
        "linewidth": 1,
        "mirror": False,
        "range": [np.log10(0.0005), np.log10(1000)],
        "minor": {"showgrid": True, "gridcolor": "rgba(0, 0, 0, 0.02)"},
    },
    template="plotly_white",
    plot_bgcolor="#F8F9FA",
    paper_bgcolor="#FFFFFF",
    legend={
        "title": {"text": "Material Family", "font": {"size": 18, "color": "#333333"}},
        "font": {"size": 16},
        "bgcolor": "rgba(255, 255, 255, 0.94)",
        "bordercolor": "rgba(0, 0, 0, 0.1)",
        "borderwidth": 1,
        "x": 0.98,
        "y": 0.02,
        "xanchor": "right",
        "yanchor": "bottom",
        "itemsizing": "constant",
    },
    width=1600,
    height=900,
    margin={"l": 80, "r": 60, "t": 100, "b": 80},
    font={"family": "Arial, Helvetica, sans-serif"},
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
