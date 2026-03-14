""" pyplots.ai
phase-diagram-pt: Thermodynamic Phase Diagram (Pressure-Temperature)
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 83/100 | Created: 2026-03-14
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_line,
    geom_point,
    ggplot,
    labs,
    scale_color_manual,
    scale_x_continuous,
    scale_y_log10,
    theme,
    theme_minimal,
)


# Data - Water phase diagram
# Triple point: 273.16 K, 611.73 Pa
# Critical point: 647.1 K, 22.064 MPa = 22064000 Pa
R = 8.314  # J/(mol·K)
T_triple = 273.16
P_triple = 611.73
T_critical = 647.1
P_critical = 22.064e6

# Solid-gas boundary (sublimation curve) using Clausius-Clapeyron
L_sub = 51060  # J/mol, latent heat of sublimation
T_sub = np.linspace(200, T_triple, 80)
P_sub = P_triple * np.exp((L_sub / R) * (1 / T_triple - 1 / T_sub))

# Liquid-gas boundary (vaporization curve) using Clausius-Clapeyron
L_vap = 40700  # J/mol, latent heat of vaporization
T_vap = np.linspace(T_triple, T_critical, 100)
P_vap = P_triple * np.exp((L_vap / R) * (1 / T_triple - 1 / T_vap))

# Solid-liquid boundary (melting curve) - water has negative slope
# Use linear approximation in log space: nearly vertical, slight negative slope
P_melt = np.logspace(np.log10(P_triple), np.log10(P_critical * 5), 80)
# For water, dT/dP is slightly negative (~-7.4e-8 K/Pa)
T_melt = T_triple - 7.4e-8 * (P_melt - P_triple)

# Build dataframe for boundary curves
df_sub = pd.DataFrame({"temperature": T_sub, "pressure": P_sub, "boundary": "Solid–Gas"})
df_vap = pd.DataFrame({"temperature": T_vap, "pressure": P_vap, "boundary": "Liquid–Gas"})
df_melt = pd.DataFrame({"temperature": T_melt, "pressure": P_melt, "boundary": "Solid–Liquid"})
df = pd.concat([df_sub, df_vap, df_melt], ignore_index=True)

# Special points
df_points = pd.DataFrame(
    {
        "temperature": [T_triple, T_critical],
        "pressure": [P_triple, P_critical],
        "label": ["Triple Point", "Critical Point"],
    }
)

# Phase region fill areas
# Solid region: left of solid-liquid and above solid-gas
# Liquid region: between solid-liquid and liquid-gas
# Gas region: below liquid-gas and solid-gas
P_min = 10
P_max = 2e9
T_min = 180
T_max = 750

# Plot
boundary_colors = {"Solid–Gas": "#306998", "Liquid–Gas": "#e74c3c", "Solid–Liquid": "#27ae60"}

plot = (
    ggplot(df, aes(x="temperature", y="pressure", color="boundary"))
    + geom_line(size=2.0)
    + geom_point(
        data=df_points,
        mapping=aes(x="temperature", y="pressure"),
        color="#1a1a1a",
        fill="#FFD43B",
        size=6,
        stroke=1.5,
        shape="o",
        inherit_aes=False,
    )
    + scale_color_manual(values=boundary_colors)
    + scale_y_log10(
        labels=lambda lst: [
            f"{v:.0f} Pa"
            if v < 1000
            else f"{v / 1000:.0f} kPa"
            if v < 1e6
            else f"{v / 1e6:.0f} MPa"
            if v < 1e9
            else f"{v / 1e9:.0f} GPa"
            for v in lst
        ],
        limits=(P_min, P_max),
    )
    + scale_x_continuous(limits=(T_min, T_max))
    # Phase region labels
    + annotate("text", x=220, y=5e7, label="SOLID", size=18, color="#306998", alpha=0.5, fontweight="bold")
    + annotate("text", x=460, y=5e7, label="LIQUID", size=18, color="#e74c3c", alpha=0.5, fontweight="bold")
    + annotate("text", x=500, y=50, label="GAS", size=18, color="#27ae60", alpha=0.5, fontweight="bold")
    + annotate(
        "text",
        x=710,
        y=5e8,
        label="SUPERCRITICAL\nFLUID",
        size=12,
        color="#8e44ad",
        alpha=0.5,
        fontweight="bold",
        ha="center",
    )
    # Triple point label
    + annotate(
        "text",
        x=T_triple + 18,
        y=P_triple * 0.25,
        label=f"Triple Point\n({T_triple} K, {P_triple:.0f} Pa)",
        size=10,
        color="#1a1a1a",
        ha="left",
        va="top",
    )
    # Critical point label
    + annotate(
        "text",
        x=T_critical - 15,
        y=P_critical * 0.15,
        label=f"Critical Point\n({T_critical} K, {P_critical / 1e6:.1f} MPa)",
        size=10,
        color="#1a1a1a",
        ha="right",
        va="top",
    )
    + labs(
        x="Temperature (K)",
        y="Pressure",
        title="Water Phase Diagram · phase-diagram-pt · plotnine · pyplots.ai",
        color="Phase Boundary",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14, color="#2d2d2d"),
        axis_title=element_text(size=20, color="#2d2d2d"),
        axis_text=element_text(size=16, color="#555555"),
        plot_title=element_text(size=22, weight="bold", color="#1a1a1a"),
        legend_title=element_text(size=16, weight="bold"),
        legend_text=element_text(size=14),
        legend_position="right",
        panel_background=element_rect(fill="#fafafa", color="none"),
        plot_background=element_rect(fill="#ffffff", color="none"),
        panel_grid_major=element_line(color="#e0e0e0", size=0.3),
        panel_grid_minor=element_blank(),
        axis_line_x=element_line(color="#999999", size=0.6),
        axis_line_y=element_line(color="#999999", size=0.6),
        plot_margin=0.04,
    )
)

plot.save("plot.png", dpi=300, verbose=False)
