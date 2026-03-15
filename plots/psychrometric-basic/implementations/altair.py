""" pyplots.ai
psychrometric-basic: Psychrometric Chart for HVAC
Library: altair 6.0.0 | Python 3.14.3
Quality: 82/100 | Created: 2026-03-15
"""

import altair as alt
import numpy as np
import pandas as pd


# Constants
P_ATM = 101325  # Pa, standard atmospheric pressure

# Data - Generate psychrometric curves
t_range = np.linspace(-10, 50, 200)


# Saturation pressure (ASHRAE) - vectorized inline
t_k = t_range + 273.15
p_sat = np.where(
    t_range >= 0,
    np.exp(
        -5.8002206e3 / t_k
        + 1.3914993
        - 4.8640239e-2 * t_k
        + 4.1764768e-5 * t_k**2
        - 1.4452093e-8 * t_k**3
        + 6.5459673 * np.log(t_k)
    ),
    np.exp(
        -5.6745359e3 / t_k
        + 6.3925247
        - 9.677843e-3 * t_k
        + 6.2215701e-7 * t_k**2
        + 2.0747825e-9 * t_k**3
        - 9.484024e-13 * t_k**4
        + 4.1635019 * np.log(t_k)
    ),
)

# Relative humidity curves (10% to 100%)
rh_curves = []
for rh_pct in range(10, 110, 10):
    rh_frac = rh_pct / 100
    p_w = rh_frac * p_sat
    w_vals = 0.621945 * p_w / (P_ATM - p_w) * 1000  # g/kg
    w_vals = np.clip(w_vals, 0, 30)
    for t, w in zip(t_range, w_vals, strict=True):
        if 0 < w <= 30:
            rh_curves.append({"t_db": float(t), "w": float(w), "rh": f"{rh_pct}%"})

rh_df = pd.DataFrame(rh_curves)

# Wet-bulb temperature lines (psychrometric equation)
wb_lines = []
for t_wb_val in range(0, 36, 5):
    t_wb_k = t_wb_val + 273.15
    p_sat_wb = np.exp(
        -5.8002206e3 / t_wb_k
        + 1.3914993
        - 4.8640239e-2 * t_wb_k
        + 4.1764768e-5 * t_wb_k**2
        - 1.4452093e-8 * t_wb_k**3
        + 6.5459673 * np.log(t_wb_k)
    )
    w_s_wb = 0.621945 * p_sat_wb / (P_ATM - p_sat_wb)
    for t_db in np.linspace(max(-10, t_wb_val), 50, 80):
        w = (2501 * w_s_wb - 1.006 * (t_db - t_wb_val)) / (2501 + 1.86 * t_db - 4.186 * t_wb_val)
        w_gkg = w * 1000
        if 0 <= w_gkg <= 30:
            wb_lines.append({"t_db": float(t_db), "w": float(w_gkg), "wb": f"{t_wb_val}°C"})

wb_df = pd.DataFrame(wb_lines)

# Enthalpy lines (h = 1.006*t + w*(2501 + 1.86*t), solve for w)
enthalpy_lines = []
for h_val in range(10, 120, 10):
    for t_db in np.linspace(-10, 50, 80):
        w_gkg = (h_val - 1.006 * t_db) / (2.501 + 0.00186 * t_db)
        if 0 <= w_gkg <= 30:
            enthalpy_lines.append({"t_db": float(t_db), "w": float(w_gkg), "h": f"{h_val} kJ/kg"})

enthalpy_df = pd.DataFrame(enthalpy_lines)

# Specific volume lines (v = 0.287042*T_k*(1+1.6078*w)/P, solve for w)
vol_lines = []
for v_val in [0.75, 0.80, 0.85, 0.90, 0.95]:
    for t_db in np.linspace(-10, 50, 80):
        w = (v_val * P_ATM / 1000 / (0.287042 * (t_db + 273.15)) - 1) / 1.6078
        w_gkg = w * 1000
        if 0 <= w_gkg <= 30:
            vol_lines.append({"t_db": float(t_db), "w": float(w_gkg), "v": f"{v_val} m³/kg"})

vol_df = pd.DataFrame(vol_lines)

# Comfort zone (20-26°C, 30-60% RH)
comfort_temps = np.linspace(20, 26, 30)
comfort_k = comfort_temps + 273.15
comfort_psat = np.exp(
    -5.8002206e3 / comfort_k
    + 1.3914993
    - 4.8640239e-2 * comfort_k
    + 4.1764768e-5 * comfort_k**2
    - 1.4452093e-8 * comfort_k**3
    + 6.5459673 * np.log(comfort_k)
)
comfort_w_lo = 0.621945 * 0.30 * comfort_psat / (P_ATM - 0.30 * comfort_psat) * 1000
comfort_w_hi = 0.621945 * 0.60 * comfort_psat / (P_ATM - 0.60 * comfort_psat) * 1000
comfort_df = pd.DataFrame({"t_db": comfort_temps, "w": comfort_w_lo, "w2": comfort_w_hi})

