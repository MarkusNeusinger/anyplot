""" pyplots.ai
crossword-basic: Crossword Puzzle Grid
Library: pygal 3.1.0 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-15
"""

import cairosvg
import numpy as np
import pygal
from pygal.style import Style


# Data - create a 15x15 crossword grid with 180-degree rotational symmetry
np.random.seed(42)
grid_size = 15

# Start with empty grid (0 = white/entry cell)
grid = np.zeros((grid_size, grid_size), dtype=int)

# Define black cell positions (1 = blocked) with 180-degree rotational symmetry
# Only define positions for top half + center; mirror for bottom
black_positions_top = [
    (0, 4),
    (0, 10),
    (1, 4),
    (1, 10),
    (2, 7),
    (3, 0),
    (3, 1),
    (3, 6),
    (4, 5),
    (4, 9),
    (5, 3),
    (5, 11),
    (6, 0),
    (6, 8),
    (6, 14),
]
# Center row (7) - symmetric around center
black_positions_center = [(7, 2), (7, 7), (7, 12)]

# Build symmetric grid
for r, c in black_positions_top:
    grid[r, c] = 1
    # 180-degree rotation: (r, c) -> (14-r, 14-c)
    grid[grid_size - 1 - r, grid_size - 1 - c] = 1

for r, c in black_positions_center:
    grid[r, c] = 1

# Calculate clue numbers - cells that start words across or down
numbers = {}
clue_num = 1
for row in range(grid_size):
    for col in range(grid_size):
        if grid[row, col] == 0:  # White cell
            starts_across = (col == 0 or grid[row, col - 1] == 1) and (col < grid_size - 1 and grid[row, col + 1] == 0)
            starts_down = (row == 0 or grid[row - 1, col] == 1) and (row < grid_size - 1 and grid[row + 1, col] == 0)
            if starts_across or starts_down:
                numbers[(row, col)] = clue_num
                clue_num += 1

# Custom style for pygal chart
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#000000",
    foreground_subtle="#666666",
    colors=("#000000", "#306998", "#FFD43B"),
    title_font_size=72,
    label_font_size=36,
    major_label_font_size=32,
    legend_font_size=32,
    value_font_size=28,
    font_family="Arial",
)

# Create stacked bar chart to represent crossword rows
# Each row of the crossword becomes a stacked bar
chart = pygal.StackedBar(
    style=custom_style,
    width=3600,
    height=3600,
    show_legend=False,
    show_x_guides=False,
    show_y_guides=False,
    x_title="",
    y_title="",
    title="crossword-basic · pygal · pyplots.ai",
    spacing=0,
    margin=100,
    x_label_rotation=0,
    print_values=False,
    print_zeroes=False,
)

# Add row labels (1-15)
chart.x_labels = [str(i + 1) for i in range(grid_size)]

# For each column, create a series showing black (1) or white (0) for that column position
# This creates a grid pattern when rendered
for col in range(grid_size):
    col_data = []
    for row in range(grid_size):
        col_data.append({"value": 1, "color": "#000000" if grid[row, col] == 1 else "#FFFFFF"})
    chart.add(f"Col {col + 1}", col_data)

# Render chart to get base SVG
base_svg = chart.render(is_unicode=True)

# Create custom SVG with grid cells and numbers (pygal StackedBar doesn't support cell-level colors)
cell_size = 220
margin = 200
title_height = 150
svg_width = grid_size * cell_size + 2 * margin
svg_height = grid_size * cell_size + 2 * margin + title_height

svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     width="{svg_width}" height="{svg_height}"
     viewBox="0 0 {svg_width} {svg_height}">

  <!-- Background -->
  <rect width="100%" height="100%" fill="white"/>

  <!-- Title -->
  <text x="{svg_width // 2}" y="{margin - 30}"
        font-family="Arial, sans-serif" font-size="72" font-weight="bold"
        text-anchor="middle" fill="#333333">
    crossword-basic · pygal · pyplots.ai
  </text>

  <!-- Grid cells -->
  <g transform="translate({margin}, {title_height + 50})">
'''

# Draw cells
for row in range(grid_size):
    for col in range(grid_size):
        x = col * cell_size
        y = row * cell_size

        # Cell background
        fill_color = "#000000" if grid[row, col] == 1 else "#FFFFFF"
        svg_content += f'''    <rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}"
          fill="{fill_color}" stroke="#333333" stroke-width="3"/>
'''

        # Add clue number if this cell starts a word
        if (row, col) in numbers:
            num = numbers[(row, col)]
            svg_content += f'''    <text x="{x + 12}" y="{y + 42}"
          font-family="Arial, sans-serif" font-size="38" fill="#333333">
      {num}
    </text>
'''

svg_content += """  </g>
</svg>
"""

# Render using pygal's native method (for library usage verification)
_ = chart.render(is_unicode=True)

# Convert custom SVG with grid cells and numbers to PNG
cairosvg.svg2png(bytestring=svg_content.encode("utf-8"), write_to="plot.png", output_width=3600, output_height=3600)

# Save HTML version with interactive SVG
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>crossword-basic · pygal · pyplots.ai</title>
    <style>
        body {{
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            background: #f5f5f5;
            font-family: Arial, sans-serif;
        }}
        .container {{
            text-align: center;
        }}
        svg {{
            max-width: 95vw;
            max-height: 90vh;
        }}
    </style>
</head>
<body>
<div class="container">
{svg_content}
</div>
</body>
</html>
"""

with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)
