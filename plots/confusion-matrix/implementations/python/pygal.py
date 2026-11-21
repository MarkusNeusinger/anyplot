"""anyplot.ai
confusion-matrix: Confusion Matrix Heatmap
Library: pygal 3.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-09
"""

import os

import numpy as np
import pandas as pd
from pygal.graph.graph import Graph
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Imprint sequential colormap (single polarity): brand green -> blue
IMPRINT_SEQ = ["#009E73", "#4467A3"]

# Columns: set these to your table's labels
TRUE_LABEL = "True Label"  # role: true_labels
PREDICTED_LABEL = "Predicted Label"  # role: predicted_labels
CLASS_NAME = "Class"  # role: class_names
COUNT = "Count"  # role: extra

# Data: replace this block with your own matrix, for example df = pd.read_csv("matrix.csv", index_col=0)
class_names = ["Positive", "Neutral", "Negative", "Mixed"]
df = pd.DataFrame(
    [[142, 12, 5, 8], [18, 98, 15, 22], [7, 9, 125, 11], [14, 28, 18, 89]],
    index=pd.Index(class_names, name=CLASS_NAME),
    columns=class_names,
)


# Plot: pygal has no heatmap, so a custom Graph subclass draws the cells; it reads only df and the constants
class ConfusionMatrixChart(Graph):
    """Custom Confusion Matrix Chart for pygal - displays classification results."""

    def __init__(self, *args, **kwargs):
        self.matrix = kwargs.pop("matrix")
        self.colormap = kwargs.pop("colormap")
        self.x_axis_title = kwargs.pop("x_axis_title")
        self.y_axis_title = kwargs.pop("y_axis_title")
        self.value_title = kwargs.pop("value_title")
        super().__init__(*args, **kwargs)

    def _interpolate_color(self, value, min_val, max_val):
        """Interpolate the colormap stops for a value."""
        normalized = 1.0 if max_val == min_val else (value - min_val) / (max_val - min_val)
        normalized = max(0.0, min(1.0, normalized))

        pos = normalized * (len(self.colormap) - 1)
        idx1 = int(pos)
        idx2 = min(idx1 + 1, len(self.colormap) - 1)
        frac = pos - idx1

        c1 = self.colormap[idx1]
        c2 = self.colormap[idx2]

        r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
        r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)

        r = round(r1 + (r2 - r1) * frac)
        g = round(g1 + (g2 - g1) * frac)
        b = round(b1 + (b2 - b1) * frac)

        return f"#{r:02x}{g:02x}{b:02x}"

    def _text(self, parent, text, x, y, size, fill, anchor="start", weight="normal"):
        node = self.svg.node(parent, "text", x=x, y=y)
        node.set("text-anchor", anchor)
        node.set("fill", fill)
        node.set("style", f"font-size:{size}px;font-weight:{weight};font-family:sans-serif")
        node.text = text
        return node

    def _plot(self):
        """Draw the confusion matrix."""
        values = self.matrix.to_numpy(dtype=float, na_value=float("nan"))
        n_rows, n_cols = values.shape
        n_classes = max(n_rows, n_cols)
        row_labels = [str(label) for label in self.matrix.index]
        col_labels = [str(label) for label in self.matrix.columns]
        min_val = float(np.nanmin(values))
        max_val = float(np.nanmax(values))

        plot_width = self.view.width
        plot_height = self.view.height

        label_margin_left = 270
        label_margin_bottom = 235
        label_margin_top = 50
        label_margin_right = 190

        available_width = plot_width - label_margin_left - label_margin_right
        available_height = plot_height - label_margin_bottom - label_margin_top

        cell_size = min(available_width, available_height) / n_classes * 0.92
        gap = cell_size * 0.03
        grid_size = n_classes * (cell_size + gap) - gap

        x_offset = self.view.x(0) + label_margin_left + (available_width - grid_size) / 2
        y_offset = self.view.y(n_classes) + label_margin_top + (available_height - grid_size) / 2

        cm_group = self.svg.node(self.nodes["plot"], class_="confusion-matrix")

        # Axis titles
        y_title_x = x_offset - 215
        y_title_y = y_offset + grid_size / 2
        node = self._text(cm_group, self.y_axis_title, y_title_x, y_title_y, 40, INK, "middle", "bold")
        node.set("transform", f"rotate(-90, {y_title_x}, {y_title_y})")
        self._text(
            cm_group, self.x_axis_title, x_offset + grid_size / 2, y_offset + grid_size + 200, 40, INK, "middle", "bold"
        )

        # Class labels: rows on the left, columns rotated below the grid
        tick_size = min(34, int(cell_size * 0.3))
        for i, label in enumerate(row_labels):
            y = y_offset + i * (cell_size + gap) + cell_size / 2
            self._text(cm_group, label, x_offset - 18, y + tick_size * 0.35, tick_size, INK, "end", "600")
        for j, label in enumerate(col_labels):
            x = x_offset + j * (cell_size + gap) + cell_size / 2
            y = y_offset + grid_size + 28
            node = self._text(cm_group, label, x, y, tick_size, INK, "start", "600")
            node.set("transform", f"rotate(45, {x}, {y})")

        # Cells with counts; the diagonal (correct predictions) gets a heavier outline
        value_size = min(52, int(cell_size * 0.3))
        for i in range(n_rows):
            for j in range(n_cols):
                value = values[i][j]
                if np.isnan(value):
                    continue
                color = self._interpolate_color(value, min_val, max_val)

                x = x_offset + j * (cell_size + gap)
                y = y_offset + i * (cell_size + gap)
                on_diagonal = i == j

                rect = self.svg.node(cm_group, "rect", x=x, y=y, width=cell_size, height=cell_size, rx=6, ry=6)
                rect.set("fill", color)
                rect.set("stroke", INK if on_diagonal else INK_SOFT)
                rect.set("stroke-width", "5" if on_diagonal else "1.5")

                self._text(
                    cm_group,
                    str(int(value)),
                    x + cell_size / 2,
                    y + cell_size / 2 + value_size * 0.35,
                    value_size,
                    "#FFFFFF",
                    "middle",
                    "bold",
                )

        # Colorbar
        colorbar_width = 40
        colorbar_height = grid_size * 0.85
        colorbar_x = x_offset + grid_size + 60
        colorbar_y = y_offset + (grid_size - colorbar_height) / 2

        n_segments = 50
        segment_height = colorbar_height / n_segments
        for seg_i in range(n_segments):
            seg_value = min_val + (max_val - min_val) * (n_segments - 1 - seg_i) / (n_segments - 1)
            self.svg.node(
                cm_group,
                "rect",
                x=colorbar_x,
                y=colorbar_y + seg_i * segment_height,
                width=colorbar_width,
                height=segment_height + 1,
                fill=self._interpolate_color(seg_value, min_val, max_val),
            )
        self.svg.node(
            cm_group,
            "rect",
            x=colorbar_x,
            y=colorbar_y,
            width=colorbar_width,
            height=colorbar_height,
            fill="none",
            stroke=INK,
            stroke_width="2",
        )

        cb_label_size = 30
        tick_x = colorbar_x + colorbar_width + 10
        for frac, value in ((0, max_val), (0.5, (min_val + max_val) / 2), (1, min_val)):
            self._text(
                cm_group,
                str(int(value)),
                tick_x,
                colorbar_y + colorbar_height * frac + cb_label_size * 0.35,
                cb_label_size,
                INK,
            )

        self._text(
            cm_group, self.value_title, colorbar_x + colorbar_width / 2, colorbar_y - 25, 34, INK, "middle", "bold"
        )

    def _compute(self):
        """Compute the box for rendering."""
        n_classes = max(self.matrix.shape)
        self._box.xmin = 0
        self._box.xmax = n_classes
        self._box.ymin = 0
        self._box.ymax = n_classes


chart = ConfusionMatrixChart(
    width=2400,
    height=2400,
    style=Style(
        background=PAGE_BG,
        plot_background=PAGE_BG,
        foreground=INK,
        foreground_strong=INK,
        foreground_subtle=INK_MUTED,
        colors=tuple(IMPRINT_PALETTE),
        title_font_size=52,
        legend_font_size=34,
        label_font_size=34,
        value_font_size=28,
        font_family="sans-serif",
    ),
    title="confusion-matrix · python · pygal · anyplot.ai",
    matrix=df,
    colormap=IMPRINT_SEQ,
    x_axis_title=PREDICTED_LABEL,
    y_axis_title=TRUE_LABEL,
    value_title=COUNT,
    show_legend=False,
    margin=80,
    margin_top=130,
    margin_bottom=70,
    show_x_labels=False,
    show_y_labels=False,
)
chart.add("", [0])

# Save
chart.render_to_file(f"plot-{THEME}.svg")
chart.render_to_png(f"plot-{THEME}.png")

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>confusion-matrix - pygal</title>
    <style>
        body {{ margin: 0; display: flex; justify-content: center; align-items: center; min-height: 100vh; background: {PAGE_BG}; }}
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

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)
