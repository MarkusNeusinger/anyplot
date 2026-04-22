""" pyplots.ai
mosaic-categorical: Mosaic Plot for Categorical Association Analysis
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-11
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


class MosaicPlot(Graph):
    """Custom Mosaic Plot for pygal - visualizes contingency table relationships."""

    def __init__(self, *args, **kwargs):
        self.contingency_data = kwargs.pop("contingency_data", {})
        self.row_labels = kwargs.pop("row_labels", [])
        self.col_labels = kwargs.pop("col_labels", [])
        self.colors = kwargs.pop("cell_colors", ["#306998", "#FFD43B", "#4CAF50", "#E91E63"])
        self.gap_ratio = kwargs.pop("gap_ratio", 0.02)
        super().__init__(*args, **kwargs)

    def _plot(self):
        """Draw the mosaic plot."""
        if not self.contingency_data or not self.row_labels or not self.col_labels:
            return

        n_rows = len(self.row_labels)
        n_cols = len(self.col_labels)

        # Calculate column totals (marginal proportions for category_1)
        col_totals = []
        for col in self.col_labels:
            total = sum(self.contingency_data.get((row, col), 0) for row in self.row_labels)
            col_totals.append(total)

        grand_total = sum(col_totals)
        if grand_total == 0:
            return

        col_proportions = [t / grand_total for t in col_totals]

        # Get plot dimensions
        plot_width = self.view.width
        plot_height = self.view.height

        # Calculate margins
        margin_left = 380
        margin_right = 100
        margin_top = 120
        margin_bottom = 280

        available_width = plot_width - margin_left - margin_right
        available_height = plot_height - margin_top - margin_bottom

        # Gap between columns and rows
        col_gap = available_width * self.gap_ratio
        row_gap = available_height * self.gap_ratio

        # Calculate actual drawing area minus gaps
        total_col_gaps = col_gap * (n_cols - 1)
        total_row_gaps = row_gap * (n_rows - 1)
        drawing_width = available_width - total_col_gaps
        drawing_height = available_height - total_row_gaps

        x_offset = self.view.x(0) + margin_left
        y_offset = self.view.y(n_rows) + margin_top

        # Create group for the mosaic plot
        plot_node = self.nodes["plot"]
        mosaic_group = self.svg.node(plot_node, class_="mosaic-plot")

        # Draw each column (category_1) with variable width
        current_x = x_offset
        for j, col in enumerate(self.col_labels):
            col_width = drawing_width * col_proportions[j]

            # Calculate row proportions within this column
            col_total = col_totals[j]
            if col_total == 0:
                current_x += col_width + col_gap
                continue

            row_values = [self.contingency_data.get((row, col), 0) for row in self.row_labels]
            row_proportions = [v / col_total for v in row_values]

            # Draw cells within this column (stack vertically)
            current_y = y_offset
            for i, row in enumerate(self.row_labels):
                cell_height = drawing_height * row_proportions[i]
                if cell_height < 1:
                    current_y += cell_height + row_gap
                    continue

                # Get color for this row category
                color = self.colors[i % len(self.colors)]

                # Draw cell rectangle
                rect = self.svg.node(
                    mosaic_group,
                    "rect",
                    x=current_x,
                    y=current_y,
                    width=max(col_width, 1),
                    height=max(cell_height, 1),
                    rx=3,
                    ry=3,
                )
                rect.set("fill", color)
                rect.set("stroke", "#ffffff")
                rect.set("stroke-width", "3")
                rect.set("fill-opacity", "0.85")

                # Add frequency label if cell is large enough
                freq = self.contingency_data.get((row, col), 0)
                if cell_height > 60 and col_width > 80:
                    label_size = min(40, int(min(col_width, cell_height) * 0.35))
                    text_x = current_x + col_width / 2
                    text_y = current_y + cell_height / 2 + label_size * 0.35

                    text_node = self.svg.node(mosaic_group, "text", x=text_x, y=text_y)
                    text_node.set("text-anchor", "middle")
                    text_node.set("fill", "#ffffff")
                    text_node.set("style", f"font-size:{label_size}px;font-weight:bold;font-family:sans-serif")
                    text_node.set("text-shadow", "1px 1px 2px rgba(0,0,0,0.5)")
                    text_node.text = str(freq)

                current_y += cell_height + row_gap

            # Draw column label at the bottom
            col_label_size = 44
            label_x = current_x + col_width / 2
            label_y = y_offset + available_height + 60
            text_node = self.svg.node(mosaic_group, "text", x=label_x, y=label_y)
            text_node.set("text-anchor", "middle")
            text_node.set("fill", "#333333")
            text_node.set("style", f"font-size:{col_label_size}px;font-weight:bold;font-family:sans-serif")
            text_node.text = col

            # Draw proportion label below column label
            prop_label_size = 32
            prop_label_y = label_y + 50
            text_node = self.svg.node(mosaic_group, "text", x=label_x, y=prop_label_y)
            text_node.set("text-anchor", "middle")
            text_node.set("fill", "#666666")
            text_node.set("style", f"font-size:{prop_label_size}px;font-family:sans-serif")
            text_node.text = f"({col_proportions[j] * 100:.1f}%)"

            current_x += col_width + col_gap

        # Draw row labels on the left (legend)
        for i, row in enumerate(self.row_labels):
            color = self.colors[i % len(self.colors)]

            # Calculate approximate vertical position based on cumulative proportions
            # Use the first column proportions as reference
            first_col = self.col_labels[0]
            first_col_total = col_totals[0] if col_totals[0] > 0 else 1

            cumulative = 0
            for k, r in enumerate(self.row_labels):
                if k < i:
                    cumulative += self.contingency_data.get((r, first_col), 0) / first_col_total

            row_prop = self.contingency_data.get((row, first_col), 0) / first_col_total
            center_y = y_offset + drawing_height * (cumulative + row_prop / 2) + i * row_gap

            # Draw color swatch
            swatch_size = 30
            swatch_x = x_offset - 180
            swatch_y = center_y - swatch_size / 2

            rect = self.svg.node(
                mosaic_group, "rect", x=swatch_x, y=swatch_y, width=swatch_size, height=swatch_size, rx=4, ry=4
            )
            rect.set("fill", color)
            rect.set("stroke", "#333333")
            rect.set("stroke-width", "1")

            # Draw row label
            row_label_size = 40
            text_x = swatch_x + swatch_size + 15
            text_y = center_y + row_label_size * 0.35
            text_node = self.svg.node(mosaic_group, "text", x=text_x, y=text_y)
            text_node.set("text-anchor", "start")
            text_node.set("fill", "#333333")
            text_node.set("style", f"font-size:{row_label_size}px;font-weight:bold;font-family:sans-serif")
            text_node.text = row

        # Add axis titles
        # X-axis title
        x_title_size = 48
        x_title_x = x_offset + available_width / 2
        x_title_y = y_offset + available_height + 160
        text_node = self.svg.node(mosaic_group, "text", x=x_title_x, y=x_title_y)
        text_node.set("text-anchor", "middle")
        text_node.set("fill", "#333333")
        text_node.set("style", f"font-size:{x_title_size}px;font-weight:bold;font-family:sans-serif")
        text_node.text = "Passenger Class"

        # Y-axis title (rotated)
        y_title_size = 48
        y_title_x = x_offset - 320
        y_title_y = y_offset + available_height / 2
        text_node = self.svg.node(mosaic_group, "text", x=y_title_x, y=y_title_y)
        text_node.set("text-anchor", "middle")
        text_node.set("fill", "#333333")
        text_node.set("style", f"font-size:{y_title_size}px;font-weight:bold;font-family:sans-serif")
        text_node.set("transform", f"rotate(-90, {y_title_x}, {y_title_y})")
        text_node.text = "Survival Status"

    def _compute(self):
        """Compute the box for rendering."""
        n_rows = len(self.row_labels) if self.row_labels else 1
        n_cols = len(self.col_labels) if self.col_labels else 1
        self._box.xmin = 0
        self._box.xmax = n_cols
        self._box.ymin = 0
        self._box.ymax = n_rows


# Generate data - Titanic survival data (classic categorical association example)
np.random.seed(42)

# Create Titanic-like survival data
# Class: 1st, 2nd, 3rd
# Survival: Survived, Did Not Survive
data = {
    ("Survived", "1st Class"): 203,
    ("Did Not Survive", "1st Class"): 122,
    ("Survived", "2nd Class"): 118,
    ("Did Not Survive", "2nd Class"): 167,
    ("Survived", "3rd Class"): 178,
    ("Did Not Survive", "3rd Class"): 528,
}

row_labels = ["Survived", "Did Not Survive"]
col_labels = ["1st Class", "2nd Class", "3rd Class"]

# Custom style for large canvas
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
    value_font_size=36,
    font_family="sans-serif",
)

# Colors for survival categories (Python Blue for survived, muted red for did not survive)
survival_colors = ["#306998", "#C75B5B"]

# Create mosaic plot
chart = MosaicPlot(
    width=4800,
    height=2700,
    style=custom_style,
    title="mosaic-categorical · pygal · pyplots.ai",
    contingency_data=data,
    row_labels=row_labels,
    col_labels=col_labels,
    cell_colors=survival_colors,
    gap_ratio=0.015,
    show_legend=False,
    margin=100,
    margin_top=220,
    margin_bottom=150,
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
    <title>mosaic-categorical - pygal</title>
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
