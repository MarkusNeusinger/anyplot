""" pyplots.ai
psychrometric-basic: Psychrometric Chart for HVAC
Library: altair 6.0.0 | Python 3.14.3
Quality: 86/100 | Created: 2026-03-15
"""

import altair as alt
import numpy as np
import pandas as pd


# Constants
P_ATM = 101325  # Pa, standard atmospheric pressure

# Precompute saturation pressure over a fine grid (ASHRAE formula, computed once)
_t_grid = np.linspace(-10, 50, 500)
_t_grid_k = _t_grid + 273.15
_p_sat_grid = np.where(
    _t_grid >= 0,
    np.exp(
        -5.8002206e3 / _t_grid_k
        + 1.3914993
        - 4.8640239e-2 * _t_grid_k
        + 4.1764768e-5 * _t_grid_k**2
        - 1.4452093e-8 * _t_grid_k**3
        + 6.5459673 * np.log(_t_grid_k)
    ),
    np.exp(
        -5.6745359e3 / _t_grid_k
        + 6.3925247
        - 9.677843e-3 * _t_grid_k
        + 6.2215701e-7 * _t_grid_k**2
        + 2.0747825e-9 * _t_grid_k**3
        - 9.484024e-13 * _t_grid_k**4
        + 4.1635019 * np.log(_t_grid_k)
    ),
)

# Interpolation-based saturation pressure lookup (replaces 6x formula repetition)
p_sat_at = lambda t: np.interp(t, _t_grid, _p_sat_grid)  # noqa: E731

# Data - Generate psychrometric curves
t_range = np.linspace(-10, 50, 200)
p_sat = p_sat_at(t_range)

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

# Wet-bulb temperature lines
wb_lines = []
for t_wb_val in range(0, 36, 5):
    p_sat_wb = float(p_sat_at(t_wb_val))
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
comfort_psat = p_sat_at(comfort_temps)
comfort_w_lo = 0.621945 * 0.30 * comfort_psat / (P_ATM - 0.30 * comfort_psat) * 1000
comfort_w_hi = 0.621945 * 0.60 * comfort_psat / (P_ATM - 0.60 * comfort_psat) * 1000
comfort_df = pd.DataFrame({"t_db": comfort_temps, "w": comfort_w_lo, "w2": comfort_w_hi})

# HVAC process path: cooling and dehumidification (35°C/50%RH -> 13°C/sat)
t1, t2 = 35.0, 13.0
p_sat_t1, p_sat_t2 = float(p_sat_at(t1)), float(p_sat_at(t2))
w1 = 0.621945 * 0.50 * p_sat_t1 / (P_ATM - 0.50 * p_sat_t1) * 1000
w2 = 0.621945 * 1.00 * p_sat_t2 / (P_ATM - 1.00 * p_sat_t2) * 1000

process_points = pd.DataFrame(
    {
        "t_db": [t1, t2],
        "w": [float(w1), float(w2)],
        "label": ["Outdoor Air (35°C, 50% RH)", "Supply Air (13°C, 100% RH)"],
        "rh_pct": ["50%", "100%"],
        "order": [0, 1],
    }
)

# RH label positions (staggered to avoid overlap)
rh_labels = []
for rh_pct in range(10, 110, 10):
    rh_frac = rh_pct / 100
    # Stagger label temperatures to reduce convergence overlap
    if rh_pct == 100:
        t_label = 33
    elif rh_pct >= 80:
        t_label = 36
    elif rh_pct >= 60:
        t_label = 40
    elif rh_pct >= 40:
        t_label = 44
    else:
        t_label = 47
    p_sat_label = float(p_sat_at(t_label))
    w_label = 0.621945 * rh_frac * p_sat_label / (P_ATM - rh_frac * p_sat_label) * 1000
    if w_label <= 30:
        rh_labels.append({"t_db": float(t_label), "w": float(w_label), "label": f"{rh_pct}%"})

rh_label_df = pd.DataFrame(rh_labels)

# Wet-bulb labels (offset from saturation curve to avoid overlap with enthalpy labels)
wb_labels_data = []
for t_wb_val in range(0, 36, 5):
    p_sat_wb = float(p_sat_at(t_wb_val))
    w_wb_label = 0.621945 * p_sat_wb / (P_ATM - p_sat_wb) * 1000
    if w_wb_label <= 28:
        wb_labels_data.append({"t_db": float(t_wb_val) + 1.5, "w": float(w_wb_label) + 0.8, "label": f"{t_wb_val}°C"})

