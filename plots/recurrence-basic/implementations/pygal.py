""" pyplots.ai
recurrence-basic: Recurrence Plot for Nonlinear Time Series
Library: pygal 3.1.0 | Python 3.14.3
Quality: 86/100 | Created: 2026-03-14
"""

import sys

import numpy as np
from scipy.integrate import solve_ivp
from scipy.spatial.distance import cdist


sys.path = [p for p in sys.path if "implementations" not in p]

from pygal.graph.graph import Graph  # noqa: E402
from pygal.style import Style  # noqa: E402


class RecurrencePlotChart(Graph):
    """Custom recurrence plot chart extending pygal's Graph base class."""

    def __init__(self, *args, **kwargs):
        self.distance_matrix = kwargs.pop("distance_matrix", [])
        self.threshold = kwargs.pop("threshold", 0.0)
        self.colormap = kwargs.pop("colormap", [])
        self.x_axis_title = kwargs.pop("x_axis_title", "")
        self.y_axis_title = kwargs.pop("y_axis_title", "")
        self.annotations = kwargs.pop("annotations", [])
        super().__init__(*args, **kwargs)

    def _interpolate_color(self, value, min_val, max_val):
        if max_val == min_val:
            return self.colormap[-1]
        normalized = max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))
        pos = normalized * (len(self.colormap) - 1)
        idx1 = int(pos)
        idx2 = min(idx1 + 1, len(self.colormap) - 1)
        frac = pos - idx1
        c1, c2 = self.colormap[idx1], self.colormap[idx2]
        r = int(int(c1[1:3], 16) + (int(c2[1:3], 16) - int(c1[1:3], 16)) * frac)
        g = int(int(c1[3:5], 16) + (int(c2[3:5], 16) - int(c1[3:5], 16)) * frac)
        b = int(int(c1[5:7], 16) + (int(c2[5:7], 16) - int(c1[5:7], 16)) * frac)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _plot(self):
        if len(self.distance_matrix) == 0:
            return

        n = len(self.distance_matrix)
        plot_width = self.view.width
        plot_height = self.view.height

        label_margin_left = 300
        label_margin_bottom = 300
        label_margin_top = 40
        label_margin_right = 280

        available_width = plot_width - label_margin_left - label_margin_right
        available_height = plot_height - label_margin_bottom - label_margin_top

        grid_size = min(available_width, available_height)
        cell_size = grid_size / n

        x_offset = self.view.x(0) + label_margin_left + (available_width - grid_size) / 2
        y_offset = self.view.y(n) + label_margin_top + (available_height - grid_size) / 2

        plot_node = self.nodes["plot"]
        rp_group = self.svg.node(plot_node, class_="recurrence-plot")

        threshold = self.threshold

        # Background fill for non-recurrent region
        self.svg.node(rp_group, "rect", x=x_offset, y=y_offset, width=grid_size, height=grid_size).set(
            "style", "fill:#eef2f7;stroke:none"
        )

        # Draw cells — only recurrent pairs (distance <= threshold)
        for i in range(n):
            for j in range(n):
                dist = self.distance_matrix[i][j]
                if dist <= threshold:
                    x = x_offset + j * cell_size
                    y = y_offset + i * cell_size
                    color = self._interpolate_color(threshold - dist, 0, threshold)
                    rect = self.svg.node(
                        rp_group, "rect", x=x, y=y, width=max(cell_size, 1.2), height=max(cell_size, 1.2)
                    )
                    rect.set("fill", color)
                    rect.set("stroke", "none")

        # Outer border with refined styling
        self.svg.node(rp_group, "rect", x=x_offset, y=y_offset, width=grid_size, height=grid_size).set(
            "style", "fill:none;stroke:#2c3e50;stroke-width:3"
        )

        # Tick marks and labels
        tick_font_size = 34
        tick_interval = 50
        tick_length = 12
        for t in range(0, n + 1, tick_interval):
            if t >= n:
                t = n - 1
            tx = x_offset + t * cell_size
            ty = y_offset + t * cell_size

            # X-axis tick marks (bottom)
            self.svg.node(
                rp_group, "line", x1=tx, y1=y_offset + grid_size, x2=tx, y2=y_offset + grid_size + tick_length
            ).set("style", "stroke:#2c3e50;stroke-width:2")

            # X-axis tick labels
            text_node = self.svg.node(rp_group, "text", x=tx, y=y_offset + grid_size + tick_length + 40)
            text_node.set("text-anchor", "middle")
            text_node.set("fill", "#2c3e50")
            text_node.set("style", f"font-size:{tick_font_size}px;font-family:sans-serif")
            text_node.text = str(t)

            # Y-axis tick marks (left)
            self.svg.node(rp_group, "line", x1=x_offset - tick_length, y1=ty, x2=x_offset, y2=ty).set(
                "style", "stroke:#2c3e50;stroke-width:2"
            )

            # Y-axis tick labels
            text_node = self.svg.node(rp_group, "text", x=x_offset - tick_length - 12, y=ty + tick_font_size * 0.35)
            text_node.set("text-anchor", "end")
            text_node.set("fill", "#2c3e50")
            text_node.set("style", f"font-size:{tick_font_size}px;font-family:sans-serif")
            text_node.text = str(t)

        # Y-axis title (rotated)
        y_title_size = 46
        y_title_x = x_offset - 230
        y_title_y = y_offset + grid_size / 2
        text_node = self.svg.node(rp_group, "text", x=y_title_x, y=y_title_y)
        text_node.set("text-anchor", "middle")
        text_node.set("fill", "#1a252f")
        text_node.set("style", f"font-size:{y_title_size}px;font-weight:600;font-family:sans-serif")
        text_node.set("transform", f"rotate(-90, {y_title_x}, {y_title_y})")
        text_node.text = self.y_axis_title

        # X-axis title (bottom)
        x_title_size = 46
        x_title_x = x_offset + grid_size / 2
        x_title_y = y_offset + grid_size + 120
        text_node = self.svg.node(rp_group, "text", x=x_title_x, y=x_title_y)
        text_node.set("text-anchor", "middle")
        text_node.set("fill", "#1a252f")
        text_node.set("style", f"font-size:{x_title_size}px;font-weight:600;font-family:sans-serif")
        text_node.text = self.x_axis_title

        # Colorbar
        cb_width = 44
        cb_height = grid_size
        cb_x = x_offset + grid_size + 50
        cb_y = y_offset
        n_segments = 80

        for seg_i in range(n_segments):
            seg_val = threshold * (n_segments - 1 - seg_i) / (n_segments - 1)
            seg_color = self._interpolate_color(seg_val, 0, threshold)
            seg_y = cb_y + seg_i * (cb_height / n_segments)
            self.svg.node(
                rp_group, "rect", x=cb_x, y=seg_y, width=cb_width, height=cb_height / n_segments + 1, fill=seg_color
            )

        # Colorbar border
        self.svg.node(rp_group, "rect", x=cb_x, y=cb_y, width=cb_width, height=cb_height).set(
            "style", "fill:none;stroke:#2c3e50;stroke-width:1.5"
        )

        # Colorbar tick marks and labels
        cb_label_size = 30
        cb_ticks = [0.0, threshold * 0.25, threshold * 0.5, threshold * 0.75, threshold]
        for tick_val in cb_ticks:
            tick_y = cb_y + (1.0 - tick_val / threshold) * cb_height
            # Tick mark
            self.svg.node(rp_group, "line", x1=cb_x + cb_width, y1=tick_y, x2=cb_x + cb_width + 8, y2=tick_y).set(
                "style", "stroke:#2c3e50;stroke-width:1.5"
            )
            # Label
            text_node = self.svg.node(rp_group, "text", x=cb_x + cb_width + 14, y=tick_y + cb_label_size * 0.35)
            text_node.set("fill", "#2c3e50")
            text_node.set("style", f"font-size:{cb_label_size}px;font-family:sans-serif")
            text_node.text = f"{tick_val:.1f}"

        # Colorbar title (rotated, right side)
        cb_title_size = 34
        cb_title_x = cb_x + cb_width + 80
        cb_title_y = cb_y + cb_height / 2
        text_node = self.svg.node(rp_group, "text", x=cb_title_x, y=cb_title_y)
        text_node.set("text-anchor", "middle")
        text_node.set("fill", "#1a252f")
        text_node.set("style", f"font-size:{cb_title_size}px;font-weight:600;font-family:sans-serif")
        text_node.set("transform", f"rotate(90, {cb_title_x}, {cb_title_y})")
        text_node.text = "Euclidean Distance"

        # Annotations for key recurrence features
        annotation_font = 32
        annotation_color = "#c0392b"
        for ann in self.annotations:
            ax = x_offset + ann["x"] * cell_size
            ay = y_offset + ann["y"] * cell_size
            # Arrow line from label to point
            lx = ax + ann.get("dx", 80)
            ly = ay + ann.get("dy", -80)
            self.svg.node(rp_group, "line", x1=lx, y1=ly, x2=ax, y2=ay).set(
                "style", f"stroke:{annotation_color};stroke-width:2.5;stroke-dasharray:8,4"
            )
            # Small dot at arrow endpoint
            self.svg.node(rp_group, "circle", cx=ax, cy=ay, r=5, fill=annotation_color)
            # Label text
            text_node = self.svg.node(rp_group, "text", x=lx + ann.get("tdx", 6), y=ly + ann.get("tdy", -10))
            text_node.set("fill", annotation_color)
            text_node.set(
                "style", f"font-size:{annotation_font}px;font-style:italic;font-weight:500;font-family:sans-serif"
            )
            text_node.text = ann["label"]

    def _compute(self):
        n = len(self.distance_matrix) if len(self.distance_matrix) > 0 else 1
        self._box.xmin = 0
        self._box.xmax = n
        self._box.ymin = 0
        self._box.ymax = n


