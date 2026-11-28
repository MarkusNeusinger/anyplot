"""anyplot.ai
heatmap-cohort-retention: Cohort Retention Heatmap
Library: pygal 3.1.3 | Python 3.13.14
Quality: pending | Updated: 2026-06-20
"""

import math
import os
import sys
from itertools import pairwise

import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Imprint sequential ramp for filled cells (fields): light = low retention, dark = high
SEQ_FIELDS = (
    [(0.0, "#66E2B2"), (0.369, "#009E73"), (0.803, "#024582"), (1.0, "#351E45")]
    if THEME == "light"
    else [(0.0, "#404C02"), (0.487, "#009E73"), (1.0, "#CDD9FF")]
)

# Remove script dir so "pygal" resolves to the installed package, not this file
_cwd = sys.path.pop(0)
from pygal.graph.graph import Graph
from pygal.style import Style


sys.path.insert(0, _cwd)

# Columns: set these to your table's column names
COHORT = "Signup Cohort"  # role: cohort
PERIOD = "Months Since Signup"  # role: period
RETENTION = "Retention %"  # role: retention_rate
COHORT_SIZE = "Cohort size"  # role: cohort_size

# Data: replace this block with your own table, for example df = pd.read_csv("retention.csv")
np.random.seed(42)
cohort_names = [f"{m} 2024" for m in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct"]]
sizes = [1200, 1350, 980, 1520, 1100, 1430, 1280, 1050, 1380, 1150]
base_retention = [100.0, 65.0, 48.0, 40.0, 34.0, 30.0, 27.0, 25.0, 23.5, 22.0]

rows = []
for i, (name, size) in enumerate(zip(cohort_names, sizes, strict=True)):
    for j in range(len(base_retention) - i):
        if j == 0:
            rate = 100.0
        else:
            lift = -4.0 if i == 3 else i * 1.8
            rate = round(float(np.clip(base_retention[j] + lift + np.random.uniform(-2.0, 2.0), 5.0, 100.0)), 1)
        rows.append({COHORT: name, PERIOD: j, RETENTION: rate, COHORT_SIZE: size})
df = pd.DataFrame(rows)


# Plot
def ramp_color(stops, t):
    """The hex at t (0 to 1) along (position, hex) stops, blended linearly in sRGB."""
    if not math.isfinite(t):
        return "none"
    t = min(max(t, 0.0), 1.0)
    (p0, c0), (p1, c1) = next((a, b) for a, b in pairwise(stops) if t <= b[0])
    share = (t - p0) / (p1 - p0)
    return "#" + "".join(
        f"{round(int(c0[i : i + 2], 16) * (1 - share) + int(c1[i : i + 2], 16) * share):02X}" for i in (1, 3, 5)
    )


def text_on(bg):
    """Dark or light ink, whichever has the higher contrast on the cell color."""

    def lum(hex_color):
        lin = [(c / 255) ** 2.2 for c in (int(hex_color[i : i + 2], 16) for i in (1, 3, 5))]
        return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]

    light, dark = "#F0EFE8", "#1A1A17"

    def contrast(a, b):
        return (max(lum(a), lum(b)) + 0.05) / (min(lum(a), lum(b)) + 0.05)

    return light if contrast(bg, light) >= contrast(bg, dark) else dark


FONT = "font-family:'Segoe UI',Roboto,sans-serif"


