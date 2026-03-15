""" pyplots.ai
psychrometric-basic: Psychrometric Chart for HVAC
Library: pygal 3.1.0 | Python 3.14.3
Quality: 72/100 | Created: 2026-03-15
"""

import math

import numpy as np
import pygal
from pygal.style import Style


# Constants
P_ATM = 101325.0  # Pa (standard atmosphere)

# Data — precompute all psychrometric curves
t_range = np.linspace(-10, 50, 250)
rh_levels = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1]

# Precompute saturation vapor pressure for each temperature (ASHRAE formula)
pws_arr = np.zeros(len(t_range))
for i, t in enumerate(t_range):
    tk = t + 273.15
    if t >= 0:
        ln_p = (
            -5.8002206e3 / tk
            + 1.3914993
            - 4.8640239e-2 * tk
            + 4.1764768e-5 * tk**2
            - 1.4452093e-8 * tk**3
            + 6.5459673 * math.log(tk)
        )
    else:
        ln_p = (
            -5.6745359e3 / tk
            + 6.3925247
            - 9.6778430e-3 * tk
            + 6.2215701e-7 * tk**2
            + 2.0747825e-9 * tk**3
            - 9.4840240e-13 * tk**4
            + 4.1635019 * math.log(tk)
        )
    pws_arr[i] = math.exp(ln_p)

# Humidity ratio (g/kg) for each (temperature, RH) pair
rh_curves = {}
for rh in rh_levels:
    pts = []
    for i, t in enumerate(t_range):
        pw = rh * pws_arr[i]
        w_gkg = 0.62198 * pw / (P_ATM - pw) * 1000
        if 0 <= w_gkg <= 30:
            pts.append((round(float(t), 2), round(w_gkg, 3)))
    rh_curves[rh] = pts

