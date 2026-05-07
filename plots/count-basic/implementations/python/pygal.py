""" anyplot.ai
count-basic: Basic Count Plot
Library: pygal 3.1.0 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-07
"""

import os
import sys
from collections import Counter


# Work around naming conflict: pygal.py filename shadows pygal package
sys.path.pop(0)

import pygal
from pygal.style import Style


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

OKABE_ITO = ("#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442")

# Data - Survey responses from customer feedback
responses = [
    "Satisfied",
    "Very Satisfied",
    "Satisfied",
    "Neutral",
    "Dissatisfied",
    "Very Satisfied",
    "Satisfied",
    "Satisfied",
    "Very Satisfied",
    "Neutral",
    "Satisfied",
    "Neutral",
    "Very Satisfied",
    "Satisfied",
    "Very Satisfied",
    "Dissatisfied",
    "Satisfied",
    "Very Satisfied",
    "Neutral",
    "Satisfied",
    "Very Satisfied",
    "Satisfied",
    "Satisfied",
    "Very Dissatisfied",
    "Satisfied",
    "Neutral",
    "Very Satisfied",
    "Satisfied",
    "Dissatisfied",
    "Satisfied",
    "Very Satisfied",
    "Satisfied",
    "Neutral",
    "Satisfied",
    "Very Satisfied",
    "Satisfied",
    "Very Satisfied",
    "Neutral",
    "Dissatisfied",
    "Satisfied",
    "Very Satisfied",
    "Satisfied",
    "Satisfied",
    "Very Satisfied",
    "Neutral",
    "Satisfied",
    "Dissatisfied",
    "Very Satisfied",
    "Satisfied",
    "Very Satisfied",
]

# Count occurrences
counts = Counter(responses)

# Define category order (logical satisfaction order)
category_order = ["Very Dissatisfied", "Dissatisfied", "Neutral", "Satisfied", "Very Satisfied"]
ordered_counts = [(cat, counts.get(cat, 0)) for cat in category_order]

# Custom style for large canvas
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
)

# Create chart
chart = pygal.Bar(
    width=4800,
    height=2700,
    style=custom_style,
    title="count-basic · pygal · anyplot.ai",
    x_title="Satisfaction Level",
    y_title="Number of Responses",
    show_legend=False,
    show_y_guides=True,
    show_x_guides=False,
    print_values=True,
    print_values_position="top",
    value_formatter=lambda x: str(int(x)),
    margin=60,
    spacing=80,
)

# Set x-axis labels
chart.x_labels = category_order

# Add data as single series
chart.add("Responses", [count for _, count in ordered_counts])

# Save outputs
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
