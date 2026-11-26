""" anyplot.ai
skewt-logp-atmospheric: Skew-T Log-P Atmospheric Diagram
Library: plotnine 0.15.9 | Python 3.14.10
Quality: 68/100 | Updated: 2026-11-26
"""

import os

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
    geom_segment,
    ggplot,
    labs,
    scale_color_manual,
    scale_linetype_manual,
    scale_x_continuous,
    scale_y_continuous,
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

# Constants: Skew-T geometry and the standard reference families
SKEW_FACTOR = np.tan(np.radians(45))  # 45-degree isotherms
P_SURFACE = 1000  # reference pressure (hPa)
P_MIN = 100
P_MAX = 1050
T_MIN = -80
T_MAX = 50
LABEL_LEVEL = 600  # pressure level (hPa) where the T / Td labels sit
ISOBARS = [1000, 850, 700, 500, 300, 200, 100]
PRESSURE_BREAKS = [1000, 850, 700, 500, 400, 300, 200, 150, 100]

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

# Plot
p_top = df[PRESSURE].min()
p_bottom = df[PRESSURE].max()


def skew_transform(temp, pressure):
    log_p = np.log10(pressure / P_SURFACE)
    return temp + SKEW_FACTOR * log_p * 40


def segments(xs, ps, label):
    return [
        {"x": xs[i], "xend": xs[i + 1], "y": ps[i], "yend": ps[i + 1], "line_type": label} for i in range(len(xs) - 1)
    ]


# Isotherms (skewed 45°)
isotherm_df = pd.DataFrame(
    [
        {
            "x": skew_transform(t_ref, P_MIN),
            "xend": skew_transform(t_ref, P_MAX),
            "y": P_MIN,
            "yend": P_MAX,
            "line_type": "Isotherms (10°C)",
        }
        for t_ref in np.arange(-100, 60, 10)
    ]
)

# Isobars (horizontal reference lines, structural, no legend entry)
isobar_df = pd.DataFrame(
    [{"x": skew_transform(T_MIN - 20, p), "xend": skew_transform(T_MAX + 20, p), "y": p, "yend": p} for p in ISOBARS]
)

# Dry adiabats (constant potential temperature)
dry_rows = []
for theta in np.arange(-40, 100, 10):
    ps = np.arange(P_MIN, P_MAX + 1, 25)
    ts = (theta + 273.15) * (ps / 1000) ** 0.286 - 273.15
    dry_rows += segments(skew_transform(ts, ps), ps, "Dry Adiabats")

# Moist adiabats (saturated adiabatic lapse rate)
moist_rows = []
for theta_e in np.arange(-30, 50, 10):
    xs, ps = [], []
    t_cur = theta_e + 5
    for p in np.arange(P_MAX, P_MIN - 1, -25):
        xs.append(skew_transform(t_cur, p))
        ps.append(p)
        t_cur -= (5.5 if t_cur > 0 else 6.0) * 0.05
    moist_rows += segments(xs, ps, "Moist Adiabats")

# Mixing ratio lines (constant saturation mixing ratio)
mixing_rows = []
for w in [1, 2, 4, 7, 10, 15, 20]:
    xs, ps = [], []
    for p in np.arange(P_MIN + 50, P_MAX + 1, 25):
        e = w * p / (622 + w)
        td = (243.5 * np.log(e / 6.112)) / (17.67 - np.log(e / 6.112))
        if T_MIN - 20 < td < T_MAX + 20:
            xs.append(skew_transform(td, p))
            ps.append(p)
    mixing_rows += segments(xs, ps, "Mixing Ratios")

all_ref_lines = pd.concat([isotherm_df, pd.DataFrame(dry_rows), pd.DataFrame(moist_rows), pd.DataFrame(mixing_rows)])

