""" anyplot.ai
heatmap-rainflow: Rainflow Counting Matrix for Fatigue Analysis
Library: pygal 3.1.3 | Python 3.14.10
Quality: 81/100 | Updated: 2026-11-28
"""

import math
import os
import sys
from itertools import pairwise

import numpy as np
import pandas as pd


# Theme tokens — Imprint palette chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
AMBER = "#DDCC77"  # Imprint amber anchor, outside the categorical pool

# Imprint sequential ramp for filled cells (fields stops, per theme)
SEQ_FIELDS = (
    [(0.0, "#66E2B2"), (0.369, "#009E73"), (0.803, "#024582"), (1.0, "#351E45")]
    if THEME == "light"
    else [(0.0, "#404C02"), (0.487, "#009E73"), (1.0, "#CDD9FF")]
)

# This file shares its name with the pygal package; temporarily remove the
# current directory from sys.path so the real package is found first.
sys.path, _saved_path = sys.path[1:], sys.path[0]
from pygal.graph.graph import Graph  # noqa: E402
from pygal.style import Style  # noqa: E402


sys.path.insert(0, _saved_path)


def ramp_color(stops, t):
    """The hex at t (0 to 1) along (position, hex) stops, blended linearly in sRGB."""
    t = min(max(t, 0.0), 1.0)
    (p0, c0), (p1, c1) = next((a, b) for a, b in pairwise(stops) if t <= b[0])
    share = (t - p0) / (p1 - p0)
    return "#" + "".join(
        f"{round(int(c0[i : i + 2], 16) * (1 - share) + int(c1[i : i + 2], 16) * share):02X}" for i in (1, 3, 5)
    )


# Columns: set these to your table's column names
AMPLITUDE = "Stress Amplitude (MPa)"  # role: amplitude
MEAN = "Mean Stress (MPa)"  # role: mean
COUNT = "Cycle Count"  # role: count

# Data: replace this block with your own table, for example df = pd.read_csv("rainflow.csv")
# Wind turbine blade root fatigue loading (variable-amplitude spectrum), one row per bin
np.random.seed(42)
n_bins = 20
amp_edges = np.linspace(0, 200, n_bins + 1)
mean_edges = np.linspace(-50, 250, n_bins + 1)
amp_centers = (amp_edges[:-1] + amp_edges[1:]) / 2
mean_centers = (mean_edges[:-1] + mean_edges[1:]) / 2

rows = []
for amp in amp_centers:
    for mean_val in mean_centers:
        primary = np.exp(-amp / 28) * np.exp(-((mean_val - 100) ** 2) / (2 * 55**2))
        vibration = 0.5 * np.exp(-amp / 10) * np.exp(-((mean_val - 55) ** 2) / (2 * 20**2))
        base = 9000 * (primary + vibration) * (1 + 0.2 * np.random.randn())
        empty = amp + abs(mean_val - 100) > 220 or base < 2
        rows.append((float(amp), float(mean_val), 0 if empty else int(round(max(0, base)))))
df = pd.DataFrame(rows, columns=[AMPLITUDE, MEAN, COUNT])

# Plot: reads only df and the constants above
table = df.pivot_table(index=AMPLITUDE, columns=MEAN, values=COUNT, sort=False, dropna=False)
table = table.iloc[::-1]  # high amplitude at the top, the fatigue-matrix convention
values = table.to_numpy(dtype=float)
matrix = values.tolist()
vmax = float(np.nanmax(values))


