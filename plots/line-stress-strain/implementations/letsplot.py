""" pyplots.ai
line-stress-strain: Engineering Stress-Strain Curve
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 92/100 | Created: 2026-03-20
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Data - Mild steel tensile test simulation
np.random.seed(42)

# Material properties for mild steel
youngs_modulus = 210000  # MPa
yield_strength = 250  # MPa
uts = 400  # MPa (ultimate tensile strength)
fracture_strain = 0.35
uts_strain = 0.22
yield_strain = yield_strength / youngs_modulus  # ~0.00119

# Elastic region (0 to yield)
n_elastic = 60
strain_elastic = np.linspace(0, yield_strain, n_elastic)
stress_elastic = youngs_modulus * strain_elastic

# Yield plateau (mild steel has a distinct yield point)
n_plateau = 20
strain_plateau = np.linspace(yield_strain, 0.015, n_plateau)
stress_plateau = yield_strength + np.random.normal(0, 1.5, n_plateau)

# Strain hardening region (from end of plateau to UTS)
n_hardening = 120
strain_hardening = np.linspace(0.015, uts_strain, n_hardening)
stress_hardening = yield_strength + (uts - yield_strength) * (
    1 - np.exp(-8 * (strain_hardening - 0.015) / (uts_strain - 0.015))
)
stress_hardening += np.random.normal(0, 1.0, n_hardening)

# Necking region (UTS to fracture)
n_necking = 60
strain_necking = np.linspace(uts_strain, fracture_strain, n_necking)
stress_necking = uts - (uts - 280) * ((strain_necking - uts_strain) / (fracture_strain - uts_strain)) ** 1.5
stress_necking += np.random.normal(0, 1.5, n_necking)

# Combine all regions
strain = np.concatenate([strain_elastic, strain_plateau, strain_hardening, strain_necking])
stress = np.concatenate([stress_elastic, stress_plateau, stress_hardening, stress_necking])

df = pd.DataFrame({"strain": strain, "stress": stress})

# 0.2% offset line for yield point determination
offset_val = 0.002
offset_line_strain = np.linspace(offset_val, offset_val + yield_strength / youngs_modulus + 0.003, 50)
offset_line_stress = youngs_modulus * (offset_line_strain - offset_val)
offset_line_stress = np.clip(offset_line_stress, 0, yield_strength + 30)
df_offset = pd.DataFrame({"strain": offset_line_strain, "stress": offset_line_stress})

# Key points
yield_point_strain = offset_val + yield_strength / youngs_modulus
yield_point_stress = yield_strength
fracture_stress = stress_necking[-1]

df_points = pd.DataFrame(
    {
        "strain": [yield_point_strain, uts_strain, fracture_strain],
        "stress": [yield_point_stress, uts, fracture_stress],
        "label": [f"Yield Point ({yield_strength} MPa)", f"UTS ({uts} MPa)", f"Fracture ({fracture_stress:.0f} MPa)"],
        "type": ["Yield", "UTS", "Fracture"],
    }
)

# Consolidated annotations DataFrame
df_annotations = pd.DataFrame(
    {
        "x": [yield_point_strain + 0.012, uts_strain + 0.015, fracture_strain - 0.045, 0.008, 0.007, 0.005, 0.11, 0.29],
        "y": [yield_point_stress + 15, uts + 10, fracture_stress - 30, 130, 60, 350, 350, 350],
        "label": [
            f"Yield Point\n({yield_strength} MPa)",
            f"UTS ({uts} MPa)",
            "Fracture",
            f"E = {youngs_modulus // 1000} GPa",
            "0.2% offset",
            "Elastic",
            "Strain Hardening",
            "Necking",
        ],
        "group": ["yield", "uts", "fracture", "modulus", "offset", "region", "region", "region"],
    }
)

# Colorblind-safe palette: blue, purple, gray (avoids orange/green pair)
color_yield = "#9467BD"  # purple
color_uts = "#D62728"  # red
color_fracture = "#7F7F7F"  # gray
color_main = "#306998"  # Python blue
color_offset = "#E377C2"  # pink

# Segment connector lines from key points to annotations (distinctive lets-plot feature)
df_segments = pd.DataFrame(
    {
        "x": [yield_point_strain, uts_strain, fracture_strain],
        "y": [yield_point_stress, uts, fracture_stress],
        "xend": [yield_point_strain + 0.011, uts_strain + 0.014, fracture_strain - 0.035],
        "yend": [yield_point_stress + 12, uts + 8, fracture_stress - 22],
    }
)

# Plot
plot = (
    ggplot()
    # Region background bands using geom_rect (distinctive lets-plot feature)
    + geom_rect(
        aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="region"),
        data=pd.DataFrame(
            {
                "xmin": [0, 0.015, uts_strain],
                "xmax": [0.015, uts_strain, fracture_strain],
                "ymin": [0, 0, 0],
                "ymax": [460, 460, 460],
                "region": ["Elastic", "Strain Hardening", "Necking"],
            }
        ),
        alpha=0.35,
    )
    + scale_fill_manual(
        values={
            "Elastic": "#DAE8FC",
            "Strain Hardening": "#FFF2CC",
            "Necking": "#F8D7DA",
            "Yield": color_yield,
            "UTS": color_uts,
            "Fracture": color_fracture,
        }
    )
    # Main stress-strain curve with tooltips (distinctive lets-plot feature)
    + geom_line(
        aes(x="strain", y="stress"),
        data=df,
        color=color_main,
        size=2.0,
        tooltips=layer_tooltips()
        .format("strain", ".4f")
        .format("stress", ".1f")
        .line("Strain: @strain")
        .line("Stress: @stress MPa"),
    )
    # 0.2% offset line
    + geom_line(aes(x="strain", y="stress"), data=df_offset, color=color_offset, size=1.2, linetype="dashed")
    # Segment connectors from points to labels (geom_segment - distinctive feature)
    + geom_segment(
        aes(x="x", y="y", xend="xend", yend="yend"), data=df_segments, color="#999999", size=0.6, linetype="dotted"
    )
    # Key points with tooltips (distinctive lets-plot feature)
    + geom_point(
        aes(x="strain", y="stress", fill="type"),
        data=df_points,
        color="white",
        size=7,
        shape=21,
        stroke=1.2,
        tooltips=layer_tooltips().line("@type").line("Strain: @strain").line("Stress: @stress MPa"),
    )
    + guides(fill="none")
    # Annotations - key points
    + geom_text(
        aes(x="x", y="y", label="label"),
        data=df_annotations.query("group == 'yield'"),
        size=11,
        color=color_yield,
        hjust=0,
    )
    + geom_text(
        aes(x="x", y="y", label="label"), data=df_annotations.query("group == 'uts'"), size=11, color=color_uts, hjust=0
    )
    + geom_text(
        aes(x="x", y="y", label="label"),
        data=df_annotations.query("group == 'fracture'"),
        size=11,
        color=color_fracture,
        hjust=0.5,
    )
    # Elastic modulus annotation
    + geom_text(
        aes(x="x", y="y", label="label"),
        data=df_annotations.query("group == 'modulus'"),
        size=10,
        color=color_main,
        hjust=0,
        fontface="italic",
    )
    # Offset label
    + geom_text(
        aes(x="x", y="y", label="label"),
        data=df_annotations.query("group == 'offset'"),
        size=9,
        color=color_offset,
        hjust=0,
        fontface="italic",
    )
    # Region labels
    + geom_text(
        aes(x="x", y="y", label="label"),
        data=df_annotations.query("group == 'region'"),
        size=12,
        color="#666666",
        fontface="italic",
    )
    # Styling
    + labs(
        x="Engineering Strain",
        y="Engineering Stress (MPa)",
        title="line-stress-strain \u00b7 letsplot \u00b7 pyplots.ai",
    )
    + scale_x_continuous(breaks=[0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35])
    + scale_y_continuous(breaks=[0, 50, 100, 150, 200, 250, 300, 350, 400, 450])
    + ggsize(1600, 900)
    + theme_minimal()
    + theme(
        axis_text=element_text(size=16, color="#555555"),
        axis_title=element_text(size=20, color="#333333"),
        plot_title=element_text(size=24, color="#222222", face="bold"),
        panel_grid_major_x=element_blank(),
        panel_grid_major_y=element_line(color="#E0E0E0", size=0.3),
        panel_grid_minor=element_blank(),
        plot_background=element_rect(fill="#FAFAFA", color="#FAFAFA"),
        panel_background=element_rect(fill="transparent", color="transparent"),
        axis_ticks=element_blank(),
        axis_ticks_length=0,
        plot_margin=[30, 40, 20, 20],
    )
)

# Save
export_ggsave(plot, filename="plot.png", path=".", scale=3)
export_ggsave(plot, filename="plot.html", path=".")
