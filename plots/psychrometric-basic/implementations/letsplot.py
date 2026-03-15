"""pyplots.ai
psychrometric-basic: Psychrometric Chart for HVAC
Library: letsplot | Python 3.13
Quality: pending | Created: 2026-03-15
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_line,
    geom_path,
    geom_point,
    geom_polygon,
    geom_text,
    ggplot,
    ggsize,
    labs,
    scale_color_identity,
    scale_fill_identity,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Constants
P_ATM = 101325.0  # Pa, standard atmospheric pressure


# Psychrometric equations (ASHRAE-based)
def saturation_pressure(t):
    """Saturation vapor pressure in Pa from dry-bulb temp in C."""
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
    """Humidity ratio (kg/kg) from dry-bulb temp and relative humidity (0-1)."""
    p_s = saturation_pressure(t_db)
    p_w = rh * p_s
    w = 0.621945 * p_w / (P_ATM - p_w)
    return w


def wet_bulb_line(t_wb, t_db_range):
    """Approximate humidity ratio along a constant wet-bulb line."""
    w_sat = humidity_ratio(t_wb, 1.0)
    h_fg = 2501.0  # kJ/kg, latent heat of vaporization at 0C
    cp_a = 1.006  # kJ/(kg·K), specific heat of dry air
    cp_w = 1.86  # kJ/(kg·K), specific heat of water vapor
    w_values = []
    for t_db in t_db_range:
        w = (h_fg * w_sat - cp_a * (t_db - t_wb)) / (h_fg + cp_w * t_db - cp_a * t_wb + (cp_w - cp_a) * t_wb)
        w_values.append(max(w, 0))
    return np.array(w_values)


def enthalpy_value(t_db, w):
    """Enthalpy of moist air in kJ/kg."""
    return 1.006 * t_db + w * (2501.0 + 1.86 * t_db)


def specific_volume_value(t_db, w):
    """Specific volume in m3/kg."""
    return 0.287042 * (t_db + 273.15) * (1 + 1.6078 * w) / (P_ATM / 1000)


# Data - Generate psychrometric curves
t_db_fine = np.linspace(-10, 50, 300)

all_frames = []

# Relative humidity curves (10% to 100%)
rh_colors = {
    0.1: "#b0b0b0",
    0.2: "#a0a0a0",
    0.3: "#909090",
    0.4: "#808080",
    0.5: "#707070",
    0.6: "#606060",
    0.7: "#505050",
    0.8: "#404040",
    0.9: "#303030",
    1.0: "#306998",
}

for rh_val in np.arange(0.1, 1.05, 0.1):
    rh_val = round(rh_val, 1)
    w_values = []
    t_valid = []
    for t in t_db_fine:
        w = humidity_ratio(t, rh_val) * 1000  # convert to g/kg
        if 0 <= w <= 30:
            w_values.append(w)
            t_valid.append(t)
    df_rh = pd.DataFrame(
        {
            "t_db": t_valid,
            "w": w_values,
            "group": f"RH {int(rh_val * 100)}%",
            "color": rh_colors[rh_val],
            "line_type": "rh",
        }
    )
    all_frames.append(df_rh)

df_rh_all = pd.concat(all_frames, ignore_index=True)

# Wet-bulb temperature lines
wb_frames = []
wb_temps = [0, 5, 10, 15, 20, 25, 30, 35]

for t_wb in wb_temps:
    t_range = np.linspace(t_wb, min(t_wb + 30, 50), 100)
    w_vals = wet_bulb_line(t_wb, t_range) * 1000  # g/kg
    mask = (w_vals >= 0) & (w_vals <= 30)
    df_wb = pd.DataFrame(
        {"t_db": t_range[mask], "w": w_vals[mask], "group": f"WB {t_wb}°C", "color": "#2ca02c", "line_type": "wb"}
    )
    wb_frames.append(df_wb)

df_wb_all = pd.concat(wb_frames, ignore_index=True)

# Enthalpy lines
enth_frames = []
enthalpy_values_list = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110]

for h_target in enthalpy_values_list:
    t_points = []
    w_points = []
    for t in np.linspace(-10, 50, 200):
        w = (h_target - 1.006 * t) / (2501.0 + 1.86 * t)
        w_gkg = w * 1000
        if 0 <= w_gkg <= 30 and -10 <= t <= 50:
            t_points.append(t)
            w_points.append(w_gkg)
    if len(t_points) > 1:
        df_h = pd.DataFrame(
            {"t_db": t_points, "w": w_points, "group": f"h={h_target}", "color": "#d62728", "line_type": "enthalpy"}
        )
        enth_frames.append(df_h)

df_enth_all = pd.concat(enth_frames, ignore_index=True)

# Specific volume lines
vol_frames = []
vol_values = [0.78, 0.80, 0.82, 0.84, 0.86, 0.88, 0.90, 0.92, 0.94]

for v_target in vol_values:
    t_points = []
    w_points = []
    for t in np.linspace(-10, 50, 200):
        w = (v_target * (P_ATM / 1000) / (0.287042 * (t + 273.15)) - 1) / 1.6078
        w_gkg = w * 1000
        if 0 <= w_gkg <= 30 and -10 <= t <= 50:
            t_points.append(t)
            w_points.append(w_gkg)
    if len(t_points) > 1:
        df_v = pd.DataFrame(
            {"t_db": t_points, "w": w_points, "group": f"v={v_target}", "color": "#9467bd", "line_type": "volume"}
        )
        vol_frames.append(df_v)

df_vol_all = pd.concat(vol_frames, ignore_index=True)

# Comfort zone polygon (20-26°C, humidity ratio at 30-60% RH)
comfort_t = [20, 26, 26, 20, 20]
comfort_w = [
    humidity_ratio(20, 0.3) * 1000,
    humidity_ratio(26, 0.3) * 1000,
    humidity_ratio(26, 0.6) * 1000,
    humidity_ratio(20, 0.6) * 1000,
    humidity_ratio(20, 0.3) * 1000,
]
df_comfort = pd.DataFrame({"t_db": comfort_t, "w": comfort_w})

# HVAC process path: cooling and dehumidification (32°C, 50% RH → 24°C, 50% RH)
state1_t, state1_rh = 32, 0.50
state2_t, state2_rh = 24, 0.50
state1_w = humidity_ratio(state1_t, state1_rh) * 1000
state2_w = humidity_ratio(state2_t, state2_rh) * 1000

df_process = pd.DataFrame({"t_db": [state1_t, state2_t], "w": [state1_w, state2_w]})

# RH label positions (placed at the right end of each curve)
rh_label_frames = []
for rh_val in np.arange(0.1, 1.05, 0.1):
    rh_val = round(rh_val, 1)
    t_label = 42 if rh_val <= 0.3 else (35 if rh_val <= 0.6 else 28)
    w_label = humidity_ratio(t_label, rh_val) * 1000
    if w_label <= 28:
        rh_label_frames.append({"t_db": t_label, "w": w_label, "label": f"{int(rh_val * 100)}%"})

df_rh_labels = pd.DataFrame(rh_label_frames)

# Wet-bulb labels
wb_label_frames = []
for t_wb in wb_temps:
    w_at_sat = humidity_ratio(t_wb, 1.0) * 1000
    if w_at_sat <= 30:
        wb_label_frames.append({"t_db": t_wb - 1, "w": w_at_sat + 0.5, "label": f"{t_wb}°C"})

df_wb_labels = pd.DataFrame(wb_label_frames)

# Enthalpy labels
enth_label_frames = []
for h_target in enthalpy_values_list:
    w_at_zero = (h_target - 1.006 * (-5)) / (2501.0 + 1.86 * (-5))
    w_gkg = w_at_zero * 1000
    if 0 < w_gkg <= 28:
        enth_label_frames.append({"t_db": -8, "w": w_gkg, "label": f"{h_target}"})

df_enth_labels = pd.DataFrame(enth_label_frames)

# Volume labels
vol_label_frames = []
for v_target in vol_values:
    w_at_45 = (v_target * (P_ATM / 1000) / (0.287042 * (45 + 273.15)) - 1) / 1.6078
    w_gkg = w_at_45 * 1000
    if 0 < w_gkg <= 28:
        vol_label_frames.append({"t_db": 46, "w": w_gkg, "label": f"{v_target}"})

df_vol_labels = pd.DataFrame(vol_label_frames)

# Plot
plot = (
    ggplot()
    # Comfort zone
    + geom_polygon(
        data=df_comfort,
        mapping=aes(x="t_db", y="w"),
        fill="#306998",
        alpha=0.12,
        color="#306998",
        size=0.8,
        linetype="dashed",
    )
    # RH curves
    + geom_line(data=df_rh_all, mapping=aes(x="t_db", y="w", group="group", color="color"), size=1.0)
    # Wet-bulb lines
    + geom_line(data=df_wb_all, mapping=aes(x="t_db", y="w", group="group"), color="#2ca02c", size=0.6, alpha=0.6)
    # Enthalpy lines
    + geom_line(data=df_enth_all, mapping=aes(x="t_db", y="w", group="group"), color="#d62728", size=0.5, alpha=0.5)
    # Specific volume lines
    + geom_line(data=df_vol_all, mapping=aes(x="t_db", y="w", group="group"), color="#9467bd", size=0.5, alpha=0.5)
    # HVAC process path
    + geom_path(
        data=df_process, mapping=aes(x="t_db", y="w"), color="#e67e22", size=2.5, arrow={"type": "closed", "length": 12}
    )
    # State points
    + geom_point(data=df_process, mapping=aes(x="t_db", y="w"), color="#e67e22", size=5, shape=16)
    # RH labels
    + geom_text(data=df_rh_labels, mapping=aes(x="t_db", y="w", label="label"), size=9, color="#505050")
    # Wet-bulb labels
    + geom_text(data=df_wb_labels, mapping=aes(x="t_db", y="w", label="label"), size=8, color="#2ca02c")
    # Comfort zone label
    + geom_text(
        data=pd.DataFrame({"t_db": [23], "w": [8.0], "label": ["Comfort\nZone"]}),
        mapping=aes(x="t_db", y="w", label="label"),
        size=10,
        color="#306998",
        fontface="bold",
    )
    # Process label
    + geom_text(
        data=pd.DataFrame({"t_db": [28], "w": [state1_w + 1.0], "label": ["Cooling &\nDehumidification"]}),
        mapping=aes(x="t_db", y="w", label="label"),
        size=9,
        color="#e67e22",
        fontface="bold",
    )
    + scale_color_identity()
    + scale_fill_identity()
    + scale_x_continuous(limits=[-10, 50], breaks=list(range(-10, 55, 5)))
    + scale_y_continuous(limits=[0, 30], breaks=list(range(0, 35, 5)))
    + labs(
        x="Dry-Bulb Temperature (°C)", y="Humidity Ratio (g/kg)", title="psychrometric-basic · letsplot · pyplots.ai"
    )
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_position="none",
        panel_grid_major=element_line(color="#e0e0e0", size=0.3),
        panel_grid_minor=element_blank(),
        plot_background=element_rect(fill="white", color="white"),
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
