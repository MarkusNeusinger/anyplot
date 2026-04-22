""" pyplots.ai
confusion-matrix: Confusion Matrix Heatmap
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


class ConfusionMatrixChart(Graph):
    """Custom Confusion Matrix Chart for pygal - displays classification results with annotations."""

    def __init__(self, *args, **kwargs):
        self.matrix_data = kwargs.pop("matrix_data", [])
        self.class_labels = kwargs.pop("class_labels", [])
        self.colormap = kwargs.pop("colormap", [])
        self.show_values = kwargs.pop("show_values", True)
        self.x_axis_title = kwargs.pop("x_axis_title", "Predicted Label")
        self.y_axis_title = kwargs.pop("y_axis_title", "True Label")
        super().__init__(*args, **kwargs)

    def _interpolate_color(self, value, min_val, max_val):
        """Interpolate color for smooth gradient."""
        if max_val == min_val:
            return self.colormap[-1]

        # Normalize value to 0-1 range
        normalized = (value - min_val) / (max_val - min_val)
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
        """Get contrasting text color based on background brightness."""
        r, g, b = int(bg_color[1:3], 16), int(bg_color[3:5], 16), int(bg_color[5:7], 16)
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        return "#ffffff" if brightness < 140 else "#333333"

    def _plot(self):
        """Draw the confusion matrix."""
        if not self.matrix_data:
            return

        n_classes = len(self.matrix_data)

        # Find value range
        all_values = [v for row in self.matrix_data for v in row]
        min_val = min(all_values)
        max_val = max(all_values)

        # Get plot dimensions
        plot_width = self.view.width
        plot_height = self.view.height

        # Calculate margins for labels
        label_margin_left = 400
        label_margin_bottom = 350
        label_margin_top = 80
        label_margin_right = 280

        available_width = plot_width - label_margin_left - label_margin_right
        available_height = plot_height - label_margin_bottom - label_margin_top

        # Square cells for confusion matrix
        cell_size = min(available_width, available_height) / n_classes * 0.92
        gap = cell_size * 0.03

        # Calculate grid dimensions
        grid_size = n_classes * (cell_size + gap) - gap

        # Center the grid
        x_offset = self.view.x(0) + label_margin_left + (available_width - grid_size) / 2
        y_offset = self.view.y(n_classes) + label_margin_top + (available_height - grid_size) / 2

        # Create group for the chart
        plot_node = self.nodes["plot"]
        cm_group = self.svg.node(plot_node, class_="confusion-matrix")

        # Draw Y-axis title (True Label) - rotated
        y_title_size = 48
        y_title_x = x_offset - 320
        y_title_y = y_offset + grid_size / 2
        text_node = self.svg.node(cm_group, "text", x=y_title_x, y=y_title_y)
        text_node.set("text-anchor", "middle")
        text_node.set("fill", "#333333")
        text_node.set("style", f"font-size:{y_title_size}px;font-weight:bold;font-family:sans-serif")
        text_node.set("transform", f"rotate(-90, {y_title_x}, {y_title_y})")
        text_node.text = self.y_axis_title

        # Draw X-axis title (Predicted Label)
        x_title_size = 48
        x_title_x = x_offset + grid_size / 2
        x_title_y = y_offset + grid_size + 280
        text_node = self.svg.node(cm_group, "text", x=x_title_x, y=x_title_y)
        text_node.set("text-anchor", "middle")
        text_node.set("fill", "#333333")
        text_node.set("style", f"font-size:{x_title_size}px;font-weight:bold;font-family:sans-serif")
        text_node.text = self.x_axis_title

        # Draw row labels (True labels) on the left
        row_font_size = min(44, int(cell_size * 0.45))
        for i, label in enumerate(self.class_labels):
            y = y_offset + i * (cell_size + gap) + cell_size / 2
            text_node = self.svg.node(cm_group, "text", x=x_offset - 25, y=y + row_font_size * 0.35)
            text_node.set("text-anchor", "end")
            text_node.set("fill", "#333333")
            text_node.set("style", f"font-size:{row_font_size}px;font-weight:600;font-family:sans-serif")
            text_node.text = label

        # Draw column labels (Predicted labels) at the bottom - rotated
        col_font_size = min(44, int(cell_size * 0.45))
        for j, label in enumerate(self.class_labels):
            x = x_offset + j * (cell_size + gap) + cell_size / 2
            y = y_offset + grid_size + 30
            text_node = self.svg.node(cm_group, "text", x=x, y=y)
            text_node.set("text-anchor", "start")
            text_node.set("fill", "#333333")
            text_node.set("style", f"font-size:{col_font_size}px;font-weight:600;font-family:sans-serif")
            text_node.set("transform", f"rotate(45, {x}, {y})")
            text_node.text = label

        # Draw cells with values
        value_font_size = min(46, int(cell_size * 0.35))
        for i in range(n_classes):
            for j in range(n_classes):
                value = self.matrix_data[i][j]
                color = self._interpolate_color(value, min_val, max_val)
                text_color = self._get_text_color(color)

                x = x_offset + j * (cell_size + gap)
                y = y_offset + i * (cell_size + gap)

                # Highlight diagonal (correct predictions) with subtle border
                stroke_color = "#306998" if i == j else "#ffffff"
                stroke_width = "4" if i == j else "2"

                # Draw cell rectangle
                rect = self.svg.node(cm_group, "rect", x=x, y=y, width=cell_size, height=cell_size, rx=6, ry=6)
                rect.set("fill", color)
                rect.set("stroke", stroke_color)
                rect.set("stroke-width", stroke_width)

                # Add value annotation
                if self.show_values:
                    text_x = x + cell_size / 2
                    text_y = y + cell_size / 2 + value_font_size * 0.35

                    text_node = self.svg.node(cm_group, "text", x=text_x, y=text_y)
                    text_node.set("text-anchor", "middle")
                    text_node.set("fill", text_color)
                    text_node.set("style", f"font-size:{value_font_size}px;font-weight:bold;font-family:sans-serif")
                    text_node.text = str(int(value))

        # Draw colorbar on the right
        colorbar_width = 55
        colorbar_height = grid_size * 0.85
        colorbar_x = x_offset + grid_size + 90
        colorbar_y = y_offset + (grid_size - colorbar_height) / 2

        # Draw gradient colorbar
        n_segments = 50
        segment_height = colorbar_height / n_segments
        for seg_i in range(n_segments):
            seg_value = min_val + (max_val - min_val) * (n_segments - 1 - seg_i) / (n_segments - 1)
            seg_color = self._interpolate_color(seg_value, min_val, max_val)
            seg_y = colorbar_y + seg_i * segment_height

            self.svg.node(
                cm_group, "rect", x=colorbar_x, y=seg_y, width=colorbar_width, height=segment_height + 1, fill=seg_color
            )

        # Colorbar border
        self.svg.node(
            cm_group,
            "rect",
            x=colorbar_x,
            y=colorbar_y,
            width=colorbar_width,
            height=colorbar_height,
            fill="none",
            stroke="#333333",
        )

        # Colorbar labels
        cb_label_size = 38
        # Max value
        text_node = self.svg.node(
            cm_group, "text", x=colorbar_x + colorbar_width + 15, y=colorbar_y + cb_label_size * 0.35
        )
        text_node.set("fill", "#333333")
        text_node.set("style", f"font-size:{cb_label_size}px;font-family:sans-serif")
        text_node.text = str(int(max_val))

        # Mid value
        mid_y = colorbar_y + colorbar_height / 2
        text_node = self.svg.node(cm_group, "text", x=colorbar_x + colorbar_width + 15, y=mid_y + cb_label_size * 0.35)
        text_node.set("fill", "#333333")
        text_node.set("style", f"font-size:{cb_label_size}px;font-family:sans-serif")
        text_node.text = str(int((min_val + max_val) / 2))

        # Min value
        text_node = self.svg.node(
            cm_group, "text", x=colorbar_x + colorbar_width + 15, y=colorbar_y + colorbar_height + cb_label_size * 0.35
        )
        text_node.set("fill", "#333333")
        text_node.set("style", f"font-size:{cb_label_size}px;font-family:sans-serif")
        text_node.text = str(int(min_val))

        # Colorbar title
        cb_title_size = 42
        cb_title_x = colorbar_x + colorbar_width / 2
        cb_title_y = colorbar_y - 35
        text_node = self.svg.node(cm_group, "text", x=cb_title_x, y=cb_title_y)
        text_node.set("text-anchor", "middle")
        text_node.set("fill", "#333333")
        text_node.set("style", f"font-size:{cb_title_size}px;font-weight:bold;font-family:sans-serif")
        text_node.text = "Count"

    def _compute(self):
        """Compute the box for rendering."""
        n_classes = len(self.matrix_data) if self.matrix_data else 1
        self._box.xmin = 0
        self._box.xmax = n_classes
        self._box.ymin = 0
        self._box.ymax = n_classes


# Data: Multi-class classification results (e.g., sentiment analysis)
np.random.seed(42)

# Class names for a sentiment analysis model
class_names = ["Positive", "Neutral", "Negative", "Mixed"]
n_classes = len(class_names)

# Create realistic confusion matrix with:
# - High values on diagonal (correct predictions)
# - Common misclassifications (Neutral confused with Mixed, etc.)
confusion_matrix = [
    [142, 12, 5, 8],  # True Positive: mostly correct, some confused with Neutral
    [18, 98, 15, 22],  # True Neutral: often confused with others
    [7, 9, 125, 11],  # True Negative: mostly correct
    [14, 28, 18, 89],  # True Mixed: hardest to classify, often confused with Neutral
]

# Custom style for 3600x3600 square canvas
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998",),
    title_font_size=72,
    legend_font_size=48,
    label_font_size=44,
    value_font_size=38,
    font_family="sans-serif",
)

# Sequential blue colormap (low values = light, high values = dark blue)
blue_colormap = [
    "#f7fbff",  # Very light
    "#deebf7",
    "#c6dbef",
    "#9ecae1",
    "#6baed6",
    "#4292c6",
    "#2171b5",
    "#08519c",
    "#08306b",  # Dark blue (Python Blue inspired)
]

# Create confusion matrix chart
chart = ConfusionMatrixChart(
    width=3600,
    height=3600,
    style=custom_style,
    title="confusion-matrix · pygal · pyplots.ai",
    matrix_data=confusion_matrix,
    class_labels=class_names,
    colormap=blue_colormap,
    show_values=True,
    x_axis_title="Predicted Label",
    y_axis_title="True Label",
    show_legend=False,
    margin=120,
    margin_top=200,
    margin_bottom=100,
    show_x_labels=False,
    show_y_labels=False,
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
    <title>confusion-matrix - pygal</title>
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
