""" pyplots.ai
line-reaction-coordinate: Reaction Coordinate Energy Diagram
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-21
"""

import sys


sys.path = [p for p in sys.path if not p.endswith("implementations")]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from plotnine import (  # noqa: E402
    aes,
    annotate,
    arrow,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_line,
    geom_point,
    geom_segment,
    ggplot,
    labs,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from scipy.interpolate import CubicSpline  # noqa: E402


# Data — single-step exothermic reaction
reactant_energy = 50.0
transition_energy = 120.0
product_energy = 20.0

control_x = np.array([0.0, 0.10, 0.20, 0.35, 0.50, 0.65, 0.80, 0.90, 1.0])
control_y = np.array([50.0, 50.0, 55.0, 90.0, 120.0, 85.0, 30.0, 20.0, 20.0])

cs = CubicSpline(control_x, control_y)
reaction_coord = np.linspace(0, 1, 300)
energy = cs(reaction_coord)

curve_df = pd.DataFrame({"reaction_coord": reaction_coord, "energy": energy})

# Key points for markers at reactant, transition state, product
key_points = pd.DataFrame(
    {"reaction_coord": [0.0, 0.50, 1.0], "energy": [reactant_energy, transition_energy, product_energy]}
)

# Arrow positions — both within data range for balanced layout
ea_x = 0.08  # Ea arrow on far left, clear of curve
dh_x = 0.88  # ΔH arrow on right side, within data range

# Colorblind-safe colors (blue/orange instead of red/green)
ea_color = "#D55E00"  # Vermillion (colorblind-safe)
dh_color = "#0072B2"  # Blue (colorblind-safe)

# Horizontal dashed reference lines connecting reactant/product levels to ΔH arrow
hline_df = pd.DataFrame(
    {
        "x": [0.0, 0.75],
        "xend": [dh_x + 0.02, dh_x + 0.02],
        "y": [reactant_energy, product_energy],
        "yend": [reactant_energy, product_energy],
    }
)

# Arrow style
arrow_head = arrow(length=0.12, type="closed")

plot = (
    ggplot(curve_df, aes(x="reaction_coord", y="energy"))
    # Dashed reference lines at reactant and product energy levels
    + geom_segment(
        hline_df,
        aes(x="x", y="y", xend="xend", yend="yend"),
        linetype="dashed",
        color="#B0B0B0",
        size=0.5,
        inherit_aes=False,
    )
    # Main energy curve
    + geom_line(color="#306998", size=2.5)
    # Key point markers at reactant, transition state, product
    + geom_point(
        key_points, aes(x="reaction_coord", y="energy"), color="#306998", fill="#306998", size=5, inherit_aes=False
    )
    # Ea double-headed arrow (reactant level → transition state)
    + annotate(
        "segment",
        x=ea_x,
        xend=ea_x,
        y=reactant_energy + 3,
        yend=transition_energy - 3,
        color=ea_color,
        size=0.8,
        arrow=arrow_head,
    )
    + annotate(
        "segment",
        x=ea_x,
        xend=ea_x,
        y=transition_energy - 3,
        yend=reactant_energy + 3,
        color=ea_color,
        size=0.8,
        arrow=arrow_head,
    )
    # Ea label
    + annotate(
        "text",
        x=ea_x + 0.04,
        y=(reactant_energy + transition_energy) / 2,
        label="Eₐ = 70 kJ/mol",
        size=14,
        color=ea_color,
        ha="left",
        fontweight="bold",
    )
    # ΔH double-headed arrow (reactant level → product level)
    + annotate(
        "segment",
        x=dh_x,
        xend=dh_x,
        y=reactant_energy - 2,
        yend=product_energy + 2,
        color=dh_color,
        size=0.8,
        arrow=arrow_head,
    )
    + annotate(
        "segment",
        x=dh_x,
        xend=dh_x,
        y=product_energy + 2,
        yend=reactant_energy - 2,
        color=dh_color,
        size=0.8,
        arrow=arrow_head,
    )
    # ΔH label
    + annotate(
        "text",
        x=dh_x + 0.03,
        y=(reactant_energy + product_energy) / 2,
        label="ΔH = −30\nkJ/mol",
        size=14,
        color=dh_color,
        ha="left",
        fontweight="bold",
    )
    # Reactants label
    + annotate(
        "text",
        x=0.02,
        y=reactant_energy + 6,
        label="Reactants\n50 kJ/mol",
        size=14,
        color="#1A3A5C",
        ha="left",
        va="bottom",
        fontweight="bold",
    )
    # Transition state label
    + annotate(
        "text",
        x=0.50,
        y=transition_energy + 6,
        label="Transition State\n120 kJ/mol",
        size=14,
        color="#1A3A5C",
        ha="center",
        va="bottom",
        fontweight="bold",
    )
    # Products label
    + annotate(
        "text",
        x=0.98,
        y=product_energy - 6,
        label="Products\n20 kJ/mol",
        size=14,
        color="#1A3A5C",
        ha="right",
        va="top",
        fontweight="bold",
    )
    # Axes and title
    + labs(
        title="line-reaction-coordinate · plotnine · pyplots.ai", x="Reaction Coordinate", y="Potential Energy (kJ/mol)"
    )
    + scale_x_continuous(breaks=[0, 0.25, 0.5, 0.75, 1.0], labels=["0", "", "0.5", "", "1.0"], expand=(0.02, 0.08))
    + scale_y_continuous(limits=[0, 145], expand=(0.02, 0.02))
    # Style — leveraging plotnine's theme system
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, ha="center", weight="bold", color="#1A3A5C", margin={"b": 15}),
        axis_title_x=element_text(size=20, color="#333333", margin={"t": 10}),
        axis_title_y=element_text(size=20, color="#333333", margin={"r": 10}),
        axis_text=element_text(size=16, color="#555555"),
        axis_line=element_line(color="#CCCCCC", size=0.5),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color="#EBEBEB", size=0.3, linetype="dotted"),
        plot_background=element_rect(fill="white", color="white"),
        panel_background=element_rect(fill="white", color="white"),
        plot_margin=0.02,
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
