"""anyplot.ai
skewt-logp-atmospheric: Skew-T Log-P Atmospheric Diagram
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 75/100 | Updated: 2026-11-26
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_cartesian,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_path,
    geom_point,
    ggplot,
    ggsave,
    ggsize,
    guide_legend,
    guides,
    labs,
    layer_tooltips,
    scale_alpha_manual,
    scale_color_manual,
    scale_linetype_manual,
    scale_size_manual,
    scale_x_continuous,
    scale_y_continuous,
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
X_SPAN = 90  # degC across the bottom axis
PANEL_ASPECT = 0.53  # panel height / width in pixels, sets the skew that draws isotherms at 45 degrees
PRESSURE_TICKS = [1000, 850, 700, 500, 400, 300, 200, 100]  # hPa
TEMPERATURE_TICKS_STEP = 10  # degC
ISOTHERM_TEMPS = np.arange(-120, 60, 10)  # degC at the surface
DRY_ADIABAT_THETAS = np.arange(230, 470, 20)  # K
MOIST_ADIABAT_START_TEMPS = np.arange(-15, 40, 5)  # degC at the surface pressure
MIXING_RATIOS = [1, 2, 4, 7, 10, 16, 24]  # g/kg
MIXING_RATIO_TOP = 600  # hPa, the conventional upper end of mixing ratio lines
EPSILON = 0.622  # molar mass ratio of water vapour to dry air
KAPPA = 0.286  # R/cp of dry air
LATENT_HEAT = 2.5e6  # J/kg
CP_AIR = 1004.0  # J/(kg K)
R_AIR = 287.0  # J/(kg K)
PAD = 0.02  # decades of pressure below the surface level

# Series names shown in the legend
S_TEMP, S_DEW = "Temperature", "Dewpoint"
S_ISO, S_DRY, S_MOIST, S_MIX = "Isotherm", "Dry adiabat", "Moist adiabat", "Mixing ratio"

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
p0 = df[PRESSURE].max()
p_top = df[PRESSURE].min()
y_bottom = -np.log10(p0) - PAD  # the vertical axis is -log10(pressure): pressure decreases upward
y_top = -np.log10(p_top) + PAD
# Skew per decade of pressure so that isotherms rise at 45 degrees on the drawn panel
skew = X_SPAN * PANEL_ASPECT / (y_top - y_bottom)


def skew_x(temp, pressure):
    """Plot x of a temperature at a pressure: isotherms are straight lines at 45 degrees."""
    return temp + skew * np.log10(p0 / pressure)


def sat_vapour_pressure(temp_c):
    return 6.112 * np.exp(17.67 * temp_c / (temp_c + 243.5))


# Axis ranges: the profiles plus a margin, and a fixed span so the angle holds
x_dew = skew_x(df[DEWPOINT], df[PRESSURE])
x_left = np.floor((x_dew.min() - 8) / TEMPERATURE_TICKS_STEP) * TEMPERATURE_TICKS_STEP
x_right = x_left + X_SPAN
p_edge = p0 * 10**PAD  # pressure at the bottom edge of the panel
grid_p = np.logspace(np.log10(p_edge), np.log10(p_top) - PAD, 120)  # hPa, bottom to top

# Reference families in one long table: Series, Line, x, y
ref_parts = []


def add_ref(series, line, temp, pressure):
    ref_parts.append(
        pd.DataFrame(
            {"Series": series, "Line": f"{series} {line}", "x": skew_x(temp, pressure), "y": -np.log10(pressure)}
        )
    )


for t in ISOTHERM_TEMPS:
    add_ref(S_ISO, t, np.full(2, float(t)), grid_p[[0, -1]])
for theta in DRY_ADIABAT_THETAS:
    add_ref(S_DRY, theta, theta * (grid_p / 1000.0) ** KAPPA - 273.15, grid_p)
for t_start in MOIST_ADIABAT_START_TEMPS:
    # Pseudo-adiabat: integrate dT/dp upward from the surface level in small steps
    temp_c, temps = float(t_start), []
    for k, p in enumerate(grid_p):
        if k:
            dp = p - grid_p[k - 1]
            for _ in range(5):
                t_k = temp_c + 273.15
                rs = EPSILON * sat_vapour_pressure(temp_c) / (p - sat_vapour_pressure(temp_c))
                lapse = (R_AIR * t_k + LATENT_HEAT * rs) / (
                    p * (CP_AIR + LATENT_HEAT**2 * rs * EPSILON / (R_AIR * t_k**2))
                )
                temp_c += lapse * dp / 5
        temps.append(temp_c)
    add_ref(S_MOIST, t_start, np.array(temps), grid_p)
mix_p = grid_p[grid_p >= MIXING_RATIO_TOP]
for w in MIXING_RATIOS:
    vapour = mix_p * w / (1000 * EPSILON + w)  # hPa
    ln_ratio = np.log(vapour / 6.112)
    add_ref(S_MIX, w, 243.5 * ln_ratio / (17.67 - ln_ratio), mix_p)
reference = pd.concat(ref_parts, ignore_index=True)

profiles = pd.concat(
    [
        pd.DataFrame(
            {
                "Series": name,
                "Line": name,
                "x": skew_x(df[column], df[PRESSURE]),
                "y": -np.log10(df[PRESSURE]),
                "reading": df[column],
                "level": df[PRESSURE],
            }
        )
        for name, column in [(S_TEMP, TEMPERATURE), (S_DEW, DEWPOINT)]
    ],
    ignore_index=True,
)

# Axis ticks: pressures at their log position, temperatures along the bottom edge
x_tick_temps = np.arange(np.ceil(x_left / 10) * 10, x_right, TEMPERATURE_TICKS_STEP)
x_breaks = skew_x(x_tick_temps, p_edge)
y_breaks = -np.log10(PRESSURE_TICKS)

series = [S_TEMP, S_DEW, S_ISO, S_DRY, S_MOIST, S_MIX]
colors = [C_TEMP, C_DEWPT, INK_SOFT, C_DRY, C_MOIST, C_MIX]
linetypes = ["solid", "dashed", "solid", "dashed", "dotdash", "dotted"]
widths = [2.0, 2.0, 0.4, 0.7, 0.8, 0.9]
alphas = [1.0, 1.0, 0.45, 0.75, 0.8, 0.85]

# Theme-adaptive chrome
GRID = "rgba(26,26,23,0.18)" if THEME == "light" else "rgba(240,239,232,0.18)"
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_border=element_blank(),
    panel_grid_major_x=element_blank(),
    panel_grid_major_y=element_line(color=GRID, size=0.3),
    panel_grid_minor=element_blank(),
    axis_title=element_text(color=INK, size=12),
    axis_text=element_text(color=INK_SOFT, size=10),
    axis_line=element_line(color=INK_SOFT),
    axis_ticks=element_line(color=INK_SOFT),
    plot_title=element_text(color=INK, size=16, face="bold"),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=10),
    legend_title=element_blank(),
    legend_position=[0.985, 0.985],
    legend_justification=[1, 1],
    plot_margin=[8, 8, 8, 8],
)

profile_tooltips = layer_tooltips().line("@Series: @reading °C").line("Pressure: @level hPa")
plot = (
    ggplot(mapping=aes(x="x", y="y", color="Series", linetype="Series", size="Series", alpha="Series"))
    + geom_path(aes(group="Line"), data=reference, tooltips="none")
    + geom_path(data=profiles, tooltips=profile_tooltips)
    + geom_point(aes(color="Series"), data=profiles, size=3.0, alpha=1.0, show_legend=False, tooltips=profile_tooltips)
    + scale_color_manual(values=colors, limits=series)
    + scale_linetype_manual(values=linetypes, limits=series)
    + scale_size_manual(values=widths, limits=series)
    + scale_alpha_manual(values=alphas, limits=series)
    + guides(color=guide_legend(), linetype=guide_legend(), size=guide_legend(), alpha=guide_legend())
    + scale_x_continuous(breaks=list(x_breaks), labels=[f"{t:.0f}" for t in x_tick_temps], expand=[0, 0])
    + scale_y_continuous(breaks=list(y_breaks), labels=[f"{p:,}" for p in PRESSURE_TICKS], expand=[0, 0])
    + coord_cartesian(xlim=[x_left, x_right], ylim=[y_bottom, y_top])
    + labs(x=TEMPERATURE, y=PRESSURE, title="skewt-logp-atmospheric · python · letsplot · anyplot.ai")
    + ggsize(800, 450)
    + anyplot_theme
)

# Save PNG and HTML for both themes
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
