"""anyplot.ai
skewt-logp-atmospheric: Skew-T Log-P Atmospheric Diagram
Library: letsplot 4.10.1 | Python 3.13.13
Quality: pending | Updated: 2026-05-21
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
    layer_tooltips,
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

# Imprint palette (all eight positions, canonical order)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
C_TEMP = IMPRINT_PALETTE[0]  # temperature profile (primary series)
C_DEWPT = IMPRINT_PALETTE[1]  # dewpoint profile
C_DRY = IMPRINT_PALETTE[4]  # dry adiabats (background reference)
C_MOIST = IMPRINT_PALETTE[3]  # moist adiabats (background reference)
C_MIX = IMPRINT_PALETTE[5]  # mixing ratio lines (background reference)

# Constants
SKEW_FACTOR = 40  # x shift per decade of pressure: gives the 45-degree isotherms
ISOTHERM_TEMPS = np.arange(-80, 50, 10)  # degC
DRY_ADIABAT_THETAS = np.arange(250, 450, 20)  # K
MOIST_ADIABAT_THETA_E = np.arange(280, 360, 10)  # K
MIXING_RATIOS = [1, 2, 4, 7, 10, 15, 20]  # g/kg

# Columns: set these to your table's column names
PRESSURE = "Pressure (hPa)"  # role: pressure
TEMPERATURE = "Temperature (°C)"  # role: temperature
DEWPOINT = "Dewpoint (°C)"  # role: dewpoint

# Data: replace this block with your own table, for example df = pd.read_csv("sounding.csv")
df = pd.DataFrame(
    {
        PRESSURE: [1000, 950, 900, 850, 800, 750, 700, 650, 600, 550, 500, 450, 400, 350, 300, 250, 200, 150, 100],
        TEMPERATURE: [25, 22, 18, 14, 10, 6, 2, -3, -8, -14, -21, -29, -38, -47, -55, -58, -56, -55, -56],
        DEWPOINT: [18, 16, 12, 8, 4, 0, -5, -12, -20, -28, -35, -42, -50, -58, -65, -70, -72, -75, -78],
    }
)

# Plot: reads only df and the constants above
# Skew-T coordinate transformation: x_plot = T + SKEW_FACTOR * log10(p0 / p)
p0 = df[PRESSURE].max()
p_top = df[PRESSURE].min()
p_range = np.array([p0, p_top])
p_levels = np.linspace(p0, p_top, 50)
skew_span = SKEW_FACTOR * np.log10(p0 / p_top)  # skew shift at the top of the diagram

df_temp = pd.DataFrame(
    {
        "pressure": df[PRESSURE],
        "temp": df[TEMPERATURE],
        "value": df[TEMPERATURE] + SKEW_FACTOR * np.log10(p0 / df[PRESSURE]),
    }
)
df_dewpoint = pd.DataFrame(
    {"pressure": df[PRESSURE], "dewpt": df[DEWPOINT], "value": df[DEWPOINT] + SKEW_FACTOR * np.log10(p0 / df[PRESSURE])}
)

# Isotherms (skewed 45-degree temperature reference lines)
isotherm_data = []
for t in ISOTHERM_TEMPS:
    t_skewed = t + SKEW_FACTOR * np.log10(p0 / p_range)
    isotherm_data.append({"x_start": t_skewed[0], "x_end": t_skewed[1], "y_start": p_range[0], "y_end": p_range[1]})
df_isotherms = pd.DataFrame(isotherm_data)

# Dry adiabats (constant potential temperature lines)
dry_adiabat_data = []
for theta in DRY_ADIABAT_THETAS:
    temps = (theta * (p_levels / p0) ** 0.286) - 273.15
    temps_skewed = temps + SKEW_FACTOR * np.log10(p0 / p_levels)
    for i in range(len(p_levels)):
        dry_adiabat_data.append({"pressure": p_levels[i], "temp_skewed": temps_skewed[i], "theta": theta})
df_dry_adiabats = pd.DataFrame(dry_adiabat_data)

# Moist adiabats (equivalent potential temperature lines)
moist_adiabat_data = []
for theta_e in MOIST_ADIABAT_THETA_E:
    t_surface = theta_e - 273.15
    for p in p_levels:
        height_factor = np.log(p0 / p) * 2.5
        t_moist = t_surface - 6.5 * height_factor * 0.8
        t_skewed = t_moist + SKEW_FACTOR * np.log10(p0 / p)
        moist_adiabat_data.append({"pressure": p, "temp_skewed": t_skewed, "theta_e": theta_e})
df_moist_adiabats = pd.DataFrame(moist_adiabat_data)

# Mixing ratio lines (constant water vapor mixing ratio)
mixing_data = []
for ws in MIXING_RATIOS:
    for p in p_levels[::5]:
        t = 35 * np.log10(ws * p / 622) - 20
        t_skewed = t + SKEW_FACTOR * np.log10(p0 / p)
        mixing_data.append({"pressure": p, "temp_skewed": t_skewed, "ws": ws})
df_mixing = pd.DataFrame(mixing_data)

# Theme-adaptive chrome
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_border=element_blank(),
    panel_grid_major=element_blank(),
    panel_grid_minor=element_blank(),
    axis_title=element_text(color=INK, size=12),
    axis_text=element_text(color=INK_SOFT, size=10),
    axis_line=element_line(color=INK_SOFT),
    axis_ticks=element_line(color=INK_SOFT),
    plot_title=element_text(color=INK, size=16, face="bold"),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=10),
    legend_title=element_text(color=INK),
    plot_margin=[8, 8, 8, 8],
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
        tooltips="none",
    )
    # Dry adiabats — dashed
    + geom_path(
        aes(x="temp_skewed", y="pressure", group="theta"),
        data=df_dry_adiabats,
        color=C_DRY,
        size=0.7,
        alpha=0.7,
        linetype="dashed",
        tooltips="none",
    )
    # Moist adiabats — dotdash
    + geom_path(
        aes(x="temp_skewed", y="pressure", group="theta_e"),
        data=df_moist_adiabats,
        color=C_MOIST,
        size=0.7,
        alpha=0.7,
        linetype="dotdash",
        tooltips="none",
    )
    # Mixing ratio lines — dotted
    + geom_path(
        aes(x="temp_skewed", y="pressure", group="ws"),
        data=df_mixing,
        color=C_MIX,
        size=0.8,
        alpha=0.8,
        linetype="dotted",
        tooltips="none",
    )
    # Temperature profile — green solid (primary series)
    + geom_path(
        aes(x="value", y="pressure"),
        data=df_temp,
        color=C_TEMP,
        size=2.0,
        tooltips=layer_tooltips().line("Temperature: @temp°C").line("Pressure: @pressure hPa"),
    )
    # Dewpoint profile — dashed (secondary series)
    + geom_path(
        aes(x="value", y="pressure"),
        data=df_dewpoint,
        color=C_DEWPT,
        size=2.0,
        linetype="dashed",
        tooltips=layer_tooltips().line("Dewpoint: @dewpt°C").line("Pressure: @pressure hPa"),
    )
    # Data points on profiles for clarity
    + geom_point(
        aes(x="value", y="pressure"),
        data=df_temp,
        color=C_TEMP,
        size=3.0,
        tooltips=layer_tooltips().line("Temperature: @temp°C").line("Pressure: @pressure hPa"),
    )
    + geom_point(
        aes(x="value", y="pressure"),
        data=df_dewpoint,
        color=C_DEWPT,
        size=3.0,
        tooltips=layer_tooltips().line("Dewpoint: @dewpt°C").line("Pressure: @pressure hPa"),
    )
    # Logarithmic inverted pressure axis
    + scale_y_log10()
    + scale_y_reverse(limits=[p0, p_top])
    + labs(x=TEMPERATURE, y=PRESSURE, title="skewt-logp-atmospheric · python · letsplot · anyplot.ai")
    + ggsize(800, 450)
    + anyplot_theme
)

# Manual legend (positioned upper-right in skewed coordinate space, from the diagram's own extent)
legend_x_start = skew_span * 2.375
legend_x_end = skew_span * 2.8
legend_text_x = skew_span * 2.85
legend_entries = [
    {"label": "Temperature", "color": C_TEMP, "linetype": "solid", "size": 2.0, "y": p_top * 1.1},
    {"label": "Dewpoint", "color": C_DEWPT, "linetype": "dashed", "size": 2.0, "y": p_top * 1.45},
    {"label": "Dry Adiabat", "color": C_DRY, "linetype": "dashed", "size": 1.2, "y": p_top * 1.9},
    {"label": "Moist Adiabat", "color": C_MOIST, "linetype": "dotdash", "size": 1.2, "y": p_top * 2.5},
    {"label": "Mixing Ratio", "color": C_MIX, "linetype": "dotted", "size": 1.2, "y": p_top * 3.3},
]

for entry in legend_entries:
    plot = plot + geom_segment(
        aes(x="x_start", xend="x_end", y="y", yend="y"),
        data=pd.DataFrame([{"x_start": legend_x_start, "x_end": legend_x_end, "y": entry["y"]}]),
        color=entry["color"],
        size=entry["size"],
        linetype=entry["linetype"],
        tooltips="none",
    )
    plot = plot + geom_text(x=legend_text_x, y=entry["y"], label=entry["label"], color=INK, size=6, hjust=0)

# Save PNG and HTML for both themes
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
