""" anyplot.ai
heatmap-calendar: Basic Calendar Heatmap
Library: pygal 3.1.0 | Python 3.14.4
Quality: 81/100 | Updated: 2026-04-27
"""

import os
import sys
from datetime import datetime, timedelta

import numpy as np


# Pop script directory so local files (pygal.py itself) don't shadow packages
_script_dir = sys.path.pop(0)

from pygal.graph.graph import Graph  # noqa: E402
from pygal.style import Style  # noqa: E402


sys.path.insert(0, _script_dir)

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
EMPTY_COLOR = "#D8D7CF" if THEME == "light" else "#2A2A27"

# Viridis sequential palette (hardcoded; perceptually uniform, colorblind-safe)
# Interpolated from matplotlib.cm.viridis at t = 0.15, 0.40, 0.65, 0.90
CELL_COLORS = [
    EMPTY_COLOR,  # no activity
    "#42337A",  # viridis ~t=0.15 — dark violet
    "#2A788E",  # viridis ~t=0.40 — teal-blue
    "#38B277",  # viridis ~t=0.65 — teal-green
    "#BCDC3B",  # viridis ~t=0.90 — yellow-green
]


class CalendarHeatmap(Graph):
    """Custom calendar heatmap chart rendered via pygal's SVG engine."""

    def __init__(self, *args, **kwargs):
        self.dates = kwargs.pop("dates", [])
        self.values = kwargs.pop("values", [])
        self.weekday_labels = kwargs.pop("weekday_labels", ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
        self.cell_colors = kwargs.pop("cell_colors", CELL_COLORS)
        super().__init__(*args, **kwargs)

    def _get_color(self, value, min_val, max_val):
        if value is None or value == 0:
            return self.cell_colors[0]
        if max_val == min_val:
            return self.cell_colors[-1]
        normalized = (value - min_val) / (max_val - min_val)
        idx = min(int(normalized * 4) + 1, len(self.cell_colors) - 1)
        return self.cell_colors[idx]

    def _plot(self):
        if not self.dates or not self.values:
            return

        date_values = dict(zip(self.dates, self.values, strict=True))
        min_date = min(self.dates)
        max_date = max(self.dates)

        non_zero_values = [v for v in self.values if v and v > 0]
        self._min_val = min(non_zero_values) if non_zero_values else 0
        self._max_val = max(non_zero_values) if non_zero_values else 1

        canvas_width = self.width
        canvas_height = self.height

        days_from_monday = min_date.weekday()
        start_date = min_date - timedelta(days=days_from_monday)

        total_days = (max_date - start_date).days + 1
        total_weeks = (total_days + 6) // 7 + 1

        title_space = 180
        month_label_height = 120
        left_margin = 240
        right_margin = 80

        available_width = canvas_width - left_margin - right_margin

        gap_ratio = 0.08
        cell_size = available_width / (total_weeks + (total_weeks - 1) * gap_ratio)
        gap = cell_size * gap_ratio

        grid_width = total_weeks * cell_size + (total_weeks - 1) * gap
        grid_height = 7 * cell_size + 6 * gap

        legend_block_height = 400
        total_content_height = month_label_height + grid_height + legend_block_height

        vertical_padding = (canvas_height - title_space - total_content_height) / 2
        vertical_padding = max(100, vertical_padding)

        x_offset = left_margin + (available_width - grid_width) / 2
        y_offset = title_space + vertical_padding + month_label_height

        graph_node = self.nodes["graph"]
        cal_group = self.svg.node(graph_node, class_="calendar-heatmap")

        # Weekday labels
        weekday_font_size = max(54, int(cell_size * 0.70))
        for i, label in enumerate(self.weekday_labels):
            y = y_offset + i * (cell_size + gap) + cell_size / 2
            text_node = self.svg.node(cal_group, "text", x=x_offset - 30, y=y + cell_size * 0.35)
            text_node.set("text-anchor", "end")
            text_node.set("fill", INK)
            text_node.set("style", f"font-size:{weekday_font_size}px;font-weight:bold;font-family:sans-serif")
            text_node.text = label

        month_positions = {}

        # Draw calendar cells
        current_date = start_date
        week = 0
        while current_date <= max_date:
            weekday = current_date.weekday()

            if current_date.day <= 7 and current_date >= min_date:
                month_key = (current_date.year, current_date.month)
                if month_key not in month_positions:
                    month_positions[month_key] = week

            value = date_values.get(current_date, 0)
            color = self._get_color(value, self._min_val, self._max_val)

            x = x_offset + week * (cell_size + gap)
            y = y_offset + weekday * (cell_size + gap)

            if current_date >= min_date:
                self.svg.node(
                    cal_group,
                    "rect",
                    x=x,
                    y=y,
                    width=cell_size,
                    height=cell_size,
                    fill=color,
                    rx=cell_size * 0.1,
                    ry=cell_size * 0.1,
                    class_="calendar-cell reactive",
                )

            if weekday == 6:
                week += 1
            current_date += timedelta(days=1)

        # Month labels
        month_font_size = max(54, int(cell_size * 0.70))
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        for (_year, month), week_pos in month_positions.items():
            x = x_offset + week_pos * (cell_size + gap)
            y = y_offset - 40
            text_node = self.svg.node(cal_group, "text", x=x, y=y)
            text_node.set("fill", INK)
            text_node.set("style", f"font-size:{month_font_size}px;font-weight:bold;font-family:sans-serif")
            text_node.text = month_names[month - 1]

        # Color scale legend
        legend_y = y_offset + grid_height + 180
        legend_cell_size = cell_size * 1.5
        legend_spacing = cell_size * 0.40
        legend_x = x_offset + grid_width / 2 - (len(self.cell_colors) * (legend_cell_size + legend_spacing)) / 2
        legend_label_size = max(56, int(cell_size * 0.70))

        text_node = self.svg.node(
            cal_group, "text", x=legend_x - legend_spacing * 2, y=legend_y + legend_cell_size * 0.7
        )
        text_node.set("text-anchor", "end")
        text_node.set("fill", INK)
        text_node.set("style", f"font-size:{legend_label_size}px;font-weight:bold;font-family:sans-serif")
        text_node.text = "Less"

        min_val = self._min_val
        max_val = self._max_val
        range_size = (max_val - min_val) / 4 if max_val > min_val else 1

        value_ranges = ["0"]
        for i in range(4):
            low = int(min_val + i * range_size) if i > 0 else 1
            high = int(min_val + (i + 1) * range_size)
            if i == 3:
                value_ranges.append(f"{low}+")
            else:
                value_ranges.append(f"{low}-{high}" if low != high else str(low))

        for i, color in enumerate(self.cell_colors):
            box_x = legend_x + i * (legend_cell_size + legend_spacing)
            self.svg.node(
                cal_group,
                "rect",
                x=box_x,
                y=legend_y,
                width=legend_cell_size,
                height=legend_cell_size,
                fill=color,
                rx=legend_cell_size * 0.1,
                ry=legend_cell_size * 0.1,
            )
            text_node = self.svg.node(
                cal_group, "text", x=box_x + legend_cell_size / 2, y=legend_y + legend_cell_size + 55
            )
            text_node.set("text-anchor", "middle")
            text_node.set("fill", INK_MUTED)
            text_node.set("style", f"font-size:{int(legend_label_size * 0.80)}px;font-family:sans-serif")
            text_node.text = value_ranges[i]

        text_node = self.svg.node(
            cal_group,
            "text",
            x=legend_x + len(self.cell_colors) * (legend_cell_size + legend_spacing) + legend_spacing * 2,
            y=legend_y + legend_cell_size * 0.7,
        )
        text_node.set("fill", INK)
        text_node.set("style", f"font-size:{legend_label_size}px;font-weight:bold;font-family:sans-serif")
        text_node.text = "More"

        # Summary stats below legend
        total_contributions = sum(v for v in self.values if v > 0)
        active_days = sum(1 for v in self.values if v > 0)
        max_streak = self._calculate_streak()
        summary_y = legend_y + legend_cell_size + 160
        summary_font_size = max(54, int(cell_size * 0.65))

        summary_text = f"{total_contributions} contributions in {len(self.dates)} days"
        text_node = self.svg.node(cal_group, "text", x=x_offset + grid_width / 2, y=summary_y)
        text_node.set("text-anchor", "middle")
        text_node.set("fill", INK)
        text_node.set("style", f"font-size:{summary_font_size}px;font-weight:bold;font-family:sans-serif")
        text_node.text = summary_text

        stats_y = summary_y + 90
        stats_text = (
            f"{active_days} active days · Longest streak: {max_streak} days"
            f" · Avg: {total_contributions / max(active_days, 1):.1f} per active day"
        )
        text_node = self.svg.node(cal_group, "text", x=x_offset + grid_width / 2, y=stats_y)
        text_node.set("text-anchor", "middle")
        text_node.set("fill", INK_MUTED)
        text_node.set("style", f"font-size:{int(summary_font_size * 0.85)}px;font-family:sans-serif")
        text_node.text = stats_text

    def _calculate_streak(self):
        max_streak = 0
        current_streak = 0
        for v in self.values:
            if v > 0:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
        return max_streak

    def _compute(self):
        self._box.xmin = 0
        self._box.xmax = 53
        self._box.ymin = 0
        self._box.ymax = 7


# Data — GitHub-style contribution pattern for 2024
np.random.seed(42)
start_date = datetime(2024, 1, 1)
end_date = datetime(2024, 12, 31)

dates = []
values = []
current = start_date

while current <= end_date:
    dates.append(current)
    weekday = current.weekday()
    base = 0 if weekday >= 5 else np.random.choice([0, 0, 1, 2, 3], p=[0.3, 0.2, 0.25, 0.15, 0.1])
    if np.random.random() < 0.05:
        base = np.random.randint(5, 15)
    if np.random.random() < 0.25:
        base = 0
    values.append(base)
    current += timedelta(days=1)

# Style
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=("#009E73",),
    title_font_size=72,
    legend_font_size=48,
    label_font_size=42,
    value_font_size=36,
    font_family="sans-serif",
)

# Plot
chart = CalendarHeatmap(
    width=4800,
    height=2700,
    style=custom_style,
    title="heatmap-calendar · pygal · anyplot.ai",
    dates=dates,
    values=values,
    cell_colors=CELL_COLORS,
    show_legend=False,
    margin=20,
    margin_top=280,
    margin_bottom=100,
    show_x_labels=False,
    show_y_labels=False,
)

chart.add("", [0])

# Save
chart.render_to_file(f"plot-{THEME}.html")
chart.render_to_png(f"plot-{THEME}.png")
