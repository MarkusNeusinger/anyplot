""" pyplots.ai
waffle-basic: Basic Waffle Chart
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-24
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


class Waffle(Graph):
    """Custom Waffle chart for pygal - displays proportions as colored squares in a grid."""

    _serie_margin = 0

    def __init__(self, *args, **kwargs):
        self.rows = kwargs.pop("rows", 10)
        self.cols = kwargs.pop("cols", 10)
        super().__init__(*args, **kwargs)

    def _plot(self):
        """Draw the waffle grid."""
        # Calculate total values and percentages
        total = sum(sum(v for v in serie.values if v is not None) for serie in self.series)
        if total == 0:
            return

        total_squares = self.rows * self.cols

        # Get plot area dimensions from the view
        plot_width = self.view.width
        plot_height = self.view.height

        # Calculate square size with gap
        square_size = min(plot_width / self.cols, plot_height / self.rows) * 0.85
        gap = square_size * 0.12

        # Center the grid
        grid_width = self.cols * (square_size + gap) - gap
        grid_height = self.rows * (square_size + gap) - gap

        # Calculate the actual plot area boundaries
        x_start = self.view.x(0)
        y_start = self.view.y(self.rows)

        # Center the grid within the plot area
        x_offset = x_start + (plot_width - grid_width) / 2
        y_offset = y_start + (plot_height - grid_height) / 2

        # Create a group for waffle squares
        plot_node = self.nodes["plot"]
        waffle_group = self.svg.node(plot_node, class_="waffle-chart")

        # Assign squares to each series
        square_index = 0
        for serie_index, serie in enumerate(self.series):
            serie_value = sum(v for v in serie.values if v is not None)
            num_squares = round(serie_value / total * total_squares)

            color = self.style.colors[serie_index % len(self.style.colors)]

            # Create a group for this series
            serie_group = self.svg.node(waffle_group, class_="series serie-%d color-%d" % (serie_index, serie_index))

            for _ in range(num_squares):
                if square_index >= total_squares:
                    break

                row = square_index // self.cols
                col = square_index % self.cols

                x = x_offset + col * (square_size + gap)
                y = y_offset + row * (square_size + gap)

                # Draw square with rounded corners
                self.svg.node(
                    serie_group,
                    "rect",
                    x=x,
                    y=y,
                    width=square_size,
                    height=square_size,
                    fill=color,
                    rx=square_size * 0.1,
                    ry=square_size * 0.1,
                    class_="waffle-square reactive",
                )

                square_index += 1

    def _compute(self):
        """Compute the box for rendering."""
        self._box.xmin = 0
        self._box.xmax = self.cols
        self._box.ymin = 0
        self._box.ymax = self.rows


# Custom style for 4800x2700 canvas
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998", "#FFD43B", "#4ECDC4", "#FF6B6B"),
    title_font_size=72,
    legend_font_size=48,
    label_font_size=36,
    value_font_size=32,
    font_family="sans-serif",
)

# Data - Budget allocation example (values should sum to 100)
categories = {"Operations": 42, "Marketing": 28, "R&D": 18, "Admin": 12}

# Create waffle chart
chart = Waffle(
    width=4800,
    height=2700,
    rows=10,
    cols=10,
    style=custom_style,
    title="Budget Allocation · waffle-basic · pygal · pyplots.ai",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    margin=80,
    margin_bottom=250,
    show_x_labels=False,
    show_y_labels=False,
)

# Add data series with percentages in labels
for category, value in categories.items():
    chart.add(f"{category} ({value}%)", [value])

# Save outputs
chart.render_to_file("plot.svg")
chart.render_to_png("plot.png")

# Also save HTML for interactive viewing
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>waffle-basic · pygal · pyplots.ai</title>
    <style>
        body {{ margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 100%; margin: 0 auto; }}
        svg {{ max-width: 100%; height: auto; }}
    </style>
</head>
<body>
    <div class="container">
        {chart.render(is_unicode=True)}
    </div>
</body>
</html>"""

with open("plot.html", "w") as f:
    f.write(html_content)
