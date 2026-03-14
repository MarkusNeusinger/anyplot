"""pyplots.ai
phase-diagram-pt: Thermodynamic Phase Diagram (Pressure-Temperature)
Library: plotnine 0.15.3 | Python 3.14.3
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
    geom_ribbon,
    geom_vline,
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
P_melt = np.logspace(np.log10(P_triple), np.log10(P_critical * 5), 80)
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

# Phase region fills using geom_ribbon - distinctive plotnine layer composition
P_min = 10
P_max = 2e9
T_min = 180
T_max = 750

# Solid region: left of triple point, above sublimation curve
n_fill = 60
T_solid_fill = np.linspace(T_min, T_triple - 1, n_fill)
P_solid_lower = P_triple * np.exp((L_sub / R) * (1 / T_triple - 1 / T_solid_fill))
df_solid = pd.DataFrame({"temperature": T_solid_fill, "ymin": P_solid_lower, "ymax": np.full(n_fill, P_max)})

# Gas region: below sublimation + vaporization curves, plus beyond critical
T_gas_sub = np.linspace(T_min, T_triple, 30)
P_gas_sub_upper = P_triple * np.exp((L_sub / R) * (1 / T_triple - 1 / T_gas_sub))
T_gas_vap = np.linspace(T_triple, T_critical, 30)
P_gas_vap_upper = P_triple * np.exp((L_vap / R) * (1 / T_triple - 1 / T_gas_vap))
T_gas_beyond = np.linspace(T_critical, T_max, 15)
P_gas_beyond_upper = np.full(15, P_critical)
df_gas = pd.DataFrame(
    {
        "temperature": np.concatenate([T_gas_sub, T_gas_vap, T_gas_beyond]),
        "ymin": np.full(75, P_min),
        "ymax": np.concatenate([P_gas_sub_upper, P_gas_vap_upper, P_gas_beyond_upper]),
    }
)

# Liquid region: between vaporization curve and top
T_liq = np.linspace(T_triple, T_critical, n_fill)
P_liq_lower = P_triple * np.exp((L_vap / R) * (1 / T_triple - 1 / T_liq))
df_liquid = pd.DataFrame({"temperature": T_liq, "ymin": P_liq_lower, "ymax": np.full(n_fill, P_max)})

# Supercritical region: beyond critical point
T_sc = np.linspace(T_critical, T_max, 30)
df_supercritical = pd.DataFrame({"temperature": T_sc, "ymin": np.full(30, P_critical), "ymax": np.full(30, P_max)})

# Colorblind-safe palette (blue, orange, purple - avoids red-green)
boundary_colors = {"Solid–Gas": "#306998", "Liquid–Gas": "#D95F02", "Solid–Liquid": "#7570B3"}


# Custom pressure formatter
def fmt_pressure(lst):
    out = []
    for v in lst:
        if v < 1000:
            out.append(f"{v:.0f} Pa")
        elif v < 1e6:
            out.append(f"{v / 1000:.0f} kPa")
        elif v < 1e9:
            out.append(f"{v / 1e6:.0f} MPa")
        else:
            out.append(f"{v / 1e9:.0f} GPa")
    return out


plot = (
    ggplot()
    # Phase region fills as separate ribbon layers (plotnine layer composition)
    + geom_ribbon(
        data=df_solid,
        mapping=aes(x="temperature", ymin="ymin", ymax="ymax"),
        fill="#306998",
        alpha=0.10,
        inherit_aes=False,
    )
    + geom_ribbon(
        data=df_gas,
        mapping=aes(x="temperature", ymin="ymin", ymax="ymax"),
        fill="#D95F02",
        alpha=0.10,
        inherit_aes=False,
    )
    + geom_ribbon(
        data=df_liquid,
        mapping=aes(x="temperature", ymin="ymin", ymax="ymax"),
        fill="#7570B3",
        alpha=0.10,
        inherit_aes=False,
    )
    + geom_ribbon(
        data=df_supercritical,
        mapping=aes(x="temperature", ymin="ymin", ymax="ymax"),
        fill="#66A61E",
        alpha=0.10,
        inherit_aes=False,
    )
    # Boundary curves
    + geom_line(data=df, mapping=aes(x="temperature", y="pressure", color="boundary"), size=2.2)
    # Special points with dual-layered markers
    + geom_point(
        data=df_points,
        mapping=aes(x="temperature", y="pressure"),
        color="#1a1a1a",
        fill="#FFD43B",
        size=7,
        stroke=1.8,
        shape="o",
        inherit_aes=False,
    )
    + scale_color_manual(values=boundary_colors)
    + scale_y_log10(labels=fmt_pressure, limits=(P_min, P_max))
    + scale_x_continuous(limits=(T_min, T_max))
    # Phase region labels
    + annotate("text", x=220, y=5e7, label="SOLID", size=18, color="#306998", alpha=0.45, fontweight="bold")
    + annotate("text", x=460, y=5e7, label="LIQUID", size=18, color="#7570B3", alpha=0.45, fontweight="bold")
    + annotate("text", x=500, y=50, label="GAS", size=18, color="#D95F02", alpha=0.45, fontweight="bold")
    + annotate(
        "text",
        x=710,
        y=5e8,
        label="SUPERCRITICAL\nFLUID",
        size=12,
        color="#66A61E",
        alpha=0.45,
        fontweight="bold",
        ha="center",
    )
    # Triple point annotation
    + annotate(
        "text",
        x=T_triple + 18,
        y=P_triple * 0.2,
        label=f"Triple Point\n({T_triple} K, {P_triple:.0f} Pa)",
        size=10,
        color="#1a1a1a",
        ha="left",
        va="top",
    )
    # Critical point annotation
    + annotate(
        "text",
        x=T_critical - 15,
        y=P_critical * 0.12,
        label=f"Critical Point\n({T_critical} K, {P_critical / 1e6:.1f} MPa)",
        size=10,
        color="#1a1a1a",
        ha="right",
        va="top",
    )
    # Dashed line showing critical temperature boundary
    + geom_vline(xintercept=T_critical, linetype="dashed", color="#888888", size=0.5, alpha=0.5)
    + labs(x="Temperature (K)", y="Pressure", title="phase-diagram-pt · plotnine · pyplots.ai", color="Phase Boundary")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14, color="#2d2d2d"),
        axis_title=element_text(size=20, color="#2d2d2d"),
        axis_text=element_text(size=16, color="#555555"),
        plot_title=element_text(size=24, weight="bold", color="#1a1a1a"),
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
