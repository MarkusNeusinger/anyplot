""" pyplots.ai
bar-stacked: Stacked Bar Chart
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

from bokeh.io import export_png
from bokeh.models import ColumnDataSource, HoverTool, Legend, LegendItem
from bokeh.plotting import figure, output_file, save


# Data: Quarterly sales by product category
categories = ["Q1", "Q2", "Q3", "Q4"]
components = ["Electronics", "Clothing", "Home & Garden", "Sports"]
colors = ["#306998", "#FFD43B", "#4ECDC4", "#E76F51"]

# Sales data (in thousands)
data = {
    "Electronics": [120, 145, 160, 190],
    "Clothing": [85, 110, 95, 130],
    "Home & Garden": [65, 90, 120, 85],
    "Sports": [45, 60, 55, 70],
}

# Calculate bottom positions for stacking
bottoms = {cat: [0] * len(categories) for cat in components}
running_total = [0] * len(categories)
for comp in components:
    bottoms[comp] = running_total.copy()
    running_total = [r + v for r, v in zip(running_total, data[comp], strict=True)]

# Create figure
p = figure(
    x_range=categories,
    width=4800,
    height=2700,
    title="bar-stacked · bokeh · pyplots.ai",
    x_axis_label="Quarter",
    y_axis_label="Sales (thousands USD)",
    toolbar_location=None,
)

# Create stacked bars with hover data
legend_items = []
for comp, color in zip(components, colors, strict=True):
    source = ColumnDataSource(
        data={
            "x": categories,
            "top": [b + v for b, v in zip(bottoms[comp], data[comp], strict=True)],
            "bottom": bottoms[comp],
            "value": data[comp],
            "component": [comp] * len(categories),
        }
    )
    renderer = p.vbar(
        x="x", top="top", bottom="bottom", width=0.7, source=source, color=color, line_color="white", line_width=2
    )
    legend_items.append(LegendItem(label=comp, renderers=[renderer]))

    # Add hover tool for each component
    hover = HoverTool(
        renderers=[renderer],
        tooltips=[("Category", "@component"), ("Quarter", "@x"), ("Sales", "@value{0,0} thousand USD")],
    )
    p.add_tools(hover)

# Add legend inside plot area for better balance
legend = Legend(
    items=legend_items,
    location="top_left",
    label_text_font_size="24pt",
    spacing=15,
    padding=20,
    background_fill_alpha=0.85,
    glyph_height=35,
    glyph_width=35,
)
p.add_layout(legend)

# Style the plot for large canvas
p.title.text_font_size = "36pt"
p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_font_size = "24pt"
p.yaxis.major_label_text_font_size = "24pt"

# Grid styling
p.xgrid.grid_line_color = None
p.ygrid.grid_line_alpha = 0.3
p.ygrid.grid_line_dash = "dashed"

# Axis styling
p.xaxis.major_tick_line_color = None
p.yaxis.minor_tick_line_color = None
p.outline_line_color = None

# Set y-axis range with padding
p.y_range.start = 0
p.y_range.end = max(running_total) * 1.1

# Save as PNG and HTML
export_png(p, filename="plot.png")
output_file("plot.html", title="bar-stacked · bokeh · pyplots.ai")
save(p)
