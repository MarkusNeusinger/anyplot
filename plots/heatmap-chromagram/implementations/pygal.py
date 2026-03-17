"""pyplots.ai
heatmap-chromagram: Music Chromagram (Pitch Class Distribution over Time)
Library: pygal 3.1.0 | Python 3.14.3
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
    """Custom chromagram heatmap extending pygal's Graph base class."""

    _series_margin = 0

    def __init__(self, *args, **kwargs):
        self.chroma_data = kwargs.pop("chroma_data", [])
        self.pitch_labels = kwargs.pop("pitch_labels", [])
        self.time_labels = kwargs.pop("time_labels", [])
        self.colormap = kwargs.pop("colormap", [])
        self.x_axis_title = kwargs.pop("x_axis_title", "")
        self.y_axis_title = kwargs.pop("y_axis_title", "")
        self.chord_regions = kwargs.pop("chord_regions", [])
        self.vmin = kwargs.pop("vmin", 0.0)
        self.vmax = kwargs.pop("vmax", 1.0)
        super().__init__(*args, **kwargs)

    def _interpolate_color(self, value):
        """Interpolate color from sequential colormap based on value."""
        normalized = max(0, min(1, (value - self.vmin) / (self.vmax - self.vmin)))
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
        """Draw the chromagram heatmap with chord region annotations."""
        if not self.chroma_data:
            return

        n_rows = len(self.chroma_data)
        n_cols = len(self.chroma_data[0])

        plot_width = self.view.width
        plot_height = self.view.height

        # Tighter margins for better canvas utilization
        margin_left = 280
        margin_bottom = 180
        margin_top = 80
        margin_right = 300

        avail_w = plot_width - margin_left - margin_right
        avail_h = plot_height - margin_bottom - margin_top

        cell_w = avail_w / n_cols
        cell_h = avail_h / n_rows
        grid_w = n_cols * cell_w
        grid_h = n_rows * cell_h

        x0 = self.view.x(0) + margin_left
        y0 = self.view.y(n_rows) + margin_top

        plot_node = self.nodes["plot"]
        hmap = self.svg.node(plot_node, class_="chromagram-heatmap")

        # --- Chord region labels and separators (Data Storytelling) ---
        region_font = 38
        region_colors = ["#e8e8e8", "#f4f4f4", "#e8e8e8", "#f4f4f4"]
        for idx, region in enumerate(self.chord_regions):
            rx = x0 + region["start"] * cell_w
            rw = (region["end"] - region["start"]) * cell_w

            # Subtle alternating background band behind heatmap
            self.svg.node(
                hmap,
                "rect",
                x=rx,
                y=y0,
                width=rw,
                height=grid_h,
                fill=region_colors[idx % len(region_colors)],
                opacity="0.15",
            )

            # Chord label above the heatmap
            label_x = rx + rw / 2
            label_y = y0 - 20
            t = self.svg.node(hmap, "text", x=label_x, y=label_y)
            t.set("text-anchor", "middle")
            t.set("fill", "#555555")
            t.set("style", f"font-size:{region_font}px;font-weight:bold;font-family:sans-serif;font-style:italic")
            t.text = region["label"]

            # Vertical separator line at chord boundary (except first)
            if region["start"] > 0:
                sep_x = rx
                self.svg.node(
                    hmap, "line", x1=sep_x, y1=y0 - 5, x2=sep_x, y2=y0 + grid_h + 5, stroke="#999999", fill="none"
                )
                self.svg.node(hmap, "line", x1=sep_x, y1=y0 - 5, x2=sep_x, y2=y0 + grid_h + 5).set(
                    "style", "stroke:#999999;stroke-width:2;stroke-dasharray:8,6"
                )

        # --- Heatmap cells ---
        for i in range(n_rows):
            row_group = self.svg.node(hmap, "g", class_=f"pitch-row-{i}")
            for j in range(n_cols):
                value = self.chroma_data[i][j]
                color = self._interpolate_color(value)
                x = x0 + j * cell_w
                y = y0 + i * cell_h

                rect = self.svg.node(
                    row_group, "rect", x=x, y=y, width=cell_w + 0.5, height=cell_h + 0.5, fill=color, stroke="none"
                )
                # Native pygal tooltip via <title> element
                title_el = self.svg.node(rect, "title")
                title_el.text = f"{self.pitch_labels[i]} @ {self.time_labels[j]}s — Energy: {value:.3f}"

        # --- Heatmap border ---
        self.svg.node(hmap, "rect", x=x0, y=y0, width=grid_w, height=grid_h, fill="none", stroke="#333333")

        # --- Y-axis: pitch class labels ---
        row_font = min(44, int(cell_h * 0.6))
        for i, label in enumerate(self.pitch_labels):
            y = y0 + i * cell_h + cell_h / 2
            t = self.svg.node(hmap, "text", x=x0 - 18, y=y + row_font * 0.35)
            t.set("text-anchor", "end")
            t.set("fill", "#333333")
            t.set("style", f"font-size:{row_font}px;font-weight:600;font-family:sans-serif")
            t.text = label

        # --- Y-axis title (rotated) ---
        if self.y_axis_title:
            yt_x = x0 - 240
            yt_y = y0 + grid_h / 2
            t = self.svg.node(hmap, "text", x=yt_x, y=yt_y)
            t.set("text-anchor", "middle")
            t.set("fill", "#333333")
            t.set("style", "font-size:48px;font-weight:bold;font-family:sans-serif")
            t.set("transform", f"rotate(-90, {yt_x}, {yt_y})")
            t.text = self.y_axis_title

        # --- X-axis: time labels ---
        col_font = 36
        step = max(1, n_cols // 10)
        for j in range(0, n_cols, step):
            x = x0 + j * cell_w + cell_w / 2
            y = y0 + grid_h + col_font + 15
            t = self.svg.node(hmap, "text", x=x, y=y)
            t.set("text-anchor", "middle")
            t.set("fill", "#333333")
            t.set("style", f"font-size:{col_font}px;font-family:sans-serif")
            t.text = self.time_labels[j]

        # --- X-axis title ---
        if self.x_axis_title:
            xt_x = x0 + grid_w / 2
            xt_y = y0 + grid_h + 130
            t = self.svg.node(hmap, "text", x=xt_x, y=xt_y)
            t.set("text-anchor", "middle")
            t.set("fill", "#333333")
            t.set("style", "font-size:48px;font-weight:bold;font-family:sans-serif")
            t.text = self.x_axis_title

        # --- Colorbar ---
        cb_w = 50
        cb_h = grid_h * 0.85
        cb_x = x0 + grid_w + 50
        cb_y = y0 + (grid_h - cb_h) / 2

        n_seg = 60
        seg_h = cb_h / n_seg
        for s in range(n_seg):
            sv = self.vmax - (self.vmax - self.vmin) * s / (n_seg - 1)
            self.svg.node(
                hmap, "rect", x=cb_x, y=cb_y + s * seg_h, width=cb_w, height=seg_h + 1, fill=self._interpolate_color(sv)
            )

        # Colorbar border
        self.svg.node(hmap, "rect", x=cb_x, y=cb_y, width=cb_w, height=cb_h, fill="none", stroke="#333333")

        # Colorbar tick labels
        cb_font = 36
        for frac, txt in [
            (0.0, f"{self.vmax:.1f}"),
            (0.5, f"{(self.vmax + self.vmin) / 2:.1f}"),
            (1.0, f"{self.vmin:.1f}"),
        ]:
            ty = cb_y + frac * cb_h + cb_font * 0.35
            t = self.svg.node(hmap, "text", x=cb_x + cb_w + 15, y=ty)
            t.set("fill", "#333333")
            t.set("style", f"font-size:{cb_font}px;font-family:sans-serif")
            t.text = txt

        # Colorbar title
        t = self.svg.node(hmap, "text", x=cb_x + cb_w / 2, y=cb_y - 25)
        t.set("text-anchor", "middle")
        t.set("fill", "#333333")
        t.set("style", "font-size:40px;font-weight:bold;font-family:sans-serif")
        t.text = "Energy"

    def _compute(self):
        """Compute bounding box for the graph view."""
        n_cols = len(self.chroma_data[0]) if self.chroma_data else 1
        n_rows = len(self.chroma_data) if self.chroma_data else 1
        self._box.xmin = 0
        self._box.xmax = n_cols
        self._box.ymin = 0
        self._box.ymax = n_rows


# --- Data: C major -> G major -> Am -> F major chord progression ---
np.random.seed(42)

pitch_classes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
n_pitches = len(pitch_classes)
n_frames = 80
frame_duration = 0.1
time_positions = [f"{i * frame_duration:.1f}" for i in range(n_frames)]

chroma = np.random.uniform(0.02, 0.12, (n_pitches, n_frames))

# C major (C, E, G) - frames 0-19
for f in range(0, 20):
    chroma[0, f] += np.random.uniform(0.7, 0.95)
    chroma[4, f] += np.random.uniform(0.5, 0.75)
    chroma[7, f] += np.random.uniform(0.55, 0.8)

# G major (G, B, D) - frames 20-39
for f in range(20, 40):
    chroma[7, f] += np.random.uniform(0.7, 0.95)
    chroma[11, f] += np.random.uniform(0.5, 0.75)
    chroma[2, f] += np.random.uniform(0.55, 0.8)

# A minor (A, C, E) - frames 40-59
for f in range(40, 60):
    chroma[9, f] += np.random.uniform(0.7, 0.95)
    chroma[0, f] += np.random.uniform(0.5, 0.75)
    chroma[4, f] += np.random.uniform(0.55, 0.8)

# F major (F, A, C) - frames 60-79
for f in range(60, 80):
    chroma[5, f] += np.random.uniform(0.7, 0.95)
    chroma[9, f] += np.random.uniform(0.5, 0.75)
    chroma[0, f] += np.random.uniform(0.55, 0.8)

# Smooth transitions
for f in range(n_frames - 1):
    chroma[:, f + 1] = 0.3 * chroma[:, f] + 0.7 * chroma[:, f + 1]

chroma = np.clip(chroma, 0, 1)

# Reverse so C is at bottom, B at top
chroma_display = chroma[::-1]
pitch_labels_display = pitch_classes[::-1]

# Chord region definitions for storytelling annotations
chord_regions = [
    {"start": 0, "end": 20, "label": "C major"},
    {"start": 20, "end": 40, "label": "G major"},
    {"start": 40, "end": 60, "label": "A minor"},
    {"start": 60, "end": 80, "label": "F major"},
]

# pygal Style configuration
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#999999",
    colors=("#306998",),
    title_font_size=64,
    legend_font_size=40,
    label_font_size=40,
    value_font_size=36,
    font_family="sans-serif",
)

# Inferno-inspired sequential colormap
sequential_colormap = [
    "#000004",
    "#1b0c41",
    "#4a0c6b",
    "#781c6d",
    "#a52c60",
    "#cf4446",
    "#ed6925",
    "#fb9b06",
    "#f7d13d",
    "#fcffa4",
]

# Create chart using pygal Graph extension pattern
chart = ChromagramHeatmap(
    width=4800,
    height=2700,
    style=custom_style,
    title="heatmap-chromagram · pygal · pyplots.ai",
    chroma_data=chroma_display.tolist(),
    pitch_labels=pitch_labels_display,
    time_labels=time_positions,
    colormap=sequential_colormap,
    chord_regions=chord_regions,
    show_legend=False,
    margin=80,
    margin_top=160,
    margin_bottom=60,
    show_x_labels=False,
    show_y_labels=False,
    x_axis_title="Time (seconds)",
    y_axis_title="Pitch Class",
    vmin=0.0,
    vmax=1.0,
)

# Add series to trigger pygal rendering pipeline
chart.add("chromagram", [0])

# Render outputs using pygal's native methods
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
