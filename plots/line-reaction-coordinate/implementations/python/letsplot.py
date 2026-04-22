""" pyplots.ai
line-reaction-coordinate: Reaction Coordinate Energy Diagram
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 91/100 | Created: 2026-03-21
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

# Piecewise smooth curve: Gaussian peak on sigmoid transition
peak_pos = 0.45
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
energy[reaction_coord < 0.1] = reactant_energy
energy[reaction_coord > 0.9] = product_energy

df = pd.DataFrame({"reaction_coordinate": reaction_coord, "energy": energy})

# Key values
ea = transition_energy - reactant_energy
delta_h = product_energy - reactant_energy

# Shaded region under curve for visual richness
area_df = df.copy()

# Colorblind-safe palette: blue (#306998) and orange (#E67E22) instead of red-green
ea_color = "#D35400"  # deep orange for Ea
dh_color = "#2471A3"  # steel blue for ΔH
curve_color = "#306998"  # Python blue
label_color = "#2C3E50"  # dark slate

# Horizontal reference lines at energy levels
hline_df = pd.DataFrame(
    {
        "x": [0.0, 0.0],
        "xend": [1.0, 1.0],
        "y": [reactant_energy, product_energy],
        "yend": [reactant_energy, product_energy],
    }
)

# Ea arrow segments (double-headed)
ea_arrow_df = pd.DataFrame(
    {
        "x": [0.20, 0.20],
        "y": [reactant_energy + 2, transition_energy - 2],
        "xend": [0.20, 0.20],
        "yend": [transition_energy - 2, reactant_energy + 2],
    }
)

# ΔH arrow segments (double-headed)
dh_arrow_df = pd.DataFrame(
    {
        "x": [0.80, 0.80],
        "y": [reactant_energy - 2, product_energy + 2],
        "xend": [0.80, 0.80],
        "yend": [product_energy + 2, reactant_energy - 2],
    }
)

# Build plot with lets-plot distinctive features
plot = (
    ggplot(df, aes(x="reaction_coordinate", y="energy"))  # noqa: F405
    # Shaded area under the energy curve using geom_area
    + geom_area(fill=curve_color, alpha=0.08)  # noqa: F405
    # Horizontal dashed reference lines
    + geom_segment(  # noqa: F405
        data=hline_df,
        mapping=aes(x="x", xend="xend", y="y", yend="yend"),  # noqa: F405
        linetype="dashed",
        color="#B0B0B0",
        size=0.7,
    )
    # Main energy curve - prominent
    + geom_line(color=curve_color, size=2.5)  # noqa: F405
    # Ea double-headed arrow (orange - colorblind safe)
    + geom_segment(  # noqa: F405
        data=ea_arrow_df,
        mapping=aes(x="x", xend="xend", y="y", yend="yend"),  # noqa: F405
        color=ea_color,
        size=1.3,
        arrow=arrow(length=10, type="open"),  # noqa: F405
    )
    # ΔH double-headed arrow (steel blue - colorblind safe)
    + geom_segment(  # noqa: F405
        data=dh_arrow_df,
        mapping=aes(x="x", xend="xend", y="y", yend="yend"),  # noqa: F405
        color=dh_color,
        size=1.3,
        arrow=arrow(length=10, type="open"),  # noqa: F405
    )
    # Labels using geom_label (lets-plot distinctive: label_padding, label_r)
    + geom_label(  # noqa: F405
        data=pd.DataFrame({"x": [0.08], "y": [reactant_energy - 8], "label": ["Reactants\n50 kJ/mol"]}),
        mapping=aes(x="x", y="y", label="label"),  # noqa: F405
        size=15,
        color=label_color,
        fill="#F8F9FA",
        alpha=0.85,
        label_padding=0.4,
        label_r=0.3,
        label_size=0,
    )
    + geom_label(  # noqa: F405
        data=pd.DataFrame({"x": [peak_pos], "y": [transition_energy + 8], "label": ["Transition State\n120 kJ/mol"]}),
        mapping=aes(x="x", y="y", label="label"),  # noqa: F405
        size=15,
        color=label_color,
        fill="#F8F9FA",
        alpha=0.85,
        label_padding=0.4,
        label_r=0.3,
        label_size=0,
    )
    + geom_label(  # noqa: F405
        data=pd.DataFrame({"x": [0.92], "y": [product_energy - 8], "label": ["Products\n20 kJ/mol"]}),
        mapping=aes(x="x", y="y", label="label"),  # noqa: F405
        size=15,
        color=label_color,
        fill="#F8F9FA",
        alpha=0.85,
        label_padding=0.4,
        label_r=0.3,
        label_size=0,
    )
    # Energy annotation labels with colored backgrounds matching their arrows
    + geom_label(  # noqa: F405
        data=pd.DataFrame(
            {"x": [0.20], "y": [(reactant_energy + transition_energy) / 2], "label": [f"Ea = {ea:.0f} kJ/mol"]}
        ),
        mapping=aes(x="x", y="y", label="label"),  # noqa: F405
        size=16,
        color="#FFFFFF",
        fill=ea_color,
        alpha=0.9,
        label_padding=0.5,
        label_r=0.3,
        label_size=0,
        fontface="bold",
    )
    + geom_label(  # noqa: F405
        data=pd.DataFrame(
            {"x": [0.80], "y": [(reactant_energy + product_energy) / 2], "label": [f"ΔH = {delta_h:.0f} kJ/mol"]}
        ),
        mapping=aes(x="x", y="y", label="label"),  # noqa: F405
        size=16,
        color="#FFFFFF",
        fill=dh_color,
        alpha=0.9,
        label_padding=0.5,
        label_r=0.3,
        label_size=0,
        fontface="bold",
    )
    # Scales
    + scale_x_continuous(  # noqa: F405
        name="Reaction Coordinate", breaks=[], expand=[0.02, 0.02]
    )
    + scale_y_continuous(  # noqa: F405
        name="Potential Energy (kJ/mol)", limits=[0, 145]
    )
    + labs(title="line-reaction-coordinate · letsplot · pyplots.ai")  # noqa: F405
    + coord_cartesian(ylim=[0, 145])  # noqa: F405
    + ggsize(1600, 900)  # noqa: F405
    # Lets-plot distinctive: flavor for base styling + element_geom for global defaults
    + flavor_high_contrast_light()  # noqa: F405
    + theme(  # noqa: F405
        axis_text=element_text(size=16, color="#555555"),  # noqa: F405
        axis_title=element_text(size=20, color="#333333"),  # noqa: F405
        plot_title=element_text(size=24, hjust=0.5, color="#2C3E50", face="bold"),  # noqa: F405
        axis_text_x=element_blank(),  # noqa: F405
        axis_ticks_x=element_blank(),  # noqa: F405
        axis_line_x=element_line(color="#CCCCCC", size=0.6),  # noqa: F405
        axis_line_y=element_line(color="#CCCCCC", size=0.6),  # noqa: F405
        panel_grid_major_y=element_line(color="#EEEEEE", size=0.3),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
        panel_grid_major_x=element_blank(),  # noqa: F405
        legend_position="none",
        plot_background=element_rect(fill="#FFFFFF", color="#FFFFFF"),  # noqa: F405
        panel_background=element_rect(fill="#FAFBFC", color="#FAFBFC"),  # noqa: F405
    )
)

# Save
ggsave(plot, filename="plot.png", path=".", scale=3)
ggsave(plot, filename="plot.html", path=".")
