""" pyplots.ai
heatmap-rainflow: Rainflow Counting Matrix for Fatigue Analysis
Library: pygal 3.1.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-02
"""

import math
import sys

import numpy as np


# This file shadows the pygal package; temporarily adjust path for the real package
sys.path, _saved = sys.path[1:], sys.path[0]
from pygal.graph.graph import Graph  # noqa: E402
from pygal.style import Style  # noqa: E402


sys.path.insert(0, _saved)


class RainflowHeatmap(Graph):
    """Rainflow cycle counting matrix rendered as a 2D heatmap via pygal SVG."""

    def __init__(self, *args, **kwargs):
        self.matrix_data = kwargs.pop("matrix_data", [])
        self.row_labels = kwargs.pop("row_labels", [])
        self.col_labels = kwargs.pop("col_labels", [])
        self.colormap = kwargs.pop("colormap", [])
        self.vmax = kwargs.pop("vmax", 1)
        self.x_axis_title = kwargs.pop("x_axis_title", "")
        self.y_axis_title = kwargs.pop("y_axis_title", "")
        self.colorbar_title = kwargs.pop("colorbar_title", "")
        self.subtitle_text = kwargs.pop("subtitle_text", "")
        super().__init__(*args, **kwargs)

    def _plot(self):
        if not self.matrix_data:
            return

        cmap = self.colormap
        log_max = math.log10(self.vmax + 1)

        def color_at(t):
            """Interpolate colormap at normalized position t in [0, 1]."""
            t = max(0.0, min(1.0, t))
            pos = t * (len(cmap) - 1)
            lo = int(pos)
            hi = min(lo + 1, len(cmap) - 1)
            f = pos - lo
            c1, c2 = cmap[lo], cmap[hi]
            rgb = tuple(int(int(c1[k : k + 2], 16) * (1 - f) + int(c2[k : k + 2], 16) * f) for k in (1, 3, 5))
            return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

        def log_norm(value):
            """Normalize count via log10 to [0, 1]. Returns -1 for zero."""
            if value <= 0:
                return -1.0
            return math.log10(value + 1) / log_max

        def svg_text(parent, x, y, label, size, **kw):
            """Add SVG text node using pygal's node system."""
            node = self.svg.node(parent, "text", x=x, y=y)
            node.set("text-anchor", kw.get("anchor", "middle"))
            node.set("fill", kw.get("fill", "#333"))
            weight = "bold" if kw.get("bold") else "normal"
            if kw.get("weight"):
                weight = kw["weight"]
            family = kw.get("family", "sans-serif")
            style_str = f"font-size:{size}px;font-weight:{weight};font-family:{family}"
            if kw.get("letter_spacing"):
                style_str += f";letter-spacing:{kw['letter_spacing']}px"
            node.set("style", style_str)
            if "rotation" in kw:
                node.set("transform", f"rotate({kw['rotation']}, {x}, {y})")
            node.text = label

        nr = len(self.matrix_data)
        nc = len(self.matrix_data[0])
        pw, ph = self.view.width, self.view.height

        # Proportional margins — optimized for canvas utilization
        ml = int(pw * 0.10)
        mr = int(pw * 0.10)
        mt = int(ph * 0.04)
        mb = int(ph * 0.10)

        aw, ah = pw - ml - mr, ph - mt - mb
        cw = aw / nc * 0.97
        ch = ah / nr * 0.97
        gap = min(cw, ch) * 0.015
        gw = nc * (cw + gap) - gap
        gh = nr * (ch + gap) - gap

        x0 = self.view.x(0) + ml + (aw - gw) / 2
        y0 = self.view.y(nr) + mt + (ah - gh) / 2

        g = self.svg.node(self.nodes["plot"], class_="heatmap")

        # Subtitle — typographic hierarchy for data storytelling
        if self.subtitle_text:
            svg_text(
                g, pw / 2 + self.view.x(0), y0 - 25, self.subtitle_text, 34, fill="#777", weight="300", letter_spacing=1
            )

        # Subtle background panel behind heatmap grid
        pad = 14
        panel = self.svg.node(g, "rect", x=x0 - pad, y=y0 - pad, width=gw + 2 * pad, height=gh + 2 * pad, rx=6, ry=6)
        panel.set("fill", "#fafafa")
        panel.set("stroke", "#e0e0e0")
        panel.set("stroke-width", "1")

        # Y-axis title (rotated)
        if self.y_axis_title:
            svg_text(g, x0 - int(pw * 0.082), y0 + gh / 2, self.y_axis_title, 46, bold=True, rotation=-90)

        # Row labels — every other to prevent crowding
        rf = min(30, int(ch * 0.5))
        for i, lbl in enumerate(self.row_labels):
            if i % 2 == 0 or i == nr - 1:
                svg_text(g, x0 - 16, y0 + i * (ch + gap) + ch / 2 + rf * 0.35, lbl, rf, anchor="end", fill="#666")

        # Column labels — horizontal, every 3rd for clean spacing
        cf = min(30, int(cw * 0.45))
        for j, lbl in enumerate(self.col_labels):
            if j % 3 == 0 or j == nc - 1:
                x = x0 + j * (cw + gap) + cw / 2
                y = y0 + gh + gap + cf + 10
                svg_text(g, x, y, lbl, cf, fill="#666")

        # X-axis title
        if self.x_axis_title:
            svg_text(g, x0 + gw / 2, y0 + gh + int(ph * 0.08), self.x_axis_title, 46, bold=True)

        # Find top 3 peak cells for annotation and emphasis
        cell_values = []
        for i in range(nr):
            for j in range(nc):
                if self.matrix_data[i][j] > 0:
                    cell_values.append((self.matrix_data[i][j], i, j))
        cell_values.sort(reverse=True)
        top_peaks = {(i, j) for _, i, j in cell_values[:3]}
        peak_cell = (cell_values[0][1], cell_values[0][2]) if cell_values else None

        # Draw heatmap cells
        for i in range(nr):
            for j in range(nc):
                val = self.matrix_data[i][j]
                cx = x0 + j * (cw + gap)
                cy = y0 + i * (ch + gap)
                norm = log_norm(val)

                fill = "#ffffff" if norm < 0 else color_at(norm)
                stroke = "#e8e8e8" if norm < 0 else "none"
                sw = "0.5"

                # Glow halo on absolute peak cell
                if (i, j) == peak_cell:
                    glow = self.svg.node(g, "rect", x=cx - 4, y=cy - 4, width=cw + 8, height=ch + 8, rx=5, ry=5)
                    glow.set("fill", "none")
                    glow.set("stroke", "#fde725")
                    glow.set("stroke-width", "5")
                    glow.set("opacity", "0.5")
                    stroke = "#1a1a1a"
                    sw = "2.5"

                rect = self.svg.node(g, "rect", x=cx, y=cy, width=cw, height=ch, rx=3, ry=3)
                rect.set("fill", fill)
                rect.set("stroke", stroke)
                rect.set("stroke-width", sw)

                # Annotate top 3 peaks with background pill for readability
                if (i, j) in top_peaks:
                    txt = f"{int(val):,}"
                    sz = min(int(ch * 0.36), int(cw * 0.30), 26)
                    ink = "#ffffff" if norm > 0.45 else "#222222"

                    # Background pill for contrast
                    pill_w = len(txt) * sz * 0.6 + 14
                    pill_h = sz + 10
                    pill = self.svg.node(
                        g,
                        "rect",
                        x=cx + cw / 2 - pill_w / 2,
                        y=cy + ch / 2 - pill_h / 2,
                        width=pill_w,
                        height=pill_h,
                        rx=pill_h / 2,
                        ry=pill_h / 2,
                    )
                    pill.set("fill", "#000000" if norm > 0.45 else "#ffffff")
                    pill.set("fill-opacity", "0.3" if norm > 0.45 else "0.75")

                    svg_text(g, cx + cw / 2, cy + ch / 2 + sz * 0.35, txt, sz, fill=ink, bold=True)

        # --- Colorbar with smooth gradient ---
        cb_w = int(pw * 0.016)
        cb_h = int(gh * 0.85)
        cb_x = x0 + gw + int(pw * 0.025)
        cb_y = y0 + (gh - cb_h) / 2
        n_seg = 120
        seg_h = cb_h / n_seg

        for si in range(n_seg):
            t = 1 - si / (n_seg - 1)
            self.svg.node(g, "rect", x=cb_x, y=cb_y + si * seg_h, width=cb_w, height=seg_h + 1, fill=color_at(t))

        # Colorbar border
        border = self.svg.node(g, "rect", x=cb_x, y=cb_y, width=cb_w, height=cb_h, rx=3, ry=3)
        border.set("fill", "none")
        border.set("stroke", "#444")
        border.set("stroke-width", "1.5")

        # Colorbar ticks (log scale: 0, 1, 10, 100, 1000, ...)
        max_pow = int(math.log10(self.vmax)) if self.vmax > 0 else 0
        for tv in [0] + [10**p for p in range(max_pow + 1)]:
            t = 0 if tv == 0 else math.log10(tv + 1) / log_max
            ty = cb_y + cb_h * (1 - t)
            self.svg.node(g, "line", x1=cb_x + cb_w, y1=ty, x2=cb_x + cb_w + 10, y2=ty, stroke="#444")
            label = f"{int(tv):,}" if tv >= 1000 else str(int(tv))
            svg_text(g, cb_x + cb_w + 16, ty + 10, label, 30, anchor="start", fill="#555")

        # Colorbar title
        if self.colorbar_title:
            svg_text(g, cb_x + cb_w / 2, cb_y - 28, self.colorbar_title, 36, bold=True)

    def _compute(self):
        nr = len(self.matrix_data) if self.matrix_data else 1
        nc = len(self.matrix_data[0]) if self.matrix_data and self.matrix_data[0] else 1
        self._box.xmin, self._box.xmax = 0, nc
        self._box.ymin, self._box.ymax = 0, nr


