""" pyplots.ai
windrose-basic: Wind Rose Chart
Library: pygal 3.1.0 | Python 3.13.11
Quality: 78/100 | Created: 2025-12-24
"""

import numpy as np
import pygal
from pygal.style import Style


# Seed for reproducibility
np.random.seed(42)

# Generate realistic wind data (1 year of hourly measurements)
n_observations = 8760  # ~1 year hourly

# Simulate prevailing winds from SW (225°) and W (270°) with some variation
# Use mixture of distributions to create realistic patterns
directions = np.concatenate(
    [
        np.random.normal(225, 30, int(n_observations * 0.35)),  # SW dominant
        np.random.normal(270, 25, int(n_observations * 0.25)),  # W secondary
        np.random.normal(180, 40, int(n_observations * 0.15)),  # S occasional
        np.random.uniform(0, 360, int(n_observations * 0.25)),  # Random variation
    ]
)
directions = directions % 360  # Normalize to 0-360

# Generate corresponding wind speeds (Weibull-like distribution)
# Higher speeds correlate with SW/W directions
speeds = np.concatenate(
    [
        np.random.weibull(2, int(n_observations * 0.35)) * 8,  # SW: moderate-strong
        np.random.weibull(2.2, int(n_observations * 0.25)) * 9,  # W: stronger
        np.random.weibull(1.8, int(n_observations * 0.15)) * 6,  # S: lighter
        np.random.weibull(1.5, int(n_observations * 0.25)) * 5,  # Others: light
    ]
)

# Define 8 direction sectors (N, NE, E, SE, S, SW, W, NW)
direction_labels = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]

# Define wind speed ranges (m/s)
speed_bins = [0, 3, 6, 9, 12, np.inf]
speed_labels = ["0-3 m/s", "3-6 m/s", "6-9 m/s", "9-12 m/s", ">12 m/s"]

# Calculate frequencies for each direction and speed bin
frequencies = {label: [] for label in speed_labels}

for dir_center in [0, 45, 90, 135, 180, 225, 270, 315]:
    # Get indices for this direction sector
    if dir_center == 0:
        # North spans 337.5-360 and 0-22.5
        mask = (directions >= 337.5) | (directions < 22.5)
    else:
        low = dir_center - 22.5
        high = dir_center + 22.5
        mask = (directions >= low) & (directions < high)

    dir_speeds = speeds[mask]

    # Count frequencies in each speed bin
    for j, (low_speed, high_speed) in enumerate(zip(speed_bins[:-1], speed_bins[1:], strict=True)):
        count = np.sum((dir_speeds >= low_speed) & (dir_speeds < high_speed))
        freq_pct = (count / len(directions)) * 100
        frequencies[speed_labels[j]].append(round(freq_pct, 2))

# Build cumulative values for proper stacked rendering
# Each layer shows the cumulative sum up to that speed range
# We'll draw from outermost (total) to innermost (calm only)
cumulative = {}
for i, label in enumerate(speed_labels):
    # Sum from bin 0 to bin i (inclusive) - cumulative from calm to strong
    cumulative[label] = [sum(frequencies[speed_labels[k]][j] for k in range(i + 1)) for j in range(8)]

# Custom style for large canvas - cool to warm colors for wind speeds
# Colors assigned per-series (added strongest first, so colors match that order)
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#222222",
    foreground_subtle="#666666",
    colors=("#E74C3C", "#FF8C42", "#FFD43B", "#5BA0D0", "#A8D5BA"),  # Strong→Calm (draw order)
    title_font_size=56,
    label_font_size=48,
    major_label_font_size=48,
    legend_font_size=36,
    value_font_size=28,
    value_label_font_size=28,
    tooltip_font_size=28,
    stroke_width=1,
    opacity=1.0,
    opacity_hover=1.0,
    guide_stroke_width=0.5,
    guide_stroke_color="#cccccc",
)

# Create radar chart (wind rose)
chart = pygal.Radar(
    width=3600,
    height=3600,
    style=custom_style,
    title="windrose-basic · pygal · pyplots.ai",
    y_title="Frequency (%)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=5,
    legend_box_size=32,
    fill=True,
    stroke=True,
    show_dots=False,
    inner_radius=0,
    truncate_legend=-1,
    margin=100,
    spacing=50,
    show_y_guides=True,
    show_x_guides=False,
)

# Set direction labels
chart.x_labels = direction_labels

# Add series from strongest to calmest (drawing order)
# Strongest winds drawn first (largest cumulative), then weaker winds overlay on top
# This creates proper visual stacking where each layer is visible
reversed_labels = list(reversed(speed_labels))  # [">12 m/s", "9-12 m/s", ...]
for label in reversed_labels:
    chart.add(label, cumulative[label])

# Save outputs
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")
