"""pyplots.ai
psychrometric-basic: Psychrometric Chart for HVAC
Library: bokeh | Python 3.13
Quality: pending | Created: 2026-03-15
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import Label
from bokeh.plotting import figure
from bokeh.resources import CDN


# Constants
P_ATM = 101325.0  # Standard atmospheric pressure (Pa)


# Saturation vapor pressure (Pa) from dry-bulb temperature (°C) using ASHRAE formula
def _psat(t):
    tk = t + 273.15
    if isinstance(t, np.ndarray):
        result = np.empty_like(tk)
        mask = tk >= 273.15
        # Above 0°C
        c8, c9, c10, c11, c12, c13 = -5.8002206e3, 1.3914993, -4.8640239e-2, 4.1764768e-5, -1.4452093e-8, 6.5459673
        result[mask] = np.exp(
            c8 / tk[mask] + c9 + c10 * tk[mask] + c11 * tk[mask] ** 2 + c12 * tk[mask] ** 3 + c13 * np.log(tk[mask])
        )
        # Below 0°C
        c1, c2, c3, c4 = -5.6745359e3, 6.3925247, -9.677843e-3, 6.2215701e-7
        c5, c6, c7 = 2.0747825e-9, -9.484024e-13, 4.1635019
        result[~mask] = np.exp(
            c1 / tk[~mask]
            + c2
            + c3 * tk[~mask]
            + c4 * tk[~mask] ** 2
            + c5 * tk[~mask] ** 3
            + c6 * tk[~mask] ** 4
            + c7 * np.log(tk[~mask])
        )
        return result
    else:
        if tk >= 273.15:
            c8, c9, c10, c11, c12, c13 = -5.8002206e3, 1.3914993, -4.8640239e-2, 4.1764768e-5, -1.4452093e-8, 6.5459673
            return np.exp(c8 / tk + c9 + c10 * tk + c11 * tk**2 + c12 * tk**3 + c13 * np.log(tk))
        else:
            c1, c2, c3, c4 = -5.6745359e3, 6.3925247, -9.677843e-3, 6.2215701e-7
            c5, c6, c7 = 2.0747825e-9, -9.484024e-13, 4.1635019
            return np.exp(c1 / tk + c2 + c3 * tk + c4 * tk**2 + c5 * tk**3 + c6 * tk**4 + c7 * np.log(tk))


# Humidity ratio (g/kg) from dry-bulb temp (°C) and relative humidity (0-1)
def _humidity_ratio(t, rh):
    ps = _psat(t)
    pw = rh * ps
    w = 0.621998 * pw / (P_ATM - pw)
    return w * 1000  # g/kg


# Wet-bulb temperature to dry-bulb + humidity ratio curve
def _wetbulb_line(twb, t_range):
    ps_wb = _psat(twb)
    ws_wb = 0.621998 * ps_wb / (P_ATM - ps_wb) * 1000  # g/kg
    # Psychrometric relation: W = Ws_wb - 1.006 * (T - Twb) / (2501 - 2.326 * Twb) * 1000
    w = ws_wb - 1.006 * (t_range - twb) / (2501.0 - 2.326 * twb) * 1000
    return w


# Enthalpy (kJ/kg) to dry-bulb + humidity ratio
def _enthalpy_line(h, t_range):
    # h = 1.006*T + W/1000*(2501 + 1.86*T) => W = (h - 1.006*T) / (2501 + 1.86*T) * 1000
    w = (h - 1.006 * t_range) / (2501.0 + 1.86 * t_range) * 1000
    return w


# Specific volume line
def _specific_volume_line(v, t_range):
    # v = 0.287055 * (T+273.15) * (1 + 1.6078*W/1000) / 101.325
    # => W = (v * 101.325 / (0.287055 * (T+273.15)) - 1) / 1.6078 * 1000
    w = (v * 101.325 / (0.287055 * (t_range + 273.15)) - 1) / 1.6078 * 1000
    return w


# Data
t_db = np.linspace(-10, 50, 500)

# Plot
p = figure(
    width=4800,
    height=2700,
    title="psychrometric-basic · bokeh · pyplots.ai",
    x_axis_label="Dry-Bulb Temperature (°C)",
    y_axis_label="Humidity Ratio (g/kg)",
    toolbar_location=None,
    tools="",
    x_range=(-12, 52),
    y_range=(0, 30),
)

# Relative humidity curves (10% to 100%)
rh_colors = {
    1.0: "#306998",  # Saturation curve - prominent
    0.9: "#5a8faa",
    0.8: "#6fa0b8",
    0.7: "#84b1c6",
    0.6: "#99c2d4",
    0.5: "#a8ccdc",
    0.4: "#b8d6e4",
    0.3: "#c8e0ec",
    0.2: "#d8eaf4",
    0.1: "#e8f4fc",
}

for rh_val in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
    w = _humidity_ratio(t_db, rh_val)
    mask = (w >= 0) & (w <= 30)
    t_plot = t_db[mask]
    w_plot = w[mask]
    lw = 4 if rh_val == 1.0 else 1.5
    p.line(t_plot, w_plot, line_color=rh_colors[rh_val], line_width=lw, line_alpha=0.9)

    # Label at the right end of each curve
    if len(t_plot) > 0:
        idx = -1
        # Find a good label position (where w < 29 to stay in bounds)
        for ii in range(len(t_plot) - 1, -1, -1):
            if w_plot[ii] < 28:
                idx = ii
                break
        label_text = f"{int(rh_val * 100)}%"
        p.add_layout(
            Label(
                x=t_plot[idx],
                y=w_plot[idx],
                text=label_text,
                text_font_size="14pt",
                text_color=rh_colors[rh_val] if rh_val < 1.0 else "#306998",
                text_font_style="bold" if rh_val == 1.0 else "normal",
                x_offset=5,
                y_offset=5,
            )
        )

# Wet-bulb temperature lines
wb_temps = [0, 5, 10, 15, 20, 25, 30, 35]
for twb in wb_temps:
    t_range = np.linspace(twb, 50, 300)
    w = _wetbulb_line(twb, t_range)
    mask = (w >= 0) & (w <= 30) & (t_range >= -10)
    if np.any(mask):
        t_plot = t_range[mask]
        w_plot = w[mask]
        p.line(t_plot, w_plot, line_color="#e07b39", line_width=1.2, line_alpha=0.6, line_dash="dashed")
        # Label near the saturation curve (start of line)
        if len(t_plot) > 0:
            p.add_layout(
                Label(
                    x=t_plot[0],
                    y=w_plot[0],
                    text=f"{twb}°C",
                    text_font_size="12pt",
                    text_color="#e07b39",
                    x_offset=-30,
                    y_offset=8,
                )
            )

# Enthalpy lines (kJ/kg)
enthalpy_values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
for h in enthalpy_values:
    t_range = np.linspace(-10, 50, 300)
    w = _enthalpy_line(h, t_range)
    mask = (w >= 0) & (w <= 30) & (t_range >= -10) & (t_range <= 50)
    if np.any(mask):
        t_plot = t_range[mask]
        w_plot = w[mask]
        p.line(t_plot, w_plot, line_color="#8b5e3c", line_width=1.0, line_alpha=0.45, line_dash="dotted")
        # Label at upper end
        if len(t_plot) > 2:
            idx = 0
            for ii in range(len(t_plot)):
                if w_plot[ii] > 1 and w_plot[ii] < 29:
                    idx = ii
                    break
            p.add_layout(
                Label(
                    x=t_plot[idx],
                    y=w_plot[idx],
                    text=f"{h} kJ/kg",
                    text_font_size="11pt",
                    text_color="#8b5e3c",
                    text_alpha=0.7,
                    x_offset=-10,
                    y_offset=8,
                )
            )

# Specific volume lines (m³/kg)
sv_values = [0.78, 0.80, 0.82, 0.84, 0.86, 0.88, 0.90, 0.92]
for v in sv_values:
    t_range = np.linspace(-10, 50, 300)
    w = _specific_volume_line(v, t_range)
    mask = (w >= 0) & (w <= 30) & (t_range >= -10) & (t_range <= 50)
    if np.any(mask):
        t_plot = t_range[mask]
        w_plot = w[mask]
        p.line(t_plot, w_plot, line_color="#6b8e5e", line_width=1.0, line_alpha=0.45, line_dash="dashdot")
        # Label at bottom of line
        if len(t_plot) > 2:
            idx = -1
            for ii in range(len(t_plot) - 1, -1, -1):
                if w_plot[ii] < 2:
                    idx = ii
                    break
            p.add_layout(
                Label(
                    x=t_plot[idx],
                    y=w_plot[idx],
                    text=f"{v} m³/kg",
                    text_font_size="10pt",
                    text_color="#6b8e5e",
                    text_alpha=0.7,
                    x_offset=0,
                    y_offset=-18,
                )
            )

# Comfort zone (20-26°C, 30-60% RH) - follow RH curves for top/bottom boundaries
comfort_t_fine = np.linspace(20, 26, 50)
comfort_w_bottom = _humidity_ratio(comfort_t_fine, 0.3)
comfort_w_top = _humidity_ratio(comfort_t_fine, 0.6)
comfort_xs = np.concatenate([comfort_t_fine, comfort_t_fine[::-1]]).tolist()
comfort_ys = np.concatenate([comfort_w_bottom, comfort_w_top[::-1]]).tolist()
p.patch(
    comfort_xs, comfort_ys, fill_color="#306998", fill_alpha=0.10, line_color="#306998", line_width=2.5, line_alpha=0.4
)
p.add_layout(
    Label(
        x=23,
        y=(_humidity_ratio(23, 0.3) + _humidity_ratio(23, 0.6)) / 2,
        text="Comfort Zone",
        text_font_size="16pt",
        text_color="#306998",
        text_font_style="bold",
        text_align="center",
    )
)

# HVAC process path: cooling and dehumidification
# State 1: hot humid outdoor air (35°C, 60% RH)
# State 2: conditioned supply air (15°C, 90% RH) - typical AHU coil output
state1_t, state1_rh = 35, 0.60
state2_t, state2_rh = 15, 0.90
state1_w = _humidity_ratio(state1_t, state1_rh)
state2_w = _humidity_ratio(state2_t, state2_rh)

p.line([state1_t, state2_t], [state1_w, state2_w], line_color="#cc3333", line_width=4, line_alpha=0.85)

# Arrowhead - normalize in display space (account for aspect ratio)
x_scale = 64.0  # x range span
y_scale = 30.0  # y range span
dx_n = (state2_t - state1_t) / x_scale
dy_n = (state2_w - state1_w) / y_scale
length_n = np.sqrt(dx_n**2 + dy_n**2)
ux_n, uy_n = dx_n / length_n, dy_n / length_n
px_n, py_n = -uy_n, ux_n
ah_len, ah_w = 0.012, 0.005  # in normalized units
p.patch(
    x=[
        state2_t,
        state2_t - ux_n * ah_len * x_scale + px_n * ah_w * x_scale,
        state2_t - ux_n * ah_len * x_scale - px_n * ah_w * x_scale,
    ],
    y=[
        state2_w,
        state2_w - uy_n * ah_len * y_scale + py_n * ah_w * y_scale,
        state2_w - uy_n * ah_len * y_scale - py_n * ah_w * y_scale,
    ],
    fill_color="#cc3333",
    line_color="#cc3333",
)

# State point markers
p.scatter([state1_t, state2_t], [state1_w, state2_w], size=16, color="#cc3333", line_color="white", line_width=2)
p.add_layout(
    Label(
        x=state1_t,
        y=state1_w,
        text="Outdoor Air (35°C, 60% RH)",
        text_font_size="14pt",
        text_color="#cc3333",
        x_offset=8,
        y_offset=10,
    )
)
p.add_layout(
    Label(
        x=state2_t,
        y=state2_w,
        text="Supply Air (15°C, 90% RH)",
        text_font_size="14pt",
        text_color="#cc3333",
        x_offset=8,
        y_offset=-20,
    )
)

# Style
p.title.text_font_size = "28pt"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

p.xgrid.grid_line_color = "#cccccc"
p.ygrid.grid_line_color = "#cccccc"
p.xgrid.grid_line_alpha = 0.2
p.ygrid.grid_line_alpha = 0.2

p.background_fill_color = "#fafafa"
p.border_fill_color = "white"
p.outline_line_color = None

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="psychrometric-basic · bokeh · pyplots.ai")
