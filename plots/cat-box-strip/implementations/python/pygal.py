""" anyplot.ai
cat-box-strip: Box Plot with Strip Overlay
Library: pygal 3.1.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-13
"""

import os

import numpy as np
import pygal
from pygal.style import Style


# Theme tokens from environment
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Okabe-Ito palette (colorblind-safe, first series is brand green #009E73)
IMPRINT = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477")

# Data - Test scores across education levels
np.random.seed(42)
categories = ["High School", "Bachelor's", "Master's", "PhD"]
data = {
    "High School": np.random.normal(68, 12, 45),
    "Bachelor's": np.random.normal(78, 10, 50),
    "Master's": np.random.normal(82, 8, 38),
    "PhD": np.random.normal(85, 7, 42),
}

# Add realistic outliers
data["High School"] = np.append(data["High School"], [95, 48])
data["Bachelor's"] = np.append(data["Bachelor's"], [58, 98])
data["Master's"] = np.append(data["Master's"], [62, 95])
data["PhD"] = np.append(data["PhD"], [65, 100])

# Clamp all values to 0-100 range
for key in data:
    data[key] = np.clip(data[key], 0, 100)

# Color sequence: 6 colors for box plot elements + 4 for strip points (one per category)
color_sequence = []
for i in range(4):
    color_sequence.extend([IMPRINT[i]] * 6)  # 6 box elements per category
for i in range(4):
    color_sequence.append(IMPRINT[i])  # 1 strip series per category

# Custom style for 4800x2700 px canvas with theme-adaptive colors
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=tuple(color_sequence),
    title_font_size=28,
    label_font_size=22,
    major_label_font_size=18,
    legend_font_size=16,
    value_font_size=14,
    opacity=0.7,
)

# Create XY chart for combined box plot with strip overlay
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="cat-box-strip · pygal · anyplot.ai",
    x_title="Education Level",
    y_title="Test Score",
    show_legend=False,
    stroke=True,
    fill=True,
    dots_size=0,
    show_x_guides=True,
    show_y_guides=True,
    xrange=(0, 5),
    range=(0, 105),
    margin=100,
    explicit_size=True,
)

# Layout parameters
box_width = 0.25
cap_width = 0.15

# Pre-compute box plot components and strip points
strip_data = []
box_data = []

for i, (category, values) in enumerate(data.items()):
    center_x = i + 1  # X position for this group (1, 2, 3, 4)
    values = np.array(values)

    # --- Box Plot Statistics ---
    median = float(np.median(values))
    q1 = float(np.percentile(values, 25))
    q3 = float(np.percentile(values, 75))
    iqr = q3 - q1
    whisker_low = float(max(values.min(), q1 - 1.5 * iqr))
    whisker_high = float(min(values.max(), q3 + 1.5 * iqr))
    box_data.append((center_x, median, q1, q3, whisker_low, whisker_high))

    # --- Strip Points with Jitter ---
    np.random.seed(42 + i)
    jitter = np.random.uniform(-0.12, 0.12, len(values))
    strip_points = [(center_x + j, float(v)) for j, v in zip(jitter, values, strict=True)]
    strip_data.append((category, strip_points))

# Draw box plots first (so strip points appear on top)
for center_x, median, q1, q3, whisker_low, whisker_high in box_data:
    # IQR box (filled rectangle)
    quartile_box = [
        (center_x - box_width, q1),
        (center_x - box_width, q3),
        (center_x + box_width, q3),
        (center_x + box_width, q1),
        (center_x - box_width, q1),
    ]
    chart.add("", quartile_box, stroke=True, fill=True, show_dots=False, stroke_style={"width": 6})

    # Median line (horizontal line within box)
    median_line = [(center_x - box_width * 1.1, median), (center_x + box_width * 1.1, median)]
    chart.add("", median_line, stroke=True, fill=False, show_dots=False, stroke_style={"width": 10})

    # Whiskers (vertical lines from box to caps)
    whisker_bottom = [(center_x, q1), (center_x, whisker_low)]
    whisker_top = [(center_x, q3), (center_x, whisker_high)]
    chart.add("", whisker_bottom, stroke=True, fill=False, show_dots=False, stroke_style={"width": 6})
    chart.add("", whisker_top, stroke=True, fill=False, show_dots=False, stroke_style={"width": 6})

    # Whisker caps (horizontal lines at ends)
    cap_bottom = [(center_x - cap_width, whisker_low), (center_x + cap_width, whisker_low)]
    cap_top = [(center_x - cap_width, whisker_high), (center_x + cap_width, whisker_high)]
    chart.add("", cap_bottom, stroke=True, fill=False, show_dots=False, stroke_style={"width": 6})
    chart.add("", cap_top, stroke=True, fill=False, show_dots=False, stroke_style={"width": 6})

# Add strip points on top with transparency
for _category, strip_points in strip_data:
    chart.add("", strip_points, stroke=False, fill=False, dots_size=16)

# X-axis labels for categories
chart.x_labels = [
    {"value": 0, "label": ""},
    {"value": 1, "label": "High School"},
    {"value": 2, "label": "Bachelor's"},
    {"value": 3, "label": "Master's"},
    {"value": 4, "label": "PhD"},
    {"value": 5, "label": ""},
]

# Save outputs
chart.render_to_file(f"plot-{THEME}.html")
chart.render_to_png(f"plot-{THEME}.png")
