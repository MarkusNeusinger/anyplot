""" pyplots.ai
scatter-ashby-material: Ashby Material Selection Chart
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 85/100 | Created: 2026-03-11
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_abline,
    geom_point,
    geom_text,
    ggplot,
    guide_legend,
    guides,
    labs,
    scale_color_manual,
    scale_fill_manual,
    scale_x_log10,
    scale_y_log10,
    stat_ellipse,
    theme,
    theme_minimal,
)


# Data - Density (kg/m^3) vs Young's Modulus (GPa) for common engineering materials
np.random.seed(42)

families = {
    "Metals": {"density": (2700, 8900), "modulus": (45, 400), "n": 30},
    "Ceramics": {"density": (2200, 4500), "modulus": (150, 450), "n": 20},
    "Polymers": {"density": (900, 1500), "modulus": (0.2, 4.0), "n": 25},
    "Composites": {"density": (1400, 2200), "modulus": (15, 200), "n": 20},
    "Elastomers": {"density": (900, 1300), "modulus": (0.001, 0.1), "n": 18},
    "Foams": {"density": (25, 300), "modulus": (0.001, 0.3), "n": 18},
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

# Compute label positions from group centroids in log space
family_order = list(families.keys())
label_rows = []
for family in family_order:
    subset = df[df["family"] == family]
    log_d = np.log10(subset["density"].values)
    log_m = np.log10(subset["modulus"].values)
    centroid_d, centroid_m = log_d.mean(), log_m.mean()

    # Nudge labels away from crowded upper-right region
    nudge_x, nudge_y = 0, 0
    if family == "Ceramics":
        nudge_y = 0.35
        nudge_x = -0.15
    elif family == "Composites":
        nudge_y = -0.3
    elif family == "Metals":
        nudge_x = 0.2
    elif family == "Foams":
        nudge_x = -0.15
    label_rows.append(
        {"family": family, "density": 10 ** (centroid_d + nudge_x), "modulus": 10 ** (centroid_m + nudge_y)}
    )

df_labels = pd.DataFrame(label_rows)

# Colors - distinct hues with good colorblind separation
palette = {
    "Metals": "#306998",
    "Ceramics": "#C75B39",
    "Polymers": "#4DAF4A",
    "Composites": "#17BECF",
    "Elastomers": "#984EA3",
    "Foams": "#A6761D",
}

# Set categorical ordering
df["family"] = pd.Categorical(df["family"], categories=family_order, ordered=True)
df_labels["family"] = pd.Categorical(df_labels["family"], categories=family_order, ordered=True)

# Performance index guide lines: E/rho = constant (slope=1 in log-log space)
# log10(E) = log10(rho) + log10(C), so intercept = log10(C)
# Three lines for lightweight stiffness: E/rho = 0.01, 1, 100 GPa/(kg/m³)
guide_intercepts = [np.log10(c) for c in [0.001, 0.1, 10]]
guide_labels_data = pd.DataFrame(
    {
        "density": [15, 15, 15],
        "modulus": [15 * 0.001, 15 * 0.1, 15 * 10],
        "label": ["E/ρ = 0.001", "E/ρ = 0.1", "E/ρ = 10"],
    }
)

# Plot
plot = (
    ggplot(df, aes(x="density", y="modulus"))
    # Performance index guide lines (behind everything)
    + geom_abline(intercept=guide_intercepts[0], slope=1, linetype="dashed", color="#B0B0B0", size=0.5, alpha=0.6)
    + geom_abline(intercept=guide_intercepts[1], slope=1, linetype="dashed", color="#B0B0B0", size=0.5, alpha=0.6)
    + geom_abline(intercept=guide_intercepts[2], slope=1, linetype="dashed", color="#B0B0B0", size=0.5, alpha=0.6)
    # Guide line labels
    + geom_text(
        guide_labels_data,
        aes(x="density", y="modulus", label="label"),
        size=8,
        color="#999999",
        fontstyle="italic",
        ha="left",
        va="bottom",
        show_legend=False,
    )
    # Stat ellipse envelopes - plotnine-native alternative to scipy ConvexHull
    + stat_ellipse(
        aes(fill="family", group="family"),
        geom="polygon",
        level=0.90,
        alpha=0.12,
        color="#666666",
        size=0.3,
        linetype="solid",
    )
    # Scatter points
    + geom_point(aes(color="family"), size=4.5, alpha=0.8, stroke=0.3)
    + scale_x_log10()
    + scale_y_log10()
    + scale_color_manual(values=palette, name="Material Family")
    + scale_fill_manual(values=palette)
    + labs(
        x="Density (kg/m³)",
        y="Young's Modulus (GPa)",
        title="scatter-ashby-material · plotnine · pyplots.ai",
        subtitle="Density vs. stiffness with E/ρ performance index lines",
    )
    # Family labels
    + geom_text(
        df_labels,
        aes(x="density", y="modulus", label="family"),
        size=15,
        fontweight="bold",
        color="#2A2A2A",
        alpha=0.85,
        show_legend=False,
    )
    + guides(color=guide_legend(override_aes={"size": 5, "alpha": 1}), fill="none")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold", margin={"b": 5}),
        plot_subtitle=element_text(size=16, color="#666666", margin={"b": 15}),
        axis_title=element_text(size=20, margin={"t": 10, "r": 10}),
        axis_text=element_text(size=16, color="#333333"),
        legend_title=element_text(size=18, weight="bold"),
        legend_text=element_text(size=16),
        legend_position="right",
        legend_background=element_rect(fill="#FAFAFA", color="#E0E0E0", size=0.5),
        legend_key=element_rect(fill="white", color="none"),
        panel_grid_minor=element_blank(),
        panel_grid_major=element_line(color="#DCDCDC", size=0.3, alpha=0.4),
        panel_background=element_rect(fill="#F8F9FA", color="none"),
        panel_border=element_blank(),
        axis_line=element_line(color="#999999", size=0.4),
        plot_background=element_rect(fill="white", color="none"),
        plot_margin=0.04,
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
