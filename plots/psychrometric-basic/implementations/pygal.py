""" pyplots.ai
psychrometric-basic: Psychrometric Chart for HVAC
Library: pygal 3.1.0 | Python 3.14.3
Quality: 77/100 | Created: 2026-03-15
"""

import math

import cairosvg
import numpy as np
import pygal
from pygal.style import Style


# Constants
P_ATM = 101325.0  # Pa (standard atmosphere)


def sat_pressure(t_celsius):
    """ASHRAE saturation vapor pressure (Pa) from dry-bulb temperature (°C)."""
    tk = t_celsius + 273.15
    if t_celsius >= 0:
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
    return math.exp(ln_p)


def humidity_ratio(t_celsius, rh):
    """Humidity ratio (g/kg) from temperature and relative humidity (0-1)."""
    pw = rh * sat_pressure(t_celsius)
    return 0.62198 * pw / (P_ATM - pw) * 1000


# Data — precompute all psychrometric curves
t_range = np.linspace(-10, 50, 250)
pws_arr = np.array([sat_pressure(float(t)) for t in t_range])

rh_levels = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1]
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
                w_gkg = humidity_ratio(t_f, rh_pct / 100)
                w_sat = humidity_ratio(t_f, 1.0)
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
                w_sat = humidity_ratio(t_f, 1.0)
                if 0 <= w_g <= min(30, w_sat + 0.2):
                    pts.append((round(t_f, 2), round(w_g, 3)))
                break
    if len(pts) > 2:
        pts.sort(key=lambda p: p[0])
        step = max(1, len(pts) // 25)
        sv_lines[sv_target] = pts[::step]

# Enthalpy lines (h = 1.006*t + w*(2501 + 1.86*t), w in kg/kg)
enthalpy_values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
enthalpy_lines = {}
for h_target in enthalpy_values:
    pts = []
    for t in np.linspace(-10, 50, 200):
        t_f = float(t)
        w_kgkg = (h_target - 1.006 * t_f) / (2501 + 1.86 * t_f)
        w_gkg = w_kgkg * 1000
        w_sat = humidity_ratio(t_f, 1.0)
        if 0 <= w_gkg <= min(30, w_sat + 0.2):
            pts.append((round(t_f, 2), round(w_gkg, 3)))
    if len(pts) > 2:
        pts.sort(key=lambda p: p[0])
        step = max(1, len(pts) // 25)
        enthalpy_lines[h_target] = pts[::step]

# Comfort zone polygon (20-26°C, 30-60% RH)
comfort_t = np.linspace(20, 26, 40)
comfort_bottom = [humidity_ratio(float(t), 0.30) for t in comfort_t]
comfort_top = [humidity_ratio(float(t), 0.60) for t in comfort_t]
comfort_pts = [(round(float(t), 2), round(w, 3)) for t, w in zip(comfort_t, comfort_bottom, strict=True)] + [
    (round(float(t), 2), round(w, 3)) for t, w in zip(reversed(comfort_t), reversed(comfort_top), strict=False)
]
comfort_pts.append(comfort_pts[0])

# HVAC process: cooling and dehumidification (35°C/60%RH → 24°C/50%RH)
hvac_states = [(35.0, round(humidity_ratio(35, 0.60), 3)), (24.0, round(humidity_ratio(24, 0.50), 3))]

# Color palette — distinct families per property type
blue_rh = ["#0d3b66", "#1a4d80", "#276099", "#3572b0", "#4384c4", "#5195d4", "#5fa5e0", "#6db5ea", "#7bc4f2", "#89d1f8"]
orange_wb = "#d4792a"
purple_sv = "#7b5ea7"
teal_enth = "#2a8a8a"

palette = tuple(blue_rh + [orange_wb] * 7 + [purple_sv] * 5 + [teal_enth] * 10 + ["#4caf6e", "#c62828"])

# Style
custom_style = Style(
    background="#ffffff",
    plot_background="#fafbfc",
    foreground="#2d2d2d",
    foreground_strong="#111111",
    foreground_subtle="#e8ebef",
    opacity=".85",
    opacity_hover="1",
    colors=palette,
    title_font_size=72,
    label_font_size=42,
    major_label_font_size=46,
    legend_font_size=34,
    value_font_size=34,
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
    show_legend=False,
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
    margin_bottom=60,
    margin_top=70,
    margin_left=80,
    margin_right=50,
    truncate_legend=-1,
    js=[],
)

# RH curves — saturation (100%) thickest, all visible
for rh in rh_levels:
    rh_pct = int(rh * 100)
    w = 5.5 if rh == 1.0 else max(2.2, 1.5 + rh * 2)
    chart.add(f"{rh_pct}% RH", rh_curves[rh], show_dots=False, stroke_style={"width": w, "linecap": "round"})

# Wet-bulb lines — dashed orange
for tw in wb_temps:
    chart.add(
        f"Tw={tw}°C",
        wb_lines.get(tw, []),
        show_dots=False,
        stroke_style={"width": 1.8, "dasharray": "12, 6", "linecap": "round"},
    )

# Specific volume lines — dotted purple
for sv in sv_values:
    chart.add(
        f"v={sv} m³/kg",
        sv_lines.get(sv, []),
        show_dots=False,
        stroke_style={"width": 1.5, "dasharray": "4, 8", "linecap": "round"},
    )

# Enthalpy lines — dash-dot teal
for h in enthalpy_values:
    chart.add(
        f"h={h} kJ/kg",
        enthalpy_lines.get(h, []),
        show_dots=False,
        stroke_style={"width": 1.4, "dasharray": "14, 4, 4, 4", "linecap": "round"},
    )

# Comfort zone — filled green
chart.add(
    "Comfort Zone (20–26°C, 30–60% RH)",
    comfort_pts,
    show_dots=False,
    fill=True,
    stroke_style={"width": 2.5, "linecap": "round"},
)

# HVAC process — bold red with dots at state points
chart.add(
    "Cooling & Dehumidification (A→B)",
    [
        {"value": hvac_states[0], "label": "State A: 35°C, 60% RH"},
        {"value": hvac_states[1], "label": "State B: 24°C, 50% RH"},
    ],
    show_dots=True,
    dots_size=14,
    stroke_style={"width": 4.5, "linecap": "round"},
)

# Render SVG first, then inject text labels directly into SVG before PNG export
svg_content = chart.render(is_unicode=True)

# Inject direct labels onto curves by adding SVG <text> elements
# Compute chart area coordinates from pygal's viewBox
# pygal uses viewBox="0 0 4800 2700" with margins
plot_left = 80 + 120  # margin_left + y-axis labels space
plot_right = 4800 - 50  # width - margin_right
plot_top = 70 + 80  # margin_top + title space
plot_bottom = 2700 - 60 - 80  # height - margin_bottom - x-axis space

x_min, x_max = -10, 50
y_min, y_max = 0, 30


def to_svg_x(val):
    return plot_left + (val - x_min) / (x_max - x_min) * (plot_right - plot_left)


def to_svg_y(val):
    return plot_bottom - (val - y_min) / (y_max - y_min) * (plot_bottom - plot_top)


labels_svg = []

# RH labels at right edge of each curve
rh_label_temps = {1.0: 18, 0.9: 22, 0.8: 26, 0.7: 29, 0.6: 32, 0.5: 35, 0.4: 38, 0.3: 41, 0.2: 44, 0.1: 47}
for rh in rh_levels:
    rh_pct = int(rh * 100)
    t_l = rh_label_temps[rh]
    w_l = humidity_ratio(t_l, rh)
    if 0 < w_l < 30:
        sx, sy = to_svg_x(t_l), to_svg_y(w_l)
        labels_svg.append(
            f'<text x="{sx}" y="{sy - 8}" font-size="34" font-family="Trebuchet MS, sans-serif" '
            f'fill="#0d3b66" font-weight="bold" text-anchor="middle">{rh_pct}%</text>'
        )

# Wet-bulb labels near lower-right end of each line (avoid overlap with RH labels)
for tw in wb_temps:
    pts = wb_lines.get(tw, [])
    if pts:
        p = pts[-2] if len(pts) > 2 else pts[-1]
        sx, sy = to_svg_x(p[0]), to_svg_y(p[1])
        labels_svg.append(
            f'<text x="{sx + 10}" y="{sy + 5}" font-size="28" font-family="Trebuchet MS, sans-serif" '
            f'fill="{orange_wb}" font-weight="bold" text-anchor="start">Tw {tw}°C</text>'
        )

# Specific volume labels
for sv in sv_values:
    pts = sv_lines.get(sv, [])
    if pts:
        p = pts[len(pts) // 4]
        sx, sy = to_svg_x(p[0]), to_svg_y(p[1])
        labels_svg.append(
            f'<text x="{sx}" y="{sy - 8}" font-size="28" font-family="Trebuchet MS, sans-serif" '
            f'fill="{purple_sv}" text-anchor="middle">{sv}</text>'
        )

# Enthalpy labels near lower end of line (every other to reduce clutter)
for h in [10, 30, 50, 70, 90]:
    pts = enthalpy_lines.get(h, [])
    if pts:
        p = pts[-2] if len(pts) > 2 else pts[-1]
        sx, sy = to_svg_x(p[0]), to_svg_y(p[1])
        labels_svg.append(
            f'<text x="{sx}" y="{sy + 30}" font-size="28" font-family="Trebuchet MS, sans-serif" '
            f'fill="{teal_enth}" font-weight="bold" text-anchor="middle">h={h}</text>'
        )

# Comfort zone label
cz_x, cz_y = 23, (humidity_ratio(23, 0.45))
sx, sy = to_svg_x(cz_x), to_svg_y(cz_y)
labels_svg.append(
    f'<text x="{sx}" y="{sy}" font-size="36" font-family="Trebuchet MS, sans-serif" '
    f'fill="#2e7d32" font-weight="bold" text-anchor="middle">Comfort Zone</text>'
)

# HVAC state point labels
sx_a, sy_a = to_svg_x(hvac_states[0][0]), to_svg_y(hvac_states[0][1])
labels_svg.append(
    f'<text x="{sx_a + 20}" y="{sy_a - 20}" font-size="36" font-family="Trebuchet MS, sans-serif" '
    f'fill="#c62828" font-weight="bold" text-anchor="start">A (35°C)</text>'
)
sx_b, sy_b = to_svg_x(hvac_states[1][0]), to_svg_y(hvac_states[1][1])
labels_svg.append(
    f'<text x="{sx_b - 20}" y="{sy_b - 20}" font-size="36" font-family="Trebuchet MS, sans-serif" '
    f'fill="#c62828" font-weight="bold" text-anchor="end">B (24°C)</text>'
)

# Insert labels before closing </svg>
label_block = "\n".join(labels_svg)
svg_labeled = svg_content.replace("</svg>", f"{label_block}\n</svg>")

# Save labeled SVG as HTML and render to PNG via cairosvg
with open("plot.html", "w") as f:
    f.write(svg_labeled)

cairosvg.svg2png(bytestring=svg_labeled.encode("utf-8"), write_to="plot.png")
