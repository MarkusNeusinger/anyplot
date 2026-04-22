""" pyplots.ai
sudoku-basic: Basic Sudoku Grid
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import sys


# Temporarily remove current directory from path to avoid name collision
_cwd = sys.path[0] if sys.path[0] else "."
if _cwd in sys.path:
    sys.path.remove(_cwd)

from pygal.graph.graph import Graph  # noqa: E402
from pygal.style import Style  # noqa: E402


# Restore path
sys.path.insert(0, _cwd)


class SudokuGrid(Graph):
    """Custom Sudoku Grid chart for pygal - displays a 9x9 grid with numbers."""

    def __init__(self, *args, **kwargs):
        self.grid_data = kwargs.pop("grid_data", [[0] * 9 for _ in range(9)])
        self.cell_color = kwargs.pop("cell_color", "#306998")
        self.grid_line_color = kwargs.pop("grid_line_color", "#000000")
        self.thin_line_color = kwargs.pop("thin_line_color", "#999999")
        super().__init__(*args, **kwargs)

    def _plot(self):
        """Draw the Sudoku grid."""
        # Get plot dimensions
        plot_width = self.view.width
        plot_height = self.view.height

        # Calculate grid size to fit within the view
        margin_top = 100
        margin_bottom = 80
        margin_sides = 80

        available_width = plot_width - 2 * margin_sides
        available_height = plot_height - margin_top - margin_bottom

        # Use the smaller dimension to keep grid square
        grid_size = min(available_width, available_height)
        cell_size = grid_size / 9

        # Center the grid
        x_offset = self.view.x(0) + margin_sides + (available_width - grid_size) / 2
        y_offset = self.view.y(9) + margin_top + (available_height - grid_size) / 2

        # Create group for the sudoku grid
        plot_node = self.nodes["plot"]
        sudoku_group = self.svg.node(plot_node, class_="sudoku-grid")

        # Draw background
        self.svg.node(
            sudoku_group,
            "rect",
            x=x_offset,
            y=y_offset,
            width=grid_size,
            height=grid_size,
            fill="white",
            stroke=self.grid_line_color,
        )
        self.svg.node(sudoku_group, "rect", x=x_offset, y=y_offset, width=grid_size, height=grid_size, fill="white")

        # Draw thin lines for individual cells (every cell except where thick lines go)
        thin_width = 2
        for i in range(1, 9):
            if i % 3 != 0:  # Skip positions where thick lines will go
                # Horizontal line
                y_pos = y_offset + i * cell_size
                self.svg.node(
                    sudoku_group,
                    "line",
                    x1=x_offset,
                    y1=y_pos,
                    x2=x_offset + grid_size,
                    y2=y_pos,
                    stroke=self.thin_line_color,
                )
                line = self.svg.node(sudoku_group, "line", x1=x_offset, y1=y_pos, x2=x_offset + grid_size, y2=y_pos)
                line.set("stroke", self.thin_line_color)
                line.set("stroke-width", str(thin_width))

                # Vertical line
                x_pos = x_offset + i * cell_size
                line = self.svg.node(sudoku_group, "line", x1=x_pos, y1=y_offset, x2=x_pos, y2=y_offset + grid_size)
                line.set("stroke", self.thin_line_color)
                line.set("stroke-width", str(thin_width))

        # Draw thick lines for 3x3 box boundaries
        thick_width = 8
        for i in range(0, 10, 3):
            # Horizontal line
            y_pos = y_offset + i * cell_size
            line = self.svg.node(sudoku_group, "line", x1=x_offset, y1=y_pos, x2=x_offset + grid_size, y2=y_pos)
            line.set("stroke", self.grid_line_color)
            line.set("stroke-width", str(thick_width))

            # Vertical line
            x_pos = x_offset + i * cell_size
            line = self.svg.node(sudoku_group, "line", x1=x_pos, y1=y_offset, x2=x_pos, y2=y_offset + grid_size)
            line.set("stroke", self.grid_line_color)
            line.set("stroke-width", str(thick_width))

        # Draw numbers
        font_size = int(cell_size * 0.6)
        for row in range(9):
            for col in range(9):
                value = self.grid_data[row][col]
                if value != 0:
                    x = x_offset + col * cell_size + cell_size / 2
                    y = y_offset + row * cell_size + cell_size / 2 + font_size * 0.35

                    text_node = self.svg.node(sudoku_group, "text", x=x, y=y)
                    text_node.set("text-anchor", "middle")
                    text_node.set("fill", self.cell_color)
                    text_node.set("style", f"font-size:{font_size}px;font-weight:bold;font-family:Arial,sans-serif")
                    text_node.text = str(value)

    def _compute(self):
        """Compute the box for rendering."""
        self._box.xmin = 0
        self._box.xmax = 9
        self._box.ymin = 0
        self._box.ymax = 9


# Sample Sudoku puzzle data (0 = empty cell)
# Classic puzzle with starting numbers
grid = [
    [5, 3, 0, 0, 7, 0, 0, 0, 0],
    [6, 0, 0, 1, 9, 5, 0, 0, 0],
    [0, 9, 8, 0, 0, 0, 0, 6, 0],
    [8, 0, 0, 0, 6, 0, 0, 0, 3],
    [4, 0, 0, 8, 0, 3, 0, 0, 1],
    [7, 0, 0, 0, 2, 0, 0, 0, 6],
    [0, 6, 0, 0, 0, 0, 2, 8, 0],
    [0, 0, 0, 4, 1, 9, 0, 0, 5],
    [0, 0, 0, 0, 8, 0, 0, 7, 9],
]

# Custom style for 3600x3600 square canvas (appropriate for grid-based visualization)
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#000000",
    foreground_subtle="#666666",
    colors=("#306998",),
    title_font_size=72,
    legend_font_size=48,
    label_font_size=48,
    value_font_size=64,
    font_family="Arial, sans-serif",
)

# Create Sudoku grid
chart = SudokuGrid(
    width=3600,
    height=3600,
    style=custom_style,
    title="sudoku-basic · pygal · pyplots.ai",
    grid_data=grid,
    cell_color="#306998",
    grid_line_color="#000000",
    thin_line_color="#999999",
    show_legend=False,
    margin=100,
    margin_top=200,
    margin_bottom=100,
    show_x_labels=False,
    show_y_labels=False,
)

# Add a dummy series to trigger _plot (pygal requires at least one series)
chart.add("", [0])

# Save output
chart.render_to_file("plot.svg")
chart.render_to_png("plot.png")

# Also save HTML for interactivity
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>sudoku-basic - pygal</title>
    <style>
        body {{ margin: 0; display: flex; justify-content: center; align-items: center; min-height: 100vh; background: #f5f5f5; }}
        .chart {{ max-width: 100%; height: auto; }}
    </style>
</head>
<body>
    <figure class="chart">
        {chart.render(is_unicode=True)}
    </figure>
</body>
</html>
"""

with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)
