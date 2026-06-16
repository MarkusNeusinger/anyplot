"""anyplot.ai
psychrometric-basic: Psychrometric Chart for HVAC
Library: letsplot 4.10.1 | Python 3.13.12
Quality: 81/100 | Updated: 2026-06-16
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    arrow,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_line,
    geom_path,
    geom_point,
    geom_polygon,
    geom_segment,
    geom_text,
    ggplot,
    ggsize,
    labs,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme-adaptive chrome (only data colors stay constant across themes)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "#E3E0D6" if THEME == "light" else "#33332E"

# Imprint palette — one hue per psychrometric property family
SATURATION = "#009E73"  # brand green — saturation curve & RH family (★ first series)
WET_BULB = "#4467A3"  # blue
ENTHALPY = "#BD8233"  # ochre
VOLUME = "#C475FD"  # lavender
COMFORT = "#2ABCCD"  # cyan — comfort-zone region
PROCESS = "#AE3030"  # matte red — HVAC process path (focal point)

# Constants
P_ATM = 101325.0  # Pa, standard sea-level atmospheric pressure (101.325 kPa)


# Psychrometric equations (ASHRAE Fundamentals)
def saturation_pressure(t):
    t_k = t + 273.15
    if t >= 0:
        ln_ps = (
            -5.8002206e3 / t_k
            + 1.3914993
            - 4.8640239e-2 * t_k
            + 4.1764768e-5 * t_k**2
            - 1.4452093e-8 * t_k**3
            + 6.5459673 * np.log(t_k)
        )
    else:
        ln_ps = (
            -5.6745359e3 / t_k
            + 6.3925247
            - 9.677843e-3 * t_k
            + 6.2215701e-7 * t_k**2
            + 2.0747825e-9 * t_k**3
            - 9.484024e-13 * t_k**4
            + 4.1635019 * np.log(t_k)
        )
    return np.exp(ln_ps)


def humidity_ratio(t_db, rh):
    p_s = saturation_pressure(t_db)
    p_w = rh * p_s
    return 0.621945 * p_w / (P_ATM - p_w)


def wet_bulb_line(t_wb, t_db_range):
    w_sat = humidity_ratio(t_wb, 1.0)
    h_fg, cp_a, cp_w = 2501.0, 1.006, 1.86
    w_values = [
        max((h_fg * w_sat - cp_a * (t_db - t_wb)) / (h_fg + cp_w * t_db - cp_a * t_wb + (cp_w - cp_a) * t_wb), 0)
        for t_db in t_db_range
    ]
    return np.array(w_values)


# Data — relative-humidity curves (10% to 100%)
t_db_fine = np.linspace(-10, 50, 300)
rh_frames = []
for rh_val in np.round(np.arange(0.1, 1.05, 0.1), 1):
    w_vals, t_valid = [], []
    for t in t_db_fine:
        w = humidity_ratio(t, rh_val) * 1000  # g/kg
        if 0 <= w <= 30:
            w_vals.append(w)
            t_valid.append(t)
    rh_frames.append(pd.DataFrame({"t_db": t_valid, "w": w_vals, "group": f"rh{rh_val}"}))
df_rh = pd.concat(rh_frames, ignore_index=True)
# Saturation curve (100% RH) — the prominent upper boundary
df_sat = df_rh[df_rh["group"] == "rh1.0"]
df_rh_inner = df_rh[df_rh["group"] != "rh1.0"]

# Wet-bulb temperature lines
wb_temps = [0, 5, 10, 15, 20, 25, 30, 35]
wb_frames = []
for t_wb in wb_temps:
    t_range = np.linspace(t_wb, min(t_wb + 30, 50), 100)
    w_vals = wet_bulb_line(t_wb, t_range) * 1000
    mask = (w_vals >= 0) & (w_vals <= 30)
    wb_frames.append(pd.DataFrame({"t_db": t_range[mask], "w": w_vals[mask], "group": f"wb{t_wb}"}))
df_wb = pd.concat(wb_frames, ignore_index=True)

# Constant-enthalpy lines (kJ/kg)
enthalpy_values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110]
enth_frames = []
for h_target in enthalpy_values:
    t_points, w_points = [], []
    for t in np.linspace(-10, 50, 200):
        w_gkg = (h_target - 1.006 * t) / (2501.0 + 1.86 * t) * 1000
        if 0 <= w_gkg <= 30:
            t_points.append(t)
            w_points.append(w_gkg)
    if len(t_points) > 1:
        enth_frames.append(pd.DataFrame({"t_db": t_points, "w": w_points, "group": f"h{h_target}"}))
df_enth = pd.concat(enth_frames, ignore_index=True)

# Constant specific-volume lines (m3/kg)
vol_values = [0.78, 0.80, 0.82, 0.84, 0.86, 0.88, 0.90, 0.92, 0.94]
vol_frames = []
for v_target in vol_values:
    t_points, w_points = [], []
    for t in np.linspace(-10, 50, 200):
        w_gkg = (v_target * (P_ATM / 1000) / (0.287042 * (t + 273.15)) - 1) / 1.6078 * 1000
        if 0 <= w_gkg <= 30:
            t_points.append(t)
            w_points.append(w_gkg)
    if len(t_points) > 1:
        vol_frames.append(pd.DataFrame({"t_db": t_points, "w": w_points, "group": f"v{v_target}"}))
df_vol = pd.concat(vol_frames, ignore_index=True)

# Comfort zone polygon (20-26 C, 30-60% RH)
df_comfort = pd.DataFrame(
    {
        "t_db": [20, 26, 26, 20],
        "w": [
            humidity_ratio(20, 0.3) * 1000,
            humidity_ratio(26, 0.3) * 1000,
            humidity_ratio(26, 0.6) * 1000,
            humidity_ratio(20, 0.6) * 1000,
        ],
    }
)

# HVAC process path: cooling + dehumidification (32 C / 50% RH -> 24 C / 50% RH)
s1_t, s2_t = 32, 24
df_process = pd.DataFrame(
    {"t_db": [s1_t, s2_t], "w": [humidity_ratio(s1_t, 0.50) * 1000, humidity_ratio(s2_t, 0.50) * 1000]}
)

# Direct labels (all property lines labelled on-chart, not in a legend)
# RH labels — staggered along their curves to avoid the crowded upper-left
rh_label_t = {0.1: 44, 0.2: 44, 0.3: 40, 0.4: 35, 0.5: 31, 0.6: 28, 0.7: 24, 0.8: 21, 0.9: 17, 1.0: 12}
rh_labels = []
for rh_val, t_label in rh_label_t.items():
    w_label = humidity_ratio(t_label, rh_val) * 1000
    if w_label <= 28:
        rh_labels.append({"t_db": t_label, "w": w_label, "label": f"{int(rh_val * 100)}%"})
df_rh_labels = pd.DataFrame(rh_labels)

# Wet-bulb labels — placed below the saturation curve, only every other line to declutter
df_wb_labels = pd.DataFrame(
    [
        {"t_db": t_wb + 3.2, "w": humidity_ratio(t_wb, 1.0) * 1000 - 0.6, "label": f"{t_wb}°C wb"}
        for t_wb in wb_temps
        if t_wb % 10 == 0 and humidity_ratio(t_wb, 1.0) * 1000 <= 27
    ]
)

# Enthalpy labels — on the left edge
df_enth_labels = pd.DataFrame(
    [
        {"t_db": -8, "w": w_gkg, "label": f"{h} kJ/kg"}
        for h in enthalpy_values
        for w_gkg in [(h - 1.006 * (-5)) / (2501.0 + 1.86 * (-5)) * 1000]
        if 0 < w_gkg <= 28
    ]
)

# Specific-volume labels — on the right edge
df_vol_labels = pd.DataFrame(
    [
        {"t_db": 46, "w": w_gkg, "label": f"{v} m³/kg"}
        for v in vol_values
        for w_gkg in [(v * (P_ATM / 1000) / (0.287042 * (45 + 273.15)) - 1) / 1.6078 * 1000]
        if 0 < w_gkg <= 28
    ]
)

# Plot
plot = (
    ggplot()
    # Comfort zone region
    + geom_polygon(data=df_comfort, mapping=aes(x="t_db", y="w"), fill=COMFORT, alpha=0.16, color=COMFORT, size=1.0)
    # Specific-volume lines (secondary family)
    + geom_line(data=df_vol, mapping=aes(x="t_db", y="w", group="group"), color=VOLUME, size=0.6, alpha=0.7)
    # Enthalpy lines (secondary family)
    + geom_line(data=df_enth, mapping=aes(x="t_db", y="w", group="group"), color=ENTHALPY, size=0.6, alpha=0.7)
    # Wet-bulb lines
    + geom_line(data=df_wb, mapping=aes(x="t_db", y="w", group="group"), color=WET_BULB, size=0.7, alpha=0.7)
    # Inner RH curves (10-90%)
    + geom_line(data=df_rh_inner, mapping=aes(x="t_db", y="w", group="group"), color=INK_MUTED, size=0.7, alpha=0.7)
    # Saturation curve (100% RH) — prominent upper boundary
    + geom_line(data=df_sat, mapping=aes(x="t_db", y="w"), color=SATURATION, size=2.4)
    # HVAC process path with arrowhead (focal point)
    + geom_path(
        data=df_process,
        mapping=aes(x="t_db", y="w"),
        color=PROCESS,
        size=2.6,
        arrow=arrow(type="closed", length=14, angle=20),
    )
    + geom_point(data=df_process, mapping=aes(x="t_db", y="w"), color=PROCESS, size=5.5, shape=21, fill=PAGE_BG)
    # Direct labels
    + geom_text(data=df_rh_labels, mapping=aes(x="t_db", y="w", label="label"), size=4.6, color=INK_MUTED)
    + geom_text(data=df_wb_labels, mapping=aes(x="t_db", y="w", label="label"), size=4.2, color=WET_BULB)
    + geom_text(data=df_enth_labels, mapping=aes(x="t_db", y="w", label="label"), size=4.2, color=ENTHALPY, hjust=1)
    + geom_text(data=df_vol_labels, mapping=aes(x="t_db", y="w", label="label"), size=4.2, color=VOLUME, hjust=0)
    + geom_text(
        data=pd.DataFrame({"t_db": [23], "w": [7.6], "label": ["Comfort\nzone"]}),
        mapping=aes(x="t_db", y="w", label="label"),
        size=6.4,
        color=COMFORT,
        fontface="bold",
    )
    + geom_text(
        data=pd.DataFrame({"t_db": [40.5], "w": [16.5], "label": ["Cooling &\ndehumidification"]}),
        mapping=aes(x="t_db", y="w", label="label"),
        size=5.4,
        color=PROCESS,
        fontface="bold",
    )
    + geom_segment(
        data=pd.DataFrame({"x": [38.5], "xend": [33.0], "y": [16.0], "yend": [14.2]}),
        mapping=aes(x="x", y="y", xend="xend", yend="yend"),
        color=PROCESS,
        size=0.6,
        alpha=0.7,
    )
    + scale_x_continuous(limits=[-10, 51], breaks=list(range(-10, 55, 5)))
    + scale_y_continuous(limits=[0, 30], breaks=list(range(0, 35, 5)))
    + labs(
        x="Dry-bulb temperature (°C)",
        y="Humidity ratio (g/kg)",
        title="psychrometric-basic · python · letsplot · anyplot.ai",
    )
    + theme_minimal()
    + theme(
        plot_title=element_text(size=16, face="bold", color=INK),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        legend_position="none",
        panel_grid_major=element_line(color=GRID, size=0.4),
        panel_grid_minor=element_blank(),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    )
    + ggsize(800, 450)
)

# Save (3200 × 1800 px at scale=4) + interactive HTML
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