# --- Data: wind turbine blade root fatigue loading ---
np.random.seed(42)

n_amp_bins = 20
n_mean_bins = 20

amp_edges = np.linspace(0, 200, n_amp_bins + 1)
mean_edges = np.linspace(-50, 250, n_mean_bins + 1)
amp_centers = (amp_edges[:-1] + amp_edges[1:]) / 2
mean_centers = (mean_edges[:-1] + mean_edges[1:]) / 2

counts = np.zeros((n_amp_bins, n_mean_bins))
for i in range(n_amp_bins):
    for j in range(n_mean_bins):
        amp, mean_val = amp_centers[i], mean_centers[j]
        primary = np.exp(-amp / 28) * np.exp(-((mean_val - 100) ** 2) / (2 * 55**2))
        vibration = 0.5 * np.exp(-amp / 10) * np.exp(-((mean_val - 55) ** 2) / (2 * 20**2))
        base = 9000 * (primary + vibration) * (1 + 0.2 * np.random.randn())
        if amp + abs(mean_val - 100) > 220 or base < 2:
            counts[i][j] = 0
        else:
            counts[i][j] = int(round(max(0, base)))

# Flip so high amplitude is at top
matrix = counts[::-1].tolist()
vmax = int(np.max(counts))

# Extended viridis — 16 stops for smoother gradient transitions
viridis = [
    "#440154",
    "#46085c",
    "#482878",
    "#3b3f8f",
    "#3e4989",
    "#31688e",
    "#26828e",
    "#1f9e89",
    "#2eb37c",
    "#35b779",
    "#5ec962",
    "#6ece58",
    "#9cd648",
    "#b5de2b",
    "#d8e219",
    "#fde725",
]

