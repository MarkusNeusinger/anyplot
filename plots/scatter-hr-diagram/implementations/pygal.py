""" pyplots.ai
scatter-hr-diagram: Hertzsprung-Russell Diagram
Library: pygal 3.1.0 | Python 3.14.3
Quality: 72/100 | Created: 2026-03-07
"""

import numpy as np
import pygal
from pygal.style import Style


# Data — synthetic stellar populations for the HR diagram
np.random.seed(42)

# Main sequence stars (diagonal band from hot/bright to cool/dim)
n_main = 200
main_temp = np.random.uniform(3000, 35000, n_main)
main_log_lum = np.interp(main_temp, [3000, 5000, 8000, 15000, 35000], [-2, -0.5, 1.5, 3.5, 5.5])
main_log_lum += np.random.normal(0, 0.3, n_main)

# Red giants (cool but luminous)
n_giants = 40
giant_temp = np.random.uniform(3200, 5500, n_giants)
giant_log_lum = np.random.uniform(1.5, 3.2, n_giants)

# Supergiants (very luminous, range of temperatures)
n_super = 15
super_temp = np.random.uniform(3500, 25000, n_super)
super_log_lum = np.random.uniform(4.0, 5.8, n_super)

# White dwarfs (hot but very dim)
n_wd = 30
wd_temp = np.random.uniform(5000, 30000, n_wd)
wd_log_lum = np.random.uniform(-4, -1.5, n_wd)

# The Sun as reference
sun_temp = 5778.0
sun_log_lum = 0.0

# All stars combined
all_temps = np.concatenate([main_temp, giant_temp, super_temp, wd_temp])
all_log_lums = np.concatenate([main_log_lum, giant_log_lum, super_log_lum, wd_log_lum])

# Spectral type classification based on temperature
# Use negative temperature for x-axis to reverse direction (hot left, cool right)
spectral_bounds = [
    ("O/B Stars", 10000, 50000),
    ("A Stars", 7500, 10000),
    ("F/G Stars", 5200, 7500),
    ("K Stars", 3700, 5200),
    ("M Stars", 2000, 3700),
]

groups = {name: [] for name, _, _ in spectral_bounds}
for t, log_l in zip(all_temps, all_log_lums, strict=True):
    for name, lo, hi in spectral_bounds:
        if lo <= t < hi or (name == "O/B Stars" and t >= hi):
            groups[name].append((-float(t), float(log_l)))
            break

# Style — spectral colors matching astrophysical convention
font = "DejaVu Sans, Helvetica, Arial, sans-serif"
custom_style = Style(
    background="white",
    plot_background="#fafafa",
    foreground="#2a2a2a",
    foreground_strong="#2a2a2a",
    foreground_subtle="#e0e0e0",
    guide_stroke_color="#e0e0e0",
    colors=("#6699ff", "#bbccff", "#ffdd44", "#ff9933", "#ee4422", "#222222"),
    font_family=font,
    title_font_family=font,
    title_font_size=52,
    label_font_size=38,
    major_label_font_size=36,
    legend_font_size=32,
    legend_font_family=font,
    value_font_size=26,
    tooltip_font_size=26,
    tooltip_font_family=font,
    opacity=0.7,
    opacity_hover=0.95,
)

# Chart — XY scatter with negated x-axis for reversed temperature
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="Hertzsprung-Russell Diagram \u00b7 scatter-hr-diagram \u00b7 pygal \u00b7 pyplots.ai",
    x_title="\u2190 Surface Temperature (K) \u2192 Cool",
    y_title="log\u2081\u2080 Luminosity (L\u2609)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=6,
    legend_box_size=22,
    stroke=False,
    dots_size=7,
    show_x_guides=True,
    show_y_guides=True,
    xrange=(-40000, -2000),
    range=(-5, 7),
    x_value_formatter=lambda x: f"{abs(x):,.0f} K",
    value_formatter=lambda y: f"{y:.1f}",
    margin_bottom=100,
    margin_left=80,
    margin_right=40,
    margin_top=50,
    truncate_legend=-1,
    print_values=False,
    js=[],
)

# Add each spectral group as a separate series
series_order = ["O/B Stars", "A Stars", "F/G Stars", "K Stars", "M Stars"]
for stype in series_order:
    pts = groups.get(stype, [])
    chart.add(stype, pts, stroke=False)

# Add the Sun as a distinct reference point
chart.add(
    "Sun \u2609",
    [{"value": (-sun_temp, sun_log_lum), "label": "The Sun (5778 K, 1 L\u2609)"}],
    stroke=False,
    dots_size=14,
)

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