# HVAC process path: cooling and dehumidification (35°C/50%RH -> 13°C/sat)
t1, t2 = 35.0, 13.0
t1_k, t2_k = t1 + 273.15, t2 + 273.15
p_sat_t1 = np.exp(
    -5.8002206e3 / t1_k
    + 1.3914993
    - 4.8640239e-2 * t1_k
    + 4.1764768e-5 * t1_k**2
    - 1.4452093e-8 * t1_k**3
    + 6.5459673 * np.log(t1_k)
)
p_sat_t2 = np.exp(
    -5.8002206e3 / t2_k
    + 1.3914993
    - 4.8640239e-2 * t2_k
    + 4.1764768e-5 * t2_k**2
    - 1.4452093e-8 * t2_k**3
    + 6.5459673 * np.log(t2_k)
)
w1 = 0.621945 * 0.50 * p_sat_t1 / (P_ATM - 0.50 * p_sat_t1) * 1000
w2 = 0.621945 * 1.00 * p_sat_t2 / (P_ATM - 1.00 * p_sat_t2) * 1000

process_points = pd.DataFrame(
    {
        "t_db": [t1, t2],
        "w": [float(w1), float(w2)],
        "label": ["Outdoor Air (35°C, 50% RH)", "Supply Air (13°C, 100% RH)"],
        "order": [0, 1],
    }
)

# RH label positions (placed along right side of curves)
rh_labels = []
for rh_pct in range(10, 110, 10):
    rh_frac = rh_pct / 100
    t_label = 35 if rh_pct == 100 else (38 if rh_pct >= 70 else (42 if rh_pct >= 40 else 46))
    t_label_k = t_label + 273.15
    p_sat_label = np.exp(
        -5.8002206e3 / t_label_k
        + 1.3914993
        - 4.8640239e-2 * t_label_k
        + 4.1764768e-5 * t_label_k**2
        - 1.4452093e-8 * t_label_k**3
        + 6.5459673 * np.log(t_label_k)
    )
    w_label = 0.621945 * rh_frac * p_sat_label / (P_ATM - rh_frac * p_sat_label) * 1000
    if w_label <= 30:
        rh_labels.append({"t_db": float(t_label), "w": float(w_label), "label": f"{rh_pct}%"})

rh_label_df = pd.DataFrame(rh_labels)

# Wet-bulb labels (at saturation curve)
wb_labels_data = []
for t_wb_val in range(0, 36, 5):
    t_wb_k2 = t_wb_val + 273.15
    p_sat_wb2 = np.exp(
        -5.8002206e3 / t_wb_k2
        + 1.3914993
        - 4.8640239e-2 * t_wb_k2
        + 4.1764768e-5 * t_wb_k2**2
        - 1.4452093e-8 * t_wb_k2**3
        + 6.5459673 * np.log(t_wb_k2)
    )
    w_wb_label = 0.621945 * p_sat_wb2 / (P_ATM - p_sat_wb2) * 1000
    if w_wb_label <= 30:
        wb_labels_data.append({"t_db": float(t_wb_val), "w": float(w_wb_label), "label": f"{t_wb_val}°C"})

wb_label_df = pd.DataFrame(wb_labels_data)

# Enthalpy labels (along left edge or top)
enthalpy_labels = []
for h_val in range(10, 120, 10):
    w_at_left = (h_val - 1.006 * (-10)) / (2.501 + 0.00186 * (-10))
    if 0 <= w_at_left <= 30:
        enthalpy_labels.append({"t_db": -10.0, "w": float(w_at_left), "label": f"{h_val}"})
    else:
        t_at_top = (h_val - 2.501 * 30) / (1.006 + 0.00186 * 30)
        if -10 <= t_at_top <= 50:
            enthalpy_labels.append({"t_db": float(t_at_top), "w": 30.0, "label": f"{h_val}"})

enthalpy_label_df = pd.DataFrame(enthalpy_labels)

# Volume labels (along bottom)
vol_labels = []
for v_val in [0.75, 0.80, 0.85, 0.90, 0.95]:
    w_at_bot = (v_val * P_ATM / 1000 / (0.287042 * (45 + 273.15)) - 1) / 1.6078 * 1000
    if 0 <= w_at_bot <= 30:
        vol_labels.append({"t_db": 45.0, "w": float(w_at_bot), "label": f"{v_val}"})

vol_label_df = pd.DataFrame(vol_labels)

# Plot
x_scale = alt.Scale(domain=[-10, 50])
y_scale = alt.Scale(domain=[0, 30])

# Saturation curve (100% RH) - visually prominent
sat_df = rh_df[rh_df["rh"] == "100%"]
saturation = (
    alt.Chart(sat_df)
    .mark_line(strokeWidth=3, color="#306998")
    .encode(
        x=alt.X("t_db:Q", scale=x_scale, title="Dry-Bulb Temperature (°C)"),
        y=alt.Y("w:Q", scale=y_scale, title="Humidity Ratio (g/kg)"),
    )
)

