""" anyplot.ai
phase-diagram-pt: Thermodynamic Phase Diagram (Pressure-Temperature)
Library: letsplot 4.10.1 | Python 3.13.13
Quality: 83/100 | Updated: 2026-06-08
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    flavor_high_contrast_dark,
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

# Imprint palette — canonical order (hybrid-v3)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Phase region fill colors — theme-adaptive subtle backgrounds
FILL_GAS = "#FFF8E1" if THEME == "light" else "#302C00"
FILL_SOLID = "#EDE9F8" if THEME == "light" else "#1E1930"
FILL_LIQUID = "#E0F2F1" if THEME == "light" else "#00302E"

# Water phase diagram — physically accurate (Clausius-Clapeyron equations)
# Triple point: 273.16 K, 611.73 Pa | Critical point: 647.1 K, 22.064 MPa
triple_t, triple_p = 273.16, 611.73
critical_t, critical_p = 647.1, 22.064e6

# Solid-gas boundary (sublimation curve)
temp_solid_gas = np.linspace(200, triple_t, 80)
L_sub = 51059.0
R = 8.314
pressure_solid_gas = triple_p * np.exp((L_sub / R) * (1 / triple_t - 1 / temp_solid_gas))

# Liquid-gas boundary (vaporization curve — triple point to critical point)
temp_liquid_gas = np.linspace(triple_t, critical_t, 100)
L_vap = 40660.0
pressure_liquid_gas = triple_p * np.exp((L_vap / R) * (1 / triple_t - 1 / temp_liquid_gas))

# Solid-liquid boundary (melting curve — negative slope, water anomaly)
temp_solid_liquid = np.linspace(200, 273.16, 80)
pressure_solid_liquid = triple_p + (temp_solid_liquid - triple_t) * (-13.5e6)
pressure_solid_liquid = np.clip(pressure_solid_liquid, triple_p, 1e9)

# DataFrames for boundary curves
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

# Phase region fill areas
gas_temp = np.concatenate([temp_solid_gas, temp_liquid_gas])
gas_pressure_upper = np.concatenate([pressure_solid_gas, pressure_liquid_gas])
df_gas_fill = pd.DataFrame({"temperature": gas_temp, "ymax": gas_pressure_upper, "ymin": 0.01, "phase": "Gas"})
df_solid_fill = pd.DataFrame(
    {"temperature": temp_solid_liquid, "ymax": 2e9, "ymin": pressure_solid_liquid, "phase": "Solid"}
)
df_liquid_fill = pd.DataFrame(
    {"temperature": temp_liquid_gas, "ymax": 2e9, "ymin": pressure_liquid_gas, "phase": "Liquid"}
)

# Special points — triple point and critical point
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
    {"temperature": [225.0, 450.0, 450.0], "pressure": [5e7, 5e8, 500.0], "text": ["SOLID", "LIQUID", "GAS"]}
)

# Boundary curve colors — first 3 Imprint palette positions
boundary_colors = IMPRINT_PALETTE[:3]

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK_SOFT, size=0.3),
    panel_grid_minor=element_blank(),
    axis_title=element_text(size=12, color=INK),
    axis_text=element_text(size=10, color=INK_SOFT),
    axis_line=element_line(color=INK_SOFT),
    plot_title=element_text(size=16, color=INK, margin=[0, 0, 8, 0]),
    legend_text=element_text(size=10, color=INK_SOFT),
    legend_title=element_text(size=12, color=INK),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_position="bottom",
)

plot = (
    ggplot()
    # Subtle phase region fills
    + geom_area(data=df_gas_fill, mapping=aes(x="temperature", y="ymax"), fill=FILL_GAS, alpha=0.6, inherit_aes=False)
    + geom_area(
        data=df_solid_fill, mapping=aes(x="temperature", y="ymax"), fill=FILL_SOLID, alpha=0.5, inherit_aes=False
    )
    + geom_area(
        data=df_liquid_fill, mapping=aes(x="temperature", y="ymax"), fill=FILL_LIQUID, alpha=0.5, inherit_aes=False
    )
    # Phase boundary curves with interactive tooltips (lets-plot distinctive)
    + geom_line(
        data=df_boundaries,
        mapping=aes(x="temperature", y="pressure", color="boundary"),
        size=1.2,
        tooltips=layer_tooltips().line("@boundary").line("T = @temperature K").line("P = @pressure Pa"),
    )
    # Special points with diamond markers
    + geom_point(
        data=df_points,
        mapping=aes(x="temperature", y="pressure"),
        color=INK,
        size=4,
        shape=18,
        inherit_aes=False,
        tooltips=layer_tooltips().line("@point_type"),
    )
    # Triple point annotation
    + geom_text(
        data=df_points.iloc[[0]],
        mapping=aes(x="temperature", y="pressure", label="label"),
        color=INK,
        size=6,
        nudge_x=50,
        nudge_y=0.5,
        label_padding=0.3,
        inherit_aes=False,
    )
    # Critical point annotation
    + geom_text(
        data=df_points.iloc[[1]],
        mapping=aes(x="temperature", y="pressure", label="label"),
        color=INK,
        size=6,
        nudge_x=-55,
        nudge_y=0.7,
        label_padding=0.3,
        inherit_aes=False,
    )
    # Phase region labels — bold, subdued
    + geom_text(
        data=df_labels,
        mapping=aes(x="temperature", y="pressure", label="text"),
        color=INK_MUTED,
        size=9,
        fontface="bold",
        alpha=0.85,
        inherit_aes=False,
    )
    + scale_color_manual(values=boundary_colors)
    + scale_y_log10()
    + scale_x_continuous(breaks=[200, 300, 400, 500, 600, 700])
    + labs(
        x="Temperature (K)", y="Pressure (Pa)", title="phase-diagram-pt · letsplot · pyplots.ai", color="Phase Boundary"
    )
    + theme_minimal()
    + (flavor_high_contrast_light() if THEME == "light" else flavor_high_contrast_dark())
    + anyplot_theme
    + ggsize(800, 450)
)

ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
