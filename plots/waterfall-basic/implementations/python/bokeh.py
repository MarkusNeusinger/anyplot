""" pyplots.ai
waterfall-basic: Basic Waterfall Chart
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-24
"""

from bokeh.io import export_png
from bokeh.models import ColumnDataSource, FactorRange, Label
from bokeh.plotting import figure, save


# Data - quarterly financial breakdown from revenue to net income
categories = ["Starting Revenue", "Product Sales", "Services", "Refunds", "Operating Costs", "Marketing", "Net Income"]
# First value is the starting total, last value will be calculated as final total
# Middle values are changes (positive = increase, negative = decrease)
changes = [150000, 50000, 35000, -8000, -75000, -22000, 0]  # Last is placeholder for total

# Calculate waterfall positions
running_total = 0
bar_bottoms = []
bar_tops = []
bar_colors = []
display_values = []  # For labels

for i, (_cat, change) in enumerate(zip(categories, changes, strict=True)):
    if i == 0:
        # Starting total - full bar from 0
        running_total = change
        bar_bottoms.append(0)
        bar_tops.append(running_total)
        bar_colors.append("#306998")  # Python Blue for totals
        display_values.append(running_total)
    elif i == len(categories) - 1:
        # Final total - full bar from 0 to current running total
        bar_bottoms.append(0)
        bar_tops.append(running_total)
        bar_colors.append("#306998")  # Python Blue for totals
        display_values.append(running_total)
    else:
        # Intermediate changes
        if change >= 0:
            bar_bottoms.append(running_total)
            bar_tops.append(running_total + change)
            bar_colors.append("#2ECC71")  # Green for positive
        else:
            bar_bottoms.append(running_total + change)
            bar_tops.append(running_total)
            bar_colors.append("#E74C3C")  # Red for negative
        running_total += change
        display_values.append(change)

# Create data source
source = ColumnDataSource(data={"categories": categories, "bottom": bar_bottoms, "top": bar_tops, "color": bar_colors})

# Create figure (4800 x 2700 px)
p = figure(
    x_range=FactorRange(*categories, range_padding=0.1),
    width=4800,
    height=2700,
    title="waterfall-basic · bokeh · pyplots.ai",
    x_axis_label="Financial Category",
    y_axis_label="Amount ($)",
    toolbar_location=None,
)

# Draw bars
p.vbar(
    x="categories",
    top="top",
    bottom="bottom",
    width=0.6,
    source=source,
    color="color",
    line_color="white",
    line_width=2,
    alpha=0.9,
)

# Calculate running totals for connector lines
running_totals = []
rt = 0
for i, change in enumerate(changes):
    if i == 0:
        rt = change
    elif i < len(changes) - 1:
        rt += change
    running_totals.append(rt)

# Draw connector lines between bars (showing running total flow)
for i in range(len(categories) - 2):  # Don't draw connector to final total bar
    # The connector should be at the running total level after bar i
    connector_y = running_totals[i]

    p.line(
        x=[categories[i], categories[i + 1]],
        y=[connector_y, connector_y],
        line_color="#7F8C8D",
        line_width=2,
        line_dash="dashed",
        alpha=0.7,
    )

# Add value labels on bars
max_value = max(bar_tops)
label_offset = max_value * 0.03  # 3% of max value for offset

for i, (_cat, _bottom, top, display_val) in enumerate(
    zip(categories, bar_bottoms, bar_tops, display_values, strict=True)
):
    # Label position - above the bar
    label_y = top + label_offset

    if i == 0 or i == len(categories) - 1:
        # Total bars - show absolute value
        label_text = f"${display_val:,.0f}"
    else:
        # Change bars - show with sign
        if display_val >= 0:
            label_text = f"+${display_val:,.0f}"
        else:
            label_text = f"-${abs(display_val):,.0f}"

    label = Label(
        x=i,
        y=label_y,
        text=label_text,
        text_font_size="20pt",
        text_align="center",
        text_baseline="bottom",
        text_color="#2C3E50",
    )
    p.add_layout(label)

# Style
p.title.text_font_size = "32pt"
p.xaxis.axis_label_text_font_size = "24pt"
p.yaxis.axis_label_text_font_size = "24pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.xaxis.major_label_orientation = 0.5  # Slight rotation for readability

# Grid styling
p.xgrid.grid_line_color = None
p.ygrid.grid_line_alpha = 0.3
p.ygrid.grid_line_dash = "dashed"

# Background
p.background_fill_color = "#FAFAFA"
p.border_fill_color = "#FFFFFF"

# Axis styling
p.yaxis.formatter.use_scientific = False
p.y_range.start = 0
p.y_range.end = max_value * 1.15  # 15% padding above max
p.min_border_left = 80  # Extra left margin for y-axis labels

# Save as PNG and HTML
export_png(p, filename="plot.png")
save(p, filename="plot.html", title="waterfall-basic · bokeh · pyplots.ai")
