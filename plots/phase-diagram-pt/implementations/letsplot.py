"""pyplots.ai
phase-diagram-pt: Thermodynamic Phase Diagram (Pressure-Temperature)
Library: letsplot | Python 3.13
Quality: pending | Created: 2026-03-14
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_text,
    geom_line,
    geom_point,
    geom_text,
    ggplot,
    ggsize,
    labs,
    scale_color_manual,
    scale_x_continuous,
    scale_y_log10,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Data - Water phase diagram (realistic values)
# Triple point: 273.16 K, 611.73 Pa (0.00604 atm)
# Critical point: 647.1 K, 22.064 MPa (217.7 atm)
triple_t, triple_p = 273.16, 611.73
critical_t, critical_p = 647.1, 22.064e6

# Solid-gas boundary (sublimation curve) - Clausius-Clapeyron approximation
temp_solid_gas = np.linspace(200, triple_t, 80)
L_sub = 51059.0
R = 8.314
pressure_solid_gas = triple_p * np.exp((L_sub / R) * (1 / triple_t - 1 / temp_solid_gas))

# Liquid-gas boundary (vaporization curve) - from triple point to critical point
temp_liquid_gas = np.linspace(triple_t, critical_t, 100)
L_vap = 40660.0
pressure_liquid_gas = triple_p * np.exp((L_vap / R) * (1 / triple_t - 1 / temp_liquid_gas))

# Solid-liquid boundary (melting curve) - nearly vertical, negative slope for water
temp_solid_liquid = np.linspace(200, 273.16, 80)
pressure_solid_liquid = triple_p + (temp_solid_liquid - triple_t) * (-13.5e6)
pressure_solid_liquid = np.clip(pressure_solid_liquid, triple_p, 1e9)

# Build DataFrames for each boundary
df_sublimation = pd.DataFrame(
    {"temperature": temp_solid_gas, "pressure": pressure_solid_gas, "boundary": "Solid–Gas (Sublimation)"}
)

df_vaporization = pd.DataFrame(
    {"temperature": temp_liquid_gas, "pressure": pressure_liquid_gas, "boundary": "Liquid–Gas (Vaporization)"}
)

df_melting = pd.DataFrame(
    {"temperature": temp_solid_liquid, "pressure": pressure_solid_liquid, "boundary": "Solid–Liquid (Melting)"}
)

df_boundaries = pd.concat([df_sublimation, df_vaporization, df_melting], ignore_index=True)

# Special points
df_points = pd.DataFrame(
    {
        "temperature": [triple_t, critical_t],
        "pressure": [triple_p, critical_p],
        "label": ["Triple Point\n(273.16 K, 611.73 Pa)", "Critical Point\n(647.1 K, 22.06 MPa)"],
        "hjust": [0.0, 1.0],
        "point_type": ["Triple Point", "Critical Point"],
    }
)

# Phase region labels
df_labels = pd.DataFrame(
    {"temperature": [220.0, 420.0, 420.0], "pressure": [5e7, 5e8, 800], "text": ["SOLID", "LIQUID", "GAS"]}
)

# Plot
boundary_colors = ["#306998", "#E8583E", "#5BA35B"]

plot = (
    ggplot(df_boundaries, aes(x="temperature", y="pressure", color="boundary"))
    + geom_line(size=2.5)
    + geom_point(
        data=df_points, mapping=aes(x="temperature", y="pressure"), color="#1A1A1A", size=7, shape=18, inherit_aes=False
    )
    + geom_text(
        data=df_points.iloc[[0]],
        mapping=aes(x="temperature", y="pressure", label="label"),
        color="#1A1A1A",
        size=11,
        nudge_x=45,
        nudge_y=0.5,
        label_padding=0.3,
        inherit_aes=False,
    )
    + geom_text(
        data=df_points.iloc[[1]],
        mapping=aes(x="temperature", y="pressure", label="label"),
        color="#1A1A1A",
        size=11,
        nudge_x=-50,
        nudge_y=0.7,
        label_padding=0.3,
        inherit_aes=False,
    )
    + geom_text(
        data=df_labels,
        mapping=aes(x="temperature", y="pressure", label="text"),
        color="#555555",
        size=16,
        fontface="bold",
        inherit_aes=False,
    )
    + scale_color_manual(values=boundary_colors)
    + scale_y_log10()
    + scale_x_continuous(breaks=[200, 300, 400, 500, 600, 700])
    + labs(
        x="Temperature (K)",
        y="Pressure (Pa)",
        title="Water Phase Diagram · phase-diagram-pt · letsplot · pyplots.ai",
        color="Phase Boundary",
    )
    + theme_minimal()
    + theme(
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=22),
        legend_text=element_text(size=14),
        legend_title=element_text(size=16),
        legend_position="bottom",
        panel_grid_minor=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