class RainflowHeatmap(Graph):
    def __init__(self, *args, **kwargs):
        self.matrix_data = kwargs.pop("matrix_data", [])
        self.row_labels = kwargs.pop("row_labels", [])
        self.col_labels = kwargs.pop("col_labels", [])
        self.vmax = kwargs.pop("vmax", 1)
        self.x_axis_title = kwargs.pop("x_axis_title", "")
        self.y_axis_title = kwargs.pop("y_axis_title", "")
        self.colorbar_title = kwargs.pop("colorbar_title", "")
        self.subtitle_text = kwargs.pop("subtitle_text", "")
        super().__init__(*args, **kwargs)

    def _plot(self):
        if not self.matrix_data:
            return

        log_max = math.log10(self.vmax + 1)

        def log_norm(value):
            if value <= 0:
                return -1.0
            return math.log10(value + 1) / log_max

        def svg_text(parent, x, y, label, size, **kw):
            node = self.svg.node(parent, "text", x=x, y=y)
            node.set("text-anchor", kw.get("anchor", "middle"))
            node.set("fill", kw.get("fill", INK))
            weight = "bold" if kw.get("bold") else "normal"
            if kw.get("weight"):
                weight = kw["weight"]
            style_str = f"font-size:{size}px;font-weight:{weight};font-family:sans-serif"
            if kw.get("letter_spacing"):
                style_str += f";letter-spacing:{kw['letter_spacing']}px"
            node.set("style", style_str)
            if "rotation" in kw:
                node.set("transform", f"rotate({kw['rotation']}, {x}, {y})")
            node.text = label

        nr = len(self.matrix_data)
        nc = len(self.matrix_data[0])
        pw, ph = self.view.width, self.view.height

        # Proportional margins within the view area
        ml = int(pw * 0.09)
        mr = int(pw * 0.09)
        mt = int(ph * 0.02)
        mb = int(ph * 0.08)

        aw, ah = pw - ml - mr, ph - mt - mb
        cw = aw / nc * 0.97
        ch = ah / nr * 0.97
        gap = min(cw, ch) * 0.015
        gw = nc * (cw + gap) - gap
        gh = nr * (ch + gap) - gap

        x0 = self.view.x(0) + ml + (aw - gw) / 2
        y0 = self.view.y(nr) + mt + (ah - gh) / 2

        g = self.svg.node(self.nodes["plot"], class_="heatmap")

        # Subtitle sits in the margin_top gap between pygal title and grid
        if self.subtitle_text:
            svg_text(
                g,
                pw / 2 + self.view.x(0),
                y0 - 30,
                self.subtitle_text,
                44,
                fill=INK_MUTED,
                weight="300",
                letter_spacing=1,
            )

        # Elevated background panel behind heatmap grid
        pad = 14
        panel = self.svg.node(g, "rect", x=x0 - pad, y=y0 - pad, width=gw + 2 * pad, height=gh + 2 * pad, rx=6, ry=6)
        panel.set("fill", ELEVATED_BG)
        panel.set("stroke", INK_MUTED)
        panel.set("stroke-width", "0.8")
        panel.set("stroke-opacity", "0.4")

        # Y-axis title (rotated 90°)
        if self.y_axis_title:
            svg_text(g, x0 - int(pw * 0.075), y0 + gh / 2, self.y_axis_title, 46, bold=True, fill=INK, rotation=-90)

        # Row labels — every other to prevent crowding
        rf = min(30, int(ch * 0.5))
        for i, lbl in enumerate(self.row_labels):
            if i % 2 == 0 or i == nr - 1:
                svg_text(g, x0 - 16, y0 + i * (ch + gap) + ch / 2 + rf * 0.35, lbl, rf, anchor="end", fill=INK_SOFT)

        # Column labels — every 3rd for clean spacing
        cf = min(30, int(cw * 0.45))
        for j, lbl in enumerate(self.col_labels):
            if j % 3 == 0 or j == nc - 1:
                x = x0 + j * (cw + gap) + cw / 2
                y = y0 + gh + gap + cf + 10
                svg_text(g, x, y, lbl, cf, fill=INK_SOFT)

        # X-axis title
        if self.x_axis_title:
            svg_text(g, x0 + gw / 2, y0 + gh + int(ph * 0.07), self.x_axis_title, 46, bold=True, fill=INK)

        # Absolute peak cell: the one annotated, with an amber halo
        cell_values = [
            (self.matrix_data[i][j], i, j)
            for i in range(nr)
            for j in range(nc)
            if not math.isnan(self.matrix_data[i][j]) and self.matrix_data[i][j] > 0
        ]
        peak_cell = max(cell_values)[1:] if cell_values else None

        # Draw heatmap cells; a missing value draws nothing
        for i in range(nr):
            for j in range(nc):
                val = self.matrix_data[i][j]
                if math.isnan(val):
                    continue
                cx = x0 + j * (cw + gap)
                cy = y0 + i * (ch + gap)
                norm = log_norm(val)

                fill = PAGE_BG if norm < 0 else ramp_color(SEQ_FIELDS, norm)
                stroke = INK_MUTED if norm < 0 else "none"
                sw = "0.5"

                if (i, j) == peak_cell:
                    glow = self.svg.node(g, "rect", x=cx - 4, y=cy - 4, width=cw + 8, height=ch + 8, rx=5, ry=5)
                    glow.set("fill", "none")
                    glow.set("stroke", AMBER)
                    glow.set("stroke-width", "5")
                    glow.set("opacity", "0.7")
                    stroke = INK
                    sw = "2.5"

                rect = self.svg.node(g, "rect", x=cx, y=cy, width=cw, height=ch, rx=3, ry=3)
                rect.set("fill", fill)
                rect.set("stroke", stroke)
                rect.set("stroke-width", sw)

                # Peak value on a page-colored pill so it reads on any cell color
                if (i, j) == peak_cell:
                    txt = f"{int(val):,}"
                    sz = min(int(ch * 0.36), 30)
                    pill_w = len(txt) * sz * 0.6 + 14
                    pill_h = sz + 10
                    pill_cx = cx + cw / 2
                    pill_cy = cy + ch / 2
                    pill = self.svg.node(
                        g,
                        "rect",
                        x=pill_cx - pill_w / 2,
                        y=pill_cy - pill_h / 2,
                        width=pill_w,
                        height=pill_h,
                        rx=pill_h / 2,
                        ry=pill_h / 2,
                    )
                    pill.set("fill", PAGE_BG)
                    pill.set("fill-opacity", "0.9")
                    svg_text(g, pill_cx, pill_cy + sz * 0.35, txt, sz, fill=INK, bold=True)

        # Smooth gradient colorbar (120-segment approximation)
        cb_w = int(pw * 0.016)
        cb_h = int(gh * 0.85)
        cb_x = x0 + gw + int(pw * 0.025)
        cb_y = y0 + (gh - cb_h) / 2
        n_seg = 120
        seg_h = cb_h / n_seg

        for si in range(n_seg):
            t = 1 - si / (n_seg - 1)
            self.svg.node(
                g, "rect", x=cb_x, y=cb_y + si * seg_h, width=cb_w, height=seg_h + 1, fill=ramp_color(SEQ_FIELDS, t)
            )

        # Colorbar border
        border = self.svg.node(g, "rect", x=cb_x, y=cb_y, width=cb_w, height=cb_h, rx=3, ry=3)
        border.set("fill", "none")
        border.set("stroke", INK_SOFT)
        border.set("stroke-width", "1.5")

        # Colorbar ticks (log scale: 0, 1, 10, 100, 1000, ...)
        max_pow = int(math.log10(self.vmax)) if self.vmax >= 1 else 0
        for tv in [0] + [10**p for p in range(max_pow + 1)]:
            t = 0 if tv == 0 else math.log10(tv + 1) / log_max
            ty = cb_y + cb_h * (1 - t)
            self.svg.node(g, "line", x1=cb_x + cb_w, y1=ty, x2=cb_x + cb_w + 10, y2=ty, stroke=INK_SOFT)
            label = f"{int(tv):,}" if tv >= 1000 else str(int(tv))
            svg_text(g, cb_x + cb_w + 16, ty + 10, label, 30, anchor="start", fill=INK_SOFT)

        # Colorbar title
        if self.colorbar_title:
            svg_text(g, cb_x + cb_w / 2, cb_y - 28, self.colorbar_title, 36, bold=True, fill=INK)

    def _compute(self):
        nr = len(self.matrix_data) if self.matrix_data else 1
        nc = len(self.matrix_data[0]) if self.matrix_data and self.matrix_data[0] else 1
        self._box.xmin, self._box.xmax = 0, nc
        self._box.ymin, self._box.ymax = 0, nr


custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    guide_stroke_color=INK_MUTED,
    major_guide_stroke_color=INK_MUTED,
    colors=IMPRINT_PALETTE,
    title_font_size=66,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=2.5,
)

chart = RainflowHeatmap(
    width=2400,
    height=2400,
    style=custom_style,
    title="heatmap-rainflow · python · pygal · anyplot.ai",
    subtitle_text="Wind Turbine Blade Root — Variable Amplitude Fatigue Spectrum",
    matrix_data=matrix,
    row_labels=[f"{v:.0f}" for v in table.index],
    col_labels=[f"{v:.0f}" for v in table.columns],
    vmax=vmax,
    show_legend=False,
    margin=80,
    margin_top=140,
    margin_bottom=60,
    show_x_labels=False,
    show_y_labels=False,
    x_axis_title=MEAN,
    y_axis_title=AMPLITUDE,
    colorbar_title=COUNT,
    explicit_size=True,
    pretty_print=True,
)

# Pygal requires at least one series to trigger the rendering pipeline
chart.add("", [0])

chart.render_to_png(f"plot-{THEME}.png")

# Interactive HTML export — leverages pygal's distinctive SVG/JS output
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>heatmap-rainflow · python · pygal · anyplot.ai</title>
    <style>
        body {{ margin: 0; display: flex; justify-content: center;
               align-items: center; min-height: 100vh; background: {PAGE_BG}; }}
        .chart {{ max-width: 100%; height: auto; }}
    </style>
</head>
<body>
    <figure class="chart">{chart.render(is_unicode=True)}</figure>
</body>
</html>"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)
