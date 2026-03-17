"""pyplots.ai
heatmap-chromagram: Music Chromagram (Pitch Class Distribution over Time)
Library: pygal | Python 3.13
Quality: pending | Created: 2026-03-17
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


class ChromagramHeatmap(Graph):
    """Custom chromagram heatmap for pygal - displays pitch class energy over time."""

    def __init__(self, *args, **kwargs):
        self.chroma_data = kwargs.pop("chroma_data", [])
        self.pitch_labels = kwargs.pop("pitch_labels", [])
        self.time_labels = kwargs.pop("time_labels", [])
        self.colormap = kwargs.pop("colormap", [])
        self.x_axis_title = kwargs.pop("x_axis_title", "")
        self.y_axis_title = kwargs.pop("y_axis_title", "")
        self.vmin = kwargs.pop("vmin", 0.0)
        self.vmax = kwargs.pop("vmax", 1.0)
        super().__init__(*args, **kwargs)

    def _interpolate_color(self, value):
        """Interpolate color from sequential colormap based on value."""
        normalized = (value - self.vmin) / (self.vmax - self.vmin)
        normalized = max(0, min(1, normalized))

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

    def _get_text_color(self, bg_color):
        """Get contrasting text color based on background brightness."""
        r, g, b = int(bg_color[1:3], 16), int(bg_color[3:5], 16), int(bg_color[5:7], 16)
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        return "#ffffff" if brightness < 140 else "#333333"

    def _plot(self):
        """Draw the chromagram heatmap."""
        if not self.chroma_data:
            return

        n_rows = len(self.chroma_data)
        n_cols = len(self.chroma_data[0])

        plot_width = self.view.width
        plot_height = self.view.height

        # Margins for labels, axis titles, and colorbar
        label_margin_left = 340
        label_margin_bottom = 200
        label_margin_top = 40
        label_margin_right = 340

        available_width = plot_width - label_margin_left - label_margin_right
        available_height = plot_height - label_margin_bottom - label_margin_top

        # Calculate cell dimensions - rectangular cells for time series
        cell_width = available_width / n_cols
        cell_height = available_height / n_rows

        grid_width = n_cols * cell_width
        grid_height = n_rows * cell_height

        x_offset = self.view.x(0) + label_margin_left
        y_offset = self.view.y(n_rows) + label_margin_top

        plot_node = self.nodes["plot"]
        heatmap_group = self.svg.node(plot_node, class_="chromagram-heatmap")

        # Draw y-axis title (rotated)
        if self.y_axis_title:
            y_title_size = 48
            y_title_x = x_offset - 300
            y_title_y = y_offset + grid_height / 2
            text_node = self.svg.node(heatmap_group, "text", x=y_title_x, y=y_title_y)
            text_node.set("text-anchor", "middle")
            text_node.set("fill", "#333333")
            text_node.set("style", f"font-size:{y_title_size}px;font-weight:bold;font-family:sans-serif")
            text_node.set("transform", f"rotate(-90, {y_title_x}, {y_title_y})")
            text_node.text = self.y_axis_title

        # Draw pitch class labels on the left (y-axis)
        row_font_size = min(44, int(cell_height * 0.6))
        for i, label in enumerate(self.pitch_labels):
            y = y_offset + i * cell_height + cell_height / 2
            text_node = self.svg.node(heatmap_group, "text", x=x_offset - 20, y=y + row_font_size * 0.35)
            text_node.set("text-anchor", "end")
            text_node.set("fill", "#333333")
            text_node.set("style", f"font-size:{row_font_size}px;font-weight:600;font-family:sans-serif")
            text_node.text = label

        # Draw time labels on the x-axis (every 10th frame)
        col_font_size = 36
        step = max(1, n_cols // 10)
        for j in range(0, n_cols, step):
            x = x_offset + j * cell_width + cell_width / 2
            y = y_offset + grid_height + col_font_size + 15
            text_node = self.svg.node(heatmap_group, "text", x=x, y=y)
            text_node.set("text-anchor", "middle")
            text_node.set("fill", "#333333")
            text_node.set("style", f"font-size:{col_font_size}px;font-family:sans-serif")
            text_node.text = self.time_labels[j]

        # Draw x-axis title
        if self.x_axis_title:
            x_title_size = 48
            x_title_x = x_offset + grid_width / 2
            x_title_y = y_offset + grid_height + 140
            text_node = self.svg.node(heatmap_group, "text", x=x_title_x, y=x_title_y)
            text_node.set("text-anchor", "middle")
            text_node.set("fill", "#333333")
            text_node.set("style", f"font-size:{x_title_size}px;font-weight:bold;font-family:sans-serif")
            text_node.text = self.x_axis_title

        # Draw heatmap cells
        for i in range(n_rows):
            for j in range(n_cols):
                value = self.chroma_data[i][j]
                color = self._interpolate_color(value)

                x = x_offset + j * cell_width
                y = y_offset + i * cell_height

                rect = self.svg.node(heatmap_group, "rect", x=x, y=y, width=cell_width + 0.5, height=cell_height + 0.5)
                rect.set("fill", color)
                rect.set("stroke", "none")

                # Add tooltip with pitch, time, and energy
                title = self.svg.node(rect, "title")
                title.text = f"{self.pitch_labels[i]} at {self.time_labels[j]}s: {value:.3f}"

        # Draw colorbar on the right
        colorbar_width = 50
        colorbar_height = grid_height * 0.85
        colorbar_x = x_offset + grid_width + 60
        colorbar_y = y_offset + (grid_height - colorbar_height) / 2

        n_segments = 60
        segment_height = colorbar_height / n_segments
        for seg_i in range(n_segments):
            seg_value = self.vmax - (self.vmax - self.vmin) * seg_i / (n_segments - 1)
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

        # Colorbar labels
        cb_label_size = 36
        for frac, label_text in [
            (0.0, f"{self.vmax:.1f}"),
            (0.5, f"{(self.vmax + self.vmin) / 2:.1f}"),
            (1.0, f"{self.vmin:.1f}"),
        ]:
            label_y = colorbar_y + frac * colorbar_height + cb_label_size * 0.35
            text_node = self.svg.node(heatmap_group, "text", x=colorbar_x + colorbar_width + 15, y=label_y)
            text_node.set("fill", "#333333")
            text_node.set("style", f"font-size:{cb_label_size}px;font-family:sans-serif")
            text_node.text = label_text

        # Colorbar title
        cb_title_size = 40
        cb_title_x = colorbar_x + colorbar_width / 2
        cb_title_y = colorbar_y - 30
        text_node = self.svg.node(heatmap_group, "text", x=cb_title_x, y=cb_title_y)
        text_node.set("text-anchor", "middle")
        text_node.set("fill", "#333333")
        text_node.set("style", f"font-size:{cb_title_size}px;font-weight:bold;font-family:sans-serif")
        text_node.text = "Energy"

    def _compute(self):
        """Compute the box for rendering."""
        n_cols = len(self.chroma_data[0]) if self.chroma_data else 1
        n_rows = len(self.chroma_data) if self.chroma_data else 1
        self._box.xmin = 0
        self._box.xmax = n_cols
        self._box.ymin = 0
        self._box.ymax = n_rows


# Data: Synthetic chromagram simulating a C major -> G major -> Am -> F major progression
np.random.seed(42)

pitch_classes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
n_pitches = len(pitch_classes)
n_frames = 80
frame_duration = 0.1
time_positions = [f"{i * frame_duration:.1f}" for i in range(n_frames)]

# Initialize with low background energy
chroma = np.random.uniform(0.02, 0.12, (n_pitches, n_frames))

# Pitch class indices: C=0, C#=1, D=2, D#=3, E=4, F=5, F#=6, G=7, G#=8, A=9, A#=10, B=11

# C major chord (C, E, G) - frames 0-19
for frame in range(0, 20):
    chroma[0, frame] += np.random.uniform(0.7, 0.95)  # C
    chroma[4, frame] += np.random.uniform(0.5, 0.75)  # E
    chroma[7, frame] += np.random.uniform(0.55, 0.8)  # G

# G major chord (G, B, D) - frames 20-39
for frame in range(20, 40):
    chroma[7, frame] += np.random.uniform(0.7, 0.95)  # G
    chroma[11, frame] += np.random.uniform(0.5, 0.75)  # B
    chroma[2, frame] += np.random.uniform(0.55, 0.8)  # D

# A minor chord (A, C, E) - frames 40-59
for frame in range(40, 60):
    chroma[9, frame] += np.random.uniform(0.7, 0.95)  # A
    chroma[0, frame] += np.random.uniform(0.5, 0.75)  # C
    chroma[4, frame] += np.random.uniform(0.55, 0.8)  # E

# F major chord (F, A, C) - frames 60-79
for frame in range(60, 80):
    chroma[5, frame] += np.random.uniform(0.7, 0.95)  # F
    chroma[9, frame] += np.random.uniform(0.5, 0.75)  # A
    chroma[0, frame] += np.random.uniform(0.55, 0.8)  # C

# Add smooth transitions between chords
for frame in range(n_frames - 1):
    chroma[:, frame + 1] = 0.3 * chroma[:, frame] + 0.7 * chroma[:, frame + 1]

# Clip to [0, 1]
chroma = np.clip(chroma, 0, 1)

# Reverse rows so C is at the bottom and B at the top
chroma_display = chroma[::-1]
pitch_labels_display = pitch_classes[::-1]

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
    label_font_size=40,
    value_font_size=36,
    font_family="sans-serif",
)

# Sequential colormap (inferno-inspired): dark -> bright
sequential_colormap = [
    "#000004",  # Near black (0.0)
    "#1b0c41",  # Deep purple
    "#4a0c6b",  # Purple
    "#781c6d",  # Dark magenta
    "#a52c60",  # Magenta
    "#cf4446",  # Red-orange
    "#ed6925",  # Orange
    "#fb9b06",  # Yellow-orange
    "#f7d13d",  # Yellow
    "#fcffa4",  # Light yellow (1.0)
]

# Plot
chart = ChromagramHeatmap(
    width=4800,
    height=2700,
    style=custom_style,
    title="heatmap-chromagram · pygal · pyplots.ai",
    chroma_data=chroma_display.tolist(),
    pitch_labels=pitch_labels_display,
    time_labels=time_positions,
    colormap=sequential_colormap,
    show_legend=False,
    margin=100,
    margin_top=180,
    margin_bottom=80,
    show_x_labels=False,
    show_y_labels=False,
    x_axis_title="Time (seconds)",
    y_axis_title="Pitch Class",
    vmin=0.0,
    vmax=1.0,
)

# Add dummy series to trigger _plot
chart.add("", [0])

# Save
chart.render_to_file("plot.svg")
chart.render_to_png("plot.png")

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>heatmap-chromagram - pygal</title>
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
