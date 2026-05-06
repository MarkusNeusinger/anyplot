""" anyplot.ai
waterfall-basic: Basic Waterfall Chart
Library: pygal 3.1.0 | Python 3.13.13
Quality: 82/100 | Updated: 2026-05-06
"""

import os

import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Okabe-Ito palette: position 1 (positive), position 2 (negative), position 3 (totals)
OKABE_ITO = ("#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442")

# Data: Quarterly financial breakdown from revenue to net income
categories = ["Q1 Revenue", "Product Sales", "Services", "COGS", "Operating Exp", "Other Income", "Taxes", "Net Income"]
changes = [500, 150, 80, -180, -120, 25, -68, None]

# Calculate running totals and positions for waterfall effect
running_total = 0
bar_bottoms = []
bar_heights = []
bar_types = []
display_values = []
running_totals = []

for i, val in enumerate(changes):
    if i == 0:
        bar_bottoms.append(0)
        bar_heights.append(val)
        bar_types.append("total")
        display_values.append(val)
        running_total = val
        running_totals.append(running_total)
    elif val is None:
        bar_bottoms.append(0)
        bar_heights.append(running_total)
        bar_types.append("total")
        display_values.append(running_total)
        running_totals.append(running_total)
    elif val >= 0:
        bar_bottoms.append(running_total)
        bar_heights.append(val)
        bar_types.append("positive")
        display_values.append(val)
        running_total += val
        running_totals.append(running_total)
    else:
        running_total += val
        bar_bottoms.append(running_total)
        bar_heights.append(abs(val))
        bar_types.append("negative")
        display_values.append(val)
        running_totals.append(running_total)

# Create custom style with theme-adaptive colors
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=OKABE_ITO,
    title_font_size=28,
    label_font_size=18,
    major_label_font_size=16,
    legend_font_size=16,
    value_font_size=14,
    stroke_width=3,
)

# Create stacked bar chart to achieve waterfall effect
chart = pygal.StackedBar(
    width=4800,
    height=2700,
    style=custom_style,
    title="waterfall-basic · pygal · anyplot.ai",
    x_title="Category",
    y_title="Amount ($K)",
    show_legend=True,
    legend_at_bottom=True,
    show_y_guides=True,
    show_x_guides=False,
    print_values=True,
    print_values_position="center",
    truncate_legend=-1,
    truncate_label=-1,
    x_label_rotation=25,
    margin=80,
    margin_bottom=250,
    spacing=25,
)

# Set x-axis labels
labels_with_totals = [f"{cat} (${running_totals[i]}K)" for i, cat in enumerate(categories)]
chart.x_labels = labels_with_totals

# Build data series: spacer (invisible), totals, positive changes, negative changes
spacer_data = []
total_data = []
positive_data = []
negative_data = []

for i in range(len(categories)):
    bottom = bar_bottoms[i]
    height = bar_heights[i]
    btype = bar_types[i]
    disp_val = display_values[i]

    spacer_data.append({"value": bottom if bottom > 0 else None, "label": ""})

    if btype == "total":
        total_data.append({"value": height, "label": f"${disp_val}K"})
        positive_data.append({"value": None})
        negative_data.append({"value": None})
    elif btype == "positive":
        total_data.append({"value": None})
        positive_data.append({"value": height, "label": f"+${disp_val}K"})
        negative_data.append({"value": None})
    else:
        total_data.append({"value": None})
        positive_data.append({"value": None})
        negative_data.append({"value": height, "label": f"${disp_val}K"})

# Add series in stack order (bottom to top)
# Hide spacer series from legend by using empty title
chart.add("", spacer_data, stroke_style={"width": 0}, show_legend=False)
chart.add("Total", total_data)
chart.add("Increase", positive_data)
chart.add("Decrease", negative_data)

# Save outputs
chart.render_to_png(f"plot-{THEME}.png")
chart.render_to_file(f"plot-{THEME}.html")
