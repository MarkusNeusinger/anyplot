""" pyplots.ai
pictogram-basic: Pictogram Chart (Isotype Visualization)
Library: pygal 3.1.0 | Python 3.14.3
Quality: 87/100 | Created: 2026-03-10
"""

import pygal
from pygal.style import Style


# Data - Fruit production (thousands of tonnes)
# Apples dominates at 35k — over 4× the smallest producer (Mangoes, 8k)
categories = ["Apples", "Oranges", "Bananas", "Grapes", "Mangoes"]
values = [35, 22, 18, 15, 8]  # 35 and 15 are exact multiples of 5
icon_unit = 5  # Each dot represents 5 thousand tonnes

# Build dot matrix data: each full unit = 1.0, partial = visible fraction
# Minimum 0.6 keeps partial dots clearly visible as "partial"
max_icons = max(v // icon_unit + (1 if v % icon_unit else 0) for v in values)
dot_data = {}
for cat, val in zip(categories, values, strict=True):
    full = val // icon_unit
    remainder = val % icon_unit
    row = [1.0] * full
    if remainder:
        row.append(max(remainder / icon_unit, 0.6))
    # Pad with None so all rows same length
    row += [None] * (max_icons - len(row))
    dot_data[cat] = row

# Palette: saturated leader color (Apples) vs muted earth tones for others
# Creates strong focal point on the dominant category; colorblind-safe
palette = (
    "#1A5276",  # Bold steel blue for leader (Apples) — saturated focal point
    "#B7950B",  # Muted gold (Oranges) — less saturated, recedes
    "#117A65",  # Deep sage (Bananas) — quiet complement
    "#76448A",  # Dusty violet (Grapes) — muted, secondary
    "#A93226",  # Muted brick (Mangoes) — warm anchor, lower intensity
)

# Style — refined sans-serif typography, generous sizing for 4800×2700
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#2C3E50",
    foreground_strong="#1B2631",
    foreground_subtle="transparent",
    colors=palette,
    title_font_size=54,
    label_font_size=48,
    major_label_font_size=38,
    legend_font_size=38,
    value_font_size=26,
    tooltip_font_size=24,
    font_family="Helvetica, Arial, sans-serif",
)

# Chart — pygal.Dot as pictogram approximation with large dots
# Title tells the story: Apples dominate at 4× the smallest
chart = pygal.Dot(
    width=4800,
    height=2700,
    style=custom_style,
    title=(
        "Fruit Production — Apples Lead at 4× Mangoes (each dot ≈ 5 000 tonnes)\npictogram-basic · pygal · pyplots.ai"
    ),
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=5,
    legend_box_size=30,
    show_x_guides=False,
    show_y_guides=False,
    show_x_labels=True,
    spacing=50,
    margin=60,
    margin_left=120,
    margin_right=40,
    margin_top=120,
    margin_bottom=180,
    x_label_rotation=0,
    truncate_label=-1,
    truncate_legend=-1,
    dot_size=52,
    print_values=False,
    stroke=False,
    value_formatter=lambda v: f"{int(v * icon_unit)}k t" if v else "",
)

# X-axis labels show cumulative value scale with unit
chart.x_labels = [f"{(i + 1) * icon_unit}k" for i in range(max_icons)]

# Add each category as a series in descending order — visual hierarchy
for cat in categories:
    chart.add(cat, dot_data[cat])

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
