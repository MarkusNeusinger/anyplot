"""
line-stress-strain: Engineering Stress-Strain Curve
Library: plotnine | Language: python
"""

import os
import sys

import numpy as np
import pandas as pd


# Work around naming conflict between plotnine.py script and plotnine package
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir in sys.path:
    sys.path.remove(script_dir)
if "" in sys.path:
    sys.path.remove("")
if "." in sys.path:
    sys.path.remove(".")

from plotnine import (  # noqa: E402
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
    scale_size_identity,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
REGION_ALPHA = 0.18 if THEME == "light" else 0.28

# Imprint palette — position 1 is always the first categorical series
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

np.random.seed(42)

youngs_modulus = 210000  # MPa
yield_stress = 250  # MPa
uts = 400  # MPa
fracture_strain = 0.35
necking_strain = 0.22

# Elastic region
elastic_strain = np.linspace(0, yield_stress / youngs_modulus, 40)
elastic_stress = youngs_modulus * elastic_strain

# Yield plateau (part of the plastic region — not a separate band per spec)
plateau_strain = np.linspace(elastic_strain[-1], 0.025, 15)
plateau_stress = np.full_like(plateau_strain, yield_stress)

# Strain hardening (power law)
hardening_strain = np.linspace(0.025, necking_strain, 80)
hardening_stress = yield_stress + (uts - yield_stress) * ((hardening_strain - 0.025) / (necking_strain - 0.025)) ** 0.45

# Necking to fracture
necking_strain_vals = np.linspace(necking_strain, fracture_strain, 40)
necking_stress = (
    uts - (uts - 320) * ((necking_strain_vals - necking_strain) / (fracture_strain - necking_strain)) ** 1.3
)

strain = np.concatenate([elastic_strain, plateau_strain[1:], hardening_strain[1:], necking_strain_vals[1:]])
stress = np.concatenate([elastic_stress, plateau_stress[1:], hardening_stress[1:], necking_stress[1:]])
df = pd.DataFrame({"strain": strain, "stress": stress})

# 0.2% offset line
offset = 0.002
elastic_end = yield_stress / youngs_modulus  # ~0.00119
offset_strain_end = (yield_stress + 50) / youngs_modulus + offset

# Critical points
yield_point_strain = elastic_end + offset
yield_point_stress = yield_stress
fracture_stress_pt = float(necking_stress[-1])

df_points = pd.DataFrame(
    {
        "strain": [yield_point_strain, necking_strain, fracture_strain],
        "stress": [yield_point_stress, uts, fracture_stress_pt],
        "color": [IMPRINT[4]] * 3,
        "size": [3.0, 3.0, 3.0],
    }
)

# Region labels: 3 regions per spec (elastic, strain hardening, necking)
# Yield plateau is a critical point, not a separate shaded band
df_regions = pd.DataFrame(
    {"strain": [0.003, 0.13, 0.29], "stress": [430, 335, 385], "label": ["Elastic", "Strain\nHardening", "Necking"]}
)

plot = (
    ggplot()
    # Three region shadings: elastic, plastic (strain hardening), necking
    + annotate("rect", xmin=0, xmax=elastic_end, ymin=0, ymax=460, alpha=REGION_ALPHA, fill=IMPRINT[2])
    + annotate("rect", xmin=elastic_end, xmax=necking_strain, ymin=0, ymax=460, alpha=REGION_ALPHA, fill=IMPRINT[3])
    + annotate("rect", xmin=necking_strain, xmax=fracture_strain, ymin=0, ymax=460, alpha=REGION_ALPHA, fill=IMPRINT[4])
    # Main stress-strain curve (Imprint position 1 — first categorical series)
    + geom_line(df, aes(x="strain", y="stress"), color=IMPRINT[0], size=1.0)
    # 0.2% offset construction line
    + geom_segment(
        aes(x=offset, xend=offset_strain_end, y=0, yend=yield_stress + 50),
        color=IMPRINT[4],
        size=0.6,
        linetype="dashed",
    )
    + annotate("text", x=0.011, y=52, label="0.2% offset", size=3.0, color=IMPRINT[4], fontstyle="italic")
    # Critical point markers
    + geom_point(df_points, aes(x="strain", y="stress", color="color", size="size"))
    + scale_color_identity()
    + scale_size_identity()
    # Critical point labels — individual positions for clarity near y-axis
    + annotate(
        "text",
        x=yield_point_strain + 0.018,
        y=yield_point_stress + 22,
        label="Yield Point\n(0.2% offset)",
        size=3.0,
        color=INK,
        fontweight="bold",
    )
    + annotate("text", x=necking_strain, y=uts + 28, label="UTS", size=3.0, color=INK, fontweight="bold")
    + annotate(
        "text",
        x=fracture_strain - 0.012,
        y=fracture_stress_pt + 28,
        label="Fracture",
        size=3.0,
        color=INK,
        fontweight="bold",
    )
    # Region labels
    + geom_text(df_regions, aes(x="strain", y="stress", label="label"), size=3.0, color=INK_SOFT, fontstyle="italic")
    # Elastic modulus annotation
    + annotate(
        "text", x=0.028, y=145, label=f"E = {youngs_modulus // 1000} GPa", size=3.5, color=IMPRINT[2], fontweight="bold"
    )
    + labs(x="Engineering Strain", y="Engineering Stress (MPa)", title="line-stress-strain · plotnine · pyplots.ai")
    + scale_x_continuous(breaks=np.arange(0, 0.40, 0.05))
    + scale_y_continuous(breaks=np.arange(0, 500, 50))
    + coord_cartesian(xlim=(0, 0.38), ylim=(0, 460))
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        text=element_text(size=7),
        plot_title=element_text(size=12, weight="bold", color=INK),
        axis_title=element_text(size=10, color=INK, weight="bold"),
        axis_text=element_text(size=8, color=INK_SOFT),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.15),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_border=element_rect(color=INK_SOFT, fill=None),
        axis_line=element_line(color=INK_SOFT),
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
