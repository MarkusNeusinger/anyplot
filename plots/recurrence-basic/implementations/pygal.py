""" pyplots.ai
recurrence-basic: Recurrence Plot for Nonlinear Time Series
Library: pygal 3.1.0 | Python 3.14.3
Quality: 78/100 | Created: 2026-03-14
"""

import sys

import numpy as np
from scipy.integrate import solve_ivp
from scipy.spatial.distance import cdist


# Temporarily remove current directory from path to avoid name collision
_cwd = sys.path[0] if sys.path[0] else "."
if _cwd in sys.path:
    sys.path.remove(_cwd)

from pygal.graph.graph import Graph  # noqa: E402
from pygal.style import Style  # noqa: E402


sys.path.insert(0, _cwd)


class RecurrencePlotChart(Graph):
    """Custom recurrence plot chart for pygal."""

    def __init__(self, *args, **kwargs):
        self.distance_matrix = kwargs.pop("distance_matrix", [])
        self.threshold = kwargs.pop("threshold", 0.0)
        self.time_labels = kwargs.pop("time_labels", [])
        self.colormap = kwargs.pop("colormap", [])
        self.x_axis_title = kwargs.pop("x_axis_title", "Time Index")
        self.y_axis_title = kwargs.pop("y_axis_title", "Time Index")
        super().__init__(*args, **kwargs)

    def _interpolate_color(self, value, min_val, max_val):
        if max_val == min_val:
            return self.colormap[-1]
        normalized = (value - min_val) / (max_val - min_val)
        normalized = max(0.0, min(1.0, normalized))
        pos = normalized * (len(self.colormap) - 1)
        idx1 = int(pos)
        idx2 = min(idx1 + 1, len(self.colormap) - 1)
        frac = pos - idx1
        c1, c2 = self.colormap[idx1], self.colormap[idx2]
        r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
        r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
        r = int(r1 + (r2 - r1) * frac)
        g = int(g1 + (g2 - g1) * frac)
        b = int(b1 + (b2 - b1) * frac)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _plot(self):
        if len(self.distance_matrix) == 0:
            return

        n = len(self.distance_matrix)
        plot_width = self.view.width
        plot_height = self.view.height

        label_margin_left = 380
        label_margin_bottom = 380
        label_margin_top = 60
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

        # Draw cells — only recurrent pairs (distance < threshold)
        for i in range(n):
            for j in range(n):
                dist = self.distance_matrix[i][j]
                if dist <= threshold:
                    x = x_offset + j * cell_size
                    y = y_offset + i * cell_size
                    # Color by closeness: 0 distance = darkest, threshold = lightest recurrent
                    color = self._interpolate_color(threshold - dist, 0, threshold)
                    rect = self.svg.node(
                        rp_group, "rect", x=x, y=y, width=max(cell_size, 1.2), height=max(cell_size, 1.2)
                    )
                    rect.set("fill", color)
                    rect.set("stroke", "none")

        # Grid border
        self.svg.node(
            rp_group, "rect", x=x_offset, y=y_offset, width=grid_size, height=grid_size, fill="none", stroke="#999999"
        )
        self.svg.node(rp_group, "rect", x=x_offset, y=y_offset, width=grid_size, height=grid_size).set(
            "style", "fill:none;stroke:#666666;stroke-width:2"
        )

        # Axis tick labels (every 50 time steps)
        tick_font_size = 36
        tick_interval = 50
        for t in range(0, n + 1, tick_interval):
            if t >= n:
                t = n - 1
            # X-axis ticks (bottom)
            tx = x_offset + t * cell_size
            text_node = self.svg.node(rp_group, "text", x=tx, y=y_offset + grid_size + 50)
            text_node.set("text-anchor", "middle")
            text_node.set("fill", "#333333")
            text_node.set("style", f"font-size:{tick_font_size}px;font-family:sans-serif")
            text_node.text = str(t)

            # Y-axis ticks (left)
            ty = y_offset + t * cell_size
            text_node = self.svg.node(rp_group, "text", x=x_offset - 20, y=ty + tick_font_size * 0.35)
            text_node.set("text-anchor", "end")
            text_node.set("fill", "#333333")
            text_node.set("style", f"font-size:{tick_font_size}px;font-family:sans-serif")
            text_node.text = str(t)

        # Y-axis title (rotated)
        y_title_size = 48
        y_title_x = x_offset - 280
        y_title_y = y_offset + grid_size / 2
        text_node = self.svg.node(rp_group, "text", x=y_title_x, y=y_title_y)
        text_node.set("text-anchor", "middle")
        text_node.set("fill", "#333333")
        text_node.set("style", f"font-size:{y_title_size}px;font-weight:bold;font-family:sans-serif")
        text_node.set("transform", f"rotate(-90, {y_title_x}, {y_title_y})")
        text_node.text = self.y_axis_title

        # X-axis title (bottom)
        x_title_size = 48
        x_title_x = x_offset + grid_size / 2
        x_title_y = y_offset + grid_size + 140
        text_node = self.svg.node(rp_group, "text", x=x_title_x, y=x_title_y)
        text_node.set("text-anchor", "middle")
        text_node.set("fill", "#333333")
        text_node.set("style", f"font-size:{x_title_size}px;font-weight:bold;font-family:sans-serif")
        text_node.text = self.x_axis_title

        # Colorbar (right of grid)
        cb_width = 50
        cb_height = grid_size * 0.8
        cb_x = x_offset + grid_size + 60
        cb_y = y_offset + (grid_size - cb_height) / 2
        n_segments = 50

        for seg_i in range(n_segments):
            seg_val = threshold * (n_segments - 1 - seg_i) / (n_segments - 1)
            seg_color = self._interpolate_color(seg_val, 0, threshold)
            seg_y = cb_y + seg_i * (cb_height / n_segments)
            self.svg.node(
                rp_group, "rect", x=cb_x, y=seg_y, width=cb_width, height=cb_height / n_segments + 1, fill=seg_color
            )

        self.svg.node(rp_group, "rect", x=cb_x, y=cb_y, width=cb_width, height=cb_height, fill="none", stroke="#333333")

        # Colorbar labels
        cb_label_size = 34
        # Top label (closest / distance 0)
        text_node = self.svg.node(rp_group, "text", x=cb_x + cb_width + 14, y=cb_y + cb_label_size * 0.35)
        text_node.set("fill", "#333333")
        text_node.set("style", f"font-size:{cb_label_size}px;font-family:sans-serif")
        text_node.text = "0.0"

        # Mid label
        text_node = self.svg.node(
            rp_group, "text", x=cb_x + cb_width + 14, y=cb_y + cb_height / 2 + cb_label_size * 0.35
        )
        text_node.set("fill", "#333333")
        text_node.set("style", f"font-size:{cb_label_size}px;font-family:sans-serif")
        text_node.text = f"{threshold / 2:.1f}"

        # Bottom label (threshold)
        text_node = self.svg.node(rp_group, "text", x=cb_x + cb_width + 14, y=cb_y + cb_height + cb_label_size * 0.35)
        text_node.set("fill", "#333333")
        text_node.set("style", f"font-size:{cb_label_size}px;font-family:sans-serif")
        text_node.text = f"{threshold:.1f}"

        # Colorbar title
        cb_title_size = 38
        text_node = self.svg.node(rp_group, "text", x=cb_x + cb_width / 2, y=cb_y - 30)
        text_node.set("text-anchor", "middle")
        text_node.set("fill", "#333333")
        text_node.set("style", f"font-size:{cb_title_size}px;font-weight:bold;font-family:sans-serif")
        text_node.text = "Distance"

    def _compute(self):
        n = len(self.distance_matrix) if len(self.distance_matrix) > 0 else 1
        self._box.xmin = 0
        self._box.xmax = n
        self._box.ymin = 0
        self._box.ymax = n


