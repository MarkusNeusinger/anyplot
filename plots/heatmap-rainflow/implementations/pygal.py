""" pyplots.ai
heatmap-rainflow: Rainflow Counting Matrix for Fatigue Analysis
Library: pygal 3.1.0 | Python 3.14.3
Quality: 82/100 | Created: 2026-03-02
"""

import math
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


class RainflowHeatmap(Graph):
    """Custom Rainflow Counting Matrix Heatmap for pygal."""

    def __init__(self, *args, **kwargs):
        self.matrix_data = kwargs.pop("matrix_data", [])
        self.row_labels = kwargs.pop("row_labels", [])
        self.col_labels = kwargs.pop("col_labels", [])
        self.colormap = kwargs.pop("colormap", [])
        self.vmax = kwargs.pop("vmax", 1)
        self.log_scale = kwargs.pop("log_scale", True)
        self.x_axis_title = kwargs.pop("x_axis_title", "")
        self.y_axis_title = kwargs.pop("y_axis_title", "")
        self.colorbar_title = kwargs.pop("colorbar_title", "")
        super().__init__(*args, **kwargs)

    def _interpolate_color(self, value):
        """Interpolate color from sequential colormap based on normalized value [0, 1]."""
        normalized = max(0, min(1, value))
        pos = normalized * (len(self.colormap) - 1)
        idx1 = int(pos)
        idx2 = min(idx1 + 1, len(self.colormap) - 1)
        frac = pos - idx1

        c1 = self.colormap[idx1]
        c2 = self.colormap[idx2]

        r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
        r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)

        r = int(r1 + (r2 - r1) * frac)
        g = int(g1 + (g2 - g1) * frac)
        b = int(b1 + (b2 - b1) * frac)

        return f"#{r:02x}{g:02x}{b:02x}"

    def _normalize_value(self, value):
        """Normalize a count value to [0, 1] using log scale."""
        if value <= 0:
            return -1
        log_val = math.log10(value + 1)
        log_max = math.log10(self.vmax + 1)
        return log_val / log_max if log_max > 0 else 0

    def _plot(self):
        """Draw the rainflow counting matrix heatmap."""
        if not self.matrix_data:
            return

        n_rows = len(self.matrix_data)
        n_cols = len(self.matrix_data[0]) if n_rows > 0 else 0

        plot_width = self.view.width
        plot_height = self.view.height

        # Layout margins
        label_margin_left = 520
        label_margin_bottom = 300
        label_margin_top = 60
        label_margin_right = 400

        available_width = plot_width - label_margin_left - label_margin_right
        available_height = plot_height - label_margin_bottom - label_margin_top

        cell_w = available_width / n_cols * 0.97
        cell_h = available_height / n_rows * 0.97
        gap = min(cell_w, cell_h) * 0.01

        grid_width = n_cols * (cell_w + gap) - gap
        grid_height = n_rows * (cell_h + gap) - gap

        x_offset = self.view.x(0) + label_margin_left + (available_width - grid_width) / 2
        y_offset = self.view.y(n_rows) + label_margin_top + (available_height - grid_height) / 2

        plot_node = self.nodes["plot"]
        heatmap_group = self.svg.node(plot_node, class_="rainflow-heatmap")

        # Y-axis title (rotated)
        if self.y_axis_title:
            y_title_size = 52
            y_title_x = x_offset - 460
            y_title_y = y_offset + grid_height / 2
            text_node = self.svg.node(heatmap_group, "text", x=y_title_x, y=y_title_y)
            text_node.set("text-anchor", "middle")
            text_node.set("fill", "#333333")
            text_node.set("style", f"font-size:{y_title_size}px;font-weight:bold;font-family:sans-serif")
            text_node.set("transform", f"rotate(-90, {y_title_x}, {y_title_y})")
            text_node.text = self.y_axis_title

        # Row labels (amplitude bins) — show every other to avoid crowding
        row_font_size = min(36, int(cell_h * 0.6))
        for i, label in enumerate(self.row_labels):
            if i % 2 == 0 or i == len(self.row_labels) - 1:
                y = y_offset + i * (cell_h + gap) + cell_h / 2
                text_node = self.svg.node(heatmap_group, "text", x=x_offset - 20, y=y + row_font_size * 0.35)
                text_node.set("text-anchor", "end")
                text_node.set("fill", "#333333")
                text_node.set("style", f"font-size:{row_font_size}px;font-weight:500;font-family:sans-serif")
                text_node.text = label

        # Column labels (mean bins) — show every other, rotated
        col_font_size = min(36, int(cell_w * 0.55))
        for j, label in enumerate(self.col_labels):
            if j % 2 == 0 or j == len(self.col_labels) - 1:
                x = x_offset + j * (cell_w + gap) + cell_w / 2
                y = y_offset + n_rows * (cell_h + gap) + 15
                text_node = self.svg.node(heatmap_group, "text", x=x, y=y)
                text_node.set("text-anchor", "start")
                text_node.set("fill", "#333333")
                text_node.set("style", f"font-size:{col_font_size}px;font-weight:500;font-family:sans-serif")
                text_node.set("transform", f"rotate(45, {x}, {y})")
                text_node.text = label

        # X-axis title
        if self.x_axis_title:
            x_title_size = 52
            x_title_x = x_offset + grid_width / 2
            x_title_y = y_offset + n_rows * (cell_h + gap) + 260
            text_node = self.svg.node(heatmap_group, "text", x=x_title_x, y=x_title_y)
            text_node.set("text-anchor", "middle")
            text_node.set("fill", "#333333")
            text_node.set("style", f"font-size:{x_title_size}px;font-weight:bold;font-family:sans-serif")
            text_node.text = self.x_axis_title

        # Draw cells
        for i in range(n_rows):
            for j in range(n_cols):
                value = self.matrix_data[i][j]
                x = x_offset + j * (cell_w + gap)
                y = y_offset + i * (cell_h + gap)

                norm = self._normalize_value(value)
                if norm < 0:
                    color = "#ffffff"
                    stroke_color = "#e0e0e0"
                else:
                    color = self._interpolate_color(norm)
                    stroke_color = "#ffffff"

                rect = self.svg.node(heatmap_group, "rect", x=x, y=y, width=cell_w, height=cell_h, rx=2, ry=2)
                rect.set("fill", color)
                rect.set("stroke", stroke_color)
                rect.set("stroke-width", "1")

        # Colorbar
        colorbar_width = 55
        colorbar_height = grid_height * 0.85
        colorbar_x = x_offset + grid_width + 80
        colorbar_y = y_offset + (grid_height - colorbar_height) / 2

        n_segments = 60
        segment_height = colorbar_height / n_segments
        for seg_i in range(n_segments):
            seg_norm = 1 - seg_i / (n_segments - 1)
            seg_color = self._interpolate_color(seg_norm)
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

        # Colorbar tick labels (log scale: powers of 10)
        cb_label_size = 36
        max_power = int(math.log10(self.vmax)) if self.vmax > 0 else 0
        tick_values = [0] + [10**p for p in range(max_power + 1)]

        for tv in tick_values:
            if tv == 0:
                norm_pos = 0
            else:
                norm_pos = math.log10(tv + 1) / math.log10(self.vmax + 1)
            tick_y = colorbar_y + colorbar_height * (1 - norm_pos)

            # Tick mark
            self.svg.node(
                heatmap_group,
                "line",
                x1=colorbar_x + colorbar_width,
                y1=tick_y,
                x2=colorbar_x + colorbar_width + 10,
                y2=tick_y,
                stroke="#333333",
            )

            text_node = self.svg.node(
                heatmap_group, "text", x=colorbar_x + colorbar_width + 18, y=tick_y + cb_label_size * 0.35
            )
            text_node.set("fill", "#333333")
            text_node.set("style", f"font-size:{cb_label_size}px;font-family:sans-serif")
            text_node.text = str(int(tv))

        # Colorbar title
        if self.colorbar_title:
            cb_title_size = 42
            cb_title_x = colorbar_x + colorbar_width / 2
            cb_title_y = colorbar_y - 40
            text_node = self.svg.node(heatmap_group, "text", x=cb_title_x, y=cb_title_y)
            text_node.set("text-anchor", "middle")
            text_node.set("fill", "#333333")
            text_node.set("style", f"font-size:{cb_title_size}px;font-weight:bold;font-family:sans-serif")
            text_node.text = self.colorbar_title

    def _compute(self):
        """Compute the box for rendering."""
        n_rows = len(self.matrix_data) if self.matrix_data else 1
        n_cols = len(self.matrix_data[0]) if self.matrix_data and self.matrix_data[0] else 1
        self._box.xmin = 0
        self._box.xmax = n_cols
        self._box.ymin = 0
        self._box.ymax = n_rows