# Other RH curves
other_rh_df = rh_df[rh_df["rh"] != "100%"]
rh_chart = (
    alt.Chart(other_rh_df)
    .mark_line(strokeWidth=1.5, opacity=0.6)
    .encode(
        x=alt.X("t_db:Q", scale=x_scale),
        y=alt.Y("w:Q", scale=y_scale),
        color=alt.Color("rh:N", scale=alt.Scale(scheme="blues"), legend=None),
        detail="rh:N",
    )
)

# RH labels
rh_text = (
    alt.Chart(rh_label_df)
    .mark_text(fontSize=13, color="#4a7fb5", fontWeight="bold")
    .encode(x=alt.X("t_db:Q", scale=x_scale), y=alt.Y("w:Q", scale=y_scale), text="label:N")
)

# Wet-bulb lines
wb_chart = (
    alt.Chart(wb_df)
    .mark_line(strokeWidth=1, strokeDash=[6, 4], opacity=0.5, color="#d45b5b")
    .encode(x=alt.X("t_db:Q", scale=x_scale), y=alt.Y("w:Q", scale=y_scale), detail="wb:N")
)

# Wet-bulb labels
wb_text = (
    alt.Chart(wb_label_df)
    .mark_text(fontSize=11, color="#d45b5b", align="right", dx=-5, dy=-8)
    .encode(x=alt.X("t_db:Q", scale=x_scale), y=alt.Y("w:Q", scale=y_scale), text="label:N")
)

# Enthalpy lines
enthalpy_chart = (
    alt.Chart(enthalpy_df)
    .mark_line(strokeWidth=1, strokeDash=[4, 6], opacity=0.4, color="#2ca02c")
    .encode(x=alt.X("t_db:Q", scale=x_scale), y=alt.Y("w:Q", scale=y_scale), detail="h:N")
)

# Enthalpy labels
enthalpy_text = (
    alt.Chart(enthalpy_label_df)
    .mark_text(fontSize=11, color="#2ca02c", align="right", dx=-3, dy=-5)
    .encode(x=alt.X("t_db:Q", scale=x_scale), y=alt.Y("w:Q", scale=y_scale), text="label:N")
)

# Specific volume lines
vol_chart = (
    alt.Chart(vol_df)
    .mark_line(strokeWidth=1, strokeDash=[2, 4], opacity=0.4, color="#9467bd")
    .encode(x=alt.X("t_db:Q", scale=x_scale), y=alt.Y("w:Q", scale=y_scale), detail="v:N")
)

# Volume labels
vol_text = (
    alt.Chart(vol_label_df)
    .mark_text(fontSize=11, color="#9467bd", align="left", dx=3, dy=-5)
    .encode(x=alt.X("t_db:Q", scale=x_scale), y=alt.Y("w:Q", scale=y_scale), text="label:N")
)

# Comfort zone shaded area
comfort = (
    alt.Chart(comfort_df)
    .mark_area(opacity=0.15, color="#2ca02c")
    .encode(x=alt.X("t_db:Q", scale=x_scale), y=alt.Y("w:Q", scale=y_scale), y2="w2:Q")
)

comfort_label = (
    alt.Chart(pd.DataFrame({"t_db": [23.0], "w": [10.0], "label": ["Comfort Zone"]}))
    .mark_text(fontSize=14, color="#2ca02c", fontWeight="bold", fontStyle="italic")
    .encode(x=alt.X("t_db:Q", scale=x_scale), y=alt.Y("w:Q", scale=y_scale), text="label:N")
)

# HVAC process path with points
process_line = (
    alt.Chart(process_points)
    .mark_line(strokeWidth=3, color="#e74c3c", point=alt.OverlayMarkDef(size=120, filled=True, color="#e74c3c"))
    .encode(x=alt.X("t_db:Q", scale=x_scale), y=alt.Y("w:Q", scale=y_scale), order="order:Q")
)

process_text = (
    alt.Chart(process_points)
    .mark_text(fontSize=12, fontWeight="bold", color="#c0392b", align="left", dx=10, dy=-12)
    .encode(x=alt.X("t_db:Q", scale=x_scale), y=alt.Y("w:Q", scale=y_scale), text="label:N")
)

# Layer all elements
chart = (
    alt.layer(
        comfort,
        rh_chart,
        saturation,
        wb_chart,
        enthalpy_chart,
        vol_chart,
        rh_text,
        wb_text,
        enthalpy_text,
        vol_text,
        comfort_label,
        process_line,
        process_text,
    )
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            text="psychrometric-basic · altair · pyplots.ai",
            fontSize=28,
            anchor="middle",
            subtitle="Standard Atmosphere (101.325 kPa) · HVAC Air Properties",
            subtitleFontSize=18,
            subtitleColor="#666666",
        ),
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, grid=True, gridOpacity=0.15)
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
