""" pyplots.ai
bubble-basic: Basic Bubble Chart
Library: pygal 3.1.0 | Python 3.14.3
Quality: 78/100 | Created: 2026-02-16
"""

import numpy as np
import pygal
from pygal.style import Style


# Data — City comparison: population density vs avg commute time, bubble = green space (%)
np.random.seed(42)
n_cities = 35

population_density = np.random.uniform(1500, 14000, n_cities)  # people per sq km
commute_time = 16 + population_density / 900 + np.random.normal(0, 2.0, n_cities)  # minutes
green_space_pct = np.clip(48 - population_density / 450 + np.random.normal(0, 10, n_cities), 5, 52)

# Area-scaled bubble sizing via 8 tiers for finer granularity
gs_min, gs_max = green_space_pct.min(), green_space_pct.max()
bubble_norm = (green_space_pct - gs_min) / (gs_max - gs_min)

n_tiers = 8
tier_bins = np.digitize(bubble_norm, np.linspace(0, 1, n_tiers + 1)[1:-1])  # 0..n_tiers-1

# Area-scaled sizes: proportional to sqrt for perceptual accuracy
tier_sizes = [int(16 + 54 * ((t + 0.5) / n_tiers) ** 0.5) for t in range(n_tiers)]

# Build tier labels showing green-space range per bin
bin_edges_pct = np.linspace(gs_min, gs_max, n_tiers + 1)
tier_labels = [f"{bin_edges_pct[t]:.0f}–{bin_edges_pct[t + 1]:.0f}% green" for t in range(n_tiers)]

# Refined sequential palette (indigo → teal → amber), 8 steps, colorblind-safe
tier_colors = [
    "#4a1486",  # deep indigo
    "#6a51a3",  # purple
    "#2171b5",  # royal blue
    "#2a9d8f",  # teal
    "#52b788",  # emerald
    "#8ab17d",  # sage
    "#d4a843",  # dark gold
    "#e9c46a",  # amber
]

# Group data by tier using np.digitize results
bins = {t: [] for t in range(n_tiers)}
for i in range(n_cities):
    t = tier_bins[i]
    bins[t].append(
        {
            "value": (round(float(population_density[i]), 1), round(float(commute_time[i]), 1)),
            "label": (
                f"Density: {population_density[i]:,.0f}/km²  |  "
                f"Commute: {commute_time[i]:.1f} min  |  "
                f"Green space: {green_space_pct[i]:.0f}%"
            ),
        }
    )

# Style — publication-quality with refined typography hierarchy
custom_style = Style(
    background="white",
    plot_background="#fafafa",
    foreground="#1a1a2e",
    foreground_strong="#1a1a2e",
    foreground_subtle="#e0e0e0",
    colors=tuple(tier_colors),
    opacity=0.62,
    opacity_hover=0.92,
    title_font_size=34,
    label_font_size=22,
    major_label_font_size=20,
    legend_font_size=17,
    value_font_size=14,
    tooltip_font_size=18,
    title_font_family="Trebuchet MS, Helvetica, sans-serif",
    label_font_family="Trebuchet MS, Helvetica, sans-serif",
    major_label_font_family="Trebuchet MS, Helvetica, sans-serif",
    legend_font_family="Trebuchet MS, Helvetica, sans-serif",
    value_font_family="Trebuchet MS, Helvetica, sans-serif",
)

# Plot — bubble chart with tight layout and refined formatting
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="bubble-basic · pygal · pyplots.ai",
    x_title="Population Density (people/km²)",
    y_title="Avg Commute Time (min)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=8,
    legend_box_size=20,
    stroke=False,
    dots_size=20,
    show_x_guides=True,
    show_y_guides=True,
    x_value_formatter=lambda x: f"{x:,.0f}",
    value_formatter=lambda x: f"{x:.1f}",
    margin_top=20,
    margin_bottom=50,
    margin_left=20,
    margin_right=20,
    tooltip_border_radius=8,
    tooltip_fancy_mode=True,
    print_values=False,
    truncate_legend=30,
    spacing=15,
)

# Add each tier as its own series with area-scaled dot size
for t in range(n_tiers):
    if bins[t]:
        chart.add(tier_labels[t], bins[t], dots_size=tier_sizes[t])
    else:
        chart.add(tier_labels[t], [], dots_size=tier_sizes[t])

# Save
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")
