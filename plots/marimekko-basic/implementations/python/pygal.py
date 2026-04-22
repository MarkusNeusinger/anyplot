""" pyplots.ai
marimekko-basic: Basic Marimekko Chart
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import sys


# Temporarily remove current directory from path to avoid name collision with pygal module
_cwd = sys.path[0] if sys.path[0] else "."
if _cwd in sys.path:
    sys.path.remove(_cwd)

from pygal.graph.graph import Graph  # noqa: E402
from pygal.style import Style  # noqa: E402


# Restore path
sys.path.insert(0, _cwd)


# Custom class required: pygal has no native Marimekko/mekko chart type.
# Variable-width stacked bars require extending the Graph base class.
class Marimekko(Graph):
    """Custom Marimekko chart - stacked bars with variable widths based on column totals."""

    _serie_margin = 0

    def __init__(self, *args, **kwargs):
        self.gap = kwargs.pop("gap", 0.02)
        super().__init__(*args, **kwargs)

    def _compute_x_labels(self):
        """Skip standard x-label computation - custom labels drawn in _plot."""
        pass

    def _compute_y_labels(self):
        """Skip standard y-label computation."""
        pass

    def _plot(self):
        """Draw the marimekko chart with variable-width bars and stacked segments."""
        if not self.series:
            return

        # Calculate column totals (determines bar widths)
        num_cols = len(self.series[0].values) if self.series else 0
        col_totals = [0] * num_cols

        for serie in self.series:
            for i, val in enumerate(serie.values):
                if val is not None:
                    col_totals[i] += val

        grand_total = sum(col_totals)
        if grand_total == 0:
            return

        # Get plot area dimensions
        plot_width = self.view.width
        plot_height = self.view.height

        # Calculate gap and usable width
        total_gap = self.gap * plot_width * (num_cols - 1)
        usable_width = plot_width - total_gap
        gap_px = self.gap * plot_width

        # Get coordinates
        x_start = self.view.x(0)
        y_bottom = self.view.y(0)

        # Create group for the marimekko chart
        plot_node = self.nodes["plot"]
        mekko_group = self.svg.node(plot_node, class_="marimekko-chart")

        # Draw bars column by column
        x_pos = x_start

        for col_idx in range(num_cols):
            col_total = col_totals[col_idx]
            if col_total == 0:
                continue

            # Bar width proportional to column total
            bar_width = (col_total / grand_total) * usable_width

            # Stack segments within this column
            y_offset = 0

            for serie_idx, serie in enumerate(self.series):
                val = serie.values[col_idx] if col_idx < len(serie.values) else None
                if val is None or val == 0:
                    continue

                # Segment height proportional to value within column
                segment_height = (val / col_total) * plot_height
                color = self.style.colors[serie_idx % len(self.style.colors)]

                # Draw rectangle (y increases downward in SVG)
                y_pos = y_bottom - y_offset - segment_height

                # Create series group
                serie_group = self.svg.node(mekko_group, class_="series serie-%d color-%d" % (serie_idx, serie_idx))

                self.svg.node(
                    serie_group,
                    "rect",
                    x=x_pos,
                    y=y_pos,
                    width=bar_width,
                    height=segment_height,
                    fill=color,
                    stroke="white",
                    **{"stroke-width": "3", "class": "rect reactive tooltip-trigger"},
                )

                # Add value label if segment is large enough
                if segment_height > 90 and bar_width > 120:
                    pct = (val / col_total) * 100
                    label_y = y_pos + segment_height / 2
                    label_x = x_pos + bar_width / 2

                    self.svg.node(
                        serie_group,
                        "text",
                        x=label_x,
                        y=label_y,
                        fill="white",
                        **{
                            "text-anchor": "middle",
                            "dominant-baseline": "middle",
                            "font-size": "36",
                            "font-weight": "bold",
                        },
                    ).text = f"{pct:.0f}%"

                y_offset += segment_height

            x_pos += bar_width + gap_px

        # Draw x-axis labels (column labels centered under each bar)
        if hasattr(self, "x_labels") and self.x_labels:
            x_pos = x_start
            for col_idx in range(num_cols):
                col_total = col_totals[col_idx]
                if col_total == 0:
                    continue

                bar_width = (col_total / grand_total) * usable_width
                label_x = x_pos + bar_width / 2
                label_y = y_bottom + 65

                label_group = self.svg.node(mekko_group, class_="x-labels")

                # Category label
                self.svg.node(
                    label_group,
                    "text",
                    x=label_x,
                    y=label_y,
                    fill="#333",
                    **{"text-anchor": "middle", "font-size": "42", "font-weight": "normal"},
                ).text = str(self.x_labels[col_idx]) if col_idx < len(self.x_labels) else ""

                # Width percentage label (shows relative market size)
                width_pct = (col_total / grand_total) * 100
                self.svg.node(
                    label_group,
                    "text",
                    x=label_x,
                    y=label_y + 55,
                    fill="#666",
                    **{"text-anchor": "middle", "font-size": "34", "font-style": "italic"},
                ).text = f"({width_pct:.0f}%)"

                x_pos += bar_width + gap_px

        # Draw Y-axis percentage scale (0%, 25%, 50%, 75%, 100%)
        y_axis_group = self.svg.node(mekko_group, class_="y-axis-labels")
        for pct in [0, 25, 50, 75, 100]:
            y_pos = y_bottom - (pct / 100) * plot_height
            label_x = x_start - 25

            self.svg.node(
                y_axis_group, "text", x=label_x, y=y_pos + 5, fill="#666", **{"text-anchor": "end", "font-size": "34"}
            ).text = f"{pct}%"

            # Draw subtle gridline
            if pct > 0:
                self.svg.node(
                    y_axis_group,
                    "line",
                    x1=x_start,
                    y1=y_pos,
                    x2=x_start + plot_width,
                    y2=y_pos,
                    stroke="#ddd",
                    **{"stroke-width": "1", "stroke-dasharray": "5,5"},
                )

        # Draw Y-axis title (rotated label)
        y_title_x = x_start - 120
        y_title_y = y_bottom - plot_height / 2
        self.svg.node(
            y_axis_group,
            "text",
            x=y_title_x,
            y=y_title_y,
            fill="#333",
            **{
                "text-anchor": "middle",
                "font-size": "42",
                "font-weight": "normal",
                "transform": f"rotate(-90, {y_title_x}, {y_title_y})",
            },
        ).text = "Share within Region (%)"

    def _compute(self):
        """Compute the bounding box for rendering."""
        self._box.xmin = 0
        self._box.xmax = 1
        self._box.ymin = 0
        self._box.ymax = 1


# Custom style for 4800x2700 canvas
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998", "#FFD43B", "#4ECDC4", "#FF6B6B", "#9B59B6"),
    title_font_size=72,
    legend_font_size=50,
    label_font_size=42,
    value_font_size=38,
    font_family="sans-serif",
)

# Data - Market share by region and product line
# Regions (x-categories) with different market sizes
regions = ["North America", "Europe", "Asia Pacific", "Latin America", "MEA"]

# Product lines (y-categories) and their share within each region
# Values represent revenue in millions USD per region
products = {
    "Enterprise": [180, 140, 200, 60, 40],
    "Consumer": [120, 130, 180, 70, 45],
    "SMB": [90, 70, 90, 35, 25],
    "Government": [60, 40, 50, 15, 10],
}

# Create marimekko chart
chart = Marimekko(
    width=4800,
    height=2700,
    gap=0.015,
    style=custom_style,
    title="marimekko-basic · pygal · pyplots.ai",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    margin=80,
    margin_left=160,
    margin_bottom=320,
    show_x_labels=False,
    show_y_labels=False,
)

chart.x_labels = regions

# Add data series for each product line
for product_name, values in products.items():
    chart.add(product_name, values)

# Save outputs
chart.render_to_file("plot.svg")
chart.render_to_png("plot.png")

# Save HTML for interactive viewing
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>marimekko-basic · pygal · pyplots.ai</title>
    <style>
        body {{ margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 100%; margin: 0 auto; }}
        svg {{ max-width: 100%; height: auto; }}
    </style>
</head>
<body>
    <div class="container">
        {chart.render(is_unicode=True)}
    </div>
</body>
</html>"""

with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)
