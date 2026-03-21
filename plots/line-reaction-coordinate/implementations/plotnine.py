"""pyplots.ai
line-reaction-coordinate: Reaction Coordinate Energy Diagram
Library: plotnine | Python 3.13
Quality: pending | Created: 2026-03-21
"""

import sys


sys.path = [p for p in sys.path if not p.endswith("implementations")]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from plotnine import (  # noqa: E402
    aes,
    annotate,
    arrow,
    coord_cartesian,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_line,
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

# Arrow positions
ea_x = 0.18  # Ea arrow on the left
dh_x = 1.06  # ΔH arrow on the far right

# Horizontal dashed reference lines (extend to ΔH arrow)
hline_df = pd.DataFrame(
    {
        "x": [0.0, 0.70],
        "xend": [dh_x + 0.02, dh_x + 0.02],
        "y": [reactant_energy, product_energy],
        "yend": [reactant_energy, product_energy],
    }
)

# Plot
arrow_head = arrow(length=0.12, type="closed")

plot = (
    ggplot(curve_df, aes(x="reaction_coord", y="energy"))
    # Dashed reference lines at reactant and product energy levels
    + geom_segment(
        hline_df,
        aes(x="x", y="y", xend="xend", yend="yend"),
        linetype="dashed",
        color="#AAAAAA",
        size=0.5,
        inherit_aes=False,
    )
    # Main energy curve
    + geom_line(color="#306998", size=2.5)
    # Ea double-headed arrow (reactant level → transition state)
    + annotate(
        "segment",
        x=ea_x,
        xend=ea_x,
        y=reactant_energy + 3,
        yend=transition_energy - 3,
        color="#C0392B",
        size=0.7,
        arrow=arrow_head,
    )
    + annotate(
        "segment",
        x=ea_x,
        xend=ea_x,
        y=transition_energy - 3,
        yend=reactant_energy + 3,
        color="#C0392B",
        size=0.7,
        arrow=arrow_head,
    )
    # Ea label
    + annotate(
        "text",
        x=ea_x - 0.04,
        y=(reactant_energy + transition_energy) / 2,
        label="Eₐ = 70\nkJ/mol",
        size=13,
        color="#C0392B",
        ha="right",
        fontweight="bold",
    )
    # ΔH double-headed arrow (reactant level → product level, far right)
    + annotate(
        "segment",
        x=dh_x,
        xend=dh_x,
        y=reactant_energy - 2,
        yend=product_energy + 2,
        color="#2E7D32",
        size=0.7,
        arrow=arrow_head,
    )
    + annotate(
        "segment",
        x=dh_x,
        xend=dh_x,
        y=product_energy + 2,
        yend=reactant_energy - 2,
        color="#2E7D32",
        size=0.7,
        arrow=arrow_head,
    )
    # ΔH label
    + annotate(
        "text",
        x=dh_x + 0.04,
        y=(reactant_energy + product_energy) / 2,
        label="ΔH = −30\nkJ/mol",
        size=13,
        color="#2E7D32",
        ha="left",
        fontweight="bold",
    )
    # Reactants label
    + annotate(
        "text",
        x=0.02,
        y=reactant_energy + 5,
        label="Reactants (50 kJ/mol)",
        size=13,
        color="#333333",
        ha="left",
        va="bottom",
        fontweight="bold",
    )
    # Transition state label
    + annotate(
        "text",
        x=0.50,
        y=transition_energy + 5,
        label="Transition State (120 kJ/mol)",
        size=13,
        color="#333333",
        ha="center",
        va="bottom",
        fontweight="bold",
    )
    # Products label
    + annotate(
        "text",
        x=0.95,
        y=product_energy + 5,
        label="Products (20 kJ/mol)",
        size=13,
        color="#333333",
        ha="right",
        va="bottom",
        fontweight="bold",
    )
    # Axes and title
    + labs(
        title="line-reaction-coordinate · plotnine · pyplots.ai", x="Reaction Coordinate", y="Potential Energy (kJ/mol)"
    )
    + scale_x_continuous(breaks=[0, 0.25, 0.5, 0.75, 1.0], labels=["0", "", "0.5", "", "1.0"])
    + scale_y_continuous(limits=[0, 145])
    + coord_cartesian(xlim=(-0.05, 1.2))
    # Style
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, ha="center", weight="bold", color="#1A3A5C"),
        axis_title=element_text(size=20, color="#333333"),
        axis_text=element_text(size=16, color="#555555"),
        axis_line=element_line(color="#CCCCCC", size=0.5),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color="#E8E8E8", size=0.4),
        plot_background=element_rect(fill="white", color="white"),
        panel_background=element_rect(fill="white", color="white"),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
