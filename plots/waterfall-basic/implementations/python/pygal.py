""" pyplots.ai
waterfall-basic: Basic Waterfall Chart
Library: pygal 3.1.0 | Python 3.13.11
Quality: 90/100 | Created: 2025-12-24
"""

import pygal
from pygal.style import Style


# Data: Quarterly financial breakdown from revenue to net income
categories = ["Q1 Revenue", "Product Sales", "Services", "COGS", "Operating Exp", "Other Income", "Taxes", "Net Income"]
changes = [500, 150, 80, -180, -120, 25, -68, None]  # None for the final total

# Calculate running totals and positions for waterfall effect
running_total = 0
bar_bottoms = []
bar_heights = []
bar_types = []  # 'total', 'positive', 'negative'
display_values = []  # Values to display on bars
running_totals = []  # Track running total at each step

for i, val in enumerate(changes):
    if i == 0:
        # Starting total
        bar_bottoms.append(0)
        bar_heights.append(val)
        bar_types.append("total")
        display_values.append(val)
        running_total = val
        running_totals.append(running_total)
    elif val is None:
        # Final total - calculate from running total
        bar_bottoms.append(0)
        bar_heights.append(running_total)
        bar_types.append("total")
        display_values.append(running_total)
        running_totals.append(running_total)
    elif val >= 0:
        # Positive change
        bar_bottoms.append(running_total)
        bar_heights.append(val)
        bar_types.append("positive")
        display_values.append(val)
        running_total += val
        running_totals.append(running_total)
    else:
        # Negative change
        running_total += val
        bar_bottoms.append(running_total)
        bar_heights.append(abs(val))
        bar_types.append("negative")
        display_values.append(val)
        running_totals.append(running_total)

# Colorblind-friendly palette using blue/teal/orange instead of red/green
# Blue for totals, teal for increases, orange for decreases
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("transparent", "#306998", "#0077B6", "#E76F00"),  # spacer, total, increase, decrease
    title_font_size=56,
    label_font_size=32,
    major_label_font_size=32,
    legend_font_size=48,
    value_font_size=32,
    value_colors=("transparent", "#FFFFFF", "#FFFFFF", "#FFFFFF"),  # White labels on colored bars
    opacity=1.0,
    opacity_hover=0.9,
)

# Create stacked bar chart to achieve waterfall effect
chart = pygal.StackedBar(
    width=4800,
    height=2700,
    style=custom_style,
    title="waterfall-basic · pygal · pyplots.ai",
    x_title="Category",
    y_title="Amount ($K)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    legend_box_size=36,
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

# Set x-axis labels with running totals displayed
# Shows category name and running total for clarity
labels_with_totals = [f"{cat} (${running_totals[i]}K)" for i, cat in enumerate(categories)]
chart.x_labels = labels_with_totals

# Build data series by type for proper coloring
spacer_data = []
total_data = []
positive_data = []
negative_data = []

for i in range(len(categories)):
    bottom = bar_bottoms[i]
    height = bar_heights[i]
    btype = bar_types[i]
    disp_val = display_values[i]

    # Spacer creates the floating effect (invisible bar from 0 to bottom)
    spacer_data.append({"value": bottom if bottom > 0 else None, "label": ""})

    # Format labels with change amount
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
chart.add("", spacer_data, stroke_style={"width": 0})  # Invisible spacer
chart.add("Total", total_data)
chart.add("Increase", positive_data)
chart.add("Decrease", negative_data)

# Save outputs
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