# Data: Simulated rainflow counting results for a wind turbine blade root
np.random.seed(42)

n_amp_bins = 20
n_mean_bins = 20

amp_edges = np.linspace(0, 200, n_amp_bins + 1)
mean_edges = np.linspace(-50, 250, n_mean_bins + 1)

amp_centers = (amp_edges[:-1] + amp_edges[1:]) / 2
mean_centers = (mean_edges[:-1] + mean_edges[1:]) / 2

# Generate realistic cycle counts
# - Low amplitude cycles are very frequent (operational vibration)
# - High amplitude cycles are rare (extreme gusts)
# - Mean stress centered around ~100 MPa (tensile preload from centrifugal force)
# - Many zero-count bins at periphery (physically impossible combinations)
counts = np.zeros((n_amp_bins, n_mean_bins))

for i in range(n_amp_bins):
    for j in range(n_mean_bins):
        amp = amp_centers[i]
        mean_val = mean_centers[j]

        # Primary operational loading
        primary = np.exp(-amp / 28) * np.exp(-((mean_val - 100) ** 2) / (2 * 55**2))

        # Low-amplitude vibration cluster
        vibration = 0.5 * np.exp(-amp / 10) * np.exp(-((mean_val - 55) ** 2) / (2 * 20**2))

        base_count = 9000 * (primary + vibration)
        noise = 1 + 0.2 * np.random.randn()
        count = max(0, base_count * noise)

        # Sharp cutoff for physically unrealistic combinations
        if amp + abs(mean_val - 100) > 220:
            count = 0
        counts[i][j] = int(round(count)) if count >= 2 else 0

