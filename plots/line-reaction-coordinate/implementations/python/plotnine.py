""" anyplot.ai
line-reaction-coordinate: Reaction Coordinate Energy Diagram
Library: plotnine 0.15.7 | Python 3.13.14
Quality: 87/100 | Updated: 2026-06-24
"""

# ruff: noqa: E402
"""anyplot.ai — line-reaction-coordinate: Reaction Coordinate Energy Diagram
Library: plotnine | Python
"""

import os
import sys


_here = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != _here]

import numpy as np
import pandas as pd
from plotnine import (
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
from scipy.interpolate import CubicSpline


# Theme-adaptive chrome tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette (hybrid-v3, 8 hues)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

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
key_points = pd.DataFrame(
    {"reaction_coord": [0.0, 0.50, 1.0], "energy": [reactant_energy, transition_energy, product_energy]}
)

# Arrow positions — balanced within data range
ea_x = 0.08  # Ea arrow, left side
dh_x = 0.82  # ΔH arrow, right side (room for label before edge)

# Annotation colors from Imprint palette (semantic roles)
ea_color = IMPRINT_PALETTE[4]  # #AE3030 matte red — activation barrier (semantic: cost/warning)
dh_color = IMPRINT_PALETTE[2]  # #4467A3 blue — enthalpy change

# Horizontal dashed reference lines at reactant and product energy levels
hline_df = pd.DataFrame(
    {
        "x": [0.0, 0.73],
        "xend": [0.84, 0.84],
        "y": [reactant_energy, product_energy],
        "yend": [reactant_energy, product_energy],
    }
)

arrow_head = arrow(length=0.12, type="closed")

plot = (
    ggplot(curve_df, aes(x="reaction_coord", y="energy"))
    # Dashed reference lines at reactant and product energy levels
    + geom_segment(
        hline_df,
        aes(x="x", y="y", xend="xend", yend="yend"),
        linetype="dashed",
        color=INK_MUTED,
        size=0.4,
        inherit_aes=False,
    )
    # Main energy curve — Imprint brand green (#009E73), first categorical series
    + geom_line(color=IMPRINT_PALETTE[0], size=1.5)
    # Key-point markers at reactant, transition state, product
    + geom_point(
        key_points,
        aes(x="reaction_coord", y="energy"),
        color=IMPRINT_PALETTE[0],
        fill=IMPRINT_PALETTE[0],
        size=3,
        inherit_aes=False,
    )
    # Ea double-headed arrow (reactant level ↔ transition state)
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
    + annotate(
        "text",
        x=ea_x + 0.04,
        y=(reactant_energy + transition_energy) / 2,
        label="Eₐ = 70 kJ/mol",
        size=3.5,
        color=ea_color,
        ha="left",
        fontweight="bold",
    )
    # ΔH double-headed arrow (reactant level ↔ product level)
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
    + annotate(
        "text",
        x=dh_x + 0.03,
        y=(reactant_energy + product_energy) / 2,
        label="ΔH = −30\nkJ/mol",
        size=3.5,
        color=dh_color,
        ha="left",
        fontweight="bold",
    )
    # State labels
    + annotate(
        "text",
        x=0.02,
        y=reactant_energy + 7,
        label="Reactants\n50 kJ/mol",
        size=3.5,
        color=INK,
        ha="left",
        va="bottom",
        fontweight="bold",
    )
    + annotate(
        "text",
        x=0.50,
        y=transition_energy + 6,
        label="Transition State\n120 kJ/mol",
        size=3.5,
        color=INK,
        ha="center",
        va="bottom",
        fontweight="bold",
    )
    + annotate(
        "text",
        x=0.93,
        y=product_energy - 5,
        label="Products\n20 kJ/mol",
        size=3.5,
        color=INK,
        ha="right",
        va="top",
        fontweight="bold",
    )
    + labs(
        title="line-reaction-coordinate · python · plotnine · anyplot.ai",
        x="Reaction Coordinate",
        y="Potential Energy (kJ/mol)",
    )
    + scale_x_continuous(breaks=[0, 0.25, 0.5, 0.75, 1.0], labels=["0", "", "0.5", "", "1.0"], expand=(0.02, 0.08))
    + scale_y_continuous(limits=[0, 145], expand=(0.02, 0.02))
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_title=element_text(size=12, ha="center", weight="bold", color=INK, margin={"b": 10}),
        axis_title_x=element_text(size=10, color=INK_SOFT, margin={"t": 8}),
        axis_title_y=element_text(size=10, color=INK_SOFT, margin={"r": 8}),
        axis_text=element_text(size=8, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.4),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color=INK, size=0.3, alpha=0.15),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        axis_ticks=element_blank(),
        plot_margin=0.04,
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