# Wet-bulb temperature lines (Stull 2011 approximation)
wb_temps = [0, 5, 10, 15, 20, 25, 30]
wb_lines = {}
for tw_target in wb_temps:
    pts = []
    for t in np.linspace(max(-10, tw_target), min(tw_target + 30, 50), 100):
        t_f = float(t)
        for rh_pct in np.linspace(1, 100, 500):
            tw = (
                t_f * math.atan(0.151977 * math.sqrt(rh_pct + 8.313659))
                + math.atan(t_f + rh_pct)
                - math.atan(rh_pct - 1.676331)
                + 0.00391838 * rh_pct**1.5 * math.atan(0.023101 * rh_pct)
                - 4.686035
            )
            if abs(tw - tw_target) < 0.25:
                tk = t_f + 273.15
                ln_p = (
                    (
                        -5.8002206e3 / tk
                        + 1.3914993
                        - 4.8640239e-2 * tk
                        + 4.1764768e-5 * tk**2
                        - 1.4452093e-8 * tk**3
                        + 6.5459673 * math.log(tk)
                    )
                    if t_f >= 0
                    else (
                        -5.6745359e3 / tk
                        + 6.3925247
                        - 9.6778430e-3 * tk
                        + 6.2215701e-7 * tk**2
                        + 2.0747825e-9 * tk**3
                        - 9.4840240e-13 * tk**4
                        + 4.1635019 * math.log(tk)
                    )
                )
                pw = (rh_pct / 100) * math.exp(ln_p)
                w_gkg = 0.62198 * pw / (P_ATM - pw) * 1000
                pw_sat = math.exp(ln_p)
                w_sat = 0.62198 * pw_sat / (P_ATM - pw_sat) * 1000
                if 0 <= w_gkg <= min(30, w_sat + 0.2):
                    pts.append((round(t_f, 2), round(w_gkg, 3)))
                break
    if len(pts) > 2:
        pts.sort(key=lambda p: p[0])
        step = max(1, len(pts) // 30)
        wb_lines[tw_target] = pts[::step]

# Specific volume lines
sv_values = [0.80, 0.84, 0.88, 0.92, 0.96]
sv_lines = {}
for sv_target in sv_values:
    pts = []
    for t in np.linspace(-10, 50, 200):
        t_f = float(t)
        tk = t_f + 273.15
        for w_test in np.linspace(0, 0.030, 300):
            sv_calc = 0.287042 * tk * (1 + 1.6078 * w_test) / (P_ATM / 1000)
            if abs(sv_calc - sv_target) < 0.0008:
                w_g = w_test * 1000
                ln_p = (
                    (
                        -5.8002206e3 / tk
                        + 1.3914993
                        - 4.8640239e-2 * tk
                        + 4.1764768e-5 * tk**2
                        - 1.4452093e-8 * tk**3
                        + 6.5459673 * math.log(tk)
                    )
                    if t_f >= 0
                    else (
                        -5.6745359e3 / tk
                        + 6.3925247
                        - 9.6778430e-3 * tk
                        + 6.2215701e-7 * tk**2
                        + 2.0747825e-9 * tk**3
                        - 9.4840240e-13 * tk**4
                        + 4.1635019 * math.log(tk)
                    )
                )
                w_sat = 0.62198 * math.exp(ln_p) / (P_ATM - math.exp(ln_p)) * 1000
                if 0 <= w_g <= min(30, w_sat + 0.2):
                    pts.append((round(t_f, 2), round(w_g, 3)))
                break
    if len(pts) > 2:
        pts.sort(key=lambda p: p[0])
        step = max(1, len(pts) // 25)
        sv_lines[sv_target] = pts[::step]

# Comfort zone polygon (20-26°C, 30-60% RH)
comfort_t = np.linspace(20, 26, 40)
comfort_bottom = []
comfort_top = []
for t in comfort_t:
    tk = float(t) + 273.15
    ln_p = (
        -5.8002206e3 / tk
        + 1.3914993
        - 4.8640239e-2 * tk
        + 4.1764768e-5 * tk**2
        - 1.4452093e-8 * tk**3
        + 6.5459673 * math.log(tk)
    )
    pws = math.exp(ln_p)
    pw_30 = 0.30 * pws
    pw_60 = 0.60 * pws
    comfort_bottom.append(0.62198 * pw_30 / (P_ATM - pw_30) * 1000)
    comfort_top.append(0.62198 * pw_60 / (P_ATM - pw_60) * 1000)

comfort_pts = [
    (round(float(t), 2), round(w, 3)) for t, w in zip(comfort_t, comfort_bottom, strict=True)
] + [
    (round(float(t), 2), round(w, 3))
    for t, w in zip(reversed(comfort_t), reversed(comfort_top), strict=False)
]
comfort_pts.append(comfort_pts[0])

# HVAC process: cooling and dehumidification (35°C/60%RH → 24°C/50%RH)
hvac_states = []
for t_s, rh_s in [(35, 0.60), (24, 0.50)]:
    tk = t_s + 273.15
    ln_p = (
        -5.8002206e3 / tk
        + 1.3914993
        - 4.8640239e-2 * tk
        + 4.1764768e-5 * tk**2
        - 1.4452093e-8 * tk**3
        + 6.5459673 * math.log(tk)
    )
    pw = rh_s * math.exp(ln_p)
    w_gkg = 0.62198 * pw / (P_ATM - pw) * 1000
    hvac_states.append((float(t_s), round(w_gkg, 3)))

# Color palette — one per series in order
# 10 RH (blue gradient) + 7 wet-bulb (orange) + 5 volume (purple) + comfort + HVAC
palette = (
    "#1a4971",
    "#306998",
    "#4a82ad",
    "#6399be",
    "#7baece",
    "#93c1da",
    "#a9d0e3",
    "#bfddeb",
    "#d4e9f2",
    "#e6f1f7",
    "#e8913a",
    "#e8913a",
    "#e8913a",
    "#e8913a",
    "#e8913a",
    "#e8913a",
    "#e8913a",
    "#9575b5",
    "#9575b5",
    "#9575b5",
    "#9575b5",
    "#9575b5",
    "#4caf6e",
    "#d04a3e",
)

# Style
custom_style = Style(
    background="#ffffff",
    plot_background="#fafbfc",
    foreground="#2d2d2d",
    foreground_strong="#111111",
    foreground_subtle="#e8ebef",
    opacity=".80",
    opacity_hover="1",
    colors=palette,
    title_font_size=72,
    label_font_size=42,
    major_label_font_size=46,
    legend_font_size=30,
    value_font_size=24,
    stroke_width=2.5,
    title_font_family="Trebuchet MS, Helvetica Neue, sans-serif",
    label_font_family="Trebuchet MS, Helvetica Neue, sans-serif",
    major_label_font_family="Trebuchet MS, Helvetica Neue, sans-serif",
    legend_font_family="Trebuchet MS, Helvetica Neue, sans-serif",
    value_font_family="Trebuchet MS, Helvetica Neue, sans-serif",
    tooltip_font_size=24,
    tooltip_font_family="Trebuchet MS, Helvetica Neue, sans-serif",
    transition="150ms ease-in",
    value_colors=(),
    guide_stroke_color="#eceef1",
    major_guide_stroke_color="#dde1e6",
)

# Chart
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="psychrometric-basic · pygal · pyplots.ai",
    x_title="Dry-Bulb Temperature (°C)",
    y_title="Humidity Ratio (g/kg)",
    show_legend=True,
    legend_at_bottom=True,
    legend_box_size=22,
    dots_size=0,
    stroke=True,
    show_x_guides=True,
    show_y_guides=True,
    xrange=(-10, 50),
    range=(0, 30),
    x_labels=list(range(-10, 55, 5)),
    y_labels=list(range(0, 32, 2)),
    x_labels_major_every=2,
    y_labels_major_every=5,
    show_minor_x_labels=True,
    show_minor_y_labels=True,
    print_values=False,
    tooltip_border_radius=8,
    tooltip_fancy_mode=True,
    explicit_size=True,
    spacing=25,
    margin_bottom=120,
    margin_top=70,
    margin_left=80,
    margin_right=50,
    truncate_legend=-1,
    js=[],
)

# RH curves — saturation (100%) drawn thickest
rh_names = {
    1.0: "100% RH (Saturation)",
    0.9: "90% RH",
    0.8: "80% RH",
    0.7: "70% RH",
    0.6: "60% RH",
    0.5: "50% RH",
    0.4: "40% RH",
    0.3: "30% RH",
    0.2: "20% RH",
    0.1: "10% RH",
}
for rh in rh_levels:
    w = 5 if rh == 1.0 else 2.0
    chart.add(rh_names[rh], rh_curves[rh], show_dots=False, stroke_style={"width": w, "linecap": "round"})

# Wet-bulb lines — dashed orange
for tw in wb_temps:
    chart.add(
        "Tw = {}°C".format(tw),
        wb_lines.get(tw, []),
        show_dots=False,
        stroke_style={"width": 1.5, "dasharray": "10, 6", "linecap": "round"},
    )

# Specific volume lines — dotted purple
for sv in sv_values:
    chart.add(
        "v = {} m³/kg".format(sv),
        sv_lines.get(sv, []),
        show_dots=False,
        stroke_style={"width": 1.2, "dasharray": "4, 7", "linecap": "round"},
    )

# Comfort zone — filled green
chart.add(
    "Comfort Zone (20-26°C, 30-60% RH)",
    comfort_pts,
    show_dots=False,
    fill=True,
    stroke_style={"width": 2.5, "linecap": "round"},
)

# HVAC process — bold red with dots at state points
chart.add(
    "Cooling & Dehumidification",
    hvac_states,
    show_dots=True,
    dots_size=14,
    stroke_style={"width": 4.5, "linecap": "round"},
)

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
