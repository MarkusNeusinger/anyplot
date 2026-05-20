"""anyplot.ai
skewt-logp-atmospheric: Skew-T Log-P Atmospheric Diagram
Library: pygal | Python 3.13
Quality: pending | Updated: 2026-05-20
"""

import os

import numpy as np
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

OKABE_ITO = ("#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442")

# Data — realistic mid-latitude atmospheric sounding
np.random.seed(42)
pressure = np.array([1000, 925, 850, 700, 500, 400, 300, 250, 200, 150, 100])
temperature = np.array([25, 20, 15, 5, -15, -28, -45, -52, -58, -62, -55])
dewpoint = np.array([18, 15, 12, -2, -22, -38, -55, -60, -65, -70, -65])

log_p = np.log10(1000.0 / pressure)
skew_factor = 35
temp_skewed = temperature + skew_factor * log_p
dewpoint_skewed = dewpoint + skew_factor * log_p

# Style
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=OKABE_ITO,
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=2.5,
)

log_p_values = [0, 0.033, 0.07, 0.155, 0.301, 0.398, 0.523, 0.602, 0.699, 0.824, 1.0]
p_labels = ["1000", "925", "850", "700", "500", "400", "300", "250", "200", "150", "100"]

# Plot
chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title="skewt-logp-atmospheric · python · pygal · anyplot.ai",
    x_title="Temperature (°C, skewed 45°)",
    y_title="Pressure (hPa)",
    show_dots=True,
    dots_size=6,
    stroke_style={"width": 4},
    show_x_guides=True,
    show_y_guides=True,
    x_label_rotation=0,
    show_legend=True,
    range=(0, 1.02),
    xrange=(-50, 75),
    y_labels=[{"value": v, "label": lbl} for v, lbl in zip(log_p_values, p_labels, strict=False)],
    truncate_legend=-1,
    legend_box_size=28,
    margin_right=380,
)

# Temperature profile (solid line with markers)
temp_points = [(float(temp_skewed[i]), float(log_p[i])) for i in range(len(pressure))]
chart.add("Temperature", temp_points, stroke_style={"width": 6})

# Dewpoint profile (dashed line with markers)
dewpoint_points = [(float(dewpoint_skewed[i]), float(log_p[i])) for i in range(len(pressure))]
chart.add("Dewpoint", dewpoint_points, stroke_style={"width": 5, "dasharray": "15,8"})

# Dry adiabat (θ=300K)
theta = 300
dry_adiabat_points = []
for p in np.linspace(1000, 100, 25):
    lp = np.log10(1000.0 / p)
    t_adiabat = theta * (p / 1000.0) ** 0.286 - 273.15
    t_skewed = t_adiabat + skew_factor * lp
    if -50 <= t_skewed <= 75:
        dry_adiabat_points.append((float(t_skewed), float(lp)))
chart.add("Dry Adiabat θ=300K", dry_adiabat_points, show_dots=False, stroke_style={"width": 3, "dasharray": "6,4"})

# Moist adiabat (starting 20°C surface)
moist_points = []
t_current = 20.0
for p in np.linspace(1000, 150, 20):
    lp = np.log10(1000.0 / p)
    t_skewed = t_current + skew_factor * lp
    if -50 <= t_skewed <= 75:
        moist_points.append((float(t_skewed), float(lp)))
    t_current -= 4.0
chart.add("Moist Adiabat", moist_points, show_dots=False, stroke_style={"width": 3, "dasharray": "10,5"})

# Mixing ratio line (r=10 g/kg)
mr_points = []
mr = 10
for p in np.linspace(1000, 300, 15):
    lp = np.log10(1000.0 / p)
    e = mr * p / (622 + mr)
    if e > 0:
        td = (243.5 * np.log(e / 6.112)) / (17.67 - np.log(e / 6.112))
        td_skewed = td + skew_factor * lp
        if -50 <= td_skewed <= 75:
            mr_points.append((float(td_skewed), float(lp)))
chart.add("Mixing Ratio r=10g/kg", mr_points, show_dots=False, stroke_style={"width": 2, "dasharray": "4,6"})

# Isotherms (0°C and -20°C reference lines)
for isotherm in [0, -20]:
    iso_points = []
    for lp in np.linspace(0, 1.0, 15):
        t_skewed = isotherm + skew_factor * lp
        if -50 <= t_skewed <= 75:
            iso_points.append((float(t_skewed), float(lp)))
    chart.add(f"{isotherm}°C Isotherm", iso_points, show_dots=False, stroke_style={"width": 2, "dasharray": "8,4"})

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
