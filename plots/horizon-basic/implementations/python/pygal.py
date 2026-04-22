""" pyplots.ai
horizon-basic: Horizon Chart
Library: pygal 3.1.0 | Python 3.13.11
Quality: 90/100 | Created: 2025-12-24
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


class HorizonChart(Graph):
    """Custom Horizon Chart for pygal - folds values into color-coded bands."""

    def __init__(self, *args, **kwargs):
        self.series_data = kwargs.pop("series_data", {})
        self.time_labels = kwargs.pop("time_labels", [])
        self.n_bands = kwargs.pop("n_bands", 3)
        self.pos_colors = kwargs.pop("pos_colors", ["#c6dbef", "#6baed6", "#2171b5"])
        self.neg_colors = kwargs.pop("neg_colors", ["#fcbba1", "#fb6a4a", "#cb181d"])
        super().__init__(*args, **kwargs)

    def _plot(self):
        """Draw the horizon chart."""
        if not self.series_data:
            return

        series_names = list(self.series_data.keys())
        n_series = len(series_names)
        n_points = len(self.time_labels)

        # Get plot dimensions
        plot_width = self.view.width
        plot_height = self.view.height

        # Layout margins
        margin_left = 400  # Space for series labels
        margin_right = 100
        margin_top = 80
        margin_bottom = 180  # Space for x-axis labels

        available_width = plot_width - margin_left - margin_right
        available_height = plot_height - margin_top - margin_bottom

        # Calculate dimensions
        row_height = available_height / n_series
        band_gap = row_height * 0.08  # Small gap between rows
        actual_row_height = row_height - band_gap
        cell_width = available_width / n_points

        x_offset = self.view.x(0) + margin_left
        y_offset = self.view.y(n_series) + margin_top

        # Create group for the chart
        plot_node = self.nodes["plot"]
        horizon_group = self.svg.node(plot_node, class_="horizon-chart")

        # Find global min/max for consistent scaling
        all_values = []
        for values in self.series_data.values():
            all_values.extend(values)
        global_max = max(abs(v) for v in all_values)

        # Band threshold
        band_size = global_max / self.n_bands

        # Draw each series
        for i, series_name in enumerate(series_names):
            values = self.series_data[series_name]
            row_y = y_offset + i * row_height

            # Draw series label
            label_font_size = min(42, int(actual_row_height * 0.5))
            text_node = self.svg.node(
                horizon_group, "text", x=x_offset - 25, y=row_y + actual_row_height / 2 + label_font_size * 0.35
            )
            text_node.set("text-anchor", "end")
            text_node.set("fill", "#333333")
            text_node.set("style", f"font-size:{label_font_size}px;font-weight:bold;font-family:sans-serif")
            text_node.text = series_name

            # Draw background for this row with clearer separation
            bg_rect = self.svg.node(
                horizon_group, "rect", x=x_offset, y=row_y, width=available_width, height=actual_row_height
            )
            bg_rect.set("fill", "#f8f9fa")
            bg_rect.set("stroke", "#d0d0d0")
            bg_rect.set("stroke-width", "2")

            # Draw horizon bands for each time point
            for j, value in enumerate(values):
                cell_x = x_offset + j * cell_width

                # Determine positive or negative
                is_positive = value >= 0
                abs_val = abs(value)

                # Calculate which bands are filled
                remaining = abs_val
                for band_idx in range(self.n_bands):
                    band_value = min(remaining, band_size)
                    if band_value <= 0:
                        break

                    # Calculate height proportion for this band
                    height_ratio = band_value / band_size
                    band_height = (actual_row_height / self.n_bands) * height_ratio

                    # Position from bottom of row
                    band_y = row_y + actual_row_height - (actual_row_height / self.n_bands) * (band_idx + height_ratio)

                    # Select color
                    if is_positive:
                        color = self.pos_colors[min(band_idx, len(self.pos_colors) - 1)]
                    else:
                        color = self.neg_colors[min(band_idx, len(self.neg_colors) - 1)]

                    # Draw band rectangle
                    rect = self.svg.node(
                        horizon_group,
                        "rect",
                        x=cell_x,
                        y=band_y,
                        width=cell_width + 0.5,  # Slight overlap to avoid gaps
                        height=band_height,
                    )
                    rect.set("fill", color)
                    rect.set("stroke", "none")

                    remaining -= band_size

        # Draw subtle vertical grid lines at regular intervals for time readability
        grid_interval = max(1, n_points // 12)
        for j in range(0, n_points + 1, grid_interval):
            grid_x = x_offset + j * cell_width
            line = self.svg.node(
                horizon_group, "line", x1=grid_x, y1=y_offset, x2=grid_x, y2=y_offset + n_series * row_height
            )
            line.set("stroke", "#cccccc")
            line.set("stroke-width", "1")
            line.set("stroke-dasharray", "4,4")

        # Draw x-axis labels
        x_label_font_size = 36
        # Show labels at regular intervals to avoid crowding
        label_interval = max(1, n_points // 12)
        for j in range(0, n_points, label_interval):
            label_x = x_offset + j * cell_width + cell_width / 2
            label_y = y_offset + n_series * row_height + 45

            text_node = self.svg.node(horizon_group, "text", x=label_x, y=label_y)
            text_node.set("text-anchor", "middle")
            text_node.set("fill", "#333333")
            text_node.set("style", f"font-size:{x_label_font_size}px;font-family:sans-serif")
            text_node.text = self.time_labels[j]

        # Draw x-axis title
        x_title_font_size = 48
        x_title_x = x_offset + available_width / 2
        x_title_y = y_offset + n_series * row_height + 120
        text_node = self.svg.node(horizon_group, "text", x=x_title_x, y=x_title_y)
        text_node.set("text-anchor", "middle")
        text_node.set("fill", "#333333")
        text_node.set("style", f"font-size:{x_title_font_size}px;font-weight:bold;font-family:sans-serif")
        text_node.text = "Time"

        # Draw legend at top right
        legend_x = x_offset + available_width - 400
        legend_y = y_offset - 50
        legend_font_size = 32

        # Positive legend
        for band_idx in range(self.n_bands):
            rect_x = legend_x + band_idx * 50
            rect = self.svg.node(horizon_group, "rect", x=rect_x, y=legend_y, width=45, height=25)
            rect.set("fill", self.pos_colors[band_idx])
            rect.set("stroke", "#999")
            rect.set("stroke-width", "1")

        text_node = self.svg.node(
            horizon_group, "text", x=legend_x + self.n_bands * 50 + 10, y=legend_y + legend_font_size * 0.7
        )
        text_node.set("fill", "#333333")
        text_node.set("style", f"font-size:{legend_font_size}px;font-family:sans-serif")
        text_node.text = "Positive"

        # Negative legend (below positive)
        legend_y2 = legend_y + 40
        for band_idx in range(self.n_bands):
            rect_x = legend_x + band_idx * 50
            rect = self.svg.node(horizon_group, "rect", x=rect_x, y=legend_y2, width=45, height=25)
            rect.set("fill", self.neg_colors[band_idx])
            rect.set("stroke", "#999")
            rect.set("stroke-width", "1")

        text_node = self.svg.node(
            horizon_group, "text", x=legend_x + self.n_bands * 50 + 10, y=legend_y2 + legend_font_size * 0.7
        )
        text_node.set("fill", "#333333")
        text_node.set("style", f"font-size:{legend_font_size}px;font-family:sans-serif")
        text_node.text = "Negative"

    def _compute(self):
        """Compute the box for rendering."""
        n_series = len(self.series_data) if self.series_data else 1
        n_points = len(self.time_labels) if self.time_labels else 1
        self._box.xmin = 0
        self._box.xmax = n_points
        self._box.ymin = 0
        self._box.ymax = n_series


# Data: Server performance metrics over 24 hours (realistic monitoring scenario)
np.random.seed(42)

# Time labels - 24 hours at 15-minute intervals
hours = []
for h in range(24):
    for m in [0, 15, 30, 45]:
        hours.append(f"{h:02d}:{m:02d}")

n_points = len(hours)

# Generate realistic server metrics (deviation from baseline)
# Positive = above normal, Negative = below normal
metrics = {"CPU Usage": [], "Memory": [], "Network I/O": [], "Disk I/O": [], "Response Time": [], "Error Rate": []}

# Base patterns for each metric
t = np.linspace(0, 24, n_points)

# CPU: Higher during business hours, spikes during peak times
cpu_base = 15 * np.sin((t - 6) * np.pi / 12) * (t > 6) * (t < 22)
cpu_noise = np.random.randn(n_points) * 8
cpu_spikes = np.zeros(n_points)
cpu_spikes[36:40] = 25  # Morning spike
cpu_spikes[48:52] = 30  # Lunch spike
metrics["CPU Usage"] = (cpu_base + cpu_noise + cpu_spikes).tolist()

# Memory: Gradual increase during day, drops during maintenance window
mem_base = 10 * np.sin((t - 4) * np.pi / 12) * (t > 4) * (t < 20)
mem_leak = np.cumsum(np.random.exponential(0.3, n_points)) * 0.5
mem_leak = mem_leak - mem_leak.mean()  # Center around zero
metrics["Memory"] = (mem_base + mem_leak + np.random.randn(n_points) * 5).tolist()

# Network: Bursty traffic patterns
net_base = 20 * np.sin((t - 8) * np.pi / 8) * (t > 8) * (t < 20)
net_bursts = np.random.poisson(3, n_points) * np.random.choice([-1, 1], n_points) * 5
metrics["Network I/O"] = (net_base + net_bursts).tolist()

# Disk I/O: Backup windows cause negative values, batch jobs cause positive
disk_base = np.zeros(n_points)
disk_base[4:12] = -20  # Backup window (negative = below normal throughput)
disk_base[52:60] = 25  # Batch processing
metrics["Disk I/O"] = (disk_base + np.random.randn(n_points) * 8).tolist()

# Response Time: Generally follows CPU but with some independent variation
response_base = np.array(metrics["CPU Usage"]) * 0.6 + np.random.randn(n_points) * 10
metrics["Response Time"] = response_base.tolist()

# Error Rate: Mostly low, occasional spikes (negative means below-average errors = good)
error_base = np.random.exponential(5, n_points) - 5
error_spikes = np.zeros(n_points)
error_spikes[38:42] = 25  # Error spike during high load
error_spikes[72:76] = 15  # Minor incident
metrics["Error Rate"] = (error_base + error_spikes).tolist()

# Custom style for 4800x2700 canvas
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998",),
    title_font_size=72,
    legend_font_size=48,
    label_font_size=42,
    value_font_size=36,
    font_family="sans-serif",
)

# Blue-orange diverging color scheme (colorblind-safe)
# Blues for positive values (intensity increases with magnitude)
pos_colors = ["#c6dbef", "#6baed6", "#2171b5"]
# Oranges/reds for negative values
neg_colors = ["#fdbe85", "#fd8d3c", "#d94701"]

# Create horizon chart
chart = HorizonChart(
    width=4800,
    height=2700,
    style=custom_style,
    title="horizon-basic · pygal · pyplots.ai",
    series_data=metrics,
    time_labels=hours,
    n_bands=3,
    pos_colors=pos_colors,
    neg_colors=neg_colors,
    show_legend=False,
    margin=120,
    margin_top=200,
    margin_bottom=100,
    show_x_labels=False,
    show_y_labels=False,
)

# Add a dummy series to trigger _plot
chart.add("", [0])

# Save outputs
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")
