""" pyplots.ai
scatter-ashby-material: Ashby Material Selection Chart
Library: letsplot 4.8.2 | Python 3.14.3
Quality: 86/100 | Created: 2026-03-11
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_abline,
    geom_point,
    geom_polygon,
    geom_segment,
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
# Per-family envelope scale: tighter for Foams to avoid extending into empty space
envelope_scales = {"Foams": 1.8, "Elastomers": 2.2}
default_scale = 2.4
for family in df["family"].unique():
    sub = df[df["family"] == family]
    log_x = np.log10(sub["density"].values)
    log_y = np.log10(sub["modulus"].values)
    cx, cy = log_x.mean(), log_y.mean()
    dx, dy = log_x - cx, log_y - cy
    cov = np.array([[np.mean(dx * dx), np.mean(dx * dy)], [np.mean(dx * dy), np.mean(dy * dy)]])
    eigvals, eigvecs = np.linalg.eigh(cov)
    scale = envelope_scales.get(family, default_scale)
    for t in theta:
        pt = eigvecs @ (np.sqrt(np.maximum(eigvals, 0.01)) * scale * np.array([np.cos(t), np.sin(t)]))
        envelope_rows.append({"family": family, "density": 10 ** (cx + pt[0]), "modulus": 10 ** (cy + pt[1])})

df_envelopes = pd.DataFrame(envelope_rows)

# Compute label positions with manual offsets to separate crowded center labels
label_offsets = {
    "Metals": (0.15, 0.2),
    "Ceramics": (-0.25, 0.3),
    "Composites": (0.25, 0.35),
    "Polymers": (0.3, -0.25),
    "Elastomers": (0.0, -0.15),
    "Foams": (-0.15, 0.15),
    "Natural Materials": (-0.35, -0.15),
}
label_rows = []
for family in df["family"].unique():
    sub = df[df["family"] == family]
    log_cx = np.log10(sub["density"]).mean()
    log_cy = np.log10(sub["modulus"]).mean()
    off_x, off_y = label_offsets.get(family, (0, 0))
    cx = 10 ** (log_cx + off_x)
    cy = 10 ** (log_cy + off_y)
    label_rows.append({"family": family, "density": cx, "modulus": cy})

df_labels = pd.DataFrame(label_rows)

# Leader lines connecting labels to envelope centers for displaced labels
leader_rows = []
for family in df["family"].unique():
    sub = df[df["family"] == family]
    log_cx = np.log10(sub["density"]).mean()
    log_cy = np.log10(sub["modulus"]).mean()
    off_x, off_y = label_offsets.get(family, (0, 0))
    if abs(off_x) > 0.2 or abs(off_y) > 0.2:
        leader_rows.append(
            {"x": 10**log_cx, "y": 10**log_cy, "xend": 10 ** (log_cx + off_x), "yend": 10 ** (log_cy + off_y)}
        )

df_leaders = pd.DataFrame(leader_rows)

# Palette: colorblind-safe with high distinction
# Metals=dark blue, Polymers=warm orange, Ceramics=teal, Composites=magenta,
# Elastomers=crimson, Foams=sky blue, Natural=brown
palette = ["#1B4F72", "#E5883E", "#2A9D8F", "#C850C0", "#E63946", "#5DADE2", "#795548"]

# Plot
plot = (
    ggplot()
    # Performance index guide lines (E/rho = constant, slope=1 on log-log)
    + geom_abline(intercept=np.log10(0.001), slope=1, color="#D0D0D0", size=0.5, linetype="dashed")
    + geom_abline(intercept=np.log10(0.01), slope=1, color="#D0D0D0", size=0.5, linetype="dashed")
    + geom_abline(intercept=np.log10(0.1), slope=1, color="#D0D0D0", size=0.5, linetype="dashed")
    # Guide line labels positioned within visible area
    + geom_text(
        data=pd.DataFrame(
            {
                "density": [35, 35, 35],
                "modulus": [0.035, 0.35, 3.5],
                "label": ["E/\u03c1 = 10\u207b\u00b3", "E/\u03c1 = 10\u207b\u00b2", "E/\u03c1 = 10\u207b\u00b9"],
            }
        ),
        mapping=aes(x="density", y="modulus", label="label"),
        size=8,
        color="#AAAAAA",
        angle=38,
        hjust=0,
    )
    # Elliptical envelopes
    + geom_polygon(data=df_envelopes, mapping=aes(x="density", y="modulus", fill="family"), alpha=0.22)
    # Data points with interactive tooltips
    + geom_point(
        data=df,
        mapping=aes(x="density", y="modulus", color="family"),
        size=7,
        alpha=0.88,
        shape=16,
        tooltips=layer_tooltips()
        .format("density", ".0f")
        .format("modulus", ".3g")
        .line("@material")
        .line("Family|@family")
        .line("Density|@{density} kg/m\u00b3")
        .line("Modulus|@{modulus} GPa"),
    )
    # Leader lines from envelope center to displaced labels
    + geom_segment(
        data=df_leaders,
        mapping=aes(x="x", y="y", xend="xend", yend="yend"),
        color="#999999",
        size=0.4,
        linetype="dotted",
    )
    # Family labels
    + geom_text(
        data=df_labels,
        mapping=aes(x="density", y="modulus", label="family"),
        size=12,
        color="#1A1A1A",
        fontface="bold",
        label_padding=0.3,
    )
    + scale_x_log10(name="Density (kg/m\u00b3)")
    + scale_y_log10(name="Young\u2019s Modulus (GPa)")
    + scale_color_manual(values=palette, name="Material Family")
    + scale_fill_manual(values=palette)
    + guides(fill="none")
    + labs(title="scatter-ashby-material \u00b7 letsplot \u00b7 pyplots.ai")
    + theme_minimal()
    + theme(
        axis_title=element_text(size=20, color="#333333", margin=[10, 10, 10, 10]),
        axis_text=element_text(size=16, color="#555555"),
        plot_title=element_text(size=24, face="bold", color="#1A1A1A", margin=[0, 0, 14, 0]),
        plot_margin=[30, 40, 20, 20],
        plot_background=element_rect(fill="#F7F7F7", color="#F7F7F7"),
        panel_background=element_rect(fill="#FFFFFF", color="#E8E8E8", size=0.5),
        legend_title=element_text(size=16, face="bold"),
        legend_text=element_text(size=14),
        panel_grid_major=element_line(size=0.25, color="#ECECEC"),
        panel_grid_minor=element_blank(),
        legend_position="right",
        legend_background=element_rect(fill="#F7F7F7", color="#F7F7F7"),
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
plot.to_html("plot.html")