class CohortRetentionHeatmap(Graph):
    """pygal has no heatmap type: a Graph subclass that draws the cells, labels and color bar as SVG."""

    _series_margin = 0

    def __init__(self, *args, **kwargs):
        self.matrix_data = kwargs.pop("matrix_data", [])
        self.row_labels = kwargs.pop("row_labels", [])
        self.col_labels = kwargs.pop("col_labels", [])
        self.cohort_sizes = kwargs.pop("cohort_sizes", [])
        super().__init__(*args, **kwargs)

    def _plot(self):
        if not self.matrix_data:
            return

        n_rows = len(self.matrix_data)
        n_cols = max(len(row) for row in self.matrix_data)
        non_null = [v for row in self.matrix_data for v in row if v is not None]
        min_val, max_val = min(non_null), max(non_null)
        span = (max_val - min_val) or 1.0

        pw, ph = self.view.width, self.view.height
        lm_l, lm_r, lm_t, lm_b = 460, 285, 130, 15
        aw, ah = pw - lm_l - lm_r, ph - lm_t - lm_b
        cw = aw / n_cols
        ch = ah / (n_rows + 0.2)
        gap = 4

        gw = n_cols * (cw + gap) - gap
        gh = n_rows * (ch + gap) - gap

        x0 = self.view.x(0) + lm_l + (aw - gw) / 2
        y0 = self.view.y(n_rows) + lm_t + (ah - gh - ch * 0.2) / 2

        pn = self.nodes["plot"]
        col_fs = min(26, int(cw * 0.34))
        row_fs = min(38, int(ch * 0.48))
        size_fs = int(row_fs * 0.92)
        val_fs = min(40, int(min(cw, ch) * 0.44))

        # Column section header
        nd = self.svg.node(pn, "text", x=x0 + gw / 2, y=y0 - 78)
        nd.set("text-anchor", "middle")
        nd.set("fill", INK_SOFT)
        nd.set("style", f"font-size:{col_fs + 4}px;font-weight:600;{FONT}")
        nd.text = PERIOD

        # Column headers
        for j, lbl in enumerate(self.col_labels):
            cx = x0 + j * (cw + gap) + cw / 2
            nd = self.svg.node(pn, "text", x=cx, y=y0 - 18)
            nd.set("text-anchor", "middle")
            nd.set("fill", INK)
            nd.set("style", f"font-size:{col_fs}px;font-weight:700;{FONT}")
            nd.text = str(lbl)

        # Row labels with cohort sizes
        for i, lbl in enumerate(self.row_labels):
            ry = y0 + i * (ch + gap) + ch / 2
            rx = x0 - 22
            nd = self.svg.node(pn, "text", x=rx, y=ry + row_fs * 0.12)
            nd.set("text-anchor", "end")
            nd.set("fill", INK)
            nd.set("style", f"font-size:{row_fs}px;font-weight:600;{FONT}")
            nd.text = str(lbl)
            nd2 = self.svg.node(pn, "text", x=rx, y=ry + row_fs * 0.12 + size_fs + 5)
            nd2.set("text-anchor", "end")
            nd2.set("fill", INK_MUTED)
            nd2.set("style", f"font-size:{size_fs}px;font-style:italic;{FONT}")
            nd2.text = f"n={self.cohort_sizes[i]:,}"

        # Y-axis title (rotated)
        ytx, yty = x0 - 355, y0 + gh / 2
        nd = self.svg.node(pn, "text", x=ytx, y=yty)
        nd.set("text-anchor", "middle")
        nd.set("fill", INK_SOFT)
        nd.set("style", f"font-size:{col_fs + 4}px;font-weight:600;{FONT}")
        nd.set("transform", f"rotate(-90, {ytx}, {yty})")
        nd.text = COHORT

        # Cells
        for i in range(n_rows):
            for j, v in enumerate(self.matrix_data[i]):
                if v is None:
                    continue
                color = ramp_color(SEQ_FIELDS, (v - min_val) / span)
                cx = x0 + j * (cw + gap)
                cy = y0 + i * (ch + gap)

                grp = self.svg.node(pn, "g")
                rect = self.svg.node(grp, "rect", x=cx, y=cy, width=cw, height=ch, rx=5, ry=5)
                rect.set("fill", color)
                rect.set("stroke", ELEVATED_BG)
                rect.set("stroke-width", "1.5")

                self._tooltip_data(
                    grp, f"{v:.1f}%", cx + cw / 2, cy + ch / 2, xlabel=f"{self.row_labels[i]} – {self.col_labels[j]}"
                )

                vt = self.svg.node(grp, "text", x=cx + cw / 2, y=cy + ch / 2 + val_fs * 0.35)
                vt.set("text-anchor", "middle")
                vt.set("fill", text_on(color))
                vt.set("style", f"font-size:{val_fs}px;font-weight:600;{FONT}")
                vt.text = f"{v:.0f}%"

        # Color bar: high retention on top
        cb_w, cb_h = 48, gh * 0.80
        cb_x, cb_y = x0 + gw + 55, y0 + (gh - cb_h) / 2
        cb_ls = 28

        defs = self.svg.node(pn, "defs")
        grad = self.svg.node(defs, "linearGradient", id="cb-gradient", x1="0", y1="0", x2="0", y2="1")
        for fi in range(21):
            f = fi / 20.0
            stop = self.svg.node(grad, "stop", offset=f"{f * 100}%")
            stop.set("stop-color", ramp_color(SEQ_FIELDS, 1.0 - f))

        cbr = self.svg.node(pn, "rect", x=cb_x, y=cb_y, width=cb_w, height=cb_h, rx=4, ry=4)
        cbr.set("fill", "url(#cb-gradient)")
        cbr.set("stroke", INK_MUTED)
        cbr.set("stroke-width", "1")

        for frac in (0.0, 0.25, 0.5, 0.75, 1.0):
            ty = cb_y + cb_h * frac
            val = max_val - span * frac
            tk = self.svg.node(pn, "line", x1=cb_x + cb_w, y1=ty, x2=cb_x + cb_w + 10, y2=ty)
            tk.set("stroke", INK_SOFT)
            tk.set("stroke-width", "1.5")
            tt = self.svg.node(pn, "text", x=cb_x + cb_w + 16, y=ty + cb_ls * 0.35)
            tt.set("fill", INK)
            tt.set("style", f"font-size:{cb_ls}px;{FONT}")
            tt.text = f"{val:.0f}%"

        cbt = self.svg.node(pn, "text", x=cb_x + cb_w + 100, y=cb_y - 30)
        cbt.set("text-anchor", "end")
        cbt.set("fill", INK_SOFT)
        cbt.set("style", f"font-size:{cb_ls}px;font-weight:600;{FONT}")
        cbt.text = RETENTION

    def _compute(self):
        self._box.xmin = 0
        self._box.xmax = max((len(row) for row in self.matrix_data), default=1)
        self._box.ymin = 0
        self._box.ymax = len(self.matrix_data) or 1


