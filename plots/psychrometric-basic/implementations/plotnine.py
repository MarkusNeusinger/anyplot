""" pyplots.ai
psychrometric-basic: Psychrometric Chart for HVAC
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 87/100 | Created: 2026-03-15
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
    geom_ribbon,
    geom_segment,
    geom_text,
    ggplot,
    labs,
    scale_alpha_identity,
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
T_MIN, T_MAX = -10, 50
W_MAX = 30

t_range = np.linspace(T_MIN, T_MAX, 300)

# Inline saturation vapor pressure (Magnus formula) and humidity ratio calculations
# psat(t) = 0.61078 * exp(17.27 * t / (t + 237.3))
# w = 622 * pw / (PATM - pw), where pw = rh/100 * psat

# Relative humidity curves (10%-100%)
rh_frames = []
for rh in range(10, 110, 10):
    pw = np.minimum(rh / 100.0 * 0.61078 * np.exp(17.27 * t_range / (t_range + 237.3)), PATM - 0.01)
    w = 622.0 * pw / (PATM - pw)
    mask = (w >= 0) & (w <= W_MAX)
    rh_frames.append(
        pd.DataFrame(
            {
                "t": t_range[mask],
                "w": w[mask],
                "group": f"RH {rh}%",
                "color": "#1B4F72" if rh == 100 else "#7FB3D8",
                "sz": 2.2 if rh == 100 else 0.55,
                "alpha": 1.0 if rh == 100 else 0.75,
            }
        )
    )
df_rh = pd.concat(rh_frames, ignore_index=True)

# RH labels: carefully positioned to avoid overlap with state points and wet-bulb labels
# Moved 50% label away from point A (35°C), shifted others for even spacing
rh_label_pos = {10: 48, 20: 44, 30: 40, 40: 36, 50: 17, 60: 32, 70: 13, 80: 9, 90: 4, 100: -5}
rh_labels = []
for rh, t_l in rh_label_pos.items():
    pw_l = rh / 100.0 * 0.61078 * np.exp(17.27 * t_l / (t_l + 237.3))
    pw_l = min(pw_l, PATM - 0.01)
    w_l = 622.0 * pw_l / (PATM - pw_l)
    if 0 < w_l < W_MAX:
        rh_labels.append({"t": t_l, "w": w_l + 1.2, "label": f"{rh}%"})
df_rh_labels = pd.DataFrame(rh_labels)

# Wet-bulb temperature lines
wb_frames = []
for twb in range(-5, 35, 5):
    pws_wb = 0.61078 * np.exp(17.27 * twb / (twb + 237.3))
    ws_wb = 622.0 * pws_wb / (PATM - pws_wb)
    t_line = np.linspace(twb, min(twb + 30, T_MAX), 150)
    w_line = ((2501.0 - 2.326 * twb) * ws_wb - 1006.0 * (t_line - twb)) / (2501.0 + 1.86 * t_line - 4.186 * twb)
    mask = (w_line >= 0) & (w_line <= W_MAX) & (t_line >= T_MIN)
    if np.sum(mask) > 2:
        wb_frames.append(pd.DataFrame({"t": t_line[mask], "w": w_line[mask], "group": f"WB {twb}°C"}))
df_wb = pd.concat(wb_frames, ignore_index=True)

# Wet-bulb labels: placed at right end of lines (lower-right), away from saturation curve
wb_labels = []
for twb in range(0, 35, 10):
    sub = df_wb[df_wb["group"] == f"WB {twb}°C"]
    if len(sub) > 0:
        row = sub.loc[sub["t"].idxmax()]
        wb_labels.append({"t": row["t"] + 1.5, "w": max(row["w"] - 0.3, 0.5), "label": f"{twb}°C"})
df_wb_labels = pd.DataFrame(wb_labels)

# Enthalpy lines (kJ/kg dry air) - wider spacing to reduce overlap
enth_frames = []
for h in range(10, 130, 20):
    t_line = np.linspace(T_MIN, T_MAX, 200)
    w_line = (h - 1.006 * t_line) / (2.501 + 0.00186 * t_line)
    mask = (w_line >= 0) & (w_line <= W_MAX) & (t_line >= T_MIN) & (t_line <= T_MAX)
    if np.sum(mask) > 2:
        enth_frames.append(pd.DataFrame({"t": t_line[mask], "w": w_line[mask], "group": f"h={h}"}))
df_enth = pd.concat(enth_frames, ignore_index=True) if enth_frames else pd.DataFrame(columns=["t", "w", "group"])

# Enthalpy labels at the right/bottom end of lines (away from saturation curve)
enth_labels = []
for h in range(10, 130, 20):
    sub = df_enth[df_enth["group"] == f"h={h}"]
    if len(sub) > 0:
        row = sub.loc[sub["t"].idxmax()]
        if row["w"] > 0.5:
            enth_labels.append({"t": row["t"] + 1.0, "w": max(row["w"] - 0.5, 0.5), "label": f"{h} kJ/kg"})
df_enth_labels = pd.DataFrame(enth_labels)

# Specific volume lines (m³/kg dry air) - wider step for clarity
sv_frames = []
for v_10 in range(80, 94, 2):
    v = v_10 / 100.0
    t_line = np.linspace(T_MIN, T_MAX, 200)
    w_line = (v * PATM / (0.287055 * (t_line + 273.15)) - 1.0) / 1.6078 * 1000.0
    mask = (w_line >= 0) & (w_line <= W_MAX) & (t_line >= T_MIN) & (t_line <= T_MAX)
    if np.sum(mask) > 2:
        sv_frames.append(pd.DataFrame({"t": t_line[mask], "w": w_line[mask], "group": f"v={v:.2f}"}))
df_sv = pd.concat(sv_frames, ignore_index=True) if sv_frames else pd.DataFrame(columns=["t", "w", "group"])

# Specific volume labels at bottom-right end (well separated from enthalpy labels)
sv_labels = []
for v_10 in range(80, 94, 4):
    v = v_10 / 100.0
    sub = df_sv[df_sv["group"] == f"v={v:.2f}"]
    if len(sub) > 0:
        row = sub.loc[sub["t"].idxmax()]
        sv_labels.append(
            {"t": min(row["t"] + 1.0, T_MAX - 1), "w": max(row["w"] - 0.8, 0.5), "label": f"{v:.2f} m³/kg"}
        )
df_sv_labels = pd.DataFrame(sv_labels)

# Comfort zone polygon (20-26°C, 30-60% RH)
pw_cz_lo = np.minimum(
    0.30 * 0.61078 * np.exp(17.27 * np.array([20.0, 26.0]) / (np.array([20.0, 26.0]) + 237.3)), PATM - 0.01
)
c_w_lo = 622.0 * pw_cz_lo / (PATM - pw_cz_lo)
pw_cz_hi = np.minimum(
    0.60 * 0.61078 * np.exp(17.27 * np.array([20.0, 26.0]) / (np.array([20.0, 26.0]) + 237.3)), PATM - 0.01
)
c_w_hi = 622.0 * pw_cz_hi / (PATM - pw_cz_hi)
df_comfort = pd.DataFrame({"t": [20, 26, 26, 20, 20], "w": [c_w_lo[0], c_w_lo[1], c_w_hi[1], c_w_hi[0], c_w_lo[0]]})

# Comfort zone ribbon for shading between RH 30% and 60% within 20-26°C
t_comfort = np.linspace(20, 26, 50)
pw_crib_lo = np.minimum(0.30 * 0.61078 * np.exp(17.27 * t_comfort / (t_comfort + 237.3)), PATM - 0.01)
pw_crib_hi = np.minimum(0.60 * 0.61078 * np.exp(17.27 * t_comfort / (t_comfort + 237.3)), PATM - 0.01)
df_comfort_ribbon = pd.DataFrame(
    {"t": t_comfort, "w_lo": 622.0 * pw_crib_lo / (PATM - pw_crib_lo), "w_hi": 622.0 * pw_crib_hi / (PATM - pw_crib_hi)}
)

# HVAC process: cooling and dehumidification
pw_a = min(0.50 * 0.61078 * np.exp(17.27 * 35 / (35 + 237.3)), PATM - 0.01)
w_a = 622.0 * pw_a / (PATM - pw_a)
pw_b = min(0.50 * 0.61078 * np.exp(17.27 * 24 / (24 + 237.3)), PATM - 0.01)
w_b = 622.0 * pw_b / (PATM - pw_b)
df_states = pd.DataFrame({"t": [35, 24], "w": [w_a, w_b], "label": ["A", "B"]})
df_arrow = pd.DataFrame({"x": [35], "y": [w_a], "xend": [24], "yend": [w_b]})

# Add linetype columns for identity scale
df_enth["lt"] = "dashed"
df_sv["lt"] = "dotted"

# Build plot using plotnine grammar of graphics with layered composition
plot = (
    ggplot()
    # Comfort zone ribbon (plotnine-distinctive: geom_ribbon with ymin/ymax mapping)
    + geom_ribbon(aes(x="t", ymin="w_lo", ymax="w_hi"), data=df_comfort_ribbon, fill="#306998", alpha=0.12)
    # Comfort zone border
    + geom_polygon(
        aes(x="t", y="w"), data=df_comfort, fill="none", color="#306998", size=0.8, linetype="solid", alpha=0.6
    )
    # RH curves with identity aesthetics for per-group color/size/alpha
    + geom_line(aes(x="t", y="w", group="group", color="color", size="sz", alpha="alpha"), data=df_rh)
    + scale_color_identity()
    + scale_size_identity()
    + scale_alpha_identity()
    # Wet-bulb lines - warm orange, distinct from RH blues
    + geom_line(aes(x="t", y="w", group="group"), data=df_wb, color="#D4760A", size=0.55, alpha=0.65)
    # Enthalpy lines - olive green, dashed, increased visibility
    + geom_line(aes(x="t", y="w", group="group", linetype="lt"), data=df_enth, color="#5B8C3E", size=0.6, alpha=0.75)
    # Specific volume lines - muted purple, dotted, distinct from enthalpy
    + geom_line(aes(x="t", y="w", group="group", linetype="lt"), data=df_sv, color="#8E5EA2", size=0.5, alpha=0.6)
    + scale_linetype_identity()
    # HVAC process arrow
    + geom_segment(
        aes(x="x", y="y", xend="xend", yend="yend"),
        data=df_arrow,
        color="#C0392B",
        size=2.0,
        arrow=arrow(length=0.18, type="closed"),
    )
    # State points with fill identity
    + geom_point(aes(x="t", y="w"), data=df_states, color="#C0392B", fill="#E74C3C", size=5, shape="o")
    # RH labels - larger, bold, positioned away from state points
    + geom_text(aes(x="t", y="w", label="label"), data=df_rh_labels, size=9.5, color="#2471A3", fontweight="bold")
    # Wet-bulb labels - at right end of lines, larger
    + geom_text(aes(x="t", y="w", label="label"), data=df_wb_labels, size=9, color="#D4760A", fontstyle="italic")
    # Enthalpy labels at right/bottom end of lines (away from saturation curve)
    + geom_text(aes(x="t", y="w", label="label"), data=df_enth_labels, size=8.5, color="#5B8C3E", ha="left")
    # Specific volume labels at bottom-right of lines
    + geom_text(aes(x="t", y="w", label="label"), data=df_sv_labels, size=8.5, color="#8E5EA2", ha="left")
    # State point annotations - repositioned to avoid comfort zone overlap
    + annotate("text", x=37, y=w_a + 1.5, label="A (35°C)", size=10, color="#C0392B", ha="left", fontweight="bold")
    + annotate("text", x=29, y=w_b + 1.8, label="B (24°C)", size=9.5, color="#C0392B", ha="left", fontweight="bold")
    # Comfort zone label - centered in the zone
    + annotate(
        "text",
        x=23,
        y=(c_w_lo.mean() + c_w_hi.mean()) / 2,
        label="Comfort\nZone",
        size=9,
        color="#306998",
        alpha=0.7,
        fontweight="bold",
        ha="center",
        va="center",
    )
    # Axes
    + labs(
        x="Dry-Bulb Temperature (°C)",
        y="Humidity Ratio (g/kg dry air)",
        title="psychrometric-basic · plotnine · pyplots.ai",
    )
    + scale_x_continuous(breaks=range(T_MIN, T_MAX + 1, 5))
    + scale_y_continuous(breaks=range(0, W_MAX + 1, 5))
    + coord_cartesian(xlim=(T_MIN - 1, T_MAX + 5), ylim=(0, W_MAX))
    # Theme: polished publication style
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold", color="#1B2631"),
        axis_title_x=element_text(size=20, color="#2C3E50"),
        axis_title_y=element_text(size=20, color="#2C3E50"),
        axis_text=element_text(size=16, color="#566573"),
        panel_grid_major=element_line(color="#E8E8E8", size=0.25),
        panel_grid_minor=element_blank(),
        legend_position="none",
        plot_background=element_rect(fill="#FAFBFC", color="none"),
        panel_background=element_rect(fill="#FAFBFC", color="none"),
    )
)

plot.save("plot.png", dpi=300)
