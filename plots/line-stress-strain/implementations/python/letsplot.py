""" anyplot.ai
line-stress-strain: Engineering Stress-Strain Curve
Library: letsplot 4.10.1 | Python 3.13.14
Quality: 86/100 | Updated: 2026-06-21
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave


LetsPlot.setup_html()  # noqa: F405

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette positions
BRAND = "#009E73"  # green — main stress-strain curve (first series)
COLOR_OFFSET = "#C475FD"  # lavender — 0.2% offset line
COLOR_YIELD = "#4467A3"  # blue — yield point
COLOR_UTS = "#AE3030"  # matte red — UTS (semantic: peak stress / failure onset)
COLOR_FRACTURE = "#BD8233"  # ochre — fracture point

# Theme-adaptive region background tints derived from Imprint palette
if THEME == "light":
    region_fill = {"Elastic": "#D6EEE6", "Strain Hardening": "#D6DDF0", "Necking": "#F0D6D6"}
else:
    region_fill = {"Elastic": "#172920", "Strain Hardening": "#171C2C", "Necking": "#2C1717"}

# Data — Mild steel tensile test simulation
np.random.seed(42)
youngs_modulus = 210000  # MPa
yield_strength = 250  # MPa
uts = 400  # MPa (ultimate tensile strength)
fracture_strain = 0.35
uts_strain = 0.22
yield_strain = yield_strength / youngs_modulus

# Elastic region (0 to yield)
strain_elastic = np.linspace(0, yield_strain, 60)
stress_elastic = youngs_modulus * strain_elastic

# Yield plateau (mild steel distinct yield point)
strain_plateau = np.linspace(yield_strain, 0.015, 20)
stress_plateau = yield_strength + np.random.normal(0, 1.5, 20)

# Strain hardening
strain_hardening = np.linspace(0.015, uts_strain, 120)
stress_hardening = yield_strength + (uts - yield_strength) * (
    1 - np.exp(-8 * (strain_hardening - 0.015) / (uts_strain - 0.015))
)
stress_hardening += np.random.normal(0, 1.0, 120)

# Necking (UTS to fracture)
strain_necking = np.linspace(uts_strain, fracture_strain, 60)
stress_necking = uts - (uts - 280) * ((strain_necking - uts_strain) / (fracture_strain - uts_strain)) ** 1.5
stress_necking += np.random.normal(0, 1.5, 60)

strain = np.concatenate([strain_elastic, strain_plateau, strain_hardening, strain_necking])
stress = np.concatenate([stress_elastic, stress_plateau, stress_hardening, stress_necking])
df = pd.DataFrame({"strain": strain, "stress": stress})

# 0.2% offset line for yield point determination
offset_val = 0.002
offset_strain = np.linspace(offset_val, offset_val + yield_strength / youngs_modulus + 0.003, 50)
offset_stress = np.clip(youngs_modulus * (offset_strain - offset_val), 0, yield_strength + 30)
df_offset = pd.DataFrame({"strain": offset_strain, "stress": offset_stress})

# Key points
yield_point_strain = offset_val + yield_strength / youngs_modulus
fracture_stress = stress_necking[-1]
df_points = pd.DataFrame(
    {
        "strain": [yield_point_strain, uts_strain, fracture_strain],
        "stress": [yield_strength, uts, fracture_stress],
        "type": ["Yield", "UTS", "Fracture"],
    }
)

# Annotation labels
df_annotations = pd.DataFrame(
    {
        "x": [yield_point_strain + 0.012, uts_strain + 0.015, fracture_strain - 0.045, 0.008, 0.007, 0.005, 0.11, 0.29],
        "y": [yield_strength + 15, uts + 10, fracture_stress - 30, 130, 60, 350, 350, 310],
        "label": [
            f"Yield Point\n({yield_strength} MPa)",
            f"UTS ({uts} MPa)",
            "Fracture",
            f"E = {youngs_modulus // 1000} GPa",
            "0.2% offset",
            "Elastic",
            "Strain\nHardening",
            "Necking",
        ],
        "group": ["yield", "uts", "fracture", "modulus", "offset", "region", "region", "region"],
    }
)

# Connector lines from key points to annotation labels
df_segments = pd.DataFrame(
    {
        "x": [yield_point_strain, uts_strain, fracture_strain],
        "y": [yield_strength, uts, fracture_stress],
        "xend": [yield_point_strain + 0.011, uts_strain + 0.014, fracture_strain - 0.035],
        "yend": [yield_strength + 12, uts + 8, fracture_stress - 22],
    }
)

# Region background rectangles
df_regions = pd.DataFrame(
    {
        "xmin": [0, 0.015, uts_strain],
        "xmax": [0.015, uts_strain, fracture_strain],
        "ymin": [0, 0, 0],
        "ymax": [460, 460, 460],
        "region": ["Elastic", "Strain Hardening", "Necking"],
    }
)

# Combined fill color mapping (regions + key points share the fill aesthetic)
fill_colors = {**region_fill, "Yield": COLOR_YIELD, "UTS": COLOR_UTS, "Fracture": COLOR_FRACTURE}

title = "line-stress-strain · python · letsplot · anyplot.ai"

# Plot
plot = (
    ggplot()
    + geom_rect(aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="region"), data=df_regions)
    + geom_line(
        aes(x="strain", y="stress"),
        data=df,
        color=BRAND,
        size=1.5,
        tooltips=layer_tooltips()
        .format("strain", ".4f")
        .format("stress", ".1f")
        .line("Strain: @strain")
        .line("Stress: @stress MPa"),
    )
    + geom_line(aes(x="strain", y="stress"), data=df_offset, color=COLOR_OFFSET, size=1.0, linetype="dashed")
    + geom_segment(
        aes(x="x", y="y", xend="xend", yend="yend"), data=df_segments, color=INK_SOFT, size=0.5, linetype="dotted"
    )
    + geom_point(
        aes(x="strain", y="stress", fill="type"),
        data=df_points,
        color=PAGE_BG,
        size=5,
        shape=21,
        stroke=1.5,
        tooltips=layer_tooltips().line("@type").line("Strain: @strain").line("Stress: @stress MPa"),
    )
    + scale_fill_manual(values=fill_colors)
    + guides(fill="none")
    + geom_text(
        aes(x="x", y="y", label="label"),
        data=df_annotations.query("group == 'yield'"),
        size=4,
        color=COLOR_YIELD,
        hjust=0,
    )
    + geom_text(
        aes(x="x", y="y", label="label"), data=df_annotations.query("group == 'uts'"), size=4, color=COLOR_UTS, hjust=0
    )
    + geom_text(
        aes(x="x", y="y", label="label"),
        data=df_annotations.query("group == 'fracture'"),
        size=4,
        color=COLOR_FRACTURE,
        hjust=0.5,
    )
    + geom_text(
        aes(x="x", y="y", label="label"),
        data=df_annotations.query("group == 'modulus'"),
        size=3.5,
        color=BRAND,
        hjust=0,
        fontface="italic",
    )
    + geom_text(
        aes(x="x", y="y", label="label"),
        data=df_annotations.query("group == 'offset'"),
        size=3.5,
        color=COLOR_OFFSET,
        hjust=0,
        fontface="italic",
    )
    + geom_text(
        aes(x="x", y="y", label="label"),
        data=df_annotations.query("group == 'region'"),
        size=4,
        color=INK_MUTED,
        fontface="italic",
    )
    + labs(x="Engineering Strain", y="Engineering Stress (MPa)", title=title)
    + scale_x_continuous(breaks=[0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35])
    + scale_y_continuous(breaks=[0, 50, 100, 150, 200, 250, 300, 350, 400, 450])
    + ggsize(800, 450)
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        plot_title=element_text(size=16, color=INK),
        panel_grid_major_x=element_blank(),
        panel_grid_major_y=element_line(color=INK_SOFT, size=0.2),
        panel_grid_minor=element_blank(),
        axis_line=element_line(color=INK_SOFT),
        axis_ticks=element_blank(),
        axis_ticks_length=0,
        plot_margin=[20, 30, 15, 15],
    )
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
