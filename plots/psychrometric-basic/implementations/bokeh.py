""" pyplots.ai
psychrometric-basic: Psychrometric Chart for HVAC
Library: bokeh 3.9.0 | Python 3.14.3
Quality: 88/100 | Created: 2026-03-15
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import Band, ColumnDataSource, HoverTool, Label, Title
from bokeh.plotting import figure
from bokeh.resources import CDN


# Constants
P_ATM = 101325.0  # Standard atmospheric pressure (Pa)
# ASHRAE saturation pressure coefficients (above 0°C)
C8, C9, C10, C11, C12, C13 = -5.8002206e3, 1.3914993, -4.8640239e-2, 4.1764768e-5, -1.4452093e-8, 6.5459673
# Below 0°C coefficients
C1, C2, C3, C4, C5, C6, C7 = -5.6745359e3, 6.3925247, -9.677843e-3, 6.2215701e-7, 2.0747825e-9, -9.484024e-13, 4.1635019

# Temperature range
t_db = np.linspace(-10, 50, 500)
tk = t_db + 273.15

# Saturation vapor pressure (vectorized)
psat = np.empty_like(tk)
above = tk >= 273.15
psat[above] = np.exp(
    C8 / tk[above] + C9 + C10 * tk[above] + C11 * tk[above] ** 2 + C12 * tk[above] ** 3 + C13 * np.log(tk[above])
)
psat[~above] = np.exp(
    C1 / tk[~above]
    + C2
    + C3 * tk[~above]
    + C4 * tk[~above] ** 2
    + C5 * tk[~above] ** 3
    + C6 * tk[~above] ** 4
    + C7 * np.log(tk[~above])
)

# Plot
p = figure(
    width=4800,
    height=2700,
    title="psychrometric-basic · bokeh · pyplots.ai",
    x_axis_label="Dry-Bulb Temperature (°C)",
    y_axis_label="Humidity Ratio (g/kg)",
    toolbar_location="above",
    tools="pan,wheel_zoom,reset,save",
    x_range=(-12, 52),
    y_range=(0, 30),
)

# --- Relative humidity curves (10% to 100%) ---
rh_colors = {
    1.0: "#1a5276",
    0.9: "#21618c",
    0.8: "#2874a6",
    0.7: "#2e86c1",
    0.6: "#3498db",
    0.5: "#5499c7",
    0.4: "#7fb3d8",
    0.3: "#6ca0c1",
    0.2: "#5b8fa8",
    0.1: "#4a7e90",
}

for rh_val in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
    pw = rh_val * psat
    w = 0.621998 * pw / (P_ATM - pw) * 1000  # g/kg
    mask = (w >= 0) & (w <= 30)
    t_plot = t_db[mask]
    w_plot = w[mask]
    lw = 5.0 if rh_val == 1.0 else 2.2
    alpha = 1.0 if rh_val == 1.0 else 0.85

    source = ColumnDataSource(data={"t": t_plot, "w": w_plot})
    line_r = p.line("t", "w", source=source, line_color=rh_colors[rh_val], line_width=lw, line_alpha=alpha)
    p.add_tools(
        HoverTool(
            renderers=[line_r],
            tooltips=[("RH", f"{int(rh_val * 100)}%"), ("Dry-Bulb", "@t{0.1} °C"), ("Humidity Ratio", "@w{0.1} g/kg")],
            line_policy="nearest",
        )
    )

    # Label - staggered positions along curves for readability
    if len(t_plot) > 0:
        label_text = f"{int(rh_val * 100)}%"
        # Place labels at staggered x-positions along the upper part of each curve
        rh_label_x = {1.0: 26, 0.9: 31, 0.8: 35, 0.7: 38, 0.6: 41, 0.5: 43, 0.4: 45, 0.3: 46, 0.2: 47, 0.1: 48}
        target_x = rh_label_x[rh_val]
        idx = np.argmin(np.abs(t_plot - target_x))
        if w_plot[idx] > 28:
            idx = np.argmin(np.abs(w_plot - 27))
        p.add_layout(
            Label(
                x=t_plot[idx],
                y=w_plot[idx],
                text=label_text,
                text_font_size="19pt",
                text_color=rh_colors[rh_val],
                text_font_style="bold" if rh_val == 1.0 else "normal",
                x_offset=6,
                y_offset=-3,
            )
        )

# --- Wet-bulb temperature lines ---
wb_temps = [0, 5, 10, 15, 20, 25, 30, 35]
for twb in wb_temps:
    t_range = np.linspace(twb, 50, 300)
    tk_wb = twb + 273.15
    ps_wb = (
        np.exp(C8 / tk_wb + C9 + C10 * tk_wb + C11 * tk_wb**2 + C12 * tk_wb**3 + C13 * np.log(tk_wb))
        if tk_wb >= 273.15
        else np.exp(C1 / tk_wb + C2 + C3 * tk_wb + C4 * tk_wb**2 + C5 * tk_wb**3 + C6 * tk_wb**4 + C7 * np.log(tk_wb))
    )
    ws_wb = 0.621998 * ps_wb / (P_ATM - ps_wb) * 1000
    w = ws_wb - 1.006 * (t_range - twb) / (2501.0 - 2.326 * twb) * 1000
    mask = (w >= 0) & (w <= 30) & (t_range >= -10)
    if np.any(mask):
        t_plot = t_range[mask]
        w_plot = w[mask]
        source = ColumnDataSource(data={"t": t_plot, "w": w_plot})
        wb_r = p.line(
            "t", "w", source=source, line_color="#e07b39", line_width=1.8, line_alpha=0.75, line_dash="dashed"
        )
        p.add_tools(
            HoverTool(
                renderers=[wb_r],
                tooltips=[("Wet-Bulb", f"{twb} °C"), ("Dry-Bulb", "@t{0.1} °C"), ("W", "@w{0.1} g/kg")],
                line_policy="nearest",
            )
        )
        # Label at upper-left portion of line (near saturation curve)
        if len(t_plot) > 5:
            mid = len(t_plot) // 3
            p.add_layout(
                Label(
                    x=t_plot[mid],
                    y=w_plot[mid],
                    text=f"{twb}°C wb",
                    text_font_size="18pt",
                    text_color="#c96a2d",
                    x_offset=2,
                    y_offset=-14,
                    text_alpha=0.9,
                )
            )

# --- Enthalpy lines (kJ/kg) - changed to warm rose/magenta for better separation from blue RH ---
enthalpy_color = "#b5338a"
enthalpy_label_color = "#9e2d78"
enthalpy_values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
for h in enthalpy_values:
    t_range = np.linspace(-10, 50, 300)
    w = (h - 1.006 * t_range) / (2501.0 + 1.86 * t_range) * 1000
    mask = (w >= 0) & (w <= 30) & (t_range >= -10) & (t_range <= 50)
    if np.any(mask):
        t_plot = t_range[mask]
        w_plot = w[mask]
        source = ColumnDataSource(data={"t": t_plot, "w": w_plot})
        enth_r = p.line(
            "t", "w", source=source, line_color=enthalpy_color, line_width=1.5, line_alpha=0.65, line_dash="dotted"
        )
        p.add_tools(
            HoverTool(
                renderers=[enth_r],
                tooltips=[("Enthalpy", f"{h} kJ/kg"), ("Dry-Bulb", "@t{0.1} °C"), ("Humidity Ratio", "@w{0.1} g/kg")],
                line_policy="nearest",
            )
        )
        # Label at upper-left end of each enthalpy line (high w) to separate from specific volume labels
        if len(t_plot) > 2:
            # Place label near top of line (high humidity ratio end)
            idx = 0
            for ii in range(len(t_plot)):
                if w_plot[ii] > 22:
                    idx = ii
                    break
                if w_plot[ii] > 12:
                    idx = ii
            p.add_layout(
                Label(
                    x=t_plot[idx],
                    y=w_plot[idx],
                    text=f"{h} kJ/kg",
                    text_font_size="16pt",
                    text_color=enthalpy_label_color,
                    text_alpha=0.9,
                    x_offset=-65,
                    y_offset=8,
                )
            )

# --- Specific volume lines (m³/kg) ---
sv_color = "#4e8c3f"
sv_label_color = "#3d7030"
sv_values = [0.78, 0.80, 0.82, 0.84, 0.86, 0.88, 0.90, 0.92]
for v in sv_values:
    t_range = np.linspace(-10, 50, 300)
    w = (v * 101.325 / (0.287055 * (t_range + 273.15)) - 1) / 1.6078 * 1000
    mask = (w >= 0) & (w <= 30) & (t_range >= -10) & (t_range <= 50)
    if np.any(mask):
        t_plot = t_range[mask]
        w_plot = w[mask]
        source = ColumnDataSource(data={"t": t_plot, "w": w_plot})
        sv_r = p.line(
            "t", "w", source=source, line_color=sv_color, line_width=1.5, line_alpha=0.65, line_dash="dashdot"
        )
        p.add_tools(
            HoverTool(
                renderers=[sv_r],
                tooltips=[("Specific Vol.", f"{v} m³/kg"), ("Dry-Bulb", "@t{0.1} °C"), ("W", "@w{0.1} g/kg")],
                line_policy="nearest",
            )
        )
        # Label at bottom of line (low w end)
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
                    text_font_size="16pt",
                    text_color=sv_label_color,
                    text_alpha=0.9,
                    x_offset=0,
                    y_offset=-18,
                )
            )

# --- Comfort zone using Band for idiomatic Bokeh ---
comfort_t = np.linspace(20, 26, 50)
comfort_psat = np.exp(
    C8 / (comfort_t + 273.15)
    + C9
    + C10 * (comfort_t + 273.15)
    + C11 * (comfort_t + 273.15) ** 2
    + C12 * (comfort_t + 273.15) ** 3
    + C13 * np.log(comfort_t + 273.15)
)
pw_lo = 0.3 * comfort_psat
pw_hi = 0.6 * comfort_psat
w_bottom = 0.621998 * pw_lo / (P_ATM - pw_lo) * 1000
w_top = 0.621998 * pw_hi / (P_ATM - pw_hi) * 1000

comfort_source = ColumnDataSource(data={"t": comfort_t, "w_lo": w_bottom, "w_hi": w_top})
band = Band(
    base="t",
    lower="w_lo",
    upper="w_hi",
    source=comfort_source,
    fill_color="#2980b9",
    fill_alpha=0.15,
    line_color="#2980b9",
    line_width=2.5,
    line_alpha=0.6,
)
p.add_layout(band)

mid_w = (w_bottom[25] + w_top[25]) / 2
p.add_layout(
    Label(
        x=23,
        y=mid_w,
        text="Comfort Zone",
        text_font_size="20pt",
        text_color="#1a6da0",
        text_font_style="bold",
        text_align="center",
    )
)

# --- HVAC process path: cooling and dehumidification ---
state1_t, state1_rh = 35, 0.60
state2_t, state2_rh = 15, 0.90
# Compute state1 humidity ratio
tk1 = state1_t + 273.15
ps1 = np.exp(C8 / tk1 + C9 + C10 * tk1 + C11 * tk1**2 + C12 * tk1**3 + C13 * np.log(tk1))
state1_w = 0.621998 * (state1_rh * ps1) / (P_ATM - state1_rh * ps1) * 1000
# Compute state2 humidity ratio
tk2 = state2_t + 273.15
ps2 = np.exp(C8 / tk2 + C9 + C10 * tk2 + C11 * tk2**2 + C12 * tk2**3 + C13 * np.log(tk2))
state2_w = 0.621998 * (state2_rh * ps2) / (P_ATM - state2_rh * ps2) * 1000

# Compute enthalpy change for annotation
h1 = 1.006 * state1_t + (state1_w / 1000) * (2501.0 + 1.86 * state1_t)
h2 = 1.006 * state2_t + (state2_w / 1000) * (2501.0 + 1.86 * state2_t)
delta_h = h2 - h1

process_source = ColumnDataSource(
    data={"t": [state1_t, state2_t], "w": [state1_w, state2_w], "label": ["Outdoor Air", "Supply Air"]}
)
p.line("t", "w", source=process_source, line_color="#c0392b", line_width=5.0, line_alpha=0.9)

# Arrowhead
x_span, y_span = 64.0, 30.0
dx_n = (state2_t - state1_t) / x_span
dy_n = (state2_w - state1_w) / y_span
length_n = np.sqrt(dx_n**2 + dy_n**2)
ux_n, uy_n = dx_n / length_n, dy_n / length_n
px_n, py_n = -uy_n, ux_n
ah_len, ah_w = 0.016, 0.007
p.patch(
    x=[
        state2_t,
        state2_t - ux_n * ah_len * x_span + px_n * ah_w * x_span,
        state2_t - ux_n * ah_len * x_span - px_n * ah_w * x_span,
    ],
    y=[
        state2_w,
        state2_w - uy_n * ah_len * y_span + py_n * ah_w * y_span,
        state2_w - uy_n * ah_len * y_span - py_n * ah_w * y_span,
    ],
    fill_color="#c0392b",
    line_color="#c0392b",
)

# State point markers with hover
state_source = ColumnDataSource(
    data={
        "t": [state1_t, state2_t],
        "w": [state1_w, state2_w],
        "name": ["Outdoor Air (35°C, 60% RH)", "Supply Air (15°C, 90% RH)"],
        "h": [f"{h1:.1f}", f"{h2:.1f}"],
    }
)
scatter_r = p.scatter("t", "w", source=state_source, size=20, color="#c0392b", line_color="white", line_width=3)
p.add_tools(
    HoverTool(
        renderers=[scatter_r],
        tooltips=[("State", "@name"), ("Dry-Bulb", "@t °C"), ("W", "@w{0.1} g/kg"), ("Enthalpy", "@h kJ/kg")],
    )
)

p.add_layout(
    Label(
        x=state1_t,
        y=state1_w,
        text="Outdoor Air (35°C, 60% RH)",
        text_font_size="17pt",
        text_color="#c0392b",
        text_font_style="bold",
        x_offset=12,
        y_offset=14,
    )
)
p.add_layout(
    Label(
        x=state2_t,
        y=state2_w,
        text="Supply Air (15°C, 90% RH)",
        text_font_size="17pt",
        text_color="#c0392b",
        text_font_style="bold",
        x_offset=12,
        y_offset=-24,
    )
)

# Energy annotation on the process path - data storytelling
mid_process_t = (state1_t + state2_t) / 2
mid_process_w = (state1_w + state2_w) / 2
p.add_layout(
    Label(
        x=mid_process_t,
        y=mid_process_w,
        text=f"Δh = {delta_h:.1f} kJ/kg",
        text_font_size="16pt",
        text_color="#922b21",
        text_font_style="italic",
        x_offset=-80,
        y_offset=16,
        background_fill_color="white",
        background_fill_alpha=0.7,
    )
)

# --- Style ---
p.title.text_font_size = "30pt"
p.title.text_color = "#1a2a3a"
p.title.text_font_style = "bold"
p.title.offset = 10

p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.axis_label_text_font_style = "bold"
p.yaxis.axis_label_text_font_style = "bold"
p.xaxis.axis_label_text_color = "#2c3e50"
p.yaxis.axis_label_text_color = "#2c3e50"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.xaxis.major_label_text_color = "#555555"
p.yaxis.major_label_text_color = "#555555"

p.xaxis.axis_line_width = 2
p.yaxis.axis_line_width = 2
p.xaxis.axis_line_color = "#555555"
p.yaxis.axis_line_color = "#555555"
p.xaxis.major_tick_line_color = "#777777"
p.yaxis.major_tick_line_color = "#777777"
p.xaxis.major_tick_line_width = 1.5
p.yaxis.major_tick_line_width = 1.5
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

p.xgrid.grid_line_color = "#d5d5d5"
p.ygrid.grid_line_color = "#d5d5d5"
p.xgrid.grid_line_alpha = 0.3
p.ygrid.grid_line_alpha = 0.3
p.xgrid.grid_line_dash = [4, 4]
p.ygrid.grid_line_dash = [4, 4]

p.background_fill_color = "#f7f9fb"
p.border_fill_color = "white"
p.outline_line_color = None

# Subtitle for context
p.add_layout(
    Title(
        text="Standard Atmosphere (101.325 kPa) · ASHRAE Psychrometric Properties",
        text_font_size="16pt",
        text_color="#7f8c8d",
        text_font_style="italic",
    ),
    "above",
)

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="psychrometric-basic · bokeh · pyplots.ai")
