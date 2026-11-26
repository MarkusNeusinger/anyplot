""" anyplot.ai
skewt-logp-atmospheric: Skew-T Log-P Atmospheric Diagram
Library: plotnine 0.15.9 | Python 3.14.10
Quality: 85/100 | Updated: 2026-11-26
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_hline,
    geom_path,
    ggplot,
    guide_legend,
    guides,
    labs,
    scale_color_manual,
    scale_linetype_manual,
    scale_x_continuous,
    scale_y_reverse,
    theme,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette (canonical order)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants: Skew-T geometry (isotherm shift per pressure decade, in degrees C; coord_fixed makes it 45 degrees)
SKEW = 80

# Column constants
PRESSURE = "Pressure (hPa)"  # role: pressure
TEMPERATURE = "Temperature (°C)"  # role: temperature
DEWPOINT = "Dewpoint (°C)"  # role: dewpoint

# Data: replace this block with your own sounding, for example df = pd.read_csv("sounding.csv")
np.random.seed(42)
pressure_levels = np.array(
    [1000, 975, 950, 925, 900, 875, 850, 825, 800, 775, 750, 700, 650]
    + [600, 550, 500, 450, 400, 350, 300, 250, 200, 175, 150, 125, 100]
)

# Temperature profile (realistic lapse rate with tropopause)
temp_profile = []
for p in pressure_levels:
    altitude_km = 44.3308 * (1 - (p / 1013.25) ** 0.190284)
    if p > 200:  # Troposphere
        t = 25 - 6.5 * altitude_km + np.random.normal(0, 1)
    else:  # Stratosphere (isothermal/slight warming)
        t = -55 + (200 - p) * 0.02 + np.random.normal(0, 0.5)
    temp_profile.append(t)

# Dewpoint profile (moisture decreases with altitude)
dewpoint_profile = []
for p, t in zip(pressure_levels, temp_profile, strict=True):
    if p > 700:
        depression = 5 + np.random.uniform(0, 5)
    elif p > 400:
        depression = 15 + np.random.uniform(0, 10)
    else:
        depression = 30 + np.random.uniform(0, 15)
    dewpoint_profile.append(t - depression)

df = pd.DataFrame({PRESSURE: pressure_levels, TEMPERATURE: temp_profile, DEWPOINT: dewpoint_profile})

# Plot: vertical coordinate is log10(pressure), drawn reversed so the surface sits at the bottom
y_bottom = np.log10(df[PRESSURE].max())
y_top = np.log10(df[PRESSURE].min())

# Isotherms: straight lines, skewed by SKEW degrees per pressure decade
iso_t = np.arange(-120, 60, 10)
isotherms = pd.DataFrame(
    {
        "curve": np.repeat([f"iso{t}" for t in iso_t], 2),
        "y": np.tile([y_bottom, y_top], len(iso_t)),
        "t": np.repeat(iso_t, 2),
        "family": "Isotherms (10 °C)",
    }
)

# Dry adiabats: constant potential temperature, T = theta * (p / 1000)^0.286
dry_theta = np.arange(-40, 180, 20)
dry_y = np.linspace(y_bottom, y_top, 40)
dry = pd.DataFrame(
    {
        "curve": np.repeat([f"dry{th}" for th in dry_theta], len(dry_y)),
        "y": np.tile(dry_y, len(dry_theta)),
        "t": ((np.repeat(dry_theta, len(dry_y)) + 273.15) * (10 ** np.tile(dry_y, len(dry_theta)) / 1000) ** 0.286)
        - 273.15,
        "family": "Dry adiabats",
    }
)

# Moist adiabats: integrate the saturated lapse rate upward from 1000 hPa
moist_start = np.arange(-10, 41, 10).astype(float)
moist_y = np.linspace(y_bottom, y_top, 150)
t_moist = np.empty((len(moist_y), len(moist_start)))
t_moist[0] = moist_start + 273.15
for k in range(len(moist_y) - 1):
    p_k = 10 ** moist_y[k]
    p_next = 10 ** moist_y[k + 1]
    t_k = t_moist[k]
    e_sat = 6.112 * np.exp(17.67 * (t_k - 273.15) / (t_k - 273.15 + 243.5))
    r_sat = 0.622 * e_sat / (p_k - e_sat)
    dt_dp = (287 * t_k + 2.5e6 * r_sat) / (p_k * (1005 + 2.5e6**2 * r_sat * 0.622 / (287 * t_k**2)))
    t_moist[k + 1] = t_k + dt_dp * (p_next - p_k)
moist = pd.DataFrame(
    {
        "curve": np.tile([f"moist{int(t0)}" for t0 in moist_start], len(moist_y)),
        "y": np.repeat(moist_y, len(moist_start)),
        "t": (t_moist - 273.15).ravel(),
        "family": "Moist adiabats",
    }
)

# Mixing ratio lines: dewpoint of air holding w g/kg at each pressure, from the surface to 600 hPa
mix_w = np.array([1, 2, 4, 8, 12, 16, 20]) / 1000
mix_y = np.linspace(y_bottom, np.log10(600), 20)
vapor = np.outer(10**mix_y, mix_w / (0.622 + mix_w)).ravel(order="F")
ln_e = np.log(vapor / 6.112)
mixing = pd.DataFrame(
    {
        "curve": np.repeat([f"mix{int(w * 1000)}" for w in mix_w], len(mix_y)),
        "y": np.tile(mix_y, len(mix_w)),
        "t": 243.5 * ln_e / (17.67 - ln_e),
        "family": "Mixing ratios",
    }
)

# Sounding profiles in the same long format
profile = pd.DataFrame(
    {
        "curve": np.repeat(["Temperature", "Dewpoint"], len(df)),
        "y": np.tile(np.log10(df[PRESSURE]), 2),
        "t": np.concatenate([df[TEMPERATURE], df[DEWPOINT]]),
        "family": np.repeat(["Temperature", "Dewpoint"], len(df)),
    }
)

# Skew the temperature axis: lines at lower pressure shift to the right
FAMILIES = ["Temperature", "Dewpoint", "Isotherms (10 °C)", "Dry adiabats", "Moist adiabats", "Mixing ratios"]
LINE_COLORS = dict(zip(FAMILIES, IMPRINT_PALETTE, strict=False))
LINE_STYLES = dict(zip(FAMILIES, ["solid", "dashed", "solid", "dashed", "dotted", "dashdot"], strict=True))
reference = pd.concat([isotherms, dry, moist, mixing], ignore_index=True)
sounding = profile
for frame in (reference, sounding):
    frame["x"] = frame["t"] + SKEW * (y_bottom - frame["y"])
    frame["family"] = pd.Categorical(frame["family"], categories=FAMILIES)
x_lo = np.floor(sounding["x"].min() / 10) * 10 - 10
x_hi = np.ceil(sounding["x"].max() / 10) * 10 + 20

# Isobars and pressure ticks at one tenth of the surface pressure's order of magnitude
isobar_step = 10 ** (np.floor(np.log10(df[PRESSURE].max())) - 1)
isobar_levels = np.arange(np.ceil(df[PRESSURE].min() / isobar_step) * isobar_step, df[PRESSURE].max() + 1, isobar_step)
tick_step = 10 ** np.floor(np.log10((x_hi - x_lo) / 5))
temperature_ticks = np.arange(np.ceil(x_lo / tick_step) * tick_step, x_hi, tick_step)

plot = (
    ggplot(mapping=aes(x="x", y="y", group="curve", color="family", linetype="family"))
    + geom_hline(yintercept=np.log10(isobar_levels), color=INK_SOFT, size=0.3, alpha=0.5)
    + geom_path(data=reference, size=0.55, alpha=0.7)
    + geom_path(data=sounding, size=1.6)
    + scale_color_manual(values=LINE_COLORS, breaks=FAMILIES, name="Line")
    + scale_linetype_manual(values=LINE_STYLES, breaks=FAMILIES, name="Line")
    + scale_x_continuous(breaks=temperature_ticks, expand=(0, 0))
    + scale_y_reverse(breaks=np.log10(isobar_levels), labels=[f"{p:g}" for p in isobar_levels], expand=(0, 0))
    + coord_fixed(ratio=SKEW, xlim=(x_lo, x_hi), ylim=(y_bottom, y_top), expand=False)
    + guides(color=guide_legend(override_aes={"size": 1.2, "alpha": 1}))
    + labs(
        x="Temperature at 1000 hPa (°C), isotherms skewed 45°",
        y=PRESSURE,
        title="skewt-logp-atmospheric · python · plotnine · anyplot.ai",
    )
    + theme(
        figure_size=(6, 6),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        panel_border=element_rect(color=INK_SOFT, fill=None),
        axis_line=element_line(color=INK_SOFT, size=0.8),
        text=element_text(size=8),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        axis_ticks_major=element_line(color=INK_SOFT, size=0.8),
        plot_title=element_text(size=11, ha="center", color=INK),
        legend_position="bottom",
        legend_title=element_text(size=9, fontweight="bold", color=INK),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color="none"),
        legend_key=element_rect(fill=ELEVATED_BG, color="none"),
        legend_key_width=26,
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=6, height=6, units="in", verbose=False)
