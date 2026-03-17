"""pyplots.ai
heatmap-risk-matrix: Risk Assessment Matrix (Probability vs Impact)
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


sys.path.insert(0, _cwd)


# Risk matrix heatmap built on pygal's Graph base
class RiskMatrixHeatmap(Graph):
    def __init__(self, *args, **kwargs):
        self.risk_scores = kwargs.pop("risk_scores", [])
        self.risk_items = kwargs.pop("risk_items", [])
        self.row_labels = kwargs.pop("row_labels", [])
        self.col_labels = kwargs.pop("col_labels", [])
        self.zone_colors = kwargs.pop("zone_colors", [])
        super().__init__(*args, **kwargs)

    def _get_zone_color(self, score):
        for max_score, color in self.zone_colors:
            if score <= max_score:
                return color
        return self.zone_colors[-1][1]

    def _get_text_color(self, bg_color):
        r, g, b = int(bg_color[1:3], 16), int(bg_color[3:5], 16), int(bg_color[5:7], 16)
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        return "#ffffff" if brightness < 150 else "#333333"

    def _plot(self):
        if not self.risk_scores:
            return

        n_rows = len(self.row_labels)
        n_cols = len(self.col_labels)

        plot_width = self.view.width
        plot_height = self.view.height

        label_margin_left = 520
        label_margin_bottom = 200
        label_margin_top = 80
        label_margin_right = 520

        available_width = plot_width - label_margin_left - label_margin_right
        available_height = plot_height - label_margin_bottom - label_margin_top

        cell_size = min(available_width / n_cols, available_height / n_rows) * 0.94
        gap = cell_size * 0.03

        grid_width = n_cols * (cell_size + gap) - gap
        grid_height = n_rows * (cell_size + gap) - gap

        x_offset = self.view.x(0) + label_margin_left + (available_width - grid_width) / 2
        y_offset = self.view.y(n_rows) + label_margin_top + (available_height - grid_height) / 2

        plot_node = self.nodes["plot"]
        heatmap_group = self.svg.node(plot_node, class_="risk-matrix")

        # Draw cells (row 0 = highest likelihood at top)
        score_font_size = int(cell_size * 0.22)
        zone_font_size = int(cell_size * 0.16)
        for i in range(n_rows):
            for j in range(n_cols):
                row_idx = n_rows - 1 - i
                score = self.risk_scores[row_idx][j]
                color = self._get_zone_color(score)

                x = x_offset + j * (cell_size + gap)
                y = y_offset + i * (cell_size + gap)

                rect = self.svg.node(heatmap_group, "rect", x=x, y=y, width=cell_size, height=cell_size, rx=6, ry=6)
                rect.set("fill", color)
                rect.set("stroke", "#ffffff")
                rect.set("stroke-width", "3")

                text_color = self._get_text_color(color)

                # Risk score number
                text_node = self.svg.node(heatmap_group, "text", x=x + cell_size / 2, y=y + cell_size * 0.35)
                text_node.set("text-anchor", "middle")
                text_node.set("fill", text_color)
                text_node.set("style", f"font-size:{score_font_size}px;font-weight:bold;font-family:sans-serif")
                text_node.text = str(score)

                # Zone label
                if score <= 4:
                    zone_label = "Low"
                elif score <= 9:
                    zone_label = "Medium"
                elif score <= 16:
                    zone_label = "High"
                else:
                    zone_label = "Critical"

                zone_node = self.svg.node(heatmap_group, "text", x=x + cell_size / 2, y=y + cell_size * 0.55)
                zone_node.set("text-anchor", "middle")
                zone_node.set("fill", text_color)
                zone_node.set("opacity", "0.7")
                zone_node.set("style", f"font-size:{zone_font_size}px;font-weight:500;font-family:sans-serif")
                zone_node.text = zone_label

        # Draw risk item markers
        np.random.seed(42)
        marker_font_size = int(cell_size * 0.13)
        marker_radius = int(cell_size * 0.065)
        for item in self.risk_items:
            name = item["name"]
            likelihood = item["likelihood"]
            impact = item["impact"]
            color = item.get("color", "#306998")

            col_idx = impact - 1
            row_display = n_rows - likelihood

            jitter_x = np.random.uniform(-cell_size * 0.2, cell_size * 0.2)
            jitter_y = np.random.uniform(-cell_size * 0.08, cell_size * 0.08)

            cx = x_offset + col_idx * (cell_size + gap) + cell_size / 2 + jitter_x
            cy = y_offset + row_display * (cell_size + gap) + cell_size * 0.78 + jitter_y

            circle = self.svg.node(heatmap_group, "circle", cx=cx, cy=cy, r=marker_radius)
            circle.set("fill", color)
            circle.set("stroke", "#ffffff")
            circle.set("stroke-width", "2.5")
            circle.set("opacity", "0.92")

            label_node = self.svg.node(heatmap_group, "text", x=cx, y=cy + marker_radius + marker_font_size + 4)
            label_node.set("text-anchor", "middle")
            label_node.set("fill", "#1a1a1a")
            label_node.set("style", f"font-size:{marker_font_size}px;font-weight:600;font-family:sans-serif")
            label_node.set("paint-order", "stroke fill")
            label_node.set("stroke", "#ffffff")
            label_node.set("stroke-width", "5")
            label_node.text = name

        # Y-axis labels (Likelihood)
        row_font_size = int(cell_size * 0.18)
        for i in range(n_rows):
            row_idx = n_rows - 1 - i
            label = self.row_labels[row_idx]
            y = y_offset + i * (cell_size + gap) + cell_size / 2

            num_node = self.svg.node(heatmap_group, "text", x=x_offset - 20, y=y + row_font_size * 0.15)
            num_node.set("text-anchor", "end")
            num_node.set("fill", "#333333")
            num_node.set("style", f"font-size:{row_font_size}px;font-weight:600;font-family:sans-serif")
            num_node.text = f"{row_idx + 1}. {label}"

        # X-axis labels (Impact)
        col_font_size = int(cell_size * 0.17)
        for j in range(n_cols):
            label = self.col_labels[j]
            x = x_offset + j * (cell_size + gap) + cell_size / 2
            y = y_offset + grid_height + 50

            num_node = self.svg.node(heatmap_group, "text", x=x, y=y)
            num_node.set("text-anchor", "middle")
            num_node.set("fill", "#333333")
            num_node.set("style", f"font-size:{col_font_size}px;font-weight:600;font-family:sans-serif")
            num_node.text = f"{j + 1}. {label}"

        # Axis titles
        title_font_size = int(cell_size * 0.22)

        # Y-axis title (rotated)
        mid_y = y_offset + grid_height / 2
        y_title = self.svg.node(heatmap_group, "text", x=x_offset - 470, y=mid_y)
        y_title.set("text-anchor", "middle")
        y_title.set("fill", "#333333")
        y_title.set("style", f"font-size:{title_font_size}px;font-weight:bold;font-family:sans-serif")
        y_title.set("transform", f"rotate(-90, {x_offset - 470}, {mid_y})")
        y_title.text = "LIKELIHOOD"

        # X-axis title
        mid_x = x_offset + grid_width / 2
        x_title = self.svg.node(heatmap_group, "text", x=mid_x, y=y_offset + grid_height + 120)
        x_title.set("text-anchor", "middle")
        x_title.set("fill", "#333333")
        x_title.set("style", f"font-size:{title_font_size}px;font-weight:bold;font-family:sans-serif")
        x_title.text = "IMPACT"

        # Legend (right side)
        legend_x = x_offset + grid_width + 60
        legend_y = y_offset + 20
        legend_font = int(cell_size * 0.16)
        legend_box = int(cell_size * 0.15)
        legend_items = [
            ("Low (1\u20134)", "#4caf50"),
            ("Medium (5\u20139)", "#ffc107"),
            ("High (10\u201316)", "#ff9800"),
            ("Critical (20\u201325)", "#d32f2f"),
        ]
        for idx, (label, color) in enumerate(legend_items):
            ly = legend_y + idx * (legend_box + 28)
            rect = self.svg.node(
                heatmap_group, "rect", x=legend_x, y=ly, width=legend_box, height=legend_box, rx=4, ry=4
            )
            rect.set("fill", color)
            rect.set("stroke", "#ffffff")
            rect.set("stroke-width", "2")

            text_node = self.svg.node(heatmap_group, "text", x=legend_x + legend_box + 16, y=ly + legend_box * 0.78)
            text_node.set("fill", "#333333")
            text_node.set("style", f"font-size:{legend_font}px;font-weight:500;font-family:sans-serif")
            text_node.text = label

        # Category legend
        cat_legend_y = legend_y + len(legend_items) * (legend_box + 28) + 50
        cat_title = self.svg.node(heatmap_group, "text", x=legend_x, y=cat_legend_y)
        cat_title.set("fill", "#333333")
        cat_title.set("style", f"font-size:{legend_font}px;font-weight:bold;font-family:sans-serif")
        cat_title.text = "Risk Categories"

        category_colors = {
            "Technical": "#1565c0",
            "Financial": "#6a1b9a",
            "Operational": "#e65100",
            "External": "#2e7d32",
        }
        for idx, (cat, color) in enumerate(category_colors.items()):
            cy = cat_legend_y + 30 + idx * (legend_box + 24)
            circle = self.svg.node(
                heatmap_group, "circle", cx=legend_x + legend_box / 2, cy=cy + legend_box / 2 - 4, r=marker_radius
            )
            circle.set("fill", color)
            circle.set("stroke", "#ffffff")
            circle.set("stroke-width", "2")

            text_node = self.svg.node(heatmap_group, "text", x=legend_x + legend_box + 16, y=cy + legend_box * 0.55)
            text_node.set("fill", "#333333")
            text_node.set("style", f"font-size:{legend_font}px;font-weight:500;font-family:sans-serif")
            text_node.text = cat

    def _compute(self):
        n_rows = len(self.row_labels) if self.row_labels else 1
        n_cols = len(self.col_labels) if self.col_labels else 1
        self._box.xmin = 0
        self._box.xmax = n_cols
        self._box.ymin = 0
        self._box.ymax = n_rows


# Data
likelihood_labels = ["Rare", "Unlikely", "Possible", "Likely", "Almost Certain"]
impact_labels = ["Negligible", "Minor", "Moderate", "Major", "Catastrophic"]

risk_scores = []
for li in range(1, 6):
    row = []
    for im in range(1, 6):
        row.append(li * im)
    risk_scores.append(row)

zone_colors = [(4, "#4caf50"), (9, "#ffc107"), (16, "#ff9800"), (25, "#d32f2f")]

category_colors = {"Technical": "#1565c0", "Financial": "#6a1b9a", "Operational": "#e65100", "External": "#2e7d32"}

risk_items = [
    {"name": "Server Outage", "likelihood": 3, "impact": 4, "category": "Technical", "color": "#1565c0"},
    {"name": "Data Breach", "likelihood": 2, "impact": 5, "category": "Technical", "color": "#1565c0"},
    {"name": "Budget Overrun", "likelihood": 4, "impact": 3, "category": "Financial", "color": "#6a1b9a"},
    {"name": "Currency Risk", "likelihood": 3, "impact": 2, "category": "Financial", "color": "#6a1b9a"},
    {"name": "Vendor Delay", "likelihood": 4, "impact": 2, "category": "Operational", "color": "#e65100"},
    {"name": "Staff Turnover", "likelihood": 4, "impact": 1, "category": "Operational", "color": "#e65100"},
    {"name": "Scope Creep", "likelihood": 5, "impact": 2, "category": "Operational", "color": "#e65100"},
    {"name": "Reg. Change", "likelihood": 2, "impact": 4, "category": "External", "color": "#2e7d32"},
    {"name": "Supply Chain", "likelihood": 3, "impact": 5, "category": "External", "color": "#2e7d32"},
    {"name": "Market Shift", "likelihood": 2, "impact": 3, "category": "Financial", "color": "#6a1b9a"},
    {"name": "Tech Debt", "likelihood": 4, "impact": 4, "category": "Technical", "color": "#1565c0"},
    {"name": "Cyber Attack", "likelihood": 1, "impact": 4, "category": "Technical", "color": "#1565c0"},
    {"name": "Key Person", "likelihood": 4, "impact": 5, "category": "Operational", "color": "#e65100"},
    {"name": "Pandemic", "likelihood": 1, "impact": 5, "category": "External", "color": "#2e7d32"},
]

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
    label_font_size=38,
    value_font_size=34,
    font_family="sans-serif",
)

# Plot
chart = RiskMatrixHeatmap(
    width=4800,
    height=2700,
    style=custom_style,
    title="heatmap-risk-matrix \u00b7 pygal \u00b7 pyplots.ai",
    risk_scores=risk_scores,
    risk_items=risk_items,
    row_labels=likelihood_labels,
    col_labels=impact_labels,
    zone_colors=zone_colors,
    show_legend=False,
    margin=100,
    margin_top=200,
    margin_bottom=80,
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
    <title>heatmap-risk-matrix - pygal</title>
    <style>
        body {{ margin: 0; display: flex; justify-content: center; align-items: center;
               min-height: 100vh; background: #f5f5f5; }}
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
