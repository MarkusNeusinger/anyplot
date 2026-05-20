"""anyplot.ai
skewt-logp-atmospheric: Skew-T Log-P Atmospheric Diagram
Library: letsplot | Python 3.13
Quality: pending | Created: 2026-05-20
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
    geom_path,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_y_log10,
    scale_y_reverse,
    theme,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Atmospheric sounding data (synthetic radiosonde profile)
np.random.seed(42)

pressure = np.array([1000, 950, 900, 850, 800, 750, 700, 650, 600, 550, 500, 450, 400, 350, 300, 250, 200, 150, 100])
temperature = np.array([25, 22, 18, 14, 10, 6, 2, -3, -8, -14, -21, -29, -38, -47, -55, -58, -56, -55, -56])
dewpoint = np.array([18, 16, 12, 8, 4, 0, -5, -12, -20, -28, -35, -42, -50, -58, -65, -70, -72, -75, -78])

# Skew-T coordinate transformation: x_plot = T + skew_factor * log10(p0/p)
p0 = 1000
skew_factor = 40

log_pressure = np.log10(p0 / pressure)
temp_skewed = temperature + skew_factor * log_pressure
dewpoint_skewed = dewpoint + skew_factor * log_pressure

df_temp = pd.DataFrame({"pressure": pressure, "value": temp_skewed})
df_dewpoint = pd.DataFrame({"pressure": pressure, "value": dewpoint_skewed})

# Generate isotherms (skewed 45-degree temperature reference lines)
isotherm_temps = np.arange(-80, 50, 10)
p_range = np.array([1000, 100])
isotherm_data = []
for t in isotherm_temps:
    log_p_vals = np.log10(p0 / p_range)
    t_skewed = t + skew_factor * log_p_vals
    isotherm_data.append({"x_start": t_skewed[0], "x_end": t_skewed[1], "y_start": p_range[0], "y_end": p_range[1]})
df_isotherms = pd.DataFrame(isotherm_data)

# Generate dry adiabats (constant potential temperature lines)
dry_adiabat_thetas = np.arange(250, 450, 20)
p_levels = np.linspace(1000, 100, 50)
dry_adiabat_data = []
for theta in dry_adiabat_thetas:
    temps = (theta * (p_levels / p0) ** 0.286) - 273.15
    log_p_vals = np.log10(p0 / p_levels)
    temps_skewed = temps + skew_factor * log_p_vals
    for i in range(len(p_levels)):
        dry_adiabat_data.append({"pressure": p_levels[i], "temp_skewed": temps_skewed[i], "theta": theta})
df_dry_adiabats = pd.DataFrame(dry_adiabat_data)

# Generate moist adiabats (equivalent potential temperature lines)
moist_adiabat_theta_e = np.arange(280, 360, 10)
moist_adiabat_data = []
for theta_e in moist_adiabat_theta_e:
    t_surface = theta_e - 273.15
    for p in p_levels:
        height_factor = np.log(p0 / p) * 2.5
        t_moist = t_surface - 6.5 * height_factor * 0.8
        log_p_val = np.log10(p0 / p)
        t_skewed = t_moist + skew_factor * log_p_val
        moist_adiabat_data.append({"pressure": p, "temp_skewed": t_skewed, "theta_e": theta_e})
df_moist_adiabats = pd.DataFrame(moist_adiabat_data)

# Generate mixing ratio lines (constant water vapor mixing ratio)
mixing_ratios = [1, 2, 4, 7, 10, 15, 20]
mixing_data = []
for ws in mixing_ratios:
    for p in p_levels[::5]:
        t = 35 * np.log10(ws * p / 622) - 20
        log_p_val = np.log10(p0 / p)
        t_skewed = t + skew_factor * log_p_val
        mixing_data.append({"pressure": p, "temp_skewed": t_skewed, "ws": ws})
df_mixing = pd.DataFrame(mixing_data)

# Theme-adaptive chrome
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_blank(),
    panel_grid_minor=element_blank(),
    axis_title=element_text(color=INK, size=12),
    axis_text=element_text(color=INK_SOFT, size=10),
    axis_line=element_line(color=INK_SOFT),
    plot_title=element_text(color=INK, size=14),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=10),
    legend_title=element_text(color=INK),
)

plot = (
    ggplot()
    # Isotherms (gray diagonal reference lines)
    + geom_segment(
        aes(x="x_start", xend="x_end", y="y_start", yend="y_end"),
        data=df_isotherms,
        color=INK_SOFT,
        size=0.4,
        alpha=0.5,
    )
    # Dry adiabats - Okabe-Ito vermillion dashed
    + geom_path(
        aes(x="temp_skewed", y="pressure", group="theta"),
        data=df_dry_adiabats,
        color="#D55E00",
        size=0.7,
        alpha=0.7,
        linetype="dashed",
    )
    # Moist adiabats - Okabe-Ito reddish purple dotdash
    + geom_path(
        aes(x="temp_skewed", y="pressure", group="theta_e"),
        data=df_moist_adiabats,
        color="#CC79A7",
        size=0.7,
        alpha=0.7,
        linetype="dotdash",
    )
    # Mixing ratio lines - Okabe-Ito green dotted
    + geom_path(
        aes(x="temp_skewed", y="pressure", group="ws"),
        data=df_mixing,
        color="#009E73",
        size=0.7,
        alpha=0.7,
        linetype="dotted",
    )
    # Temperature profile - solid red (meteorological convention)
    + geom_path(aes(x="value", y="pressure"), data=df_temp, color="#DC2626", size=2.0)
    # Dewpoint profile - dashed sky blue
    + geom_path(aes(x="value", y="pressure"), data=df_dewpoint, color="#56B4E9", size=2.0, linetype="dashed")
    # Data points on profiles for clarity
    + geom_point(aes(x="value", y="pressure"), data=df_temp, color="#DC2626", size=3.0)
    + geom_point(aes(x="value", y="pressure"), data=df_dewpoint, color="#56B4E9", size=3.0)
    # Logarithmic inverted pressure axis
    + scale_y_log10()
    + scale_y_reverse(limits=[1000, 100])
    + labs(x="Temperature (°C)", y="Pressure (hPa)", title="skewt-logp-atmospheric · python · letsplot · anyplot.ai")
    + ggsize(800, 450)
    + anyplot_theme
)

# Manual legend (positioned upper-right in skewed coordinate space)
legend_x_start = 95
legend_x_end = 112
legend_text_x = 114
legend_entries = [
    {"label": "Temperature", "color": "#DC2626", "linetype": "solid", "size": 2.0, "y": 125},
    {"label": "Dewpoint", "color": "#56B4E9", "linetype": "dashed", "size": 2.0, "y": 140},
    {"label": "Dry Adiabat", "color": "#D55E00", "linetype": "dashed", "size": 1.2, "y": 158},
    {"label": "Moist Adiabat", "color": "#CC79A7", "linetype": "dotdash", "size": 1.2, "y": 178},
    {"label": "Mixing Ratio", "color": "#009E73", "linetype": "dotted", "size": 1.2, "y": 200},
]

for entry in legend_entries:
    plot = plot + geom_segment(
        aes(x="x_start", xend="x_end", y="y", yend="y"),
        data=pd.DataFrame([{"x_start": legend_x_start, "x_end": legend_x_end, "y": entry["y"]}]),
        color=entry["color"],
        size=entry["size"],
        linetype=entry["linetype"],
    )
    plot = plot + geom_text(x=legend_text_x, y=entry["y"], label=entry["label"], color=INK, size=8, hjust=0)

# Save PNG and HTML for both themes
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
