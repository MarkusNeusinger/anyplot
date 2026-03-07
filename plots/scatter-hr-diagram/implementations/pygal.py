""" pyplots.ai
scatter-hr-diagram: Hertzsprung-Russell Diagram
Library: pygal 3.1.0 | Python 3.14.3
Quality: 87/100 | Created: 2026-03-07
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
# Use negative log10(temperature) for x-axis: reverses direction AND spreads cool stars
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
            groups[name].append((-np.log10(float(t)), float(log_l)))
            break

# Style — spectral colors matching astrophysical convention
font = "DejaVu Sans, Helvetica, Arial, sans-serif"
custom_style = Style(
    background="white",
    plot_background="#f5f5f0",
    foreground="#2a2a2a",
    foreground_strong="#2a2a2a",
    foreground_subtle="#d8d8d8",
    guide_stroke_color="#d8d8d8",
    colors=(
        "#3366cc",  # O/B Stars — strong blue
        "#9966cc",  # A Stars — medium purple (distinct from blue)
        "#ffcc22",  # F/G Stars — golden yellow
        "#ee8833",  # K Stars — orange
        "#cc2211",  # M Stars — deep red
        "#111111",  # Sun marker — black
    ),
    font_family=font,
    title_font_family=font,
    title_font_size=52,
    label_font_size=38,
    major_label_font_size=36,
    legend_font_size=30,
    legend_font_family=font,
    value_font_size=48,
    tooltip_font_size=28,
    tooltip_font_family=font,
    opacity=0.65,
    opacity_hover=0.95,
)

# Custom x-axis labels mapping -log10(T) to temperature in K
x_label_temps = [40000, 25000, 10000, 7500, 5000, 3500, 2500]
x_labels = [{"value": -np.log10(t), "label": f"{t:,} K"} for t in x_label_temps]

# Dot sizes per spectral group — smaller for crowded cool stars, larger for sparse hot stars
dot_sizes = {"O/B Stars": 10, "A Stars": 9, "F/G Stars": 8, "K Stars": 6, "M Stars": 5}

# Chart — XY scatter with -log10(T) x-axis for reversed, spread temperature
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="scatter-hr-diagram \u00b7 pygal \u00b7 pyplots.ai",
    x_title="Hot  \u2190  Surface Temperature (K)  \u2192  Cool",
    y_title="log\u2081\u2080 Luminosity (L\u2609)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=6,
    legend_box_size=22,
    stroke=False,
    dots_size=8,
    show_x_guides=True,
    show_y_guides=True,
    x_labels=x_labels,
    x_label_rotation=-25,
    xrange=(-np.log10(45000), -np.log10(2200)),
    range=(-5, 7.5),
    x_value_formatter=lambda x: f"{10 ** abs(x):,.0f} K",
    value_formatter=lambda y: f"{y:.1f}",
    margin_bottom=110,
    margin_left=80,
    margin_right=60,
    margin_top=50,
    truncate_legend=-1,
    print_labels=True,
    print_values=False,
    css=[
        "file://style.css",
        "file://graph.css",
        (
            "inline:"
            ".label{font-size:52px !important; font-weight:bold !important;"
            " font-family:DejaVu Sans, sans-serif !important;"
            " fill:#444 !important; paint-order:stroke fill;"
            " stroke:white !important; stroke-width:6px !important;}"
        ),
    ],
    js=[],
)

# Add each spectral group as a separate series with per-group dot sizes
series_order = ["O/B Stars", "A Stars", "F/G Stars", "K Stars", "M Stars"]
for stype in series_order:
    pts = groups.get(stype, [])
    chart.add(stype, pts, stroke=False, dots_size=dot_sizes[stype])

# Add the Sun as a distinct reference point
chart.add(
    "Sun \u2609",
    [{"value": (-np.log10(sun_temp), sun_log_lum), "label": "The Sun (5,778 K, 1 L\u2609)"}],
    stroke=False,
    dots_size=16,
)

# Region labels — use None title to keep them out of the legend
# Positioned at representative locations with CSS-styled label text
region_labels = [
    ("Main Sequence", -np.log10(18000), 3.0),
    ("Red Giants", -np.log10(3800), 2.8),
    ("Supergiants", -np.log10(12000), 6.2),
    ("White Dwarfs", -np.log10(18000), -3.0),
]
for region_name, rx, ry in region_labels:
    chart.add(None, [{"value": (rx, ry), "label": region_name}], stroke=False, dots_size=2, show_dots=True)

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
