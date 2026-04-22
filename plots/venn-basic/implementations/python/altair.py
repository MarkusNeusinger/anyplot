""" pyplots.ai
venn-basic: Venn Diagram
Library: altair 6.0.0 | Python 3.13.11
Quality: 88/100 | Created: 2025-12-29
"""

import math

import altair as alt
import pandas as pd


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
# Base radius scaled so circles fill canvas well
base_radius = 240
radius_a = base_radius * math.sqrt(set_sizes[0] / 100)  # 240 (100 -> 1.0)
radius_b = base_radius * math.sqrt(set_sizes[1] / 100)  # ~215 (80 -> 0.894)
radius_c = base_radius * math.sqrt(set_sizes[2] / 100)  # ~186 (60 -> 0.775)

# Position circles in traditional triangular Venn arrangement (largest sets at top)
# A (largest) at top-left, B (medium) at top-right, C (smallest) at bottom-center
center_x, center_y = 600, 620  # Slightly below center to account for title
circle_spacing = 150  # Distance from center to circle centers
angle_a = math.radians(210)  # Top-left (210 degrees)
angle_b = math.radians(330)  # Top-right (330 degrees)
angle_c = math.radians(90)  # Bottom-center (90 degrees)

cx_a = center_x + circle_spacing * math.cos(angle_a)  # A - top-left
cy_a = center_y - circle_spacing * math.sin(angle_a)  # Inverted Y for screen coords
cx_b = center_x + circle_spacing * math.cos(angle_b)  # B - top-right
cy_b = center_y - circle_spacing * math.sin(angle_b)
cx_c = center_x + circle_spacing * math.cos(angle_c)  # C - bottom-center
cy_c = center_y - circle_spacing * math.sin(angle_c)

# Colors
colors = ["#306998", "#FFD43B", "#4DAF4A"]  # Python Blue, Python Yellow, Green

# Circle sizes for mark_point (proportional to set sizes)
circle_size_a = radius_a * radius_a * 3.14
circle_size_b = radius_b * radius_b * 3.14
circle_size_c = radius_c * radius_c * 3.14

# Circle centers data with individual sizes
fill_centers = pd.DataFrame(
    {
        "x": [cx_a, cx_b, cx_c],
        "y": [cy_a, cy_b, cy_c],
        "color": colors,
        "set": set_labels,
        "size": [circle_size_a, circle_size_b, circle_size_c],
    }
)

# Region counts with positions computed relative to circle centers
# Position offsets as fractions of circle radii for better scaling
only_offset = 0.5  # Offset for exclusive regions (away from center)
region_data = pd.DataFrame(
    {
        "x": [
            cx_a + (cx_a - center_x) * only_offset,  # Only A (away from center)
            cx_b + (cx_b - center_x) * only_offset,  # Only B (away from center)
            cx_c,  # Only C (below center)
            (cx_a + cx_b) / 2,  # A ∩ B (midpoint of A and B)
            (cx_a + cx_c) / 2,  # A ∩ C (midpoint of A and C)
            (cx_b + cx_c) / 2,  # B ∩ C (midpoint of B and C)
            center_x,  # A ∩ B ∩ C (center of all three)
        ],
        "y": [
            cy_a + (cy_a - center_y) * only_offset,  # Only A
            cy_b + (cy_b - center_y) * only_offset,  # Only B
            cy_c + radius_c * 0.6,  # Only C (bottom portion)
            (cy_a + cy_b) / 2 - 50,  # A ∩ B (above midpoint)
            (cy_a + cy_c) / 2 + 20,  # A ∩ C
            (cy_b + cy_c) / 2 + 20,  # B ∩ C
            center_y,  # A ∩ B ∩ C
        ],
        "count": [str(only_a), str(only_b), str(only_c), str(only_ab), str(only_ac), str(only_bc), str(abc)],
    }
)

# Set name labels positioned relative to circle centers (outside circles)
# Labels placed at edge of circle plus offset in direction away from diagram center
label_offset = 1.3  # Multiplier for positioning labels outside circles
set_label_data = pd.DataFrame(
    {
        "x": [
            cx_a + (cx_a - center_x) * label_offset,  # A label - left of circle A
            cx_b + (cx_b - center_x) * label_offset,  # B label - right of circle B
            cx_c,  # C label - centered below circle C
        ],
        "y": [
            cy_a + (cy_a - center_y) * label_offset,  # A label - above-left
            cy_b + (cy_b - center_y) * label_offset,  # B label - above-right
            cy_c + radius_c + 60,  # C label - below circle C
        ],
        "label": set_labels,
    }
)

# Draw filled circles using point marks with proportional sizes
background_circles = (
    alt.Chart(fill_centers)
    .mark_point(shape="circle", filled=True, opacity=0.35)
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[100, 1100]), axis=None),
        y=alt.Y("y:Q", scale=alt.Scale(domain=[100, 1100]), axis=None),
        color=alt.Color("color:N", scale=None, legend=None),
        size=alt.Size("size:Q", scale=None, legend=None),
    )
)

# Circle outlines with proportional sizes
outline_circles = (
    alt.Chart(fill_centers)
    .mark_point(shape="circle", filled=False, strokeWidth=4)
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[100, 1100]), axis=None),
        y=alt.Y("y:Q", scale=alt.Scale(domain=[100, 1100]), axis=None),
        stroke=alt.Color("color:N", scale=None, legend=None),
        size=alt.Size("size:Q", scale=None, legend=None),
    )
)

# Region count labels - larger font for better legibility at 3600x3600
counts_layer = (
    alt.Chart(region_data)
    .mark_text(fontSize=42, fontWeight="bold", color="#1a1a1a")
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[100, 1100]), axis=None),
        y=alt.Y("y:Q", scale=alt.Scale(domain=[100, 1100]), axis=None),
        text="count:N",
    )
)

# Set name labels - larger font for better legibility at 3600x3600
names_layer = (
    alt.Chart(set_label_data)
    .mark_text(fontSize=36, fontWeight="bold", color="#333333")
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[100, 1100]), axis=None),
        y=alt.Y("y:Q", scale=alt.Scale(domain=[100, 1100]), axis=None),
        text="label:N",
    )
)

# Combine all layers
chart = (
    alt.layer(background_circles, outline_circles, counts_layer, names_layer)
    .properties(
        width=1200, height=1200, title=alt.Title(text="venn-basic · altair · pyplots.ai", fontSize=40, anchor="middle")
    )
    .configure_view(strokeWidth=0)
)

# Save outputs
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
