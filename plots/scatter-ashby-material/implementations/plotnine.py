"""pyplots.ai
scatter-ashby-material: Ashby Material Selection Chart
Library: plotnine | Python 3.13
Quality: pending | Created: 2026-03-11
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_point,
    geom_polygon,
    ggplot,
    guide_legend,
    guides,
    labs,
    scale_color_manual,
    scale_fill_manual,
    scale_x_log10,
    scale_y_log10,
    theme,
    theme_minimal,
)
from scipy.spatial import ConvexHull


# Data - Density (kg/m^3) vs Young's Modulus (GPa) for common engineering materials
np.random.seed(42)

families = {
    "Metals": {"density": (2700, 8900), "modulus": (45, 400), "n": 30, "center_d": 5500, "center_m": 120},
    "Ceramics": {"density": (2200, 4500), "modulus": (150, 450), "n": 20, "center_d": 3300, "center_m": 280},
    "Polymers": {"density": (900, 1500), "modulus": (0.2, 4.0), "n": 25, "center_d": 1200, "center_m": 1.5},
    "Composites": {"density": (1400, 2200), "modulus": (15, 200), "n": 20, "center_d": 1800, "center_m": 60},
    "Elastomers": {"density": (900, 1300), "modulus": (0.001, 0.1), "n": 18, "center_d": 1100, "center_m": 0.01},
    "Foams": {"density": (25, 300), "modulus": (0.001, 0.3), "n": 18, "center_d": 100, "center_m": 0.02},
}

materials = []
for family, props in families.items():
    log_d_min, log_d_max = np.log10(props["density"][0]), np.log10(props["density"][1])
    log_m_min, log_m_max = np.log10(props["modulus"][0]), np.log10(props["modulus"][1])
    density = 10 ** np.random.uniform(log_d_min, log_d_max, props["n"])
    modulus = 10 ** np.random.uniform(log_m_min, log_m_max, props["n"])
    for d, m in zip(density, modulus, strict=True):
        materials.append({"family": family, "density": d, "modulus": m})

df = pd.DataFrame(materials)

# Compute convex hull envelopes in log space with padding
hull_rows = []
label_rows = []
family_order = list(families.keys())

for family in family_order:
    subset = df[df["family"] == family]
    log_d = np.log10(subset["density"].values)
    log_m = np.log10(subset["modulus"].values)
    points = np.column_stack([log_d, log_m])

    if len(points) >= 3:
        hull = ConvexHull(points)
        hull_pts = points[hull.vertices]

        # Expand hull outward from centroid for padding
        centroid = hull_pts.mean(axis=0)
        expanded = centroid + 1.15 * (hull_pts - centroid)

        # Smooth the hull by interpolating more points along edges
        for i in range(len(expanded)):
            hull_rows.append({"family": family, "density": 10 ** expanded[i, 0], "modulus": 10 ** expanded[i, 1]})

        # Label position at centroid
        label_rows.append({"family": family, "density": 10 ** centroid[0], "modulus": 10 ** centroid[1]})

df_hulls = pd.DataFrame(hull_rows)
df_labels = pd.DataFrame(label_rows)

# Colors
palette = {
    "Metals": "#306998",
    "Ceramics": "#C75B39",
    "Polymers": "#4DAF4A",
    "Composites": "#FF7F00",
    "Elastomers": "#984EA3",
    "Foams": "#A6761D",
}

# Set categorical ordering
df["family"] = pd.Categorical(df["family"], categories=family_order, ordered=True)
df_hulls["family"] = pd.Categorical(df_hulls["family"], categories=family_order, ordered=True)
df_labels["family"] = pd.Categorical(df_labels["family"], categories=family_order, ordered=True)

# Plot
plot = (
    ggplot()
    + geom_polygon(df_hulls, aes(x="density", y="modulus", fill="family", group="family"), alpha=0.15, color="none")
    + geom_point(df, aes(x="density", y="modulus", color="family"), size=3.5, alpha=0.75, stroke=0.3)
    + scale_x_log10()
    + scale_y_log10()
    + scale_color_manual(values=palette, name="Material Family")
    + scale_fill_manual(values=palette)
    + labs(x="Density (kg/m³)", y="Young's Modulus (GPa)", title="scatter-ashby-material · plotnine · pyplots.ai")
    + guides(color=guide_legend(override_aes={"size": 5, "alpha": 1}), fill="none")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold", margin={"b": 15}),
        axis_title=element_text(size=20, margin={"t": 10, "r": 10}),
        axis_text=element_text(size=16, color="#333333"),
        legend_title=element_text(size=18, weight="bold"),
        legend_text=element_text(size=16),
        legend_position="right",
        legend_background=element_rect(fill="#FAFAFA", color="#E0E0E0", size=0.5),
        legend_key=element_rect(fill="white", color="none"),
        panel_grid_minor=element_blank(),
        panel_grid_major=element_line(color="#E0E0E0", size=0.4, alpha=0.3),
        panel_background=element_rect(fill="#FAFAFA", color="none"),
        plot_background=element_rect(fill="white", color="none"),
        plot_margin=0.04,
    )
)

# Add family labels at centroids
for _, row in df_labels.iterrows():
    plot = plot + annotate(
        "text",
        x=row["density"],
        y=row["modulus"],
        label=row["family"],
        size=11,
        fontweight="bold",
        color="#333333",
        alpha=0.7,
    )

# Save
plot.save("plot.png", dpi=300, verbose=False)