# Data — Lorenz attractor x-component
np.random.seed(42)

lorenz_sigma = 10.0
lorenz_rho = 28.0
lorenz_beta = 8.0 / 3.0
initial_state = [1.0, 1.0, 1.0]

sol = solve_ivp(
    lambda t, s: [lorenz_sigma * (s[1] - s[0]), s[0] * (lorenz_rho - s[2]) - s[1], s[0] * s[1] - lorenz_beta * s[2]],
    [0, 40],
    initial_state,
    t_eval=np.linspace(0, 40, 4000),
    method="RK45",
)

# Sample 300 points from the x-component (skip transient)
x_series = sol.y[0, 1000:]
step = len(x_series) // 300
x_series = x_series[::step][:300]

# Time-delay embedding (dimension=3, delay=5)
embedding_dim = 3
delay = 5
n_embedded = len(x_series) - (embedding_dim - 1) * delay
embedded = np.array([[x_series[i + d * delay] for d in range(embedding_dim)] for i in range(n_embedded)])

# Compute distance matrix
dist_matrix = cdist(embedded, embedded, metric="euclidean")

# Threshold: ~15% recurrence rate
sorted_dists = np.sort(dist_matrix.ravel())
recurrence_rate = 0.15
epsilon = sorted_dists[int(recurrence_rate * len(sorted_dists))]

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
    label_font_size=38,
    value_font_size=34,
    font_family="sans-serif",
)

# Sequential blue colormap (light for far → dark for close)
blue_colormap = ["#f7fbff", "#deebf7", "#c6dbef", "#9ecae1", "#6baed6", "#4292c6", "#2171b5", "#08519c", "#08306b"]

# Plot
chart = RecurrencePlotChart(
    width=3600,
    height=3600,
    style=custom_style,
    title="recurrence-basic \u00b7 pygal \u00b7 pyplots.ai",
    distance_matrix=dist_matrix.tolist(),
    threshold=float(epsilon),
    colormap=blue_colormap,
    x_axis_title="Time Index",
    y_axis_title="Time Index",
    show_legend=False,
    margin=100,
    margin_top=200,
    margin_bottom=100,
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
