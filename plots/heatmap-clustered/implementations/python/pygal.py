"""anyplot.ai
heatmap-clustered: Clustered Heatmap
Library: pygal 3.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-09
"""

import os

import numpy as np
import pandas as pd
from pygal.graph.graph import Graph
from pygal.style import Style
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import pdist


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
# imprint_div: blue (low) -> theme-adaptive midpoint -> matte red (high), centered on zero
DIVERGING_STOPS = ["#4467A3", PAGE_BG, "#AE3030"]

# Columns: set these to your table's labels
ROW_AXIS = "Drugs"  # role: row_labels
COL_AXIS = "Cell lines"  # role: column_labels
VALUE = "log IC50 (µM)"  # role: matrix

# Data: replace this block with your own labeled matrix, for example df = pd.read_csv("ic50.csv", index_col=0)
np.random.seed(42)

drugs = [
    "Paclitaxel",
    "Doxorubicin",
    "Cisplatin",
    "Gemcitabine",
    "5-Fluorouracil",
    "Irinotecan",
    "Bortezomib",
    "Sorafenib",
    "Sunitinib",
    "Erlotinib",
    "Gefitinib",
    "Lapatinib",
]
cell_lines = ["A549", "HCT116", "HT29", "MCF7", "MDA231", "OVCAR3", "SKOV3", "SW480", "U87", "KHOS"]

sensitivity_data = np.zeros((len(drugs), len(cell_lines)))

# Chemotherapy drugs: sensitive epithelial lines, resistant mesenchymal lines
chemo_drugs = [0, 1, 2, 3, 4, 5]
epithelial_lines = [0, 1, 2, 7]
mesenchymal_lines = [3, 4]
for i in chemo_drugs:
    for j in epithelial_lines:
        sensitivity_data[i, j] = np.random.randn() * 0.6 - 1.2
    for j in mesenchymal_lines:
        sensitivity_data[i, j] = np.random.randn() * 0.6 + 0.9
    for j in [5, 6, 8, 9]:
        sensitivity_data[i, j] = np.random.randn() * 0.7

# Targeted drugs: sensitive EGFR-mutant lines, weaker elsewhere
targeted_drugs = [6, 7, 8, 9, 10, 11]
for i in targeted_drugs:
    for j in [8, 9]:
        sensitivity_data[i, j] = np.random.randn() * 0.5 - 1.3
    for j in [0, 1, 2, 3]:
        sensitivity_data[i, j] = np.random.randn() * 0.5 + 0.5
    for j in [4, 5, 6, 7]:
        sensitivity_data[i, j] = np.random.randn() * 0.6

df = pd.DataFrame(sensitivity_data, index=pd.Index(drugs, name=ROW_AXIS), columns=pd.Index(cell_lines, name=COL_AXIS))


# Plot: reads only df and the constants above
def lerp_color(stops, t):
    """Piecewise-linear interpolation through hex color stops, t in [0, 1]."""
    pos = min(max(t, 0.0), 1.0) * (len(stops) - 1)
    k = min(int(pos), len(stops) - 2)
    frac = pos - k
    c0, c1 = stops[k], stops[k + 1]
    rgb = [round(int(c0[i : i + 2], 16) + (int(c1[i : i + 2], 16) - int(c0[i : i + 2], 16)) * frac) for i in (1, 3, 5)]
    return "#{:02x}{:02x}{:02x}".format(*rgb)


row_linkage = linkage(pdist(df.to_numpy()), method="ward")
col_linkage = linkage(pdist(df.T.to_numpy()), method="ward")
row_order = dendrogram(row_linkage, no_plot=True)["leaves"]
col_order = dendrogram(col_linkage, no_plot=True)["leaves"]
table = df.iloc[row_order, col_order]

limit = float(np.nanmax(np.abs(table.to_numpy())))
n_rows, n_cols = table.shape


