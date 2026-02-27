"""pyplots.ai
mohr-circle: Mohr's Circle for Stress Analysis
Library: letsplot 4.8.2 | Python 3.14.3
Quality: 85/100 | Created: 2026-02-27
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Data - stress state for a beam under combined loading
sigma_x = 80.0  # MPa, normal stress in x-direction
sigma_y = -30.0  # MPa, normal stress in y-direction
tau_xy = 50.0  # MPa, shear stress on xy-plane

# Mohr's Circle parameters
center = (sigma_x + sigma_y) / 2.0
radius = np.sqrt(((sigma_x - sigma_y) / 2.0) ** 2 + tau_xy**2)
sigma_1 = center + radius  # major principal stress
sigma_2 = center - radius  # minor principal stress
tau_max = radius  # maximum shear stress
theta_p = 0.5 * np.degrees(np.arctan2(2 * tau_xy, sigma_x - sigma_y))

# Circle geometry
theta = np.linspace(0, 2 * np.pi, 360)
df_circle = pd.DataFrame({"sigma": center + radius * np.cos(theta), "tau": radius * np.sin(theta)})

# Colorblind-safe palette (replaces red-green with crimson-teal)
C_CIRCLE = "#306998"
C_INPUT = "#B91C1C"
C_PRINCIPAL = "#0891B2"
C_SHEAR = "#D97706"

# Key point DataFrames (used for both markers and labels)
df_input = pd.DataFrame(
    {
        "sigma": [sigma_x, sigma_y],
        "tau": [tau_xy, -tau_xy],
        "label": [
            f"A (\u03c3x, \u03c4xy) = ({sigma_x:.0f}, {tau_xy:.0f})",
            f"B (\u03c3y, \u2212\u03c4xy) = ({sigma_y:.0f}, {-tau_xy:.0f})",
        ],
        "detail": [
            f"Normal: {sigma_x:.0f} MPa | Shear: {tau_xy:.0f} MPa",
            f"Normal: {sigma_y:.0f} MPa | Shear: {-tau_xy:.0f} MPa",
        ],
    }
)

df_principal = pd.DataFrame(
    {
        "sigma": [sigma_1, sigma_2],
        "tau": [0.0, 0.0],
        "label": [f"\u03c3\u2081 = {sigma_1:.1f}", f"\u03c3\u2082 = {sigma_2:.1f}"],
        "detail": [f"Max principal stress: {sigma_1:.1f} MPa", f"Min principal stress: {sigma_2:.1f} MPa"],
    }
)

df_shear = pd.DataFrame(
    {
        "sigma": [center, center],
        "tau": [tau_max, -tau_max],
        "label": [f"\u03c4_max = {tau_max:.1f}", f"\u2212\u03c4_max = {-tau_max:.1f}"],
        "detail": [f"Max shear stress: {tau_max:.1f} MPa", f"Min shear stress: {-tau_max:.1f} MPa"],
    }
)

df_center = pd.DataFrame(
    {
        "sigma": [center],
        "tau": [0.0],
        "label": [f"C ({center:.0f}, 0)"],
        "detail": [f"Mean stress: {center:.1f} MPa | Radius: {radius:.1f} MPa"],
    }
)

# Reference geometry
pad = radius * 0.35
df_hline = pd.DataFrame({"sigma": [center - radius - pad, center + radius + pad], "tau": [0.0, 0.0]})
df_vline = pd.DataFrame({"sigma": [center, center], "tau": [-radius - pad, radius + pad]})
df_diameter = pd.DataFrame({"sigma": [sigma_x, sigma_y], "tau": [tau_xy, -tau_xy]})

# Angle arc for 2θp
arc_r = radius * 0.35
arc_t = np.linspace(0, np.radians(2 * theta_p), 50)
df_arc = pd.DataFrame({"sigma": center + arc_r * np.cos(arc_t), "tau": arc_r * np.sin(arc_t)})

# Build plot
plot = (
    ggplot()  # noqa: F405
    # Reference lines through center
    + geom_line(  # noqa: F405
        data=df_hline,
        mapping=aes(x="sigma", y="tau"),  # noqa: F405
        color="#D4D4D4",
        size=0.7,
        linetype="dashed",
    )
    + geom_line(  # noqa: F405
        data=df_vline,
        mapping=aes(x="sigma", y="tau"),  # noqa: F405
        color="#D4D4D4",
        size=0.7,
        linetype="dashed",
    )
    # Subtle circle fill
    + geom_polygon(  # noqa: F405
        data=df_circle,
        mapping=aes(x="sigma", y="tau"),  # noqa: F405
        fill=C_CIRCLE,
        color=C_CIRCLE,
        alpha=0.06,
        size=0,
    )
    # Circle outline
    + geom_path(  # noqa: F405
        data=df_circle,
        mapping=aes(x="sigma", y="tau"),  # noqa: F405
        color=C_CIRCLE,
        size=1.8,
        alpha=0.85,
    )
    # Diameter line A-B
    + geom_line(  # noqa: F405
        data=df_diameter,
        mapping=aes(x="sigma", y="tau"),  # noqa: F405
        color="#737373",
        size=0.9,
        linetype="dashed",
    )
    # Angle arc
    + geom_path(  # noqa: F405
        data=df_arc,
        mapping=aes(x="sigma", y="tau"),  # noqa: F405
        color=C_SHEAR,
        size=1.3,
    )
    # Input stress points with interactive tooltips
    + geom_point(  # noqa: F405
        data=df_input,
        mapping=aes(x="sigma", y="tau"),  # noqa: F405
        color=C_INPUT,
        size=7,
        shape=16,
        tooltips=layer_tooltips().line("@label").line("@detail"),  # noqa: F405
    )
    # Principal stress points with tooltips
    + geom_point(  # noqa: F405
        data=df_principal,
        mapping=aes(x="sigma", y="tau"),  # noqa: F405
        color=C_PRINCIPAL,
        size=7,
        shape=18,
        tooltips=layer_tooltips().line("@label").line("@detail"),  # noqa: F405
    )
    # Max shear stress points with tooltips
    + geom_point(  # noqa: F405
        data=df_shear,
        mapping=aes(x="sigma", y="tau"),  # noqa: F405
        color=C_SHEAR,
        size=7,
        shape=17,
        tooltips=layer_tooltips().line("@label").line("@detail"),  # noqa: F405
    )
    # Center point with tooltip
    + geom_point(  # noqa: F405
        data=df_center,
        mapping=aes(x="sigma", y="tau"),  # noqa: F405
        color=C_CIRCLE,
        size=5,
        shape=4,
        tooltips=layer_tooltips().line("@label").line("@detail"),  # noqa: F405
    )
    # Annotation labels
    + geom_text(  # noqa: F405
        data=df_input.iloc[[0]],
        mapping=aes(x="sigma", y="tau", label="label"),  # noqa: F405
        color=C_INPUT,
        size=12,
        nudge_y=radius * 0.12,
        nudge_x=-radius * 0.05,
        hjust=1,
    )
    + geom_text(  # noqa: F405
        data=df_input.iloc[[1]],
        mapping=aes(x="sigma", y="tau", label="label"),  # noqa: F405
        color=C_INPUT,
        size=12,
        nudge_y=-radius * 0.12,
        nudge_x=radius * 0.05,
        hjust=0,
    )
    + geom_text(  # noqa: F405
        data=df_principal.iloc[[0]],
        mapping=aes(x="sigma", y="tau", label="label"),  # noqa: F405
        color=C_PRINCIPAL,
        size=12,
        nudge_y=-radius * 0.12,
        nudge_x=radius * 0.02,
        hjust=0,
    )
    + geom_text(  # noqa: F405
        data=df_principal.iloc[[1]],
        mapping=aes(x="sigma", y="tau", label="label"),  # noqa: F405
        color=C_PRINCIPAL,
        size=12,
        nudge_y=-radius * 0.12,
        nudge_x=-radius * 0.02,
        hjust=1,
    )
    # Shear labels (combined - same color, nudge, hjust)
    + geom_text(  # noqa: F405
        data=df_shear,
        mapping=aes(x="sigma", y="tau", label="label"),  # noqa: F405
        color=C_SHEAR,
        size=12,
        nudge_x=radius * 0.1,
        hjust=0,
    )
    # Angle label
    + geom_text(  # noqa: F405
        data=pd.DataFrame(
            {
                "sigma": [center + arc_r * 1.2 * np.cos(np.radians(theta_p))],
                "tau": [arc_r * 1.2 * np.sin(np.radians(theta_p))],
                "label": [f"2\u03b8p = {2 * theta_p:.1f}\u00b0"],
            }
        ),
        mapping=aes(x="sigma", y="tau", label="label"),  # noqa: F405
        color=C_SHEAR,
        size=12,
        hjust=0,
    )
    # Center label
    + geom_text(  # noqa: F405
        data=df_center,
        mapping=aes(x="sigma", y="tau", label="label"),  # noqa: F405
        color=C_CIRCLE,
        size=11,
        nudge_y=-radius * 0.12,
    )
    # Styling
    + labs(  # noqa: F405
        x="Normal Stress \u03c3 (MPa)",
        y="Shear Stress \u03c4 (MPa)",
        title="mohr-circle \u00b7 letsplot \u00b7 pyplots.ai",
        subtitle=(
            f"Stress state: \u03c3x = {sigma_x:.0f}, \u03c3y = {sigma_y:.0f},"
            f" \u03c4xy = {tau_xy:.0f} MPa \u2014 Beam under combined loading"
        ),
    )
    + coord_fixed()  # noqa: F405
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        plot_title=element_text(size=24, face="bold"),  # noqa: F405
        plot_subtitle=element_text(size=16, color="#525252", face="italic"),  # noqa: F405
        axis_title=element_text(size=20, color="#404040"),  # noqa: F405
        axis_text=element_text(size=16, color="#525252"),  # noqa: F405
        panel_grid_major=element_line(size=0.4, color="#EBEBEB"),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
        plot_background=element_rect(fill="#FAFAFA", color="#FAFAFA"),  # noqa: F405
        panel_background=element_rect(fill="white", color="#E0E0E0", size=0.5),  # noqa: F405
    )
    + ggsize(1600, 900)  # noqa: F405
)

# Save
export_ggsave(plot, filename="plot.png", path=".", scale=3)
export_ggsave(plot, filename="plot.html", path=".")
