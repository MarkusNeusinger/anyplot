"""pyplots.ai
scatter-ashby-material: Ashby Material Selection Chart
Library: letsplot | Python 3.13
Quality: pending | Created: 2026-03-11
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_text,
    geom_point,
    geom_polygon,
    geom_text,
    ggplot,
    ggsave,
    ggsize,
    guides,
    labs,
    layer_tooltips,
    scale_color_manual,
    scale_fill_manual,
    scale_x_log10,
    scale_y_log10,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Data - Density (kg/m^3) vs Young's modulus (GPa) for common engineering materials
np.random.seed(42)

families = {
    "Metals": {
        "density": [2700, 4500, 7800, 7900, 8900, 8400, 11340, 7200, 19300, 7300],
        "modulus": [69, 116, 200, 193, 117, 200, 16, 170, 79, 105],
        "names": [
            "Aluminum",
            "Titanium",
            "Steel",
            "Stainless Steel",
            "Copper",
            "Nickel Alloy",
            "Lead",
            "Cast Iron",
            "Gold",
            "Tin Alloy",
        ],
    },
    "Polymers": {
        "density": [950, 1400, 1200, 1050, 1300, 1150, 1420, 1780],
        "modulus": [0.9, 2.8, 3.5, 2.3, 3.0, 1.3, 3.3, 3.9],
        "names": ["Polyethylene", "PVC", "Nylon", "Polypropylene", "PET", "Polystyrene", "Acetal", "PEEK"],
    },
    "Ceramics": {
        "density": [3980, 3200, 2200, 5680, 2500, 3100, 6000, 3900],
        "modulus": [380, 310, 70, 210, 65, 270, 200, 350],
        "names": [
            "Alumina",
            "Silicon Nitride",
            "Glass",
            "Zirconia",
            "Porcelain",
            "Silicon Carbide",
            "Tungsten Carbide",
            "Sapphire",
        ],
    },
    "Composites": {
        "density": [1600, 2000, 1500, 1800, 1550, 1400, 1700, 1900],
        "modulus": [140, 45, 70, 25, 60, 30, 90, 50],
        "names": [
            "CFRP",
            "GFRP",
            "Aramid/Epoxy",
            "Sheet Molding",
            "Carbon/PEEK",
            "Flax/Epoxy",
            "Boron/Epoxy",
            "Glass/Vinyl Ester",
        ],
    },
    "Elastomers": {
        "density": [920, 1250, 1100, 1500, 1050, 1150, 1300],
        "modulus": [0.005, 0.01, 0.003, 0.02, 0.002, 0.008, 0.015],
        "names": ["Natural Rubber", "Neoprene", "Silicone", "Fluorocarbon", "Butyl Rubber", "EPDM", "Polyurethane"],
    },
    "Foams": {
        "density": [30, 60, 120, 200, 45, 100, 160],
        "modulus": [0.001, 0.01, 0.05, 0.2, 0.005, 0.03, 0.1],
        "names": [
            "Polyurethane Foam",
            "Polystyrene Foam",
            "PVC Foam",
            "Metallic Foam",
            "PE Foam",
            "Phenolic Foam",
            "Syntactic Foam",
        ],
    },
    "Natural Materials": {
        "density": [600, 700, 500, 1500, 1000, 800, 650],
        "modulus": [12, 14, 9, 30, 5, 10, 11],
        "names": ["Oak", "Maple", "Balsa", "Bone", "Cork", "Bamboo", "Pine"],
    },
}

# Build dataframe with scatter noise for visual spread
rows = []
for family, props in families.items():
    for d, m, name in zip(props["density"], props["modulus"], props["names"], strict=True):
        noise_d = np.exp(np.random.normal(0, 0.05))
        noise_m = np.exp(np.random.normal(0, 0.05))
        rows.append({"material": name, "family": family, "density": d * noise_d, "modulus": m * noise_m})

df = pd.DataFrame(rows)

# Compute elliptical envelopes for each material family (in log space)
envelope_rows = []
n_pts = 80
theta = np.linspace(0, 2 * np.pi, n_pts, endpoint=False)
for family in df["family"].unique():
    sub = df[df["family"] == family]
    log_x = np.log10(sub["density"].values)
    log_y = np.log10(sub["modulus"].values)
    cx, cy = log_x.mean(), log_y.mean()
    dx, dy = log_x - cx, log_y - cy
    cov = np.array([[np.mean(dx * dx), np.mean(dx * dy)], [np.mean(dx * dy), np.mean(dy * dy)]])
    eigvals, eigvecs = np.linalg.eigh(cov)
    scale = 2.6
    for t in theta:
        pt = eigvecs @ (np.sqrt(np.maximum(eigvals, 0.01)) * scale * np.array([np.cos(t), np.sin(t)]))
        envelope_rows.append({"family": family, "density": 10 ** (cx + pt[0]), "modulus": 10 ** (cy + pt[1])})

df_envelopes = pd.DataFrame(envelope_rows)

# Compute label positions (centroid of each family)
label_rows = []
for family in df["family"].unique():
    sub = df[df["family"] == family]
    cx = 10 ** np.log10(sub["density"]).mean()
    cy = 10 ** np.log10(sub["modulus"]).mean()
    label_rows.append({"family": family, "density": cx, "modulus": cy})

df_labels = pd.DataFrame(label_rows)

# Palette: colorblind-safe, distinct for 7 families
palette = ["#306998", "#E5883E", "#2A9D8F", "#8B5CF6", "#E63946", "#A8DADC", "#6D4C41"]

# Plot
plot = (
    ggplot()
    + geom_polygon(data=df_envelopes, mapping=aes(x="density", y="modulus", fill="family"), alpha=0.15)
    + geom_point(
        data=df,
        mapping=aes(x="density", y="modulus", color="family"),
        size=5,
        alpha=0.8,
        tooltips=layer_tooltips()
        .line("@material")
        .line("Family|@family")
        .line("Density|@{density} kg/m³")
        .line("Modulus|@{modulus} GPa"),
    )
    + geom_text(
        data=df_labels, mapping=aes(x="density", y="modulus", label="family"), size=12, color="#333333", fontface="bold"
    )
    + scale_x_log10(name="Density (kg/m³)")
    + scale_y_log10(name="Young's Modulus (GPa)")
    + scale_color_manual(values=palette, name="Material Family")
    + scale_fill_manual(values=palette)
    + guides(fill="none")
    + labs(title="scatter-ashby-material · letsplot · pyplots.ai")
    + theme_minimal()
    + theme(
        axis_title=element_text(size=20, margin=[10, 10, 10, 10]),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24, margin=[0, 0, 12, 0]),
        plot_margin=[30, 30, 20, 20],
        legend_title=element_text(size=16),
        legend_text=element_text(size=14),
        panel_grid_major=element_line(size=0.3, color="#E0E0E0"),
        panel_grid_minor=element_blank(),
        legend_position="right",
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
plot.to_html("plot.html")
