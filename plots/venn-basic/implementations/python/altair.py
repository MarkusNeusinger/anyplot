""" anyplot.ai
venn-basic: Venn Diagram
Library: altair 6.1.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-11
"""

import math
import os
import site
import sys


# Ensure site-packages comes before current directory to avoid shadowing
site_packages = site.getsitepackages()[0]
sys.path.insert(0, site_packages)

import altair as alt  # noqa: E402
import pandas as pd  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (first series always #009E73)
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data - Three overlapping research disciplines
set_labels = ["Machine Learning", "Statistics", "Data Engineering"]
set_sizes = [100, 80, 60]
# Overlaps: AB=30, AC=20, BC=25, ABC=10
only_a = 100 - 30 - 20 + 10  # 60
only_b = 80 - 30 - 25 + 10  # 35
only_c = 60 - 20 - 25 + 10  # 25
only_ab = 30 - 10  # 20
only_ac = 20 - 10  # 10
only_bc = 25 - 10  # 15
abc = 10

# Calculate proportional radii based on set sizes
base_radius = 280
radius_a = base_radius * math.sqrt(set_sizes[0] / 100)
radius_b = base_radius * math.sqrt(set_sizes[1] / 100)
radius_c = base_radius * math.sqrt(set_sizes[2] / 100)

# Position circles in triangular arrangement, centered vertically on canvas
center_x, center_y = 800, 450
circle_spacing = 180
angle_a = math.radians(210)
angle_b = math.radians(330)
angle_c = math.radians(90)

cx_a = center_x + circle_spacing * math.cos(angle_a)
cy_a = center_y - circle_spacing * math.sin(angle_a)
cx_b = center_x + circle_spacing * math.cos(angle_b)
cy_b = center_y - circle_spacing * math.sin(angle_b)
cx_c = center_x + circle_spacing * math.cos(angle_c)
cy_c = center_y - circle_spacing * math.sin(angle_c)

# Circle sizes for mark_point
circle_size_a = radius_a * radius_a * 3.14
circle_size_b = radius_b * radius_b * 3.14
circle_size_c = radius_c * radius_c * 3.14

# Circle centers data with Okabe-Ito colors
fill_centers = pd.DataFrame(
    {
        "x": [cx_a, cx_b, cx_c],
        "y": [cy_a, cy_b, cy_c],
        "color": IMPRINT[0:3],
        "set": set_labels,
        "size": [circle_size_a, circle_size_b, circle_size_c],
    }
)

# Region counts positioned relative to circle centers
only_offset = 0.5
region_data = pd.DataFrame(
    {
        "x": [
            cx_a + (cx_a - center_x) * only_offset,
            cx_b + (cx_b - center_x) * only_offset,
            cx_c,
            (cx_a + cx_b) / 2,
            (cx_a + cx_c) / 2,
            (cx_b + cx_c) / 2,
            center_x,
        ],
        "y": [
            cy_a + (cy_a - center_y) * only_offset,
            cy_b + (cy_b - center_y) * only_offset,
            cy_c + radius_c * 0.6,
            (cy_a + cy_b) / 2 - 50,
            (cy_a + cy_c) / 2 + 20,
            (cy_b + cy_c) / 2 + 20,
            center_y,
        ],
        "count": [str(only_a), str(only_b), str(only_c), str(only_ab), str(only_ac), str(only_bc), str(abc)],
    }
)

# Set name labels positioned outside circles
label_offset = 1.3
set_label_data = pd.DataFrame(
    {
        "x": [cx_a + (cx_a - center_x) * label_offset, cx_b + (cx_b - center_x) * label_offset, cx_c],
        "y": [cy_a + (cy_a - center_y) * label_offset, cy_b + (cy_b - center_y) * label_offset, cy_c + radius_c + 60],
        "label": set_labels,
    }
)

# Draw filled circles with transparency
background_circles = (
    alt.Chart(fill_centers)
    .mark_point(shape="circle", filled=True, opacity=0.3)
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[200, 1400]), axis=None),
        y=alt.Y("y:Q", scale=alt.Scale(domain=[100, 800]), axis=None),
        color=alt.Color("color:N", scale=None, legend=None),
        size=alt.Size("size:Q", scale=None, legend=None),
    )
)

# Circle outlines
outline_circles = (
    alt.Chart(fill_centers)
    .mark_point(shape="circle", filled=False, strokeWidth=5)
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[200, 1400]), axis=None),
        y=alt.Y("y:Q", scale=alt.Scale(domain=[100, 800]), axis=None),
        stroke=alt.Color("color:N", scale=None, legend=None),
        size=alt.Size("size:Q", scale=None, legend=None),
    )
)

# Region count labels
counts_layer = (
    alt.Chart(region_data)
    .mark_text(fontSize=32, fontWeight="bold", color=INK)
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[200, 1400]), axis=None),
        y=alt.Y("y:Q", scale=alt.Scale(domain=[100, 800]), axis=None),
        text="count:N",
    )
)

# Set name labels
names_layer = (
    alt.Chart(set_label_data)
    .mark_text(fontSize=28, fontWeight="bold", color=INK_SOFT)
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[200, 1400]), axis=None),
        y=alt.Y("y:Q", scale=alt.Scale(domain=[100, 800]), axis=None),
        text="label:N",
    )
)

# Combine all layers with theme-adaptive styling
chart = (
    alt.layer(background_circles, outline_circles, counts_layer, names_layer)
    .properties(
        width=1600,
        height=900,
        background=PAGE_BG,
        title=alt.Title(text="venn-basic · altair · anyplot.ai", fontSize=28, anchor="middle", color=INK),
    )
    .configure_view(fill=PAGE_BG, stroke=None, strokeWidth=0)
)

# Save outputs
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
