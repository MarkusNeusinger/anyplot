""" pyplots.ai
heatmap-cohort-retention: Cohort Retention Heatmap
Library: pygal 3.1.0 | Python 3.14.3
Quality: 85/100 | Created: 2026-03-16
"""

import sys

import numpy as np


# Import pygal avoiding name collision with this filename
_cwd = sys.path[0] if sys.path[0] else "."
if _cwd in sys.path:
    sys.path.remove(_cwd)

from pygal.graph.graph import Graph  # noqa: E402
from pygal.style import Style  # noqa: E402


sys.path.insert(0, _cwd)


class CohortRetentionHeatmap(Graph):
    _series_margin = 0

    def __init__(self, *args, **kwargs):
        self.matrix_data = kwargs.pop("matrix_data", [])
        self.row_labels = kwargs.pop("row_labels", [])
        self.col_labels = kwargs.pop("col_labels", [])
        self.cohort_sizes = kwargs.pop("cohort_sizes", [])
        self.colormap = kwargs.pop("colormap", [])
        super().__init__(*args, **kwargs)

    def _interpolate_color(self, value, min_val, max_val):
        if max_val == min_val:
            return self.colormap[len(self.colormap) // 2]
        normalized = max(0, min(1, (value - min_val) / (max_val - min_val)))
        pos = normalized * (len(self.colormap) - 1)
        idx1 = int(pos)
        idx2 = min(idx1 + 1, len(self.colormap) - 1)
        frac = pos - idx1
        c1, c2 = self.colormap[idx1], self.colormap[idx2]
        r = int(int(c1[1:3], 16) + (int(c2[1:3], 16) - int(c1[1:3], 16)) * frac)
        g = int(int(c1[3:5], 16) + (int(c2[3:5], 16) - int(c1[3:5], 16)) * frac)
        b = int(int(c1[5:7], 16) + (int(c2[5:7], 16) - int(c1[5:7], 16)) * frac)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _get_text_color(self, bg_color):
        r = int(bg_color[1:3], 16)
        g = int(bg_color[3:5], 16)
        b = int(bg_color[5:7], 16)
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        return "#ffffff" if brightness < 140 else "#222222"

    def _plot(self):
        if not self.matrix_data:
            return

        # Inject CSS to suppress pygal's default focus/active/hover outlines
        defs_node = self.svg.node(self.svg.root, "defs")
        style_node = self.svg.node(defs_node, "style", type="text/css")
        style_node.text = (
            ".cell rect, .cell { outline: none !important; stroke-opacity: 1; } "
            ".cell:focus rect, .cell:hover rect, .cell:active rect, "
            ".active .cell rect, .cell .active rect "
            "{ outline: none !important; } "
            "g.cell:focus, g.cell:active { outline: none; } "
            ".activate-serie, .active .reactive { outline: none !important; }"
        )

        n_rows = len(self.matrix_data)
        n_cols = max(len(row) for row in self.matrix_data)

        # Find min/max excluding None and period 0 (always 100%)
        non_null = [v for row in self.matrix_data for v in row if v is not None]
        min_val = min(non_null)
        max_val = max(non_null)

        plot_width = self.view.width
        plot_height = self.view.height

        label_margin_left = 460
        label_margin_right = 280
        label_margin_top = 130
        label_margin_bottom = 10

        available_width = plot_width - label_margin_left - label_margin_right
        available_height = plot_height - label_margin_top - label_margin_bottom

        cell_width = available_width / n_cols
        cell_height = available_height / (n_rows + 0.5)
        gap = 3

        grid_width = n_cols * (cell_width + gap) - gap
        grid_height = n_rows * (cell_height + gap) - gap

        x_offset = self.view.x(0) + label_margin_left + (available_width - grid_width) / 2
        y_offset = self.view.y(n_rows) + label_margin_top + (available_height - grid_height - cell_height * 0.5) / 2

        plot_node = self.nodes["plot"]

        # Column headers title
        col_font_size = min(38, int(cell_width * 0.48))
        header_title_y = y_offset - 80
        header_title_x = x_offset + grid_width / 2
        text_node = self.svg.node(plot_node, "text", x=header_title_x, y=header_title_y)
        text_node.set("text-anchor", "middle")
        text_node.set("fill", "#555555")
        text_node.set("style", f"font-size:{col_font_size + 4}px;font-weight:600;font-family:sans-serif")
        text_node.text = "Months Since Signup"

        # Column headers
        for j, label in enumerate(self.col_labels):
            cx = x_offset + j * (cell_width + gap) + cell_width / 2
            cy = y_offset - 18
            text_node = self.svg.node(plot_node, "text", x=cx, y=cy)
            text_node.set("text-anchor", "middle")
            text_node.set("fill", "#333333")
            text_node.set("style", f"font-size:{col_font_size}px;font-weight:700;font-family:sans-serif")
            text_node.text = str(label)

        # Row labels with cohort sizes
        row_font_size = min(36, int(cell_height * 0.50))
        size_font_size = int(row_font_size * 0.88)
        for i, label in enumerate(self.row_labels):
            ry = y_offset + i * (cell_height + gap) + cell_height / 2
            rx = x_offset - 20

            # Cohort label
            text_node = self.svg.node(plot_node, "text", x=rx, y=ry + row_font_size * 0.15)
            text_node.set("text-anchor", "end")
            text_node.set("fill", "#333333")
            text_node.set("style", f"font-size:{row_font_size}px;font-weight:600;font-family:sans-serif")
            text_node.text = str(label)

            # Cohort size below label
            if i < len(self.cohort_sizes):
                text_node = self.svg.node(plot_node, "text", x=rx, y=ry + row_font_size * 0.15 + size_font_size + 4)
                text_node.set("text-anchor", "end")
                text_node.set("fill", "#888888")
                text_node.set("style", f"font-size:{size_font_size}px;font-weight:400;font-family:sans-serif")
                text_node.text = f"n={self.cohort_sizes[i]:,}"

        # Row label title (rotated)
        row_title_x = x_offset - 340
        row_title_y = y_offset + grid_height / 2
        text_node = self.svg.node(plot_node, "text", x=row_title_x, y=row_title_y)
        text_node.set("text-anchor", "middle")
        text_node.set("fill", "#555555")
        text_node.set("style", f"font-size:{col_font_size + 4}px;font-weight:600;font-family:sans-serif")
        text_node.set("transform", f"rotate(-90, {row_title_x}, {row_title_y})")
        text_node.text = "Signup Cohort"

        # Draw cells
        value_font_size = min(38, int(min(cell_width, cell_height) * 0.46))
        for i in range(n_rows):
            for j in range(len(self.matrix_data[i])):
                value = self.matrix_data[i][j]
                if value is None:
                    continue

                color = self._interpolate_color(value, min_val, max_val)
                text_color = self._get_text_color(color)

                cx = x_offset + j * (cell_width + gap)
                cy = y_offset + i * (cell_height + gap)

                cell_group = self.svg.node(plot_node, "g", class_="cell")
                cell_group.set("style", "outline:none;stroke:none;")
                rect = self.svg.node(cell_group, "rect", x=cx, y=cy, width=cell_width, height=cell_height, rx=3, ry=3)
                rect.set("fill", color)
                rect.set("stroke", "#ffffff")
                rect.set("stroke-width", "2")
                rect.set("style", "outline:none;")

                # Tooltip
                cohort_label = self.row_labels[i] if i < len(self.row_labels) else ""
                period_label = self.col_labels[j] if j < len(self.col_labels) else ""
                self._tooltip_data(
                    cell_group,
                    f"{value:.1f}%",
                    cx + cell_width / 2,
                    cy + cell_height / 2,
                    xlabel=f"{cohort_label} / {period_label}",
                )

                # Value text
                tx = cx + cell_width / 2
                ty = cy + cell_height / 2 + value_font_size * 0.35
                text_node = self.svg.node(cell_group, "text", x=tx, y=ty)
                text_node.set("text-anchor", "middle")
                text_node.set("fill", text_color)
                text_node.set("style", f"font-size:{value_font_size}px;font-weight:500;font-family:sans-serif")
                text_node.text = f"{value:.0f}%"

        # Colorbar
        cb_width = 46
        cb_height = grid_height * 0.75
        cb_x = x_offset + grid_width + 50
        cb_y = y_offset + (grid_height - cb_height) / 2

        defs = self.svg.node(plot_node, "defs")
        gradient = self.svg.node(defs, "linearGradient", id="cb-gradient", x1="0", y1="0", x2="0", y2="1")
        for frac_i in range(21):
            frac = frac_i / 20.0
            val = max_val - (max_val - min_val) * frac
            color = self._interpolate_color(val, min_val, max_val)
            stop = self.svg.node(gradient, "stop", offset=f"{frac * 100}%")
            stop.set("stop-color", color)

        cb_rect = self.svg.node(plot_node, "rect", x=cb_x, y=cb_y, width=cb_width, height=cb_height, rx=4, ry=4)
        cb_rect.set("fill", "url(#cb-gradient)")
        cb_rect.set("stroke", "#999999")
        cb_rect.set("stroke-width", "1.5")

        cb_label_size = 28
        for frac, val in [
            (0.0, max_val),
            (0.25, max_val * 0.75 + min_val * 0.25),
            (0.5, (min_val + max_val) / 2),
            (0.75, max_val * 0.25 + min_val * 0.75),
            (1.0, min_val),
        ]:
            ty = cb_y + cb_height * frac
            tick = self.svg.node(plot_node, "line", x1=cb_x + cb_width, y1=ty, x2=cb_x + cb_width + 8, y2=ty)
            tick.set("stroke", "#666666")
            tick.set("stroke-width", "1.5")
            text_node = self.svg.node(plot_node, "text", x=cb_x + cb_width + 14, y=ty + cb_label_size * 0.35)
            text_node.set("fill", "#333333")
            text_node.set("style", f"font-size:{cb_label_size}px;font-family:sans-serif")
            text_node.text = f"{val:.0f}%"

        cb_title = self.svg.node(plot_node, "text", x=cb_x + cb_width / 2, y=cb_y - 20)
        cb_title.set("text-anchor", "middle")
        cb_title.set("fill", "#333333")
        cb_title.set("style", f"font-size:{cb_label_size + 2}px;font-weight:600;font-family:sans-serif")
        cb_title.text = "Retention %"

    def _compute(self):
        n_rows = len(self.matrix_data) if self.matrix_data else 1
        n_cols = max(len(row) for row in self.matrix_data) if self.matrix_data else 1
        self._box.xmin = 0
        self._box.xmax = n_cols
        self._box.ymin = 0
        self._box.ymax = n_rows


# Data — Monthly signup cohorts with retention rates
np.random.seed(42)

cohort_labels = [
    "Jan 2024",
    "Feb 2024",
    "Mar 2024",
    "Apr 2024",
    "May 2024",
    "Jun 2024",
    "Jul 2024",
    "Aug 2024",
    "Sep 2024",
    "Oct 2024",
]
n_cohorts = len(cohort_labels)
n_max_periods = 10

cohort_sizes = [1200, 1350, 980, 1520, 1100, 1430, 1280, 1050, 1380, 1150]

# Base retention curve that decays over time
base_retention = np.array([100.0, 65.0, 48.0, 40.0, 34.0, 30.0, 27.0, 25.0, 23.5, 22.0])

# Build triangular retention matrix with visible cohort variation
matrix = []
for i in range(n_cohorts):
    n_periods = n_max_periods - i
    row = []
    for j in range(n_periods):
        if j == 0:
            row.append(100.0)
        else:
            # Later cohorts show progressively better retention (product improvements)
            improvement = i * 1.8
            # Apr 2024 (i=3) had a bad onboarding change — worse retention
            if i == 3:
                improvement = -4.0
            noise = np.random.uniform(-2.0, 2.0)
            val = base_retention[j] + improvement + noise
            val = max(5.0, min(100.0, val))
            row.append(round(val, 1))
    matrix.append(row)

period_labels = [f"Month {i}" for i in range(n_max_periods)]

# Sequential green colormap (light to dark)
green_colormap = ["#f7fcf5", "#e5f5e0", "#c7e9c0", "#a1d99b", "#74c476", "#41ab5d", "#238b45", "#005a32"]

# Style
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#238b45",),
    title_font_size=54,
    legend_font_size=28,
    label_font_size=34,
    value_font_size=28,
    tooltip_font_size=26,
    font_family="sans-serif",
)

# Chart
chart = CohortRetentionHeatmap(
    width=4800,
    height=2700,
    style=custom_style,
    title="heatmap-cohort-retention \u00b7 pygal \u00b7 pyplots.ai",
    matrix_data=matrix,
    row_labels=cohort_labels,
    col_labels=period_labels,
    cohort_sizes=cohort_sizes,
    colormap=green_colormap,
    show_legend=False,
    margin=100,
    margin_top=200,
    margin_bottom=30,
    margin_left=120,
    margin_right=120,
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
    <title>heatmap-cohort-retention - pygal</title>
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
