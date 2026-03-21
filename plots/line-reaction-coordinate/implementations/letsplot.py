"""pyplots.ai
line-reaction-coordinate: Reaction Coordinate Energy Diagram
Library: letsplot | Python 3.13
Quality: pending | Created: 2026-03-21
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave


LetsPlot.setup_html()  # noqa: F405

# Data - Single-step exothermic reaction energy profile
reactant_energy = 50.0
transition_energy = 120.0
product_energy = 20.0

# Build smooth energy curve using Gaussian-based profile
n_points = 300
reaction_coord = np.linspace(0, 1, n_points)

# Piecewise smooth curve: cubic interpolation through key points
# Reactant plateau -> transition state peak -> product plateau
reactant_width = 0.15
product_width = 0.15
peak_pos = 0.45

# Base energy as weighted combination of start/end with Gaussian peak
sigma = 0.12
gaussian_peak = np.exp(-0.5 * ((reaction_coord - peak_pos) / sigma) ** 2)

# Smooth sigmoid transition from reactant to product level
transition = 1 / (1 + np.exp(-20 * (reaction_coord - 0.6)))
base_energy = reactant_energy * (1 - transition) + product_energy * transition

# Add the activation barrier
barrier_height = transition_energy - (
    reactant_energy * (1 - 1 / (1 + np.exp(-20 * (peak_pos - 0.6))))
    + product_energy * (1 / (1 + np.exp(-20 * (peak_pos - 0.6))))
)
energy = base_energy + barrier_height * gaussian_peak

# Flatten plateaus at start and end
flat_start = reaction_coord < 0.1
flat_end = reaction_coord > 0.9
energy[flat_start] = reactant_energy
energy[flat_end] = product_energy

df = pd.DataFrame({"reaction_coordinate": reaction_coord, "energy": energy})

# Key points for annotations
ea = transition_energy - reactant_energy
delta_h = product_energy - reactant_energy

# Annotation data - horizontal dashed lines at reactant/product levels
hline_df = pd.DataFrame(
    {"reaction_coordinate": [0.0, 0.0], "energy": [reactant_energy, product_energy], "xend": [1.0, 1.0]}
)

# Arrow annotation data for Ea (activation energy)
ea_arrow_df = pd.DataFrame(
    {
        "x": [0.18, 0.18],
        "y": [reactant_energy, transition_energy],
        "xend": [0.18, 0.18],
        "yend": [transition_energy, reactant_energy],
    }
)

# Arrow annotation data for delta H
dh_arrow_df = pd.DataFrame(
    {
        "x": [0.82, 0.82],
        "y": [reactant_energy, product_energy],
        "xend": [0.82, 0.82],
        "yend": [product_energy, reactant_energy],
    }
)

# Text labels
labels_df = pd.DataFrame(
    {
        "x": [0.05, peak_pos, 0.95, 0.18, 0.82],
        "y": [
            reactant_energy - 5,
            transition_energy + 6,
            product_energy - 5,
            (reactant_energy + transition_energy) / 2,
            (reactant_energy + product_energy) / 2,
        ],
        "label": [
            "Reactants\n50 kJ/mol",
            "Transition State\n120 kJ/mol",
            "Products\n20 kJ/mol",
            f"Ea = {ea} kJ/mol",
            f"\u0394H = {delta_h} kJ/mol",
        ],
    }
)

# Plot
plot = (
    ggplot(df, aes(x="reaction_coordinate", y="energy"))  # noqa: F405
    # Dashed reference lines at reactant and product energy levels
    + geom_segment(  # noqa: F405
        data=hline_df,
        mapping=aes(x="reaction_coordinate", xend="xend", y="energy", yend="energy"),  # noqa: F405
        linetype="dashed",
        color="#AAAAAA",
        size=0.8,
    )
    # Main energy curve
    + geom_line(color="#306998", size=2.5)  # noqa: F405
    # Ea double-headed arrow (two segments)
    + geom_segment(  # noqa: F405
        data=ea_arrow_df,
        mapping=aes(x="x", xend="xend", y="y", yend="yend"),  # noqa: F405
        color="#C0392B",
        size=1.2,
        arrow=arrow(length=10, type="open"),  # noqa: F405
    )
    # Delta H double-headed arrow
    + geom_segment(  # noqa: F405
        data=dh_arrow_df,
        mapping=aes(x="x", xend="xend", y="y", yend="yend"),  # noqa: F405
        color="#2E7D32",
        size=1.2,
        arrow=arrow(length=10, type="open"),  # noqa: F405
    )
    # Text labels
    + geom_text(  # noqa: F405
        data=labels_df, mapping=aes(x="x", y="y", label="label"), size=16, color="#2C3E50"  # noqa: F405
    )
    # Scales and labels
    + scale_x_continuous(  # noqa: F405
        name="Reaction Coordinate", breaks=[0, 0.25, 0.5, 0.75, 1.0], labels=["", "", "", "", ""]
    )
    + scale_y_continuous(  # noqa: F405
        name="Potential Energy (kJ/mol)", limits=[0, 140]
    )
    + labs(title="line-reaction-coordinate \u00b7 letsplot \u00b7 pyplots.ai")  # noqa: F405
    + ggsize(1600, 900)  # noqa: F405
    + theme(  # noqa: F405
        axis_text=element_text(size=16),  # noqa: F405
        axis_title=element_text(size=20),  # noqa: F405
        plot_title=element_text(size=24, hjust=0.5),  # noqa: F405
        axis_text_x=element_blank(),  # noqa: F405
        axis_ticks_x=element_blank(),  # noqa: F405
        axis_line_x=element_line(color="#CCCCCC", size=0.8),  # noqa: F405
        axis_line_y=element_line(color="#CCCCCC", size=0.8),  # noqa: F405
        panel_grid_major_y=element_line(color="#EEEEEE", size=0.4),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
        panel_grid_major_x=element_blank(),  # noqa: F405
        legend_position="none",
        plot_background=element_blank(),  # noqa: F405
        panel_background=element_blank(),  # noqa: F405
    )
)

# Save
ggsave(plot, filename="plot.png", path=".", scale=3)
ggsave(plot, filename="plot.html", path=".")