# Flip rows so high amplitude is at top of the matrix
matrix = counts[::-1].tolist()
amp_labels = [f"{v:.0f}" for v in amp_centers[::-1]]
mean_labels = [f"{v:.0f}" for v in mean_centers]

vmax = int(np.max(counts))

# Sequential "hot" colormap: light yellow → orange → dark red
sequential_colormap = [
    "#fff7ec",
    "#fee8c8",
    "#fdd49e",
    "#fdbb84",
    "#fc8d59",
    "#ef6548",
    "#d7301f",
    "#b30000",
    "#7f0000",
]

# Style
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998",),
    title_font_size=64,
    legend_font_size=40,
    label_font_size=36,
    value_font_size=32,
    font_family="sans-serif",
)

# Create chart
chart = RainflowHeatmap(
    width=4800,
    height=2700,
    style=custom_style,
    title="heatmap-rainflow \u00b7 pygal \u00b7 pyplots.ai",
    matrix_data=matrix,
    row_labels=amp_labels,
    col_labels=mean_labels,
    colormap=sequential_colormap,
    vmax=vmax,
    log_scale=True,
    show_legend=False,
    margin=100,
    margin_top=200,
    margin_bottom=80,
    show_x_labels=False,
    show_y_labels=False,
    x_axis_title="Mean Stress (MPa)",
    y_axis_title="Stress Amplitude (MPa)",
    colorbar_title="Cycle Count",
)

# Add dummy series to trigger _plot
chart.add("", [0])

# Save
chart.render_to_file("plot.svg")
chart.render_to_png("plot.png")

# Interactive HTML
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>heatmap-rainflow - pygal</title>
    <style>
        body {{ margin: 0; display: flex; justify-content: center; align-items: center;
               min-height: 100vh; background: #f5f5f5; }}
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
