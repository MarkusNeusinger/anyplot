""" anyplot.ai
violin-swarm: Violin Plot with Overlaid Swarm Points
Library: pygal 3.1.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-18
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

# Okabe-Ito palette - first series is always #009E73
OKABE_ITO = ("#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442")

# Data - Reaction times (ms) across 4 experimental conditions
np.random.seed(42)
data = {
    "Control": np.random.normal(320, 60, 50),
    "Treatment A": np.random.normal(280, 45, 50),
    "Treatment B": np.random.normal(250, 55, 50),
    "Treatment C": np.random.normal(290, 70, 50),
}

# Clip to realistic range (100-600ms)
for key in data:
    data[key] = np.clip(data[key], 100, 600)

# Custom style for theme-adaptive rendering
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=OKABE_ITO,
    title_font_size=28,
    label_font_size=22,
    major_label_font_size=18,
    legend_font_size=16,
    value_font_size=14,
    opacity=0.35,
    stroke_width=3,
)

# Create XY chart for violin plot with swarm overlay
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="violin-swarm · Python · pygal · anyplot.ai",
    x_title="Experimental Condition",
    y_title="Reaction Time (ms)",
    show_legend=False,
    stroke=True,
    fill=True,
    dots_size=0,
    show_x_guides=False,
    show_y_guides=True,
    range=(50, 550),
    xrange=(0, 6),
    margin=80,
)

# Parameters for violin shapes
violin_width = 0.4
n_points = 80

# Process each category
all_violins = []
all_swarms = []

for i, (_category, values) in enumerate(data.items()):
    center_x = i + 1.5

    # Create range of y values for density
    y_min, y_max = values.min(), values.max()
    padding = (y_max - y_min) * 0.2
    y_range = np.linspace(y_min - padding, y_max + padding, n_points)

    # Compute KDE using Silverman's rule
    n = len(values)
    std = np.std(values)
    iqr = np.percentile(values, 75) - np.percentile(values, 25)
    bandwidth = 0.9 * min(std, iqr / 1.34) * n ** (-0.2)

    density = np.zeros_like(y_range)
    for v in values:
        density += np.exp(-0.5 * ((y_range - v) / bandwidth) ** 2)
    density /= n * bandwidth * np.sqrt(2 * np.pi)

    # Normalize density to desired width
    density = density / density.max() * violin_width

    # Create violin shape (mirrored density)
    left_points = [(center_x - d, y) for y, d in zip(y_range, density, strict=False)]
    right_points = [(center_x + d, y) for y, d in zip(y_range[::-1], density[::-1], strict=False)]
    violin_points = left_points + right_points + [left_points[0]]

    all_violins.append(violin_points)

    # Compute swarm positions - arrange points to minimize overlap
    sorted_indices = np.argsort(values)
    positions = np.zeros(len(values))

    # Bin values and offset within bins
    y_sorted = values[sorted_indices]
    y_range_data = y_sorted.max() - y_sorted.min()
    bin_height = y_range_data / 12 if y_range_data > 0 else 1

    current_bin = []
    current_bin_y = y_sorted[0] if len(y_sorted) > 0 else 0

    for idx, y in enumerate(y_sorted):
        if y - current_bin_y > bin_height:
            # Process current bin - spread points horizontally
            n_in_bin = len(current_bin)
            if n_in_bin > 0:
                if n_in_bin > 1:
                    offsets = np.linspace(-violin_width / 2.5, violin_width / 2.5, n_in_bin)
                else:
                    offsets = [0]
                for j, bin_idx in enumerate(current_bin):
                    positions[bin_idx] = center_x + offsets[j]
            current_bin = [sorted_indices[idx]]
            current_bin_y = y
        else:
            current_bin.append(sorted_indices[idx])

    # Process last bin
    n_in_bin = len(current_bin)
    if n_in_bin > 0:
        if n_in_bin > 1:
            offsets = np.linspace(-violin_width / 2.5, violin_width / 2.5, n_in_bin)
        else:
            offsets = [0]
        for j, bin_idx in enumerate(current_bin):
            positions[bin_idx] = center_x + offsets[j]

    swarm_points = list(zip(positions, values, strict=False))
    all_swarms.extend(swarm_points)

# Add violins first (filled, semi-transparent)
for violin in all_violins:
    chart.add(None, violin, show_dots=False)

# Add swarm points as chunked series with visible dots
chunk_size = 8
swarm_chunks = [all_swarms[i : i + chunk_size] for i in range(0, len(all_swarms), chunk_size)]

for chunk in swarm_chunks:
    chart.add(None, chunk, stroke=False, fill=False, show_dots=True, dots_size=12)

# X-axis labels at violin positions
chart.x_labels = [
    {"value": 0, "label": ""},
    {"value": 1.5, "label": "Control"},
    {"value": 2.5, "label": "Treatment A"},
    {"value": 3.5, "label": "Treatment B"},
    {"value": 4.5, "label": "Treatment C"},
    {"value": 6, "label": ""},
]

# Save outputs with theme-suffixed filenames
chart.render_to_file(f"plot-{THEME}.html")
chart.render_to_png(f"plot-{THEME}.png")