wb_label_df = pd.DataFrame(wb_labels_data)

# Enthalpy labels (along left edge, skip values that would overlap with wet-bulb labels)
enthalpy_labels = []
for h_val in range(20, 120, 20):
    w_at_left = (h_val - 1.006 * (-10)) / (2.501 + 0.00186 * (-10))
    if 0 <= w_at_left <= 30:
        enthalpy_labels.append({"t_db": -9.5, "w": float(w_at_left), "label": f"{h_val} kJ/kg"})
    else:
        t_at_top = (h_val - 2.501 * 30) / (1.006 + 0.00186 * 30)
        if -10 <= t_at_top <= 50:
            enthalpy_labels.append({"t_db": float(t_at_top), "w": 30.0, "label": f"{h_val} kJ/kg"})

enthalpy_label_df = pd.DataFrame(enthalpy_labels)

# Volume labels (along bottom-right)
vol_labels = []
for v_val in [0.75, 0.80, 0.85, 0.90, 0.95]:
    w_at_bot = (v_val * P_ATM / 1000 / (0.287042 * (45 + 273.15)) - 1) / 1.6078 * 1000
    if 0 <= w_at_bot <= 30:
        vol_labels.append({"t_db": 45.0, "w": float(w_at_bot), "label": f"{v_val} m³/kg"})

vol_label_df = pd.DataFrame(vol_labels)

# Colorblind-safe palette: blue (RH), orange (wet-bulb), teal (enthalpy), purple (volume)
CLR_RH = "#306998"
CLR_WB = "#d97b0e"
CLR_ENTHALPY = "#17becf"
CLR_VOL = "#9467bd"
CLR_COMFORT = "#2ecc71"
CLR_PROCESS = "#c0392b"
CLR_BG = "#fafbfc"

# Plot
x_scale = alt.Scale(domain=[-10, 50])
y_scale = alt.Scale(domain=[0, 30])

# Saturation curve (100% RH) - visually prominent
sat_df = rh_df[rh_df["rh"] == "100%"]
saturation = (
    alt.Chart(sat_df)
    .mark_line(strokeWidth=3.5, color=CLR_RH)
    .encode(
        x=alt.X("t_db:Q", scale=x_scale, title="Dry-Bulb Temperature (°C)"),
        y=alt.Y("w:Q", scale=y_scale, title="Humidity Ratio (g/kg)"),
    )
)

# Other RH curves with tooltips
other_rh_df = rh_df[rh_df["rh"] != "100%"]
rh_chart = (
    alt.Chart(other_rh_df)
    .mark_line(strokeWidth=1.5, opacity=0.55)
    .encode(
        x=alt.X("t_db:Q", scale=x_scale),
        y=alt.Y("w:Q", scale=y_scale),
        color=alt.Color("rh:N", scale=alt.Scale(scheme="blues"), legend=None),
        detail="rh:N",
        tooltip=[
            alt.Tooltip("t_db:Q", title="Dry-Bulb (°C)", format=".1f"),
            alt.Tooltip("w:Q", title="Humidity (g/kg)", format=".1f"),
            alt.Tooltip("rh:N", title="Relative Humidity"),
        ],
    )
)

# RH labels
rh_text = (
    alt.Chart(rh_label_df)
    .mark_text(fontSize=13, color="#4a7fb5", fontWeight="bold")
    .encode(x=alt.X("t_db:Q", scale=x_scale), y=alt.Y("w:Q", scale=y_scale), text="label:N")
)

# Wet-bulb lines (orange, colorblind-safe)
wb_chart = (
    alt.Chart(wb_df)
    .mark_line(strokeWidth=1, strokeDash=[6, 4], opacity=0.5, color=CLR_WB)
    .encode(
        x=alt.X("t_db:Q", scale=x_scale),
        y=alt.Y("w:Q", scale=y_scale),
        detail="wb:N",
        tooltip=[
            alt.Tooltip("t_db:Q", title="Dry-Bulb (°C)", format=".1f"),
            alt.Tooltip("w:Q", title="Humidity (g/kg)", format=".1f"),
            alt.Tooltip("wb:N", title="Wet-Bulb Temp"),
        ],
    )
)

