""" pyplots.ai
chessboard-basic: Chess Board Grid Visualization
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-08
"""

from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
from bokeh.resources import CDN


# Data - 8x8 chess board squares
columns = list("abcdefgh")
rows = list("12345678")

# Create square data
x_coords = []
y_coords = []
colors = []

# Light square color (cream) and dark square color (brown)
light_color = "#F0D9B5"
dark_color = "#B58863"

for row_idx, _row in enumerate(rows):
    for col_idx, _col in enumerate(columns):
        # Center of each square
        x_coords.append(col_idx + 0.5)
        y_coords.append(row_idx + 0.5)
        # Alternating colors: light square at h1 (row 0, col 7)
        # Pattern: (row_idx + col_idx) even = dark, odd = light
        if (row_idx + col_idx) % 2 == 0:
            colors.append(dark_color)
        else:
            colors.append(light_color)

source = ColumnDataSource(data={"x": x_coords, "y": y_coords, "color": colors})

# Create figure with 1:1 aspect ratio (square)
p = figure(
    width=3600,
    height=3600,
    title="chessboard-basic · bokeh · pyplots.ai",
    x_range=(-0.1, 8.1),
    y_range=(-0.1, 8.1),
    tools="",
    toolbar_location=None,
)

# Draw squares as rectangles
p.rect(x="x", y="y", width=1, height=1, source=source, color="color", line_color="#333333", line_width=2)

# Style the figure
p.title.text_font_size = "32pt"
p.title.align = "center"

# Configure x-axis (columns a-h)
p.xaxis.ticker = [0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5]
p.xaxis.major_label_overrides = {0.5: "a", 1.5: "b", 2.5: "c", 3.5: "d", 4.5: "e", 5.5: "f", 6.5: "g", 7.5: "h"}
p.xaxis.major_label_text_font_size = "24pt"
p.xaxis.axis_label = "Column"
p.xaxis.axis_label_text_font_size = "22pt"

# Configure y-axis (rows 1-8)
p.yaxis.ticker = [0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5]
p.yaxis.major_label_overrides = {0.5: "1", 1.5: "2", 2.5: "3", 3.5: "4", 4.5: "5", 5.5: "6", 6.5: "7", 7.5: "8"}
p.yaxis.major_label_text_font_size = "24pt"
p.yaxis.axis_label = "Row"
p.yaxis.axis_label_text_font_size = "22pt"

# Remove grid lines (the squares themselves form the grid)
p.xgrid.visible = False
p.ygrid.visible = False

# Style axis lines
p.outline_line_color = "#333333"
p.outline_line_width = 3

# Background
p.background_fill_color = "#FAFAFA"

# Save outputs
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="chessboard-basic · bokeh · pyplots.ai")
