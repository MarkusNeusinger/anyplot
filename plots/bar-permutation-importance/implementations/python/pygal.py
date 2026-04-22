""" pyplots.ai
bar-permutation-importance: Permutation Feature Importance Plot
Library: pygal 3.1.0 | Python 3.13.11
Quality: 83/100 | Created: 2025-12-31
"""

import numpy as np
import pygal
from pygal.style import Style


# Data - Simulated permutation importance results (realistic ML feature importance)
np.random.seed(42)

# Feature names representing typical ML model features (sorted by importance, ascending)
features = [
    "Year Built",
    "Bathrooms",
    "Garage Size",
    "Lot Area",
    "Bedrooms",
    "Basement Area",
    "Total Rooms",
    "Living Area",
    "Neighborhood",
    "Overall Quality",
]

# Mean importance values (mean decrease in R² score from permutation)
# Sorted ascending for bottom-to-top display in horizontal bar
importance_mean = np.array([0.002, 0.008, 0.015, 0.024, 0.032, 0.048, 0.067, 0.095, 0.128, 0.185])

# Standard deviation across 10 permutation repetitions
importance_std = np.array([0.003, 0.005, 0.008, 0.011, 0.014, 0.018, 0.022, 0.028, 0.035, 0.042])

# Generate sequential color gradient (viridis-inspired) inline
min_imp = importance_mean.min()
max_imp = importance_mean.max()
imp_range = max_imp - min_imp if max_imp != min_imp else 1.0

# Viridis color stops: purple (0) -> teal (0.5) -> yellow (1)
viridis_stops = [(0.0, 68, 1, 84), (0.25, 58, 82, 139), (0.5, 32, 144, 140), (0.75, 94, 201, 97), (1.0, 253, 231, 36)]


def get_viridis_color(t):
    """Interpolate viridis color for normalized value t in [0, 1]."""
    for j in range(len(viridis_stops) - 1):
        t0, r0, g0, b0 = viridis_stops[j]
        t1, r1, g1, b1 = viridis_stops[j + 1]
        if t0 <= t <= t1:
            seg_t = (t - t0) / (t1 - t0)
            r = int(r0 + (r1 - r0) * seg_t)
            g = int(g0 + (g1 - g0) * seg_t)
            b = int(b0 + (b1 - b0) * seg_t)
            return f"#{r:02x}{g:02x}{b:02x}"
    return "#fde724"


bar_colors = [get_viridis_color((imp - min_imp) / imp_range) for imp in importance_mean]

# Custom style with larger fonts for 4800x2700 canvas and subtle guides
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#999999",
    guide_stroke_color="#cccccc",
    major_guide_stroke_color="#cccccc",
    colors=tuple(bar_colors),
    title_font_size=84,
    label_font_size=48,
    major_label_font_size=48,
    legend_font_size=44,
    value_font_size=40,
    stroke_width=2,
    font_family="sans-serif",
    opacity=0.95,
    guide_stroke_dasharray="4,4",
)

# Create horizontal stacked bar chart for error bar visualization
# First stack: mean value (solid), Second stack: +std (semi-transparent for error bar effect)
chart = pygal.HorizontalStackedBar(
    width=4800,
    height=2700,
    style=custom_style,
    title="bar-permutation-importance · pygal · pyplots.ai",
    x_title="Mean Decrease in R² Score",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=2,
    legend_box_size=36,
    print_values=True,
    print_values_position="top",
    show_y_guides=False,
    show_x_guides=True,
    truncate_label=-1,
    spacing=28,
    margin=80,
    margin_left=420,
    margin_bottom=200,
    range=(-0.02, importance_mean.max() + importance_std.max() + 0.02),
    zero=0,
)

# Set feature labels on y-axis
chart.x_labels = features

# Create data series: main bars (mean values) and error extensions (+std)
mean_data = list(importance_mean)
std_data = list(importance_std)

# Add mean importance bars with viridis colors
chart.add(
    "Mean Importance",
    [{"value": v, "color": c} for v, c in zip(mean_data, bar_colors, strict=True)],
    formatter=lambda x: f"{x:.3f}" if x else "",
)

# Add error bar extensions (std values) with semi-transparent styling
error_color = "rgba(100, 100, 100, 0.35)"
chart.add(
    "± Std Dev (Error Range)",
    [{"value": v, "color": error_color} for v in std_data],
    formatter=lambda x: f"±{x:.3f}" if x else "",
)

# Save outputs
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")
