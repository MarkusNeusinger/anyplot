""" anyplot.ai
windrose-basic: Wind Rose Chart
Library: pygal 3.1.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-07
"""

import os
import sys

import numpy as np


# Avoid import shadowing: remove script directory and cwd from path
_script_dir = os.path.dirname(os.path.abspath(__file__))
_cwd = os.getcwd()
sys.path = [p for p in sys.path if os.path.abspath(p) not in (_script_dir, _cwd, "")]

import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


# Restore path for later operations
sys.path.insert(0, _cwd)

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Okabe-Ito palette (positions 1-7)
IMPRINT = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477")

# Data generation
np.random.seed(42)
n_observations = 8760  # ~1 year of hourly measurements

# Simulate prevailing winds from SW (225°) and W (270°) with variation
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
cumulative = {}
for i, label in enumerate(speed_labels):
    cumulative[label] = [sum(frequencies[speed_labels[k]][j] for k in range(i + 1)) for j in range(8)]

# Custom style for large canvas with theme-adaptive colors
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT,
    title_font_size=32,
    label_font_size=24,
    major_label_font_size=22,
    legend_font_size=20,
    value_font_size=18,
    stroke_width=2.5,
    opacity=0.95,
    guide_stroke_width=1,
)

# Create radar chart (wind rose)
chart = pygal.Radar(
    width=3600,
    height=3600,
    style=custom_style,
    title="windrose-basic · pygal · anyplot.ai",
    y_title="Frequency (%)",
    show_legend=True,
    legend_at_bottom=False,
    legend_box_size=16,
    fill=True,
    stroke=True,
    show_dots=False,
    inner_radius=0.05,
    truncate_legend=-1,
    margin=120,
    spacing=40,
    show_y_guides=True,
    show_x_guides=False,
    range=(0, None),
)

# Set direction labels
chart.x_labels = direction_labels

# Add series from strongest to calmest (drawing order)
# This creates proper visual stacking with each layer visible
reversed_labels = list(reversed(speed_labels))  # [">12 m/s", "9-12 m/s", ...]
for label in reversed_labels:
    chart.add(label, cumulative[label])

# Save outputs
chart.render_to_file(f"plot-{THEME}.html")
chart.render_to_png(f"plot-{THEME}.png")
