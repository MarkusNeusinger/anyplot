""" anyplot.ai
mohr-circle: Mohr's Circle for Stress Analysis
Library: letsplot 4.10.1 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-30
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_line,
    geom_path,
    geom_point,
    geom_polygon,
    geom_text,
    ggplot,
    ggsave,
    ggsize,
    labs,
    layer_tooltips,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Theme tokens — Imprint palette, theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — semantic assignments for stress diagram elements
C_CIRCLE = "#4467A3"  # blue — structural circle outline
C_INPUT = "#AE3030"  # matte red — applied input stress points (semantic: danger/input)
C_PRINCIPAL = "#009E73"  # brand green — principal stress results (primary outcome)
C_SHEAR = "#BD8233"  # ochre — shear stress components

# Data — steel column under combined axial and bending load
sigma_x = 80.0  # MPa, axial + bending normal stress
sigma_y = -30.0  # MPa, lateral normal stress
tau_xy = 50.0  # MPa, shear stress from torsion

# Mohr's Circle geometry
center = (sigma_x + sigma_y) / 2.0
radius = np.sqrt(((sigma_x - sigma_y) / 2.0) ** 2 + tau_xy**2)
sigma_1 = center + radius
sigma_2 = center - radius
tau_max = radius
theta_p = 0.5 * np.degrees(np.arctan2(2 * tau_xy, sigma_x - sigma_y))

# Circle path
theta = np.linspace(0, 2 * np.pi, 360)
df_circle = pd.DataFrame({"sigma": center + radius * np.cos(theta), "tau": radius * np.sin(theta)})

# Input stress points A and B
df_input = pd.DataFrame(
    {
        "sigma": [sigma_x, sigma_y],
        "tau": [tau_xy, -tau_xy],
        "label": [f"A (σx={sigma_x:.0f}, τxy={tau_xy:.0f})", f"B (σy={sigma_y:.0f}, −τxy={-tau_xy:.0f})"],
        "detail": [
            f"Normal: {sigma_x:.0f} MPa | Shear: {tau_xy:.0f} MPa",
            f"Normal: {sigma_y:.0f} MPa | Shear: {-tau_xy:.0f} MPa",
        ],
    }
)

# Principal stress points (on the horizontal axis)
df_principal = pd.DataFrame(
    {
        "sigma": [sigma_1, sigma_2],
        "tau": [0.0, 0.0],
        "label": [f"σ₁ = {sigma_1:.1f}", f"σ₂ = {sigma_2:.1f}"],
        "detail": [f"Max principal: {sigma_1:.1f} MPa", f"Min principal: {sigma_2:.1f} MPa"],
    }
)

# Maximum shear stress points (top and bottom of circle)
df_shear = pd.DataFrame(
    {
        "sigma": [center, center],
        "tau": [tau_max, -tau_max],
        "label": [f"τmax = {tau_max:.1f}", f"−τmax = {tau_max:.1f}"],
        "detail": [f"Max shear: {tau_max:.1f} MPa", f"Min shear: {-tau_max:.1f} MPa"],
    }
)

# Center point
df_center = pd.DataFrame(
    {
        "sigma": [center],
        "tau": [0.0],
        "label": [f"C ({center:.0f}, 0)"],
        "detail": [f"Mean stress: {center:.1f} MPa | Radius: {radius:.1f} MPa"],
    }
)

# Reference lines through center
pad = radius * 0.45
df_hline = pd.DataFrame({"sigma": [center - radius - pad, center + radius + pad], "tau": [0.0, 0.0]})
df_vline = pd.DataFrame({"sigma": [center, center], "tau": [-radius - pad, radius + pad]})
df_diameter = pd.DataFrame({"sigma": [sigma_x, sigma_y], "tau": [tau_xy, -tau_xy]})

# Angle arc for 2θp (principal plane angle)
arc_r = radius * 0.35
arc_t = np.linspace(0, np.radians(2 * theta_p), 50)
df_arc = pd.DataFrame({"sigma": center + arc_r * np.cos(arc_t), "tau": arc_r * np.sin(arc_t)})

# Title
title = "mohr-circle · python · letsplot · anyplot.ai"

# Build plot
plot = (
    ggplot()
    # Reference lines through center
    + geom_line(data=df_hline, mapping=aes(x="sigma", y="tau"), color=INK_MUTED, size=0.6, linetype="dashed")
    + geom_line(data=df_vline, mapping=aes(x="sigma", y="tau"), color=INK_MUTED, size=0.6, linetype="dashed")
    # Circle fill (subtle) then solid outline
    + geom_polygon(data=df_circle, mapping=aes(x="sigma", y="tau"), fill=C_CIRCLE, color=C_CIRCLE, alpha=0.07, size=0)
    + geom_path(data=df_circle, mapping=aes(x="sigma", y="tau"), color=C_CIRCLE, size=2.0, alpha=0.9)
    # Diameter line A–B
    + geom_line(data=df_diameter, mapping=aes(x="sigma", y="tau"), color=INK_MUTED, size=0.8, linetype="dashed")
    # Principal plane angle arc
    + geom_path(data=df_arc, mapping=aes(x="sigma", y="tau"), color=C_SHEAR, size=1.5)
    # Input stress points (filled circle)
    + geom_point(
        data=df_input,
        mapping=aes(x="sigma", y="tau"),
        color=C_INPUT,
        size=7,
        shape=16,
        tooltips=layer_tooltips().line("@label").line("@detail"),
    )
    # Principal stress points (filled diamond)
    + geom_point(
        data=df_principal,
        mapping=aes(x="sigma", y="tau"),
        color=C_PRINCIPAL,
        size=7,
        shape=18,
        tooltips=layer_tooltips().line("@label").line("@detail"),
    )
    # Max shear stress points (filled triangle)
    + geom_point(
        data=df_shear,
        mapping=aes(x="sigma", y="tau"),
        color=C_SHEAR,
        size=7,
        shape=17,
        tooltips=layer_tooltips().line("@label").line("@detail"),
    )
    # Center marker (X cross)
    + geom_point(
        data=df_center,
        mapping=aes(x="sigma", y="tau"),
        color=INK_SOFT,
        size=5,
        shape=4,
        tooltips=layer_tooltips().line("@label").line("@detail"),
    )
    # Point A label — nudged right and up to separate from tau_max region
    + geom_text(
        data=df_input.iloc[[0]],
        mapping=aes(x="sigma", y="tau", label="label"),
        color=C_INPUT,
        size=5,
        hjust=0,
        nudge_x=radius * 0.05,
        nudge_y=radius * 0.10,
    )
    # Point B label — nudged left and down
    + geom_text(
        data=df_input.iloc[[1]],
        mapping=aes(x="sigma", y="tau", label="label"),
        color=C_INPUT,
        size=5,
        hjust=1,
        nudge_x=-radius * 0.05,
        nudge_y=-radius * 0.14,
    )
    # Principal stress labels
    + geom_text(
        data=df_principal.iloc[[0]],
        mapping=aes(x="sigma", y="tau", label="label"),
        color=C_PRINCIPAL,
        size=5,
        hjust=0.5,
        nudge_y=-radius * 0.14,
    )
    + geom_text(
        data=df_principal.iloc[[1]],
        mapping=aes(x="sigma", y="tau", label="label"),
        color=C_PRINCIPAL,
        size=5,
        hjust=0.5,
        nudge_y=-radius * 0.14,
    )
    # Tau_max label — nudged right, above the top marker
    + geom_text(
        data=df_shear.iloc[[0]],
        mapping=aes(x="sigma", y="tau", label="label"),
        color=C_SHEAR,
        size=5,
        hjust=0,
        nudge_x=radius * 0.12,
        nudge_y=radius * 0.07,
    )
    # -Tau_max label
    + geom_text(
        data=df_shear.iloc[[1]],
        mapping=aes(x="sigma", y="tau", label="label"),
        color=C_SHEAR,
        size=5,
        hjust=0,
        nudge_x=radius * 0.12,
        nudge_y=-radius * 0.07,
    )
    # Principal plane angle annotation
    + geom_text(
        data=pd.DataFrame(
            {
                "sigma": [center + arc_r * 1.5 * np.cos(np.radians(theta_p))],
                "tau": [arc_r * 1.5 * np.sin(np.radians(theta_p))],
                "label": [f"2θp = {2 * theta_p:.1f}°"],
            }
        ),
        mapping=aes(x="sigma", y="tau", label="label"),
        color=C_SHEAR,
        size=5,
        hjust=0,
    )
    # Center label
    + geom_text(
        data=df_center, mapping=aes(x="sigma", y="tau", label="label"), color=INK_SOFT, size=5, nudge_y=-radius * 0.13
    )
    # Axes, title, subtitle
    + labs(
        x="Normal Stress σ (MPa)",
        y="Shear Stress τ (MPa)",
        title=title,
        subtitle=(
            f"σx = {sigma_x:.0f}, σy = {sigma_y:.0f},"
            f" τxy = {tau_xy:.0f} MPa"
            f" | σ₁ = {sigma_1:.1f}, σ₂ = {sigma_2:.1f},"
            f" τmax = {tau_max:.1f} MPa"
        ),
    )
    + coord_fixed()
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK_MUTED, size=0.3),
        panel_grid_minor=element_blank(),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        plot_title=element_text(size=16, face="bold", color=INK),
        plot_subtitle=element_text(size=10, face="italic", color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(color=INK_SOFT),
        legend_title=element_text(color=INK),
    )
    + ggsize(600, 600)
)

# Save
ggsave(plot, f"plot-{THEME}.png", scale=4, path=".")
ggsave(plot, f"plot-{THEME}.html", path=".")