class ClusteredHeatmap(Graph):
    """pygal has no clustered heatmap: this Graph subclass draws it as SVG inside the plot node."""

    def __init__(self, *args, **kwargs):
        self.table = kwargs.pop("table")
        self.row_linkage = kwargs.pop("row_linkage")
        self.col_linkage = kwargs.pop("col_linkage")
        super().__init__(*args, **kwargs)

    def _text(self, group, x, y, text, size, anchor="start", weight="normal", fill=INK, transform=None):
        node = self.svg.node(group, "text", x=x, y=y)
        node.set("text-anchor", anchor)
        node.set("fill", fill)
        node.set("style", f"font-size:{size}px;font-weight:{weight};font-family:sans-serif")
        if transform:
            node.set("transform", transform)
        node.text = text

    def _dendrogram(self, group, link, x0, y0, width, height, rows):
        """Draw a dendrogram: root far from the matrix, leaves touching it."""
        dend = dendrogram(link, no_plot=True)
        icoord, dcoord = np.array(dend["icoord"]), np.array(dend["dcoord"])
        leaf = icoord / (len(dend["leaves"]) * 10)
        depth = dcoord / dcoord.max()
        for lf, dp in zip(leaf, depth, strict=True):
            if rows:  # leaves on the right edge, root on the left
                points = [(x0 + width * (1 - d), y0 + height * p) for p, d in zip(lf, dp, strict=True)]
            else:  # leaves on the bottom edge, root on top
                points = [(x0 + width * p, y0 + height * (1 - d)) for p, d in zip(lf, dp, strict=True)]
            path = self.svg.node(group, "path")
            path.set("d", "M " + " L ".join(f"{px:.1f} {py:.1f}" for px, py in points))
            path.set("fill", "none")
            path.set("stroke", INK_SOFT)
            path.set("stroke-width", "4")
            path.set("stroke-linejoin", "round")

    def _plot(self):
        values = self.table.to_numpy()
        rows, cols = values.shape
        group = self.svg.node(self.nodes["plot"], class_="clustered-heatmap")

        # Layout in plot-area pixels: axis title | row dendrogram | row labels | cells | colorbar
        row_font, col_font, axis_font = 46, 42, 54
        label_w = int(max(len(str(r)) for r in self.table.index) * row_font * 0.58) + 24
        ylabel_w, row_dend_w, colorbar_w = 70, 250, 50
        right_w = colorbar_w + 190
        col_dend_h = 200
        bottom_h = 150 + axis_font + 40
        heat_x = ylabel_w + row_dend_w + label_w
        heat_w = self.view.width - heat_x - right_w
        heat_y = col_dend_h + 10
        heat_h = self.view.height - heat_y - bottom_h
        cell_w, cell_h = heat_w / cols, heat_h / rows

        self._dendrogram(group, self.row_linkage, ylabel_w, heat_y, row_dend_w - 20, heat_h, rows=True)
        self._dendrogram(group, self.col_linkage, heat_x, 0, heat_w, col_dend_h, rows=False)

        for i, name in enumerate(self.table.index):
            self._text(
                group,
                heat_x - 16,
                heat_y + (i + 0.5) * cell_h + row_font * 0.35,
                str(name),
                row_font,
                anchor="end",
                weight="600",
            )

        for j, name in enumerate(self.table.columns):
            x, y = heat_x + (j + 0.5) * cell_w, heat_y + heat_h + 36
            self._text(group, x, y, str(name), col_font, weight="600", transform=f"rotate(45, {x:.1f}, {y:.1f})")

        for i in range(rows):
            for j in range(cols):
                value = values[i, j]
                fill = "none" if np.isnan(value) else lerp_color(DIVERGING_STOPS, (value / limit + 1) / 2)
                rect = self.svg.node(
                    group,
                    "rect",
                    x=heat_x + j * cell_w,
                    y=heat_y + i * cell_h,
                    width=cell_w - 2,
                    height=cell_h - 2,
                    rx=4,
                    ry=4,
                )
                rect.set("fill", fill)

        # Colorbar: top = +limit, bottom = -limit
        bar_h = heat_h * 0.75
        bar_x, bar_y = heat_x + heat_w + 50, heat_y + (heat_h - bar_h) / 2
        n_seg = 80
        for s in range(n_seg):
            t = 1 - s / (n_seg - 1)
            self.svg.node(
                group,
                "rect",
                x=bar_x,
                y=bar_y + s * bar_h / n_seg,
                width=colorbar_w,
                height=bar_h / n_seg + 1,
                fill=lerp_color(DIVERGING_STOPS, t),
            )
        self.svg.node(
            group,
            "rect",
            x=bar_x,
            y=bar_y,
            width=colorbar_w,
            height=bar_h,
            fill="none",
            stroke=INK_SOFT,
            stroke_width="2",
        )
        for val, y in [(limit, bar_y), (0, bar_y + bar_h / 2), (-limit, bar_y + bar_h)]:
            self._text(group, bar_x + colorbar_w + 14, y + 13, f"{val:+.1f}", 36)
        title_x, title_y = bar_x + colorbar_w + 14 + 115, bar_y + bar_h / 2
        self._text(
            group,
            title_x,
            title_y,
            VALUE,
            40,
            anchor="middle",
            weight="bold",
            transform=f"rotate(90, {title_x:.1f}, {title_y:.1f})",
        )

        # Axis titles
        x, y = 28, heat_y + heat_h / 2
        self._text(
            group, x, y, ROW_AXIS, axis_font, anchor="middle", weight="bold", transform=f"rotate(-90, {x}, {y:.1f})"
        )
        self._text(
            group, heat_x + heat_w / 2, self.view.height - 10, COL_AXIS, axis_font, anchor="middle", weight="bold"
        )

    def _compute(self):
        self._box.xmin, self._box.xmax = 0, self.table.shape[1]
        self._box.ymin, self._box.ymax = 0, self.table.shape[0]


custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_SOFT,
    colors=IMPRINT_PALETTE,
    title_font_size=60,
    label_font_size=44,
    major_label_font_size=40,
    legend_font_size=40,
    value_font_size=36,
    stroke_width=3,
)

chart = ClusteredHeatmap(
    width=2400,
    height=2400,
    style=custom_style,
    title="heatmap-clustered · python · pygal · anyplot.ai",
    table=table,
    row_linkage=row_linkage,
    col_linkage=col_linkage,
    show_legend=False,
    show_x_labels=False,
    show_y_labels=False,
    margin=40,
)
chart.add("", [0])

chart.render_to_png(f"plot-{THEME}.png")

chart_svg = chart.render(is_unicode=True)
if isinstance(chart_svg, bytes):
    chart_svg = chart_svg.decode("utf-8")

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(
        f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>heatmap-clustered - pygal</title>
    <style>
        body {{ margin: 0; display: flex; justify-content: center; align-items: center; min-height: 100vh; background: {PAGE_BG}; }}
        .chart {{ max-width: 100%; height: auto; }}
    </style>
</head>
<body>
    <figure class="chart">
        {chart_svg}
    </figure>
</body>
</html>
"""
    )