# Profile data in skewed coordinates; "line_type" matches the reference lines for a unified legend
profile_df = pd.DataFrame(
    {
        "pressure": np.concatenate([df[PRESSURE], df[PRESSURE]]),
        "x": np.concatenate(
            [skew_transform(df[TEMPERATURE], df[PRESSURE]), skew_transform(df[DEWPOINT], df[PRESSURE])]
        ),
        "line_type": ["Temperature"] * len(df) + ["Dewpoint"] * len(df),
    }
)

x_min = skew_transform(T_MIN - 10, P_MAX)
x_max = skew_transform(T_MAX + 10, P_MIN)

LEGEND_ORDER = ["Temperature", "Dewpoint", "Isotherms (10°C)", "Dry Adiabats", "Moist Adiabats", "Mixing Ratios"]
LINE_COLORS = {name: IMPRINT_PALETTE[i] for i, name in enumerate(LEGEND_ORDER)}
LINE_STYLES = dict(zip(LEGEND_ORDER, ["solid", "dashed", "solid", "dashed", "dotted", "dashdot"], strict=True))

profile_df = profile_df.dropna()
complete = df.dropna()
label_row = complete.iloc[(complete[PRESSURE] - LABEL_LEVEL).abs().argmin()]
pressure_breaks = [p for p in PRESSURE_BREAKS if p_top * 0.9 <= p <= p_bottom * 1.1]

plot = (
    ggplot(profile_df, aes(x="x", y="pressure"))
    # Isobars first (background structural lines, no legend entry)
    + geom_segment(
        aes(x="x", xend="xend", y="y", yend="yend"),
        data=isobar_df,
        color=INK_SOFT,
        size=0.7,
        linetype="solid",
        inherit_aes=False,
    )
    # Reference lines with color/linetype aesthetic for legend
    + geom_segment(
        aes(x="x", xend="xend", y="y", yend="yend", color="line_type", linetype="line_type"),
        data=all_ref_lines,
        size=0.6,
        inherit_aes=False,
    )
    # Temperature and dewpoint profiles (drawn on top)
    + geom_line(
        aes(x="x", y="pressure", color="line_type", linetype="line_type", group="line_type"),
        data=profile_df,
        size=2.5,
        inherit_aes=False,
    )
    + scale_color_manual(values=LINE_COLORS, name="Lines", breaks=LEGEND_ORDER)
    + scale_linetype_manual(values=LINE_STYLES, name="Lines", breaks=LEGEND_ORDER)
    + scale_y_continuous(
        trans="log10",
        limits=(p_bottom * 1.1, p_top * 0.9),
        breaks=pressure_breaks if len(pressure_breaks) > 1 else True,
        labels=lambda breaks: [f"{b:g}" for b in breaks],
    )
    + scale_x_continuous(breaks=[], labels=[], limits=(x_min - 10, x_max + 20))
    + annotate(
        "text",
        x=skew_transform(label_row[TEMPERATURE], label_row[PRESSURE]) + 6,
        y=label_row[PRESSURE],
        label="T",
        color=IMPRINT_PALETTE[0],
        size=12,
        fontweight="bold",
    )
    + annotate(
        "text",
        x=skew_transform(label_row[DEWPOINT], label_row[PRESSURE]) - 6,
        y=label_row[PRESSURE],
        label="Td",
        color=IMPRINT_PALETTE[1],
        size=12,
        fontweight="bold",
    )
    + labs(
        x=f"{TEMPERATURE.split(' (')[0]} (°C, skewed 45°)",
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
        axis_title_x=element_text(margin={"t": 8}),
        axis_title_y=element_text(margin={"r": 8}),
        axis_text_x=element_blank(),
        axis_ticks_major_x=element_blank(),
        axis_text_y=element_text(size=8, color=INK_SOFT),
        plot_title=element_text(size=12, ha="center", color=INK),
        legend_position="right",
        legend_title=element_text(size=9, fontweight="bold", color=INK),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_key_width=20,
        legend_key_height=12,
        axis_ticks_major_y=element_line(color=INK_SOFT, size=0.8),
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=6, height=6, units="in", verbose=False)
