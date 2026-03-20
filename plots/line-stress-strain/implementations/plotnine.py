"""pyplots.ai
line-stress-strain: Engineering Stress-Strain Curve
Library: plotnine | Python 3.13
Quality: pending | Created: 2026-03-20
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_blank,
    element_line,
    element_text,
    geom_line,
    geom_point,
    geom_text,
    ggplot,
    labs,
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
plateau_strain = np.linspace(elastic_strain[-1], 0.02, 15)
plateau_stress = np.full_like(plateau_strain, yield_stress)

# Strain hardening (power law)
hardening_strain = np.linspace(0.02, necking_strain, 80)
hardening_stress = yield_stress + (uts - yield_stress) * ((hardening_strain - 0.02) / (necking_strain - 0.02)) ** 0.45

# Necking to fracture (stress decreases)
necking_strain_vals = np.linspace(necking_strain, fracture_strain, 40)
necking_stress = (
    uts - (uts - 320) * ((necking_strain_vals - necking_strain) / (fracture_strain - necking_strain)) ** 1.3
)

# Combine all regions
strain = np.concatenate([elastic_strain, plateau_strain[1:], hardening_strain[1:], necking_strain_vals[1:]])
stress = np.concatenate([elastic_stress, plateau_stress[1:], hardening_stress[1:], necking_stress[1:]])

df = pd.DataFrame({"strain": strain, "stress": stress})

# 0.2% offset line
offset = 0.002
offset_strain_max = (yield_stress + 30) / youngs_modulus + offset
offset_line_strain = np.linspace(offset, offset_strain_max, 50)
offset_line_stress = youngs_modulus * (offset_line_strain - offset)
offset_line_stress = np.clip(offset_line_stress, 0, yield_stress + 30)
df_offset = pd.DataFrame({"strain": offset_line_strain, "stress": offset_line_stress})

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
    }
)

# Region labels
df_regions = pd.DataFrame(
    {
        "strain": [0.008, 0.06, 0.12, 0.29],
        "stress": [140, 140, 310, 280],
        "label": ["Elastic", "Yield\nPlateau", "Strain\nHardening", "Necking"],
    }
)

# Elastic modulus annotation
modulus_mid_strain = elastic_strain[20]
modulus_mid_stress = elastic_stress[20]

# Plot
plot = (
    ggplot()
    + geom_line(df, aes(x="strain", y="stress"), color="#306998", size=2.5)
    + geom_line(df_offset, aes(x="strain", y="stress"), color="#E74C3C", size=1, linetype="dashed")
    + geom_point(df_points, aes(x="strain", y="stress"), color="#E74C3C", size=5, fill="#E74C3C")
    + geom_text(
        df_points, aes(x="strain", y="stress", label="label"), nudge_y=30, size=11, color="#333333", fontstyle="italic"
    )
    + geom_text(df_regions, aes(x="strain", y="stress", label="label"), size=10, color="#888888", fontstyle="italic")
    + annotate(
        "text", x=0.008, y=320, label=f"E = {youngs_modulus // 1000} GPa", size=11, color="#306998", fontweight="bold"
    )
    + labs(x="Engineering Strain", y="Engineering Stress (MPa)", title="line-stress-strain · plotnine · pyplots.ai")
    + scale_x_continuous(breaks=np.arange(0, 0.40, 0.05))
    + scale_y_continuous(breaks=np.arange(0, 500, 50))
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color="#E0E0E0", size=0.5, alpha=0.4),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
