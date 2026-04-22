""" pyplots.ai
heatmap-correlation: Correlation Matrix Heatmap
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import sys

import numpy as np


# Temporarily remove current directory from path to avoid name collision
_cwd = sys.path[0] if sys.path[0] else "."
if _cwd in sys.path:
    sys.path.remove(_cwd)

from pygal.graph.graph import Graph  # noqa: E402
from pygal.style import Style  # noqa: E402


# Restore path
sys.path.insert(0, _cwd)


class CorrelationHeatmap(Graph):
    """Custom Correlation Matrix Heatmap for pygal - displays correlation coefficients with diverging colors."""

    def __init__(self, *args, **kwargs):
        self.matrix_data = kwargs.pop("matrix_data", [])
        self.labels = kwargs.pop("labels", [])
        self.colormap = kwargs.pop("colormap", [])
        self.show_values = kwargs.pop("show_values", True)
        self.x_axis_title = kwargs.pop("x_axis_title", "")
        self.y_axis_title = kwargs.pop("y_axis_title", "")
        super().__init__(*args, **kwargs)

    def _interpolate_color(self, value):
        """Interpolate color for diverging colormap centered at 0, fixed range -1 to 1."""
        # Normalize value from [-1, 1] to [0, 1]
        normalized = (value + 1) / 2
        normalized = max(0, min(1, normalized))

        # Get position in colormap
        pos = normalized * (len(self.colormap) - 1)
        idx1 = int(pos)
        idx2 = min(idx1 + 1, len(self.colormap) - 1)
        frac = pos - idx1

        # Interpolate between colors
        c1 = self.colormap[idx1]
        c2 = self.colormap[idx2]

        r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
        r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)

        r = int(r1 + (r2 - r1) * frac)
        g = int(g1 + (g2 - g1) * frac)
        b = int(b1 + (b2 - b1) * frac)

        return f"#{r:02x}{g:02x}{b:02x}"

    def _get_text_color(self, bg_color):
        """Get contrasting text color (white or dark) based on background brightness."""
        r, g, b = int(bg_color[1:3], 16), int(bg_color[3:5], 16), int(bg_color[5:7], 16)
        # Calculate perceived brightness using ITU-R BT.601
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        return "#ffffff" if brightness < 140 else "#333333"

    def _plot(self):
        """Draw the correlation matrix heatmap."""
        if not self.matrix_data:
            return

        n = len(self.matrix_data)

        # Get plot dimensions
        plot_width = self.view.width
        plot_height = self.view.height

        # Calculate cell size - leave space for labels and axis titles
        label_margin_left = 480  # Space for row labels + y-axis title
        label_margin_bottom = 280  # Space for column labels (rotated) + x-axis title
        label_margin_top = 60
        label_margin_right = 320  # Space for colorbar

        available_width = plot_width - label_margin_left - label_margin_right
        available_height = plot_height - label_margin_bottom - label_margin_top

        cell_size = min(available_width, available_height) / n * 0.95
        gap = cell_size * 0.02

        # Calculate offsets to center the grid
        grid_size = n * (cell_size + gap) - gap

        x_offset = self.view.x(0) + label_margin_left + (available_width - grid_size) / 2
        y_offset = self.view.y(n) + label_margin_top + (available_height - grid_size) / 2

        # Create group for the heatmap
        plot_node = self.nodes["plot"]
        heatmap_group = self.svg.node(plot_node, class_="correlation-heatmap")

        # Draw y-axis title (rotated, on the far left)
        if self.y_axis_title:
            y_title_size = 52
            y_title_x = x_offset - 430
            y_title_y = y_offset + grid_size / 2
            text_node = self.svg.node(heatmap_group, "text", x=y_title_x, y=y_title_y)
            text_node.set("text-anchor", "middle")
            text_node.set("fill", "#333333")
            text_node.set("style", f"font-size:{y_title_size}px;font-weight:bold;font-family:sans-serif")
            text_node.set("transform", f"rotate(-90, {y_title_x}, {y_title_y})")
            text_node.text = self.y_axis_title

        # Draw row labels on the left (increased font size)
        row_font_size = min(54, int(cell_size * 0.55))
        for i, label in enumerate(self.labels):
            y = y_offset + i * (cell_size + gap) + cell_size / 2
            text_node = self.svg.node(heatmap_group, "text", x=x_offset - 25, y=y + row_font_size * 0.35)
            text_node.set("text-anchor", "end")
            text_node.set("fill", "#333333")
            text_node.set("style", f"font-size:{row_font_size}px;font-weight:600;font-family:sans-serif")
            text_node.text = label

        # Draw column labels at the bottom (rotated, increased font size)
        col_font_size = min(54, int(cell_size * 0.55))
        for j, label in enumerate(self.labels):
            x = x_offset + j * (cell_size + gap) + cell_size / 2
            y = y_offset + n * (cell_size + gap) + 25
            text_node = self.svg.node(heatmap_group, "text", x=x, y=y)
            text_node.set("text-anchor", "start")
            text_node.set("fill", "#333333")
            text_node.set("style", f"font-size:{col_font_size}px;font-weight:600;font-family:sans-serif")
            text_node.set("transform", f"rotate(45, {x}, {y})")
            text_node.text = label

        # Draw x-axis title (at the bottom)
        if self.x_axis_title:
            x_title_size = 52
            x_title_x = x_offset + grid_size / 2
            x_title_y = y_offset + n * (cell_size + gap) + 240
            text_node = self.svg.node(heatmap_group, "text", x=x_title_x, y=x_title_y)
            text_node.set("text-anchor", "middle")
            text_node.set("fill", "#333333")
            text_node.set("style", f"font-size:{x_title_size}px;font-weight:bold;font-family:sans-serif")
            text_node.text = self.x_axis_title

        # Draw cells with correlation values
        value_font_size = min(46, int(cell_size * 0.38))
        for i in range(n):
            for j in range(n):
                value = self.matrix_data[i][j]
                color = self._interpolate_color(value)
                text_color = self._get_text_color(color)

                x = x_offset + j * (cell_size + gap)
                y = y_offset + i * (cell_size + gap)

                # Draw cell rectangle with rounded corners
                rect = self.svg.node(heatmap_group, "rect", x=x, y=y, width=cell_size, height=cell_size, rx=4, ry=4)
                rect.set("fill", color)
                rect.set("stroke", "#ffffff")
                rect.set("stroke-width", "2")

                # Add correlation value annotation
                if self.show_values:
                    text_x = x + cell_size / 2
                    text_y = y + cell_size / 2 + value_font_size * 0.35

                    text_node = self.svg.node(heatmap_group, "text", x=text_x, y=text_y)
                    text_node.set("text-anchor", "middle")
                    text_node.set("fill", text_color)
                    text_node.set("style", f"font-size:{value_font_size}px;font-weight:bold;font-family:sans-serif")
                    text_node.text = f"{value:.2f}"

        # Draw colorbar on the right (fixed range -1 to 1)
        colorbar_width = 55
        colorbar_height = grid_size * 0.85
        colorbar_x = x_offset + grid_size + 100
        colorbar_y = y_offset + (grid_size - colorbar_height) / 2

        # Draw gradient colorbar using multiple rectangles
        n_segments = 60
        segment_height = colorbar_height / n_segments
        for seg_i in range(n_segments):
            # Map segment to value in range [1, -1] (top to bottom)
            seg_value = 1 - (2 * seg_i / (n_segments - 1))
            seg_color = self._interpolate_color(seg_value)
            seg_y = colorbar_y + seg_i * segment_height

            self.svg.node(
                heatmap_group,
                "rect",
                x=colorbar_x,
                y=seg_y,
                width=colorbar_width,
                height=segment_height + 1,
                fill=seg_color,
            )

        # Colorbar border
        self.svg.node(
            heatmap_group,
            "rect",
            x=colorbar_x,
            y=colorbar_y,
            width=colorbar_width,
            height=colorbar_height,
            fill="none",
            stroke="#333333",
        )

        # Colorbar labels (fixed -1, 0, 1)
        cb_label_size = 42
        # Top: +1
        text_node = self.svg.node(
            heatmap_group, "text", x=colorbar_x + colorbar_width + 18, y=colorbar_y + cb_label_size * 0.35
        )
        text_node.set("fill", "#333333")
        text_node.set("style", f"font-size:{cb_label_size}px;font-family:sans-serif")
        text_node.text = "+1.00"

        # Middle: 0
        mid_y = colorbar_y + colorbar_height / 2
        text_node = self.svg.node(
            heatmap_group, "text", x=colorbar_x + colorbar_width + 18, y=mid_y + cb_label_size * 0.35
        )
        text_node.set("fill", "#333333")
        text_node.set("style", f"font-size:{cb_label_size}px;font-family:sans-serif")
        text_node.text = " 0.00"

        # Bottom: -1
        text_node = self.svg.node(
            heatmap_group,
            "text",
            x=colorbar_x + colorbar_width + 18,
            y=colorbar_y + colorbar_height + cb_label_size * 0.35,
        )
        text_node.set("fill", "#333333")
        text_node.set("style", f"font-size:{cb_label_size}px;font-family:sans-serif")
        text_node.text = "-1.00"

        # Colorbar title
        cb_title_size = 46
        cb_title_x = colorbar_x + colorbar_width / 2
        cb_title_y = colorbar_y - 40
        text_node = self.svg.node(heatmap_group, "text", x=cb_title_x, y=cb_title_y)
        text_node.set("text-anchor", "middle")
        text_node.set("fill", "#333333")
        text_node.set("style", f"font-size:{cb_title_size}px;font-weight:bold;font-family:sans-serif")
        text_node.text = "Correlation"

    def _compute(self):
        """Compute the box for rendering."""
        n = len(self.matrix_data) if self.matrix_data else 1
        self._box.xmin = 0
        self._box.xmax = n
        self._box.ymin = 0
        self._box.ymax = n


# Data: Correlation matrix for financial portfolio metrics
np.random.seed(42)

# Variable names for correlation analysis (8 variables for good visibility)
variables = ["Revenue", "Profit", "Customers", "Marketing", "R&D Spend", "Employees", "Market Share", "Stock Price"]
n = len(variables)

# Create a realistic correlation matrix with varied relationships
# Positive correlations: Revenue-Profit, Customers-Revenue, Stock Price-Profit
# Negative correlations: Marketing-Profit margin, R&D-Short term profit
# Weak correlations: Some unrelated metrics
correlation_matrix = np.array(
    [
        [1.00, 0.82, 0.75, 0.45, 0.28, 0.55, 0.68, 0.72],  # Revenue
        [0.82, 1.00, 0.58, -0.15, -0.22, 0.35, 0.62, 0.85],  # Profit
        [0.75, 0.58, 1.00, 0.52, 0.18, 0.48, 0.55, 0.45],  # Customers
        [0.45, -0.15, 0.52, 1.00, 0.32, 0.38, 0.42, 0.12],  # Marketing
        [0.28, -0.22, 0.18, 0.32, 1.00, 0.25, 0.15, -0.08],  # R&D Spend
        [0.55, 0.35, 0.48, 0.38, 0.25, 1.00, 0.32, 0.28],  # Employees
        [0.68, 0.62, 0.55, 0.42, 0.15, 0.32, 1.00, 0.58],  # Market Share
        [0.72, 0.85, 0.45, 0.12, -0.08, 0.28, 0.58, 1.00],  # Stock Price
    ]
)

# Convert to list of lists for the chart
matrix_data = correlation_matrix.tolist()

# Custom style for 3600x3600 square canvas (ideal for symmetric matrix)
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998",),
    title_font_size=72,
    legend_font_size=48,
    label_font_size=50,
    value_font_size=44,
    font_family="sans-serif",
)

# Diverging colormap: blue (negative) -> white (zero) -> red (positive)
# Coolwarm-style diverging palette for correlations
diverging_colormap = [
    "#2166ac",  # Strong blue (-1.0)
    "#4393c3",  # Medium blue
    "#92c5de",  # Light blue
    "#d1e5f0",  # Very light blue
    "#f7f7f7",  # White (0.0)
    "#fddbc7",  # Very light red
    "#f4a582",  # Light red
    "#d6604d",  # Medium red
    "#b2182b",  # Strong red (+1.0)
]

# Create correlation heatmap
chart = CorrelationHeatmap(
    width=3600,
    height=3600,
    style=custom_style,
    title="heatmap-correlation · pygal · pyplots.ai",
    matrix_data=matrix_data,
    labels=variables,
    colormap=diverging_colormap,
    show_values=True,
    show_legend=False,
    margin=120,
    margin_top=200,
    margin_bottom=100,
    show_x_labels=False,
    show_y_labels=False,
    x_axis_title="Business Metrics",
    y_axis_title="Business Metrics",
)

# Add a dummy series to trigger _plot (pygal requires at least one series)
chart.add("", [0])

# Save outputs
chart.render_to_file("plot.svg")
chart.render_to_png("plot.png")

# Also save HTML for interactivity
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>heatmap-correlation - pygal</title>
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
