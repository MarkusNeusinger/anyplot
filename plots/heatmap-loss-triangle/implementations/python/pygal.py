""" pyplots.ai
heatmap-loss-triangle: Actuarial Loss Development Triangle
Library: pygal 3.1.0 | Python 3.14.3
Quality: 88/100 | Created: 2026-03-09
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
        self.actual_colormap = kwargs.pop("actual_colormap", [])
        self.projected_colormap = kwargs.pop("projected_colormap", [])
        super().__init__(*args, **kwargs)

    def _interpolate_color(self, value, min_val, max_val, colormap):
        if max_val == min_val:
            return colormap[len(colormap) // 2]
        normalized = max(0, min(1, (value - min_val) / (max_val - min_val)))
        pos = normalized * (len(colormap) - 1)
        idx1 = int(pos)
        idx2 = min(idx1 + 1, len(colormap) - 1)
        frac = pos - idx1
        c1, c2 = colormap[idx1], colormap[idx2]
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
        label_margin_bottom = 10

        available_width = plot_width - label_margin_left - label_margin_right
        available_height = plot_height - label_margin_top - label_margin_bottom

        cell_width = available_width / n_cols
        cell_height = available_height / (n_rows + 1.15)
        gap = 3

        grid_width = n_cols * (cell_width + gap) - gap
        grid_height = n_rows * (cell_height + gap) - gap

        x_offset = self.view.x(0) + label_margin_left + (available_width - grid_width) / 2
        y_offset = self.view.y(n_rows) + label_margin_top + (available_height - grid_height - cell_height * 1.05) / 2

        plot_node = self.nodes["plot"]

        # Column header title
        col_font_size = min(40, int(cell_width * 0.50))
        header_title_y = y_offset - 80
        header_title_x = x_offset + grid_width / 2
        text_node = self.svg.node(plot_node, "text", x=header_title_x, y=header_title_y)
        text_node.set("text-anchor", "middle")
        text_node.set("fill", "#555555")
        text_node.set("style", f"font-size:{col_font_size + 4}px;font-weight:600;font-family:sans-serif")
        text_node.text = "Development Period (Years)"

        # Column headers (development periods)
        for j, label in enumerate(self.col_labels):
            cx = x_offset + j * (cell_width + gap) + cell_width / 2
            cy = y_offset - 18
            text_node = self.svg.node(plot_node, "text", x=cx, y=cy)
            text_node.set("text-anchor", "middle")
            text_node.set("fill", "#333333")
            text_node.set("style", f"font-size:{col_font_size}px;font-weight:700;font-family:sans-serif")
            text_node.text = str(label)

        # Row labels (accident years)
        row_font_size = min(40, int(cell_height * 0.55))
        for i, label in enumerate(self.row_labels):
            ry = y_offset + i * (cell_height + gap) + cell_height / 2 + row_font_size * 0.35
            rx = x_offset - 20
            text_node = self.svg.node(plot_node, "text", x=rx, y=ry)
            text_node.set("text-anchor", "end")
            text_node.set("fill", "#333333")
            text_node.set("style", f"font-size:{row_font_size}px;font-weight:600;font-family:sans-serif")
            text_node.text = str(label)

        # Row label title (rotated)
        row_title_x = x_offset - 260
        row_title_y = y_offset + grid_height / 2
        text_node = self.svg.node(plot_node, "text", x=row_title_x, y=row_title_y)
        text_node.set("text-anchor", "middle")
        text_node.set("fill", "#555555")
        text_node.set("style", f"font-size:{col_font_size + 4}px;font-weight:600;font-family:sans-serif")
        text_node.set("transform", f"rotate(-90, {row_title_x}, {row_title_y})")
        text_node.text = "Accident Year"

        # Draw cells with larger value font for better readability
        value_font_size = min(42, int(min(cell_width, cell_height) * 0.50))
        for i in range(n_rows):
            for j in range(n_cols):
                value = self.matrix_data[i][j]
                if value is None:
                    continue

                is_proj = self.projected_mask[i][j]
                cmap = self.projected_colormap if is_proj else self.actual_colormap
                color = self._interpolate_color(value, min_val, max_val, cmap)
                text_color = self._get_text_color(color)

                cx = x_offset + j * (cell_width + gap)
                cy = y_offset + i * (cell_height + gap)

                # Cell group for tooltip association
                cell_group = self.svg.node(plot_node, "g", class_="cell")
                rect = self.svg.node(cell_group, "rect", x=cx, y=cy, width=cell_width, height=cell_height, rx=3, ry=3)
                rect.set("fill", color)
                rect.set("stroke", "#ffffff")
                rect.set("stroke-width", "2")

                # Pygal tooltip data for SVG interactivity
                label = "Projected" if is_proj else "Actual"
                yr = self.row_labels[i] if i < len(self.row_labels) else ""
                pd = self.col_labels[j] if j < len(self.col_labels) else ""
                self._tooltip_data(
                    cell_group,
                    self.value_formatter(value),
                    cx + cell_width / 2,
                    cy + cell_height / 2,
                    xlabel=f"AY {yr} / Dev {pd} ({label})",
                )

                # Dashed border for projected cells
                if is_proj:
                    border = self.svg.node(
                        cell_group, "rect", x=cx + 2, y=cy + 2, width=cell_width - 4, height=cell_height - 4, rx=2, ry=2
                    )
                    border.set("fill", "none")
                    border.set("stroke", "#e65100")
                    border.set("stroke-width", "2")
                    border.set("stroke-dasharray", "6,4")
                    border.set("opacity", "0.5")

                # Value annotation using pygal's value_formatter
                formatted = self.value_formatter(value)
                tx = cx + cell_width / 2
                ty = cy + cell_height / 2 + value_font_size * 0.35
                text_node = self.svg.node(cell_group, "text", x=tx, y=ty)
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

        # Evaluation date diagonal using pygal's svg.line() path helper
        diag_coords = []
        for k in range(n_rows + 1):
            row_idx = k
            col_idx = n_rows - k
            if 0 <= col_idx <= n_cols and 0 <= row_idx <= n_rows:
                dx = x_offset + col_idx * (cell_width + gap) - gap / 2
                dy = y_offset + row_idx * (cell_height + gap) - gap / 2
                diag_coords.append((dx, dy))

        if len(diag_coords) > 1:
            diag_node = self.svg.line(plot_node, diag_coords, close=False, class_="eval-date-line")
            diag_node.set("fill", "none")
            diag_node.set("stroke", "#e74c3c")
            diag_node.set("stroke-width", "4")
            diag_node.set("stroke-dasharray", "12,6")
            diag_node.set("opacity", "0.85")

        # Development factors row below the grid
        df_y = y_offset + grid_height + 38
        df_font = min(34, int(cell_width * 0.38))
        if self.dev_factors:
            sep_y = y_offset + grid_height + 16
            sep_line = self.svg.node(plot_node, "line", x1=x_offset, y1=sep_y, x2=x_offset + grid_width, y2=sep_y)
            sep_line.set("stroke", "#cccccc")
            sep_line.set("stroke-width", "2")

            text_node = self.svg.node(plot_node, "text", x=x_offset - 20, y=df_y + df_font * 0.35)
            text_node.set("text-anchor", "end")
            text_node.set("fill", "#666666")
            text_node.set("style", f"font-size:{df_font}px;font-weight:700;font-family:sans-serif")
            text_node.text = "Dev Factor"

            for j, factor in enumerate(self.dev_factors):
                if factor is None:
                    continue
                fx = x_offset + j * (cell_width + gap) + cell_width / 2
                text_node = self.svg.node(plot_node, "text", x=fx, y=df_y + df_font * 0.35)
                text_node.set("text-anchor", "middle")
                text_node.set("fill", "#666666")
                text_node.set("style", f"font-size:{df_font}px;font-weight:500;font-family:sans-serif")
                text_node.text = f"{factor:.3f}"

        # Colorbar with SVG gradient for smoother rendering
        cb_width = 50
        cb_height = grid_height * 0.80
        cb_x = x_offset + grid_width + 55
        cb_y = y_offset + (grid_height - cb_height) / 2

        defs = self.svg.node(plot_node, "defs")
        gradient = self.svg.node(defs, "linearGradient", id="cb-gradient", x1="0", y1="0", x2="0", y2="1")
        for frac_i in range(21):
            frac = frac_i / 20.0
            val = max_val - (max_val - min_val) * frac
            color = self._interpolate_color(val, min_val, max_val, self.actual_colormap)
            stop = self.svg.node(gradient, "stop", offset=f"{frac * 100}%")
            stop.set("stop-color", color)

        cb_rect = self.svg.node(plot_node, "rect", x=cb_x, y=cb_y, width=cb_width, height=cb_height, rx=4, ry=4)
        cb_rect.set("fill", "url(#cb-gradient)")
        cb_rect.set("stroke", "#888888")
        cb_rect.set("stroke-width", "1.5")

        cb_label_size = 30
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
            text_node.text = self.value_formatter(val)

        cb_title_node = self.svg.node(plot_node, "text", x=cb_x + cb_width / 2, y=cb_y - 22)
        cb_title_node.set("text-anchor", "middle")
        cb_title_node.set("fill", "#333333")
        cb_title_node.set("style", f"font-size:{cb_label_size + 2}px;font-weight:600;font-family:sans-serif")
        cb_title_node.text = "Cumulative ($k)"

        # Legend: actual vs projected vs evaluation date
        legend_font = 30
        legend_y = df_y + df_font + 18 if self.dev_factors else y_offset + grid_height + 38
        legend_total_width = 780
        legend_x = x_offset + (grid_width - legend_total_width) / 2

        # Actual swatch (blue)
        self.svg.node(
            plot_node, "rect", x=legend_x, y=legend_y, width=34, height=24, fill="#4a90d9", stroke="#333333", rx=3, ry=3
        )
        text_node = self.svg.node(plot_node, "text", x=legend_x + 46, y=legend_y + 19)
        text_node.set("fill", "#333333")
        text_node.set("style", f"font-size:{legend_font}px;font-weight:600;font-family:sans-serif")
        text_node.text = "Actual"

        # Projected swatch (orange with dashed inner border)
        proj_x = legend_x + 200
        self.svg.node(
            plot_node, "rect", x=proj_x, y=legend_y, width=34, height=24, fill="#ffa726", stroke="#333333", rx=3, ry=3
        )
        proj_border = self.svg.node(
            plot_node, "rect", x=proj_x + 3, y=legend_y + 3, width=28, height=18, fill="none", rx=2, ry=2
        )
        proj_border.set("stroke", "#e65100")
        proj_border.set("stroke-width", "1.5")
        proj_border.set("stroke-dasharray", "4,3")
        text_node = self.svg.node(plot_node, "text", x=proj_x + 46, y=legend_y + 19)
        text_node.set("fill", "#333333")
        text_node.set("style", f"font-size:{legend_font}px;font-weight:600;font-family:sans-serif")
        text_node.text = "Projected (IBNR)"

        # Evaluation date line swatch
        eval_x = proj_x + 360
        line_y = legend_y + 12
        line_node = self.svg.node(plot_node, "line", x1=eval_x, y1=line_y, x2=eval_x + 44, y2=line_y)
        line_node.set("stroke", "#e74c3c")
        line_node.set("stroke-width", "3")
        line_node.set("stroke-dasharray", "8,4")
        text_node = self.svg.node(plot_node, "text", x=eval_x + 56, y=legend_y + 19)
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

# Sequential blue colormap (light to dark) for actual values
actual_colormap = ["#eef5fc", "#c6dbef", "#9ecae1", "#6baed6", "#4292c6", "#2171b5", "#08519c", "#08306b"]
# Warm orange-amber colormap for projected values
projected_colormap = ["#fff3e0", "#ffe0b2", "#ffcc80", "#ffb74d", "#ffa726", "#fb8c00", "#ef6c00", "#e65100"]

# Style using pygal's Style configuration system
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#4a90d9", "#ffa726", "#e74c3c"),
    title_font_size=56,
    legend_font_size=30,
    label_font_size=34,
    value_font_size=30,
    tooltip_font_size=28,
    font_family="sans-serif",
)

# Chart using pygal configuration attributes
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
    actual_colormap=actual_colormap,
    projected_colormap=projected_colormap,
    value_formatter=lambda x: f"{x:,.0f}",
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
