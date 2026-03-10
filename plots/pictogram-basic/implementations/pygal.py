"""pyplots.ai
pictogram-basic: Pictogram Chart (Isotype Visualization)
Library: pygal 3.1.0 | Python 3.14.3
Quality: 75/100 | Created: 2026-03-10
"""

import pygal
from pygal.style import Style


# Data - Fruit production (thousands of tonnes)
# Includes exact multiples and remainders for full feature coverage
categories = ["Apples", "Oranges", "Bananas", "Grapes", "Mangoes"]
values = [35, 22, 18, 15, 8]  # 35 and 15 are exact multiples of 5
icon_unit = 5  # Each dot represents 5 thousand tonnes

# Build dot matrix data: each full unit = 1.0, partial = visible fraction
# Use minimum 0.5 so partial dots remain legible
max_icons = max(v // icon_unit + (1 if v % icon_unit else 0) for v in values)
dot_data = {}
for cat, val in zip(categories, values, strict=True):
    full = val // icon_unit
    remainder = val % icon_unit
    row = [1.0] * full
    if remainder:
        row.append(max(remainder / icon_unit, 0.5))
    # Pad with None so all rows same length
    row += [None] * (max_icons - len(row))
    dot_data[cat] = row

# Color palette - top producer gets bold Python Blue, others use muted tones
# Creates visual hierarchy emphasizing the leader
palette = ("#1A5276", "#D4AC0D", "#1E8449", "#7D3C98", "#CB4335")

# Style
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#2C3E50",
    foreground_strong="#2C3E50",
    foreground_subtle="transparent",
    colors=palette,
    title_font_size=52,
    label_font_size=40,
    major_label_font_size=32,
    legend_font_size=32,
    value_font_size=22,
    tooltip_font_size=24,
    font_family="sans-serif",
)

# Plot
chart = pygal.Dot(
    width=4800,
    height=2700,
    style=custom_style,
    title="Fruit Production (each dot = 5k tonnes) · pictogram-basic · pygal · pyplots.ai",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=5,
    legend_box_size=24,
    show_x_guides=False,
    show_y_guides=False,
    show_x_labels=True,
    spacing=50,
    margin=60,
    margin_left=80,
    margin_right=80,
    margin_top=100,
    margin_bottom=160,
    x_label_rotation=0,
    truncate_label=-1,
    truncate_legend=-1,
    dot_size=44,
    print_values=False,
)

# X-axis labels showing cumulative value
chart.x_labels = [str((i + 1) * icon_unit) for i in range(max_icons)]

# Add each category as a series (descending order for storytelling)
for cat in categories:
    chart.add(cat, dot_data[cat])

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
