""" anyplot.ai
bar-diverging: Diverging Bar Chart
Library: pygal 3.1.0 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-08
"""

import os
import sys


if sys.path[0] == os.path.dirname(os.path.abspath(__file__)):
    sys.path.pop(0)

import pygal
from pygal.style import Style


# Theme tokens from prompts/default-style-guide.md
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# imprint semantic anchors: green for positive, red for negative
IMPRINT = ("#009E73", "#AE3030")

# Data - Customer satisfaction survey scores by department
# Positive = satisfied, Negative = dissatisfied (scale -100 to +100)
departments = [
    "Customer Support",
    "Product Quality",
    "Shipping Speed",
    "Website Experience",
    "Return Process",
    "Price Value",
    "Mobile App",
    "Documentation",
    "Response Time",
    "Overall Experience",
]

scores = [72, 45, -23, 58, -45, 31, -12, -38, 64, 52]

# Sort by value for better pattern recognition
sorted_data = sorted(zip(departments, scores, strict=True), key=lambda x: x[1])
sorted_departments = [d[0] for d in sorted_data]
sorted_scores = [d[1] for d in sorted_data]

# Custom style with theme-adaptive colors and proper font sizing
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT,
    title_font_size=28,
    label_font_size=22,
    major_label_font_size=18,
    legend_font_size=16,
    value_font_size=14,
    value_label_font_size=14,
    tooltip_font_size=14,
    stroke_width=2,
)

# Create horizontal bar chart (better for long labels)
chart = pygal.HorizontalBar(
    width=4800,
    height=2700,
    style=custom_style,
    title="Customer Satisfaction Survey · bar-diverging · pygal · anyplot.ai",
    x_title="Satisfaction Score",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=2,
    show_x_guides=True,
    show_y_guides=False,
    print_values=True,
    print_values_position="center",
    value_formatter=lambda x: f"{x:+.0f}" if x else "",
    range=(-100, 100),
    margin=50,
    spacing=20,
)

# Add data with color based on positive/negative
# Separate positive and negative for legend clarity
positive_scores = [s if s >= 0 else None for s in sorted_scores]
negative_scores = [s if s < 0 else None for s in sorted_scores]

chart.add("Satisfied", positive_scores)
chart.add("Dissatisfied", negative_scores)

# Set category labels
chart.x_labels = sorted_departments

# Save outputs with theme-suffixed filenames
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
