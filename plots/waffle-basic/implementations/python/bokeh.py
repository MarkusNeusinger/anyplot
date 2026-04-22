""" pyplots.ai
waffle-basic: Basic Waffle Chart
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-24
"""

from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, Legend, LegendItem
from bokeh.plotting import figure


# Data - Survey results on preferred programming languages
categories = ["Python", "JavaScript", "Java", "Other"]
values = [42, 28, 18, 12]  # Percentages summing to 100

# Colors - Python Blue first, then distinct colors
colors = ["#306998", "#FFD43B", "#E34F26", "#7B68EE"]

# Build waffle grid (10x10 = 100 squares)
grid_size = 10
total_squares = grid_size * grid_size

# Assign category to each square based on percentages
square_categories = []
color_map = []
for i, (cat, val) in enumerate(zip(categories, values, strict=True)):
    square_categories.extend([cat] * val)
    color_map.extend([colors[i]] * val)

# Create grid coordinates (fill left-to-right, bottom-to-top)
x_coords = []
y_coords = []
for idx in range(total_squares):
    x_coords.append(idx % grid_size)
    y_coords.append(idx // grid_size)

source = ColumnDataSource(data={"x": x_coords, "y": y_coords, "category": square_categories, "color": color_map})

# Create figure (4800 x 2700 px)
p = figure(
    width=4800,
    height=2700,
    title="Programming Language Preferences · waffle-basic · bokeh · pyplots.ai",
    x_range=(-0.7, grid_size - 0.3),
    y_range=(-0.7, grid_size - 0.3),
    tools="",
    toolbar_location=None,
)

# Draw squares with small gap between them
square_size = 0.88
renderers = []
for i, (cat, color) in enumerate(zip(categories, colors, strict=True)):
    # Filter data for this category
    indices = [j for j, c in enumerate(square_categories) if c == cat]
    cat_source = ColumnDataSource(data={"x": [x_coords[j] for j in indices], "y": [y_coords[j] for j in indices]})
    r = p.rect(
        x="x",
        y="y",
        width=square_size,
        height=square_size,
        source=cat_source,
        fill_color=color,
        line_color="white",
        line_width=2,
        fill_alpha=0.9,
    )
    renderers.append((f"{cat} ({values[i]}%)", [r]))

# Add legend
legend = Legend(items=[LegendItem(label=label, renderers=rends) for label, rends in renderers])
legend.label_text_font_size = "24pt"
legend.glyph_height = 40
legend.glyph_width = 40
legend.spacing = 15
legend.padding = 20
legend.location = "center_right"
p.add_layout(legend, "right")

# Style the plot
p.title.text_font_size = "32pt"
p.title.align = "center"

# Hide axes (waffle charts don't need them)
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False
p.outline_line_color = None

# Set background
p.background_fill_color = "#fafafa"
p.border_fill_color = "#fafafa"

# Save as PNG and HTML
export_png(p, filename="plot.png")

output_file("plot.html")
save(p)
