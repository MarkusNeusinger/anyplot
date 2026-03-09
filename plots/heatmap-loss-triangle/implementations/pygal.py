""" pyplots.ai
heatmap-loss-triangle: Actuarial Loss Development Triangle
Library: pygal 3.1.0 | Python 3.14.3
Quality: 86/100 | Created: 2026-03-09
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


class LossTriangleHeatmap(Graph):
    _series_margin = 0

    def __init__(self, *args, **kwargs):
        self.matrix_data = kwargs.pop("matrix_data", [])
        self.projected_mask = kwargs.pop("projected_mask", [])
        self.row_labels = kwargs.pop("row_labels", [])
        self.col_labels = kwargs.pop("col_labels", [])
        self.dev_factors = kwargs.pop("dev_factors", [])
        self.colormap = kwargs.pop("colormap", [])
        super().__init__(*args, **kwargs)

    def _interpolate_color(self, value, min_val, max_val, colormap=None):
        cmap = colormap or self.colormap
        if max_val == min_val:
            return cmap[len(cmap) // 2]
        normalized = max(0, min(1, (value - min_val) / (max_val - min_val)))
        pos = normalized * (len(cmap) - 1)
        idx1 = int(pos)
        idx2 = min(idx1 + 1, len(cmap) - 1)
        frac = pos - idx1
        c1, c2 = cmap[idx1], cmap[idx2]
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

        n_rows = len(self.matrix_data)
        n_cols = len(self.matrix_data[0])

        all_values = [v for row in self.matrix_data for v in row if v is not None]
        min_val = min(all_values)
        max_val = max(all_values)

        plot_width = self.view.width
        plot_height = self.view.height

        label_margin_left = 380
        label_margin_right = 320
        label_margin_top = 130
        label_margin_bottom = 30

        available_width = plot_width - label_margin_left - label_margin_right
        available_height = plot_height - label_margin_top - label_margin_bottom

        cell_width = available_width / n_cols
        cell_height = available_height / (n_rows + 1.3)
        gap = 3

        grid_width = n_cols * (cell_width + gap) - gap
        grid_height = n_rows * (cell_height + gap) - gap

        x_offset = self.view.x(0) + label_margin_left + (available_width - grid_width) / 2
        y_offset = self.view.y(n_rows) + label_margin_top + (available_height - grid_height - cell_height * 1.2) / 2

        plot_node = self.nodes["plot"]
        hm_group = self.svg.node(plot_node, class_="loss-triangle-heatmap")

        # Column header title (above column numbers with more spacing)
        col_font_size = min(38, int(cell_width * 0.48))
        header_title_y = y_offset - 80
        header_title_x = x_offset + grid_width / 2
        text_node = self.svg.node(hm_group, "text", x=header_title_x, y=header_title_y)
        text_node.set("text-anchor", "middle")
        text_node.set("fill", "#555555")
        text_node.set("style", f"font-size:{col_font_size + 4}px;font-weight:600;font-family:sans-serif")
        text_node.text = "Development Period (Years)"

        # Column headers (development periods)
        for j, label in enumerate(self.col_labels):
            cx = x_offset + j * (cell_width + gap) + cell_width / 2
            cy = y_offset - 18
            text_node = self.svg.node(hm_group, "text", x=cx, y=cy)
            text_node.set("text-anchor", "middle")
            text_node.set("fill", "#333333")
            text_node.set("style", f"font-size:{col_font_size}px;font-weight:700;font-family:sans-serif")
            text_node.text = str(label)

        # Row labels (accident years)
        row_font_size = min(38, int(cell_height * 0.52))
        for i, label in enumerate(self.row_labels):
            ry = y_offset + i * (cell_height + gap) + cell_height / 2 + row_font_size * 0.35
            rx = x_offset - 20
            text_node = self.svg.node(hm_group, "text", x=rx, y=ry)
            text_node.set("text-anchor", "end")
            text_node.set("fill", "#333333")
            text_node.set("style", f"font-size:{row_font_size}px;font-weight:600;font-family:sans-serif")
            text_node.text = str(label)

        # Row label title (rotated)
        row_title_x = x_offset - 260
        row_title_y = y_offset + grid_height / 2
        text_node = self.svg.node(hm_group, "text", x=row_title_x, y=row_title_y)
        text_node.set("text-anchor", "middle")
        text_node.set("fill", "#555555")
        text_node.set("style", f"font-size:{col_font_size + 4}px;font-weight:600;font-family:sans-serif")
        text_node.set("transform", f"rotate(-90, {row_title_x}, {row_title_y})")
        text_node.text = "Accident Year"

        # Projected cells use a warm orange-amber colormap for clear distinction
        projected_colormap = ["#fff3e0", "#ffe0b2", "#ffcc80", "#ffb74d", "#ffa726", "#fb8c00", "#ef6c00", "#e65100"]

        # Draw cells
        value_font_size = min(38, int(min(cell_width, cell_height) * 0.44))
        for i in range(n_rows):
            for j in range(n_cols):
                value = self.matrix_data[i][j]
                if value is None:
                    continue

                is_proj = self.projected_mask[i][j]
                if is_proj:
                    color = self._interpolate_color(value, min_val, max_val, projected_colormap)
                else:
                    color = self._interpolate_color(value, min_val, max_val)
                text_color = self._get_text_color(color)

                cx = x_offset + j * (cell_width + gap)
                cy = y_offset + i * (cell_height + gap)

                rect = self.svg.node(hm_group, "rect", x=cx, y=cy, width=cell_width, height=cell_height, rx=3, ry=3)
                rect.set("fill", color)
                rect.set("stroke", "#ffffff")
                rect.set("stroke-width", "2")

                # Projected cells get a dashed border for additional distinction
                if is_proj:
                    border = self.svg.node(
                        hm_group, "rect", x=cx + 2, y=cy + 2, width=cell_width - 4, height=cell_height - 4, rx=2, ry=2
                    )
                    border.set("fill", "none")
                    border.set("stroke", "#e65100")
                    border.set("stroke-width", "2")
                    border.set("stroke-dasharray", "6,4")
                    border.set("opacity", "0.5")

                # Value annotation
                formatted = f"{value:,.0f}"
                tx = cx + cell_width / 2
                ty = cy + cell_height / 2 + value_font_size * 0.35
                text_node = self.svg.node(hm_group, "text", x=tx, y=ty)
                text_node.set("text-anchor", "middle")
                text_node.set("fill", text_color)
                font_weight = "500" if not is_proj else "400"
                font_style = "normal" if not is_proj else "italic"
                text_node.set(
                    "style",
                    f"font-size:{value_font_size}px;font-weight:{font_weight};"
                    f"font-style:{font_style};font-family:sans-serif",
                )
                text_node.text = formatted

        # Diagonal line (latest evaluation date) - draw a visible line along the boundary
        diag_points = []
        for k in range(n_rows + 1):
            row_idx = k
            col_idx = n_rows - k
            if col_idx >= 0 and row_idx <= n_rows:
                dx = x_offset + col_idx * (cell_width + gap) - gap / 2
                dy = y_offset + row_idx * (cell_height + gap) - gap / 2
                diag_points.append(f"{dx},{dy}")
        if len(diag_points) > 1:
            polyline = self.svg.node(hm_group, "polyline")
            polyline.set("points", " ".join(diag_points))
            polyline.set("fill", "none")
            polyline.set("stroke", "#e74c3c")
            polyline.set("stroke-width", "4")
            polyline.set("stroke-dasharray", "12,6")
            polyline.set("opacity", "0.8")

        # Development factors row below the grid
        if self.dev_factors:
            # Separator line between grid and dev factors
            sep_y = y_offset + grid_height + 16
            sep_line = self.svg.node(hm_group, "line", x1=x_offset, y1=sep_y, x2=x_offset + grid_width, y2=sep_y)
            sep_line.set("stroke", "#cccccc")
            sep_line.set("stroke-width", "2")

            df_y = y_offset + grid_height + 38
            df_font = min(32, int(cell_width * 0.36))

            # Label
            text_node = self.svg.node(hm_group, "text", x=x_offset - 20, y=df_y + df_font * 0.35)
            text_node.set("text-anchor", "end")
            text_node.set("fill", "#666666")
            text_node.set("style", f"font-size:{df_font}px;font-weight:700;font-family:sans-serif")
            text_node.text = "Dev Factor"

            for j, factor in enumerate(self.dev_factors):
                if factor is None:
                    continue
                fx = x_offset + j * (cell_width + gap) + cell_width / 2
                text_node = self.svg.node(hm_group, "text", x=fx, y=df_y + df_font * 0.35)
                text_node.set("text-anchor", "middle")
                text_node.set("fill", "#666666")
                text_node.set("style", f"font-size:{df_font}px;font-weight:500;font-family:sans-serif")
                text_node.text = f"{factor:.3f}"

        # Colorbar
        cb_width = 45
        cb_height = grid_height * 0.75
        cb_x = x_offset + grid_width + 60
        cb_y = y_offset + (grid_height - cb_height) / 2

        n_segments = 50
        seg_height = cb_height / n_segments
        for si in range(n_segments):
            seg_val = max_val - (max_val - min_val) * si / (n_segments - 1)
            seg_color = self._interpolate_color(seg_val, min_val, max_val)
            sy = cb_y + si * seg_height
            self.svg.node(hm_group, "rect", x=cb_x, y=sy, width=cb_width, height=seg_height + 1, fill=seg_color)

        self.svg.node(hm_group, "rect", x=cb_x, y=cb_y, width=cb_width, height=cb_height, fill="none", stroke="#999999")

        cb_label_size = 28
        for frac, val in [(0.0, max_val), (0.5, (min_val + max_val) / 2), (1.0, min_val)]:
            ty = cb_y + cb_height * frac + cb_label_size * 0.35
            text_node = self.svg.node(hm_group, "text", x=cb_x + cb_width + 12, y=ty)
            text_node.set("fill", "#333333")
            text_node.set("style", f"font-size:{cb_label_size}px;font-family:sans-serif")
            text_node.text = f"{val:,.0f}"

        cb_title_node = self.svg.node(hm_group, "text", x=cb_x + cb_width / 2, y=cb_y - 20)
        cb_title_node.set("text-anchor", "middle")
        cb_title_node.set("fill", "#333333")
        cb_title_node.set("style", f"font-size:{cb_label_size + 4}px;font-weight:bold;font-family:sans-serif")
        cb_title_node.text = "Cumulative ($k)"

        # Legend: actual vs projected vs evaluation date (below dev factor row)
        legend_font = 28
        legend_y = df_y + df_font + 14 if self.dev_factors else y_offset + grid_height + 38
        legend_total_width = 720
        legend_x = x_offset + (grid_width - legend_total_width) / 2

        # Actual swatch (blue)
        self.svg.node(
            hm_group, "rect", x=legend_x, y=legend_y, width=32, height=22, fill="#4a90d9", stroke="#333333", rx=3, ry=3
        )
        text_node = self.svg.node(hm_group, "text", x=legend_x + 44, y=legend_y + 18)
        text_node.set("fill", "#333333")
        text_node.set("style", f"font-size:{legend_font}px;font-weight:600;font-family:sans-serif")
        text_node.text = "Actual"

        # Projected swatch (orange)
        proj_x = legend_x + 190
        self.svg.node(
            hm_group, "rect", x=proj_x, y=legend_y, width=32, height=22, fill="#ffa726", stroke="#333333", rx=3, ry=3
        )
        text_node = self.svg.node(hm_group, "text", x=proj_x + 44, y=legend_y + 18)
        text_node.set("fill", "#333333")
        text_node.set("style", f"font-size:{legend_font}px;font-weight:600;font-family:sans-serif")
        text_node.text = "Projected (IBNR)"

        # Evaluation date line swatch
        eval_x = proj_x + 340
        line_y = legend_y + 11
        line_node = self.svg.node(hm_group, "line", x1=eval_x, y1=line_y, x2=eval_x + 40, y2=line_y)
        line_node.set("stroke", "#e74c3c")
        line_node.set("stroke-width", "3")
        line_node.set("stroke-dasharray", "8,4")
        text_node = self.svg.node(hm_group, "text", x=eval_x + 52, y=legend_y + 18)
        text_node.set("fill", "#333333")
        text_node.set("style", f"font-size:{legend_font}px;font-weight:600;font-family:sans-serif")
        text_node.text = "Evaluation Date"

    def _compute(self):
        n_rows = len(self.matrix_data) if self.matrix_data else 1
        n_cols = len(self.matrix_data[0]) if self.matrix_data and self.matrix_data[0] else 1
        self._box.xmin = 0
        self._box.xmax = n_cols
        self._box.ymin = 0
        self._box.ymax = n_rows


# Data: Cumulative paid claims triangle (in thousands)
np.random.seed(42)

accident_years = list(range(2015, 2025))
development_periods = list(range(1, 11))
n_years = len(accident_years)
n_periods = len(development_periods)

# Base cumulative development pattern (realistic chain-ladder shape)
base_ultimate = np.array([4200, 4500, 4800, 5100, 5400, 5700, 6000, 6300, 6600, 7000], dtype=float)
# Development pattern: percentage of ultimate at each period
dev_pattern = np.array([0.15, 0.35, 0.52, 0.66, 0.78, 0.87, 0.93, 0.97, 0.99, 1.00])

# Build full triangle
triangle = np.zeros((n_years, n_periods))
is_projected = [[False] * n_periods for _ in range(n_years)]

for i in range(n_years):
    for j in range(n_periods):
        base_val = base_ultimate[i] * dev_pattern[j]
        noise = np.random.normal(0, base_val * 0.03)
        triangle[i][j] = round(base_val + noise, 0)

        # Actual data: row + col index < n_years (upper-left triangle)
        if i + j >= n_years:
            is_projected[i][j] = True

# Convert to list of lists
matrix_data = triangle.tolist()

# Calculate age-to-age development factors (weighted average across actual data)
dev_factors = []
for j in range(n_periods - 1):
    numerator = 0.0
    denominator = 0.0
    for i in range(n_years):
        if not is_projected[i][j] and not is_projected[i][j + 1]:
            numerator += triangle[i][j + 1]
            denominator += triangle[i][j]
    if denominator > 0:
        dev_factors.append(numerator / denominator)
    else:
        dev_factors.append(None)
dev_factors.append(None)  # No factor for last period

# Sequential blue colormap (light to dark)
sequential_colormap = ["#eef5fc", "#c6dbef", "#9ecae1", "#6baed6", "#4292c6", "#2171b5", "#08519c", "#08306b"]

# Style
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998",),
    title_font_size=56,
    legend_font_size=32,
    label_font_size=32,
    value_font_size=28,
    font_family="sans-serif",
)

# Chart
chart = LossTriangleHeatmap(
    width=4800,
    height=2700,
    style=custom_style,
    title="heatmap-loss-triangle \u00b7 pygal \u00b7 pyplots.ai",
    matrix_data=matrix_data,
    projected_mask=is_projected,
    row_labels=[str(y) for y in accident_years],
    col_labels=[str(p) for p in development_periods],
    dev_factors=dev_factors,
    colormap=sequential_colormap,
    show_legend=False,
    margin=100,
    margin_top=200,
    margin_bottom=50,
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
    <title>heatmap-loss-triangle - pygal</title>
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
