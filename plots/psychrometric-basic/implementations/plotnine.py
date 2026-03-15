""" pyplots.ai
psychrometric-basic: Psychrometric Chart for HVAC
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 82/100 | Created: 2026-03-15
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    arrow,
    coord_cartesian,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_line,
    geom_point,
    geom_polygon,
    geom_segment,
    geom_text,
    ggplot,
    labs,
    scale_color_identity,
    scale_linetype_identity,
    scale_size_identity,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Constants
PATM = 101.325  # kPa, standard atmospheric pressure
T_MIN, T_MAX = -10, 50  # Dry-bulb temperature range (°C)
W_MAX = 30  # Max humidity ratio for chart (g/kg)


# Psychrometric calculations
def sat_pressure(t):
    """Saturation vapor pressure (kPa) using Magnus formula."""
    return 0.61078 * np.exp(17.27 * t / (t + 237.3))


def humidity_ratio(t, rh):
    """Humidity ratio (g/kg) from dry-bulb temp and relative humidity."""
    pws = sat_pressure(t)
    pw = rh / 100.0 * pws
    pw = np.minimum(pw, PATM - 0.01)
    return 622.0 * pw / (PATM - pw)


def enthalpy_w(t, h):
    """Humidity ratio (g/kg) for constant enthalpy h (kJ/kg dry air)."""
    return (h - 1.006 * t) / (2.501 + 0.00186 * t)


def specific_volume_w(t, v):
    """Humidity ratio (g/kg) for constant specific volume v (m³/kg)."""
    return (v * PATM / (0.287055 * (t + 273.15)) - 1.0) / 1.6078 * 1000.0


# Data: Relative humidity curves (10% to 100%)
t_range = np.linspace(T_MIN, T_MAX, 300)
rh_frames = []
for rh in range(10, 110, 10):
    w = humidity_ratio(t_range, rh)
    mask = (w >= 0) & (w <= W_MAX)
    df_rh = pd.DataFrame({"t": t_range[mask], "w": w[mask], "group": f"RH {rh}%", "rh": rh})
    rh_frames.append(df_rh)
df_rh_all = pd.concat(rh_frames, ignore_index=True)
df_rh_all["color"] = np.where(df_rh_all["rh"] == 100, "#306998", "#8BAEC4")
df_rh_all["lw"] = np.where(df_rh_all["rh"] == 100, 1.8, 0.6)

# RH labels placed along curves at staggered temperatures to avoid crowding
rh_labels = []
label_temps = {10: 46, 20: 40, 30: 35, 40: 32, 50: 30, 60: 28, 70: 25, 80: 22, 90: 18, 100: 14}
for rh, t_label in label_temps.items():
    w_label = humidity_ratio(np.array([t_label]), rh)[0]
    if 0 < w_label < W_MAX:
        rh_labels.append({"t": t_label, "w": w_label + 0.7, "label": f"{rh}%"})
df_rh_labels = pd.DataFrame(rh_labels)

# Data: Wet-bulb temperature lines
wb_frames = []
for twb in range(-5, 35, 5):
    pws_wb = sat_pressure(twb)
    ws_wb = 622.0 * pws_wb / (PATM - pws_wb)
    t_line = np.linspace(twb, min(twb + 30, T_MAX), 150)
    w_line = ((2501.0 - 2.326 * twb) * ws_wb - 1006.0 * (t_line - twb)) / (2501.0 + 1.86 * t_line - 4.186 * twb)
    mask = (w_line >= 0) & (w_line <= W_MAX) & (t_line >= T_MIN)
    if np.sum(mask) > 2:
        wb_frames.append(pd.DataFrame({"t": t_line[mask], "w": w_line[mask], "group": f"WB {twb}°C"}))
df_wb_all = pd.concat(wb_frames, ignore_index=True)

# Wet-bulb labels near the saturation curve, offset to avoid RH label overlap
wb_labels = []
for twb in range(0, 35, 5):
    grp = f"WB {twb}°C"
    sub = df_wb_all[df_wb_all["group"] == grp]
    if len(sub) > 0:
        idx = sub["t"].idxmin()
        row = sub.loc[idx]
        wb_labels.append({"t": row["t"] - 2.0, "w": row["w"] + 0.8, "label": f"{twb}°C"})
df_wb_labels = pd.DataFrame(wb_labels)

# Data: Enthalpy lines (kJ/kg dry air)
enth_frames = []
for h in range(10, 130, 20):
    t_line = np.linspace(T_MIN, T_MAX, 200)
    w_line = enthalpy_w(t_line, h)
    mask = (w_line >= 0) & (w_line <= W_MAX) & (t_line >= T_MIN) & (t_line <= T_MAX)
    if np.sum(mask) > 2:
        enth_frames.append(pd.DataFrame({"t": t_line[mask], "w": w_line[mask], "group": f"h={h}"}))
df_enth_all = pd.concat(enth_frames, ignore_index=True) if enth_frames else pd.DataFrame()

# Enthalpy labels at lower-right end of each line
enth_labels = []
for h in range(10, 130, 20):
    grp = f"h={h}"
    sub = df_enth_all[df_enth_all["group"] == grp]
    if len(sub) > 0:
        idx = sub["w"].idxmin()
        row = sub.loc[idx]
        if row["t"] <= T_MAX and row["w"] >= 0:
            enth_labels.append({"t": row["t"], "w": max(row["w"] - 0.5, 0.3), "label": f"{h} kJ/kg"})
df_enth_labels = pd.DataFrame(enth_labels)

# Data: Specific volume lines (m³/kg dry air)
sv_frames = []
for v_10 in range(80, 94, 2):
    v = v_10 / 100.0
    t_line = np.linspace(T_MIN, T_MAX, 200)
    w_line = specific_volume_w(t_line, v)
    mask = (w_line >= 0) & (w_line <= W_MAX) & (t_line >= T_MIN) & (t_line <= T_MAX)
    if np.sum(mask) > 2:
        sv_frames.append(pd.DataFrame({"t": t_line[mask], "w": w_line[mask], "group": f"v={v:.2f}"}))
df_sv_all = pd.concat(sv_frames, ignore_index=True) if sv_frames else pd.DataFrame()

# Specific volume labels at bottom of each line
sv_labels = []
for v_10 in range(80, 94, 4):
    v = v_10 / 100.0
    grp = f"v={v:.2f}"
    sub = df_sv_all[df_sv_all["group"] == grp]
    if len(sub) > 0:
        idx = sub["w"].idxmin()
        row = sub.loc[idx]
        sv_labels.append({"t": row["t"] + 0.5, "w": max(row["w"] - 0.3, 0.3), "label": f"{v:.2f}"})
df_sv_labels = pd.DataFrame(sv_labels)

# Comfort zone: 20-26°C, 30-60% RH boundary
comfort_w_lo = humidity_ratio(np.array([20, 26]), 30)
comfort_w_hi = humidity_ratio(np.array([20, 26]), 60)
comfort_t = [20, 26, 26, 20, 20]
comfort_w = [comfort_w_lo[0], comfort_w_lo[1], comfort_w_hi[1], comfort_w_hi[0], comfort_w_lo[0]]
df_comfort = pd.DataFrame({"t": comfort_t, "w": comfort_w})

# HVAC process: cooling and dehumidification (35°C, 50%RH → 24°C, 50%RH)
state_a_t, state_a_rh = 35, 50
state_b_t, state_b_rh = 24, 50
w_a = humidity_ratio(np.array([state_a_t]), state_a_rh)[0]
w_b = humidity_ratio(np.array([state_b_t]), state_b_rh)[0]
df_process = pd.DataFrame({"t": [state_a_t, state_b_t], "w": [w_a, w_b], "group": "process"})
df_states = pd.DataFrame({"t": [state_a_t, state_b_t], "w": [w_a, w_b]})

# Prepare enthalpy/specific volume data with linetype column for scale_linetype_identity
df_enth_all["lt"] = "dashed"
df_sv_all["lt"] = "dotted"

# Arrow data for process path (plotnine-native geom_segment + arrow)
df_arrow = pd.DataFrame({"x": [state_a_t], "y": [w_a], "xend": [state_b_t], "yend": [w_b]})

# Plot
plot = (
    ggplot()
    # Comfort zone as polygon (follows RH curve boundaries more accurately)
    + geom_polygon(
        aes(x="t", y="w"), data=df_comfort, fill="#306998", alpha=0.10, color="#306998", size=0.7, linetype="solid"
    )
    # Relative humidity curves with identity scales for per-group styling
    + geom_line(aes(x="t", y="w", group="group", color="color", size="lw"), data=df_rh_all)
    + scale_color_identity()
    + scale_size_identity()
    # Wet-bulb lines (increased visibility)
    + geom_line(aes(x="t", y="w", group="group"), data=df_wb_all, color="#C47A2B", size=0.5, alpha=0.6)
    # Enthalpy lines (increased alpha and size for visibility)
    + geom_line(
        aes(x="t", y="w", group="group", linetype="lt"), data=df_enth_all, color="#7A9A5A", size=0.55, alpha=0.65
    )
    # Specific volume lines (increased alpha and size for visibility)
    + geom_line(aes(x="t", y="w", group="group", linetype="lt"), data=df_sv_all, color="#9B6B9E", size=0.55, alpha=0.65)
    + scale_linetype_identity()
    # HVAC process arrow (plotnine-native)
    + geom_segment(
        aes(x="x", y="y", xend="xend", yend="yend"),
        data=df_arrow,
        color="#D04040",
        size=1.8,
        arrow=arrow(length=0.15, type="closed"),
    )
    # State points
    + geom_point(aes(x="t", y="w"), data=df_states, color="#D04040", size=4.5)
    # RH labels along curves (staggered positions)
    + geom_text(aes(x="t", y="w", label="label"), data=df_rh_labels, size=7, color="#5A8AAD", fontweight="bold")
    # Wet-bulb labels (offset to avoid crowding)
    + geom_text(aes(x="t", y="w", label="label"), data=df_wb_labels, size=6.5, color="#C47A2B")
    # Enthalpy labels (increased size)
    + geom_text(aes(x="t", y="w", label="label"), data=df_enth_labels, size=6, color="#7A9A5A", ha="left")
    # Specific volume labels (increased size)
    + geom_text(aes(x="t", y="w", label="label"), data=df_sv_labels, size=6, color="#9B6B9E")
    # State point annotations
    + annotate("text", x=state_a_t + 1, y=w_a + 1.2, label="A (35°C, 50% RH)", size=8, color="#D04040", ha="left")
    + annotate("text", x=state_b_t + 1.5, y=w_b - 1.5, label="B (24°C, 50% RH)", size=8, color="#D04040", ha="left")
    + annotate(
        "text",
        x=23,
        y=comfort_w_lo.min() + 1.5,
        label="Comfort Zone",
        size=9,
        color="#306998",
        alpha=0.7,
        fontweight="bold",
    )
    # Axes and title
    + labs(
        x="Dry-Bulb Temperature (°C)",
        y="Humidity Ratio (g/kg dry air)",
        title="psychrometric-basic · plotnine · pyplots.ai",
    )
    + scale_x_continuous(breaks=range(T_MIN, T_MAX + 1, 5))
    + scale_y_continuous(breaks=range(0, W_MAX + 1, 5))
    + coord_cartesian(xlim=(T_MIN, T_MAX), ylim=(0, W_MAX))
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold", color="#222222"),
        axis_title=element_text(size=20, color="#444444"),
        axis_text=element_text(size=16, color="#666666"),
        panel_grid_major=element_line(color="#EEEEEE", size=0.3),
        panel_grid_minor=element_blank(),
        legend_position="none",
        plot_background=element_rect(fill="#FAFAFA", color="none"),
    )
)

# Save
plot.save("plot.png", dpi=300)
