""" pyplots.ai
phase-diagram-pt: Thermodynamic Phase Diagram (Pressure-Temperature)
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-14
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    flavor_high_contrast_light,
    geom_area,
    geom_line,
    geom_point,
    geom_text,
    ggplot,
    ggsize,
    labs,
    layer_tooltips,
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
    {"temperature": temp_solid_gas, "pressure": pressure_solid_gas, "boundary": "Solid\u2013Gas (Sublimation)"}
)

df_vaporization = pd.DataFrame(
    {"temperature": temp_liquid_gas, "pressure": pressure_liquid_gas, "boundary": "Liquid\u2013Gas (Vaporization)"}
)

df_melting = pd.DataFrame(
    {"temperature": temp_solid_liquid, "pressure": pressure_solid_liquid, "boundary": "Solid\u2013Liquid (Melting)"}
)

df_boundaries = pd.concat([df_sublimation, df_vaporization, df_melting], ignore_index=True)

# Phase region fill areas (for subtle background shading)
# Gas region: below sublimation + vaporization curves
gas_temp = np.concatenate([temp_solid_gas, temp_liquid_gas])
gas_pressure_upper = np.concatenate([pressure_solid_gas, pressure_liquid_gas])
df_gas_fill = pd.DataFrame({"temperature": gas_temp, "ymax": gas_pressure_upper, "ymin": 0.01, "phase": "Gas"})

# Solid region: above sublimation + above melting (left side)
solid_temp = np.concatenate([temp_solid_gas, temp_solid_liquid[::-1]])
solid_pressure = np.concatenate([pressure_solid_gas, pressure_solid_liquid[::-1]])
df_solid_fill = pd.DataFrame(
    {"temperature": temp_solid_liquid, "ymax": 2e9, "ymin": pressure_solid_liquid, "phase": "Solid"}
)

# Liquid region: between melting and vaporization curves (above vaporization, below melting extension)
df_liquid_fill = pd.DataFrame(
    {"temperature": temp_liquid_gas, "ymax": 2e9, "ymin": pressure_liquid_gas, "phase": "Liquid"}
)

# Special points
df_points = pd.DataFrame(
    {
        "temperature": [triple_t, critical_t],
        "pressure": [triple_p, critical_p],
        "label": ["Triple Point\n(273.16 K, 611.73 Pa)", "Critical Point\n(647.1 K, 22.06 MPa)"],
        "point_type": ["Triple Point", "Critical Point"],
    }
)

# Phase region labels
df_labels = pd.DataFrame(
    {"temperature": [225.0, 450.0, 450.0], "pressure": [5e7, 5e8, 500], "text": ["SOLID", "LIQUID", "GAS"]}
)

# Colorblind-safe palette (blue / orange / purple - no red-green)
boundary_colors = ["#306998", "#E69F00", "#8B5CF6"]
plot = (
    ggplot()
    # Subtle phase region fills using geom_area (lets-plot distinctive)
    + geom_area(data=df_gas_fill, mapping=aes(x="temperature", y="ymax"), fill="#FFF8E1", alpha=0.5, inherit_aes=False)
    + geom_area(
        data=df_solid_fill, mapping=aes(x="temperature", y="ymax"), fill="#E8EAF6", alpha=0.4, inherit_aes=False
    )
    + geom_area(
        data=df_liquid_fill, mapping=aes(x="temperature", y="ymax"), fill="#E0F2F1", alpha=0.4, inherit_aes=False
    )
    # Phase boundary curves with layer_tooltips (lets-plot distinctive)
    + geom_line(
        data=df_boundaries,
        mapping=aes(x="temperature", y="pressure", color="boundary"),
        size=2.8,
        tooltips=layer_tooltips().line("@boundary").line("T = @temperature K").line("P = @pressure Pa"),
    )
    # Special points with custom markers
    + geom_point(
        data=df_points,
        mapping=aes(x="temperature", y="pressure"),
        color="#1A1A1A",
        size=8,
        shape=18,
        inherit_aes=False,
        tooltips=layer_tooltips().line("@point_type"),
    )
    # Triple point label
    + geom_text(
        data=df_points.iloc[[0]],
        mapping=aes(x="temperature", y="pressure", label="label"),
        color="#1A1A1A",
        size=11,
        nudge_x=50,
        nudge_y=0.5,
        label_padding=0.3,
        inherit_aes=False,
    )
    # Critical point label
    + geom_text(
        data=df_points.iloc[[1]],
        mapping=aes(x="temperature", y="pressure", label="label"),
        color="#1A1A1A",
        size=11,
        nudge_x=-55,
        nudge_y=0.7,
        label_padding=0.3,
        inherit_aes=False,
    )
    # Phase region labels
    + geom_text(
        data=df_labels,
        mapping=aes(x="temperature", y="pressure", label="text"),
        color="#666666",
        size=18,
        fontface="bold",
        alpha=0.7,
        inherit_aes=False,
    )
    + scale_color_manual(values=boundary_colors)
    + scale_y_log10()
    + scale_x_continuous(breaks=[200, 300, 400, 500, 600, 700])
    + labs(
        x="Temperature (K)",
        y="Pressure (Pa)",
        title="phase-diagram-pt \u00b7 letsplot \u00b7 pyplots.ai",
        color="Phase Boundary",
    )
    + theme_minimal()
    + flavor_high_contrast_light()
    + theme(
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24, margin=[0, 0, 12, 0]),
        legend_text=element_text(size=14),
        legend_title=element_text(size=16),
        legend_position="bottom",
        panel_grid_minor=element_blank(),
        panel_grid_major=element_line(color="#E0E0E0", size=0.5),
        plot_background=element_rect(fill="white", color="white"),
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
