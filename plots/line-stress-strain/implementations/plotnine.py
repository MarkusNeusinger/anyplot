"""pyplots.ai
line-stress-strain: Engineering Stress-Strain Curve
Library: plotnine 0.15.3 | Python 3.14.3
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    coord_cartesian,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_line,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    labs,
    scale_color_identity,
    scale_fill_identity,
    scale_linetype_identity,
    scale_size_identity,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data - Mild steel stress-strain curve
np.random.seed(42)

youngs_modulus = 210000  # MPa
yield_stress = 250  # MPa
uts = 400  # MPa
fracture_strain = 0.35
necking_strain = 0.22

# Elastic region (0 to yield)
elastic_strain = np.linspace(0, yield_stress / youngs_modulus, 40)
elastic_stress = youngs_modulus * elastic_strain

# Yield plateau (short flat region for mild steel)
plateau_strain = np.linspace(elastic_strain[-1], 0.025, 15)
plateau_stress = np.full_like(plateau_strain, yield_stress)

# Strain hardening (power law)
hardening_strain = np.linspace(0.025, necking_strain, 80)
hardening_stress = yield_stress + (uts - yield_stress) * ((hardening_strain - 0.025) / (necking_strain - 0.025)) ** 0.45

# Necking to fracture (stress decreases)
necking_strain_vals = np.linspace(necking_strain, fracture_strain, 40)
necking_stress = (
    uts - (uts - 320) * ((necking_strain_vals - necking_strain) / (fracture_strain - necking_strain)) ** 1.3
)

# Combine all regions
strain = np.concatenate([elastic_strain, plateau_strain[1:], hardening_strain[1:], necking_strain_vals[1:]])
stress = np.concatenate([elastic_stress, plateau_stress[1:], hardening_stress[1:], necking_stress[1:]])

df = pd.DataFrame({"strain": strain, "stress": stress})

# 0.2% offset line data - extended for better visibility
offset = 0.002
offset_strain_start = offset
offset_strain_end = (yield_stress + 50) / youngs_modulus + offset

# Key points
yield_point_strain = yield_stress / youngs_modulus + offset
yield_point_stress = yield_stress
uts_strain = necking_strain
uts_stress = uts
fracture_strain_pt = fracture_strain
fracture_stress_pt = necking_stress[-1]

df_points = pd.DataFrame(
    {
        "strain": [yield_point_strain, uts_strain, fracture_strain_pt],
        "stress": [yield_point_stress, uts_stress, fracture_stress_pt],
        "label": ["Yield Point\n(0.2% offset)", "UTS", "Fracture"],
        "color": ["#C0392B", "#C0392B", "#C0392B"],
        "size": [6.0, 6.0, 6.0],
    }
)

# Region labels - repositioned for clarity
df_regions = pd.DataFrame(
    {
        "strain": [0.005, 0.015, 0.13, 0.29],
        "stress": [410, 215, 310, 370],
        "label": ["Elastic", "Yield\nPlateau", "Strain\nHardening", "Necking"],
        "color": ["#5D6D7E", "#5D6D7E", "#5D6D7E", "#5D6D7E"],
    }
)

# Region boundary strains for shading
elastic_end = yield_stress / youngs_modulus
plateau_end = 0.025

# Plot using plotnine grammar of graphics with layered composition
plot = (
    ggplot()
    # Region shading using annotate("rect") - plotnine-distinctive feature
    + annotate("rect", xmin=0, xmax=elastic_end, ymin=0, ymax=440, alpha=0.15, fill="#3498DB")
    + annotate("rect", xmin=elastic_end, xmax=plateau_end, ymin=0, ymax=440, alpha=0.15, fill="#2ECC71")
    + annotate("rect", xmin=plateau_end, xmax=necking_strain, ymin=0, ymax=440, alpha=0.12, fill="#F39C12")
    + annotate("rect", xmin=necking_strain, xmax=fracture_strain, ymin=0, ymax=440, alpha=0.12, fill="#E74C3C")
    # Main stress-strain curve
    + geom_line(df, aes(x="strain", y="stress"), color="#306998", size=2.8)
    # 0.2% offset line using geom_segment - plotnine-distinctive
    + geom_segment(
        aes(x=offset_strain_start, xend=offset_strain_end, y=0, yend=yield_stress + 50),
        color="#C0392B",
        size=1.2,
        linetype="dashed",
    )
    # Offset label near the line
    + annotate("text", x=0.012, y=60, label="0.2% offset", size=11, color="#C0392B", fontstyle="italic")
    # Key points with identity scales for direct aesthetic mapping
    + geom_point(df_points, aes(x="strain", y="stress", color="color", size="size"), fill="#C0392B")
    + scale_color_identity()
    + scale_size_identity()
    # Point labels - larger text
    + geom_text(
        df_points, aes(x="strain", y="stress", label="label"), nudge_y=32, size=15, color="#2C3E50", fontweight="bold"
    )
    # Region labels with identity color scale - larger text
    + geom_text(df_regions, aes(x="strain", y="stress", label="label", color="color"), size=14, fontstyle="italic")
    + scale_fill_identity()
    + scale_linetype_identity()
    # Modulus annotation - larger and repositioned
    + annotate(
        "text", x=0.03, y=140, label=f"E = {youngs_modulus // 1000} GPa", size=16, color="#306998", fontweight="bold"
    )
    + labs(x="Engineering Strain", y="Engineering Stress (MPa)", title="line-stress-strain · plotnine · pyplots.ai")
    + scale_x_continuous(breaks=np.arange(0, 0.40, 0.05))
    + scale_y_continuous(breaks=np.arange(0, 500, 50))
    # Coordinate control - plotnine-distinctive
    + coord_cartesian(xlim=(0, 0.38), ylim=(0, 460))
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=26, weight="bold", color="#1A2530"),
        axis_title=element_text(size=22, color="#2C3E50", weight="bold"),
        axis_text=element_text(size=16, color="#555555"),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color="#E8E8E8", size=0.4, alpha=0.5),
        plot_background=element_rect(fill="white", color="white"),
        panel_background=element_rect(fill="white", color="white"),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