style = Style(
    background="white",
    plot_background="white",
    foreground="#333",
    foreground_strong="#222",
    foreground_subtle="#999",
    colors=("#306998",),
    title_font_size=58,
    label_font_size=30,
    font_family="sans-serif",
)

chart = RainflowHeatmap(
    width=4800,
    height=2700,
    style=style,
    title="heatmap-rainflow \u00b7 pygal \u00b7 pyplots.ai",
    subtitle_text="Wind Turbine Blade Root \u2014 Variable Amplitude Fatigue Spectrum",
    matrix_data=matrix,
    row_labels=[f"{v:.0f}" for v in amp_centers[::-1]],
    col_labels=[f"{v:.0f}" for v in mean_centers],
    colormap=viridis,
    vmax=vmax,
    show_legend=False,
    margin=80,
    margin_top=180,
    margin_bottom=60,
    show_x_labels=False,
    show_y_labels=False,
    x_axis_title="Mean Stress (MPa)",
    y_axis_title="Stress Amplitude (MPa)",
    colorbar_title="Cycle Count",
    explicit_size=True,
    pretty_print=True,
)

# Pygal requires at least one series to enter the rendering pipeline
chart.add("", [0])

chart.render_to_file("plot.svg")
chart.render_to_png("plot.png")

# Interactive HTML export — distinctive pygal feature
html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>heatmap-rainflow \u00b7 pygal</title>
    <style>
        body {{ margin: 0; display: flex; justify-content: center;
               align-items: center; min-height: 100vh; background: #f5f5f5; }}
        .chart {{ max-width: 100%; height: auto; }}
    </style>
</head>
<body>
    <figure class="chart">{chart.render(is_unicode=True)}</figure>
</body>
</html>"""

with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html)