# Cohorts as rows, periods as columns; later cohorts have fewer periods, the rest stays empty
table = df.pivot_table(index=COHORT, columns=PERIOD, values=RETENTION, sort=False)
matrix = [[v for v in row if not math.isnan(v)] for row in table.to_numpy().tolist()]
cohort_sizes = df.drop_duplicates(COHORT, keep="first")[COHORT_SIZE].tolist()

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    guide_stroke_color=INK_MUTED,
    major_guide_stroke_color=INK_MUTED,
    colors=tuple(IMPRINT_PALETTE),
    title_font_size=66,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=2.5,
)

chart = CohortRetentionHeatmap(
    width=2400,
    height=2400,
    style=custom_style,
    title="heatmap-cohort-retention · python · pygal · anyplot.ai",
    matrix_data=matrix,
    row_labels=table.index.tolist(),
    col_labels=[f"Month {p}" for p in table.columns],
    cohort_sizes=cohort_sizes,
    show_legend=False,
    margin=100,
    margin_top=200,
    margin_bottom=30,
    margin_left=120,
    margin_right=120,
    show_x_labels=False,
    show_y_labels=False,
)
chart.add("data", [0])

# Save
chart.render_to_png(f"plot-{THEME}.png")
chart.render_to_file(f"plot-{THEME}.svg")

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>heatmap-cohort-retention · python · pygal · anyplot.ai</title>
    <style>
        body {{ margin: 0; background: {PAGE_BG}; display: flex; justify-content: center; align-items: center; min-height: 100vh; }}
    </style>
</head>
<body>
    {chart.render(is_unicode=True)}
</body>
</html>"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)