# Wet-bulb labels (offset to avoid overlap)
wb_text = (
    alt.Chart(wb_label_df)
    .mark_text(fontSize=12, color=CLR_WB, align="left", dx=2, dy=-6, fontWeight="bold")
    .encode(x=alt.X("t_db:Q", scale=x_scale), y=alt.Y("w:Q", scale=y_scale), text="label:N")
)

# Enthalpy lines (teal, colorblind-safe)
enthalpy_chart = (
    alt.Chart(enthalpy_df)
    .mark_line(strokeWidth=1, strokeDash=[4, 6], opacity=0.45, color=CLR_ENTHALPY)
    .encode(x=alt.X("t_db:Q", scale=x_scale), y=alt.Y("w:Q", scale=y_scale), detail="h:N")
)

# Enthalpy labels
enthalpy_text = (
    alt.Chart(enthalpy_label_df)
    .mark_text(fontSize=11, color=CLR_ENTHALPY, align="left", dx=2, dy=-4, fontWeight="bold")
    .encode(x=alt.X("t_db:Q", scale=x_scale), y=alt.Y("w:Q", scale=y_scale), text="label:N")
)

# Specific volume lines
vol_chart = (
    alt.Chart(vol_df)
    .mark_line(strokeWidth=1, strokeDash=[2, 4], opacity=0.4, color=CLR_VOL)
    .encode(x=alt.X("t_db:Q", scale=x_scale), y=alt.Y("w:Q", scale=y_scale), detail="v:N")
)

# Volume labels
vol_text = (
    alt.Chart(vol_label_df)
    .mark_text(fontSize=11, color=CLR_VOL, align="left", dx=3, dy=-5, fontWeight="bold")
    .encode(x=alt.X("t_db:Q", scale=x_scale), y=alt.Y("w:Q", scale=y_scale), text="label:N")
)

# Comfort zone shaded area
comfort = (
    alt.Chart(comfort_df)
    .mark_area(opacity=0.12, color=CLR_COMFORT)
    .encode(x=alt.X("t_db:Q", scale=x_scale), y=alt.Y("w:Q", scale=y_scale), y2="w2:Q")
)

comfort_label = (
    alt.Chart(pd.DataFrame({"t_db": [23.0], "w": [10.5], "label": ["Comfort Zone"]}))
    .mark_text(fontSize=14, color="#27ae60", fontWeight="bold", fontStyle="italic")
    .encode(x=alt.X("t_db:Q", scale=x_scale), y=alt.Y("w:Q", scale=y_scale), text="label:N")
)

# Interactive selection for HVAC process points
point_selection = alt.selection_point(on="pointerover", nearest=True, fields=["t_db"])

# HVAC process path with tooltips
process_line = (
    alt.Chart(process_points)
    .mark_line(strokeWidth=3.5, color=CLR_PROCESS, point=alt.OverlayMarkDef(size=140, filled=True, color=CLR_PROCESS))
    .encode(
        x=alt.X("t_db:Q", scale=x_scale),
        y=alt.Y("w:Q", scale=y_scale),
        order="order:Q",
        tooltip=[
            alt.Tooltip("label:N", title="State Point"),
            alt.Tooltip("t_db:Q", title="Dry-Bulb (°C)", format=".1f"),
            alt.Tooltip("w:Q", title="Humidity (g/kg)", format=".1f"),
            alt.Tooltip("rh_pct:N", title="RH"),
        ],
    )
    .add_params(point_selection)
)

# Process labels (adjusted positions to avoid overlap)
outdoor_label = (
    alt.Chart(process_points[process_points["order"] == 0])
    .mark_text(fontSize=12, fontWeight="bold", color=CLR_PROCESS, align="right", dx=-12, dy=-14)
    .encode(x=alt.X("t_db:Q", scale=x_scale), y=alt.Y("w:Q", scale=y_scale), text="label:N")
)

supply_label = (
    alt.Chart(process_points[process_points["order"] == 1])
    .mark_text(fontSize=12, fontWeight="bold", color=CLR_PROCESS, align="left", dx=12, dy=14)
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
        outdoor_label,
        supply_label,
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
            subtitleColor="#888888",
            offset=12,
        ),
    )
    .configure_axis(
        labelFontSize=18,
        titleFontSize=22,
        titleColor="#444444",
        labelColor="#555555",
        grid=True,
        gridOpacity=0.12,
        gridColor="#cccccc",
        domainColor="#999999",
    )
    .configure_view(strokeWidth=0, fill=CLR_BG)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