# --- Data: Lorenz attractor x-component ---
np.random.seed(42)

sol = solve_ivp(
    lambda t, s: [10.0 * (s[1] - s[0]), s[0] * (28.0 - s[2]) - s[1], s[0] * s[1] - 8.0 / 3.0 * s[2]],
    [0, 40],
    [1.0, 1.0, 1.0],
    t_eval=np.linspace(0, 40, 4000),
    method="RK45",
)

x_series = sol.y[0, 1000:]
step = len(x_series) // 300
x_series = x_series[::step][:300]

# Time-delay embedding (dimension=3, delay=5)
embedding_dim = 3
delay = 5
n_embedded = len(x_series) - (embedding_dim - 1) * delay
embedded = np.array([[x_series[i + d * delay] for d in range(embedding_dim)] for i in range(n_embedded)])

dist_matrix = cdist(embedded, embedded, metric="euclidean")

# Threshold: ~15% recurrence rate
sorted_dists = np.sort(dist_matrix.ravel())
epsilon = sorted_dists[int(0.15 * len(sorted_dists))]

# Annotations pointing to key recurrence features
annotations = [
    {"x": 145, "y": 145, "dx": 160, "dy": -130, "tdx": 8, "tdy": -10, "label": "Main diagonal"},
    {"x": 50, "y": 25, "dx": 180, "dy": -100, "tdx": 8, "tdy": -10, "label": "Diagonal lines (determinism)"},
    {"x": 220, "y": 200, "dx": 140, "dy": 110, "tdx": 8, "tdy": -10, "label": "Block cluster (regime change)"},
]

# Style
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#2c3e50",
    foreground_strong="#1a252f",
    foreground_subtle="#95a5a6",
    colors=("#306998",),
    title_font_size=58,
    legend_font_size=36,
    label_font_size=36,
    value_font_size=30,
    font_family="sans-serif",
)

blue_colormap = ["#f7fbff", "#deebf7", "#c6dbef", "#9ecae1", "#6baed6", "#4292c6", "#2171b5", "#08519c", "#08306b"]

chart = RecurrencePlotChart(
    width=3600,
    height=3600,
    style=custom_style,
    title="recurrence-basic \u00b7 pygal \u00b7 pyplots.ai",
    distance_matrix=dist_matrix.tolist(),
    threshold=float(epsilon),
    colormap=blue_colormap,
    x_axis_title="Time Index (steps)",
    y_axis_title="Time Index (steps)",
    annotations=annotations,
    show_legend=False,
    margin=100,
    margin_top=180,
    margin_bottom=80,
    show_x_labels=False,
    show_y_labels=False,
)

chart.add("", [0])

# Save
chart.render_to_file("plot.svg")
chart.render_to_png("plot.png")

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>recurrence-basic - pygal</title>
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
