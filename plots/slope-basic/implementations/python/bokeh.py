""" pyplots.ai
slope-basic: Basic Slope Chart (Slopegraph)
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

from bokeh.io import export_png, save
from bokeh.models import Label
from bokeh.plotting import figure
from bokeh.resources import CDN


# Data - Product sales comparison Q1 vs Q4 (10 products)
products = [
    "Product A",
    "Product B",
    "Product C",
    "Product D",
    "Product E",
    "Product F",
    "Product G",
    "Product H",
    "Product I",
    "Product J",
]
q1_sales = [85, 72, 91, 45, 68, 53, 78, 62, 40, 88]
q4_sales = [92, 65, 88, 71, 74, 48, 95, 58, 67, 82]

# Determine direction for color coding
colors = []
for start, end in zip(q1_sales, q4_sales, strict=True):
    if end > start:
        colors.append("#306998")  # Python Blue - increase
    elif end < start:
        colors.append("#FFD43B")  # Python Yellow - decrease
    else:
        colors.append("#888888")  # Gray - no change

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="slope-basic · bokeh · pyplots.ai",
    x_range=(-0.5, 1.5),
    y_range=(25, 105),
    toolbar_location=None,
)

# Style title and axes
p.title.text_font_size = "32pt"
p.title.align = "center"

# Remove x axis tick labels and set custom labels for time points
p.xaxis.visible = False
p.yaxis.axis_label = "Sales (thousands)"
p.yaxis.axis_label_text_font_size = "22pt"
p.yaxis.major_label_text_font_size = "18pt"

# Add time point labels at bottom
p.add_layout(Label(x=0, y=32, text="Q1", text_font_size="28pt", text_align="center", text_baseline="top"))
p.add_layout(Label(x=1, y=32, text="Q4", text_font_size="28pt", text_align="center", text_baseline="top"))

# Draw slope lines connecting Q1 to Q4 for each product
for product, start, end, color in zip(products, q1_sales, q4_sales, colors, strict=True):
    # Draw the connecting line
    p.line(x=[0, 1], y=[start, end], line_width=4, line_color=color, line_alpha=0.8)

    # Add markers at both endpoints
    p.scatter(x=[0, 1], y=[start, end], size=18, color=color, alpha=0.9)

    # Add labels at start (Q1) - left aligned
    p.add_layout(
        Label(
            x=-0.05,
            y=start,
            text=f"{product}: {start}",
            text_font_size="18pt",
            text_align="right",
            text_baseline="middle",
            text_color=color,
        )
    )

    # Add labels at end (Q4) - right aligned
    p.add_layout(
        Label(
            x=1.05,
            y=end,
            text=f"{end}: {product}",
            text_font_size="18pt",
            text_align="left",
            text_baseline="middle",
            text_color=color,
        )
    )

# Style grid
p.xgrid.grid_line_color = None
p.ygrid.grid_line_alpha = 0.3
p.ygrid.grid_line_dash = "dashed"

# Style outline
p.outline_line_color = None

# Save as PNG
export_png(p, filename="plot.png")

# Also save as HTML for interactive viewing
save(p, filename="plot.html", resources=CDN, title="slope-basic · bokeh · pyplots.ai")
