""" pyplots.ai
heatmap-calendar: Basic Calendar Heatmap
Library: pygal 3.1.0 | Python 3.13.11
Quality: 90/100 | Created: 2025-12-23
"""

import sys
from datetime import datetime, timedelta

import numpy as np


# Temporarily remove current directory from path to avoid name collision
_cwd = sys.path[0] if sys.path[0] else "."
if _cwd in sys.path:
    sys.path.remove(_cwd)

from pygal.graph.graph import Graph  # noqa: E402
from pygal.style import Style  # noqa: E402


# Restore path
sys.path.insert(0, _cwd)


class CalendarHeatmap(Graph):
    """Custom Calendar Heatmap for pygal - displays daily values in a calendar grid."""

    def __init__(self, *args, **kwargs):
        self.dates = kwargs.pop("dates", [])
        self.values = kwargs.pop("values", [])
        self.weekday_labels = kwargs.pop("weekday_labels", ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
        self.cell_colors = kwargs.pop("cell_colors", ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"])
        super().__init__(*args, **kwargs)

    def _get_color(self, value, min_val, max_val):
        """Get color based on value intensity."""
        if value is None or value == 0:
            return self.cell_colors[0]
        if max_val == min_val:
            return self.cell_colors[-1]
        # Normalize value to 0-1 range
        normalized = (value - min_val) / (max_val - min_val)
        # Map to color index (1-4, skip 0 which is for empty)
        idx = min(int(normalized * 4) + 1, len(self.cell_colors) - 1)
        return self.cell_colors[idx]

    def _plot(self):
        """Draw the calendar heatmap."""
        if not self.dates or not self.values:
            return

        # Create date-value mapping
        date_values = dict(zip(self.dates, self.values, strict=True))

        # Find date range
        min_date = min(self.dates)
        max_date = max(self.dates)

        # Calculate value range (excluding zeros) for dynamic legend
        non_zero_values = [v for v in self.values if v and v > 0]
        self._min_val = min(non_zero_values) if non_zero_values else 0
        self._max_val = max(non_zero_values) if non_zero_values else 1

        # Use full canvas dimensions for maximum grid utilization
        canvas_width = self.width
        canvas_height = self.height

        # Calculate weeks and dimensions
        # Adjust start to first day of the week containing min_date
        days_from_monday = min_date.weekday()
        start_date = min_date - timedelta(days=days_from_monday)

        # Calculate total weeks
        total_days = (max_date - start_date).days + 1
        total_weeks = (total_days + 6) // 7 + 1

        # Layout optimized for calendar heatmap on 4800×2700 canvas
        # Calendar has inherent ~7.5:1 aspect ratio (53 weeks × 7 days)
        # Width is the limiting factor - maximize cell size within width constraint
        # Position content in upper portion, use lower space for legend and summary
        title_space = 180  # Space for title at top
        month_label_height = 120  # Space for month labels above grid
        left_margin = 240  # Space for weekday labels
        right_margin = 80  # Right margin

        # Available width for grid
        available_width = canvas_width - left_margin - right_margin

        # Gap ratio between cells
        gap_ratio = 0.08

        # Calculate cell size based on width (the limiting factor for calendars)
        cell_size = available_width / (total_weeks + (total_weeks - 1) * gap_ratio)
        gap = cell_size * gap_ratio

        # Calculate actual grid dimensions
        grid_width = total_weeks * cell_size + (total_weeks - 1) * gap
        grid_height = 7 * cell_size + 6 * gap

        # Calculate total content height and center vertically
        # Content: month labels + grid + spacing + legend + spacing + summary lines
        legend_block_height = 400  # Legend boxes + value labels + summary text
        total_content_height = month_label_height + grid_height + legend_block_height

        # Center content vertically on canvas
        vertical_padding = (canvas_height - title_space - total_content_height) / 2
        vertical_padding = max(100, vertical_padding)  # Minimum padding

        x_offset = left_margin + (available_width - grid_width) / 2
        y_offset = title_space + vertical_padding + month_label_height

        # Create group for the calendar - use graph node for full canvas access
        # The 'graph' node is at the root level, not constrained by plot margins
        graph_node = self.nodes["graph"]
        cal_group = self.svg.node(graph_node, class_="calendar-heatmap")

        # Draw weekday labels on the left - prominent sizing
        weekday_font_size = max(54, int(cell_size * 0.70))
        for i, label in enumerate(self.weekday_labels):
            y = y_offset + i * (cell_size + gap) + cell_size / 2
            text_node = self.svg.node(cal_group, "text", x=x_offset - 30, y=y + cell_size * 0.35)
            text_node.set("text-anchor", "end")
            text_node.set("fill", "#333333")
            text_node.set("style", f"font-size:{weekday_font_size}px;font-weight:bold;font-family:sans-serif")
            text_node.text = label

        # Track months for labels
        month_positions = {}

        # Draw cells
        current_date = start_date
        week = 0
        while current_date <= max_date:
            weekday = current_date.weekday()

            # Track month positions
            if current_date.day <= 7 and current_date >= min_date:
                month_key = (current_date.year, current_date.month)
                if month_key not in month_positions:
                    month_positions[month_key] = week

            # Get value and color
            value = date_values.get(current_date, 0)
            color = self._get_color(value, self._min_val, self._max_val)

            # Calculate position
            x = x_offset + week * (cell_size + gap)
            y = y_offset + weekday * (cell_size + gap)

            # Draw cell
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

            # Move to next day
            if weekday == 6:
                week += 1
            current_date += timedelta(days=1)

        # Draw month labels at the top - prominent sizing
        month_font_size = max(54, int(cell_size * 0.70))
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        for (_year, month), week_pos in month_positions.items():
            x = x_offset + week_pos * (cell_size + gap)
            y = y_offset - 40
            text_node = self.svg.node(cal_group, "text", x=x, y=y)
            text_node.set("fill", "#333333")
            text_node.set("style", f"font-size:{month_font_size}px;font-weight:bold;font-family:sans-serif")
            text_node.text = month_names[month - 1]

        # Draw color scale legend at bottom with dynamic value ranges
        # Make legend prominent to better utilize vertical space
        legend_y = y_offset + grid_height + 180
        legend_cell_size = cell_size * 1.5  # Large legend cells for prominence
        legend_spacing = cell_size * 0.40
        legend_x = x_offset + grid_width / 2 - (len(self.cell_colors) * (legend_cell_size + legend_spacing)) / 2
        legend_label_size = max(56, int(cell_size * 0.70))

        # "Less" label
        text_node = self.svg.node(
            cal_group, "text", x=legend_x - legend_spacing * 2, y=legend_y + legend_cell_size * 0.7
        )
        text_node.set("text-anchor", "end")
        text_node.set("fill", "#333333")
        text_node.set("style", f"font-size:{legend_label_size}px;font-weight:bold;font-family:sans-serif")
        text_node.text = "Less"

        # Generate dynamic value ranges based on actual data
        min_val = self._min_val
        max_val = self._max_val
        range_size = (max_val - min_val) / 4 if max_val > min_val else 1

        # Create value labels: 0, then quartile ranges
        value_ranges = ["0"]
        for i in range(4):
            low = int(min_val + i * range_size) if i > 0 else 1
            high = int(min_val + (i + 1) * range_size)
            if i == 3:
                value_ranges.append(f"{low}+")
            else:
                value_ranges.append(f"{low}-{high}" if low != high else str(low))

        # Color boxes with dynamic numeric labels
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
            # Numeric label below each color box
            text_node = self.svg.node(
                cal_group, "text", x=box_x + legend_cell_size / 2, y=legend_y + legend_cell_size + 55
            )
            text_node.set("text-anchor", "middle")
            text_node.set("fill", "#666666")
            text_node.set("style", f"font-size:{int(legend_label_size * 0.80)}px;font-family:sans-serif")
            text_node.text = value_ranges[i]

        # "More" label
        text_node = self.svg.node(
            cal_group,
            "text",
            x=legend_x + len(self.cell_colors) * (legend_cell_size + legend_spacing) + legend_spacing * 2,
            y=legend_y + legend_cell_size * 0.7,
        )
        text_node.set("fill", "#333333")
        text_node.set("style", f"font-size:{legend_label_size}px;font-weight:bold;font-family:sans-serif")
        text_node.text = "More"

        # Add summary annotations below legend to utilize vertical space
        total_contributions = sum(v for v in self.values if v > 0)
        active_days = sum(1 for v in self.values if v > 0)
        max_streak = self._calculate_streak()
        summary_y = legend_y + legend_cell_size + 160
        summary_font_size = max(54, int(cell_size * 0.65))

        # Main summary text
        summary_text = f"{total_contributions} contributions in {len(self.dates)} days"
        text_node = self.svg.node(cal_group, "text", x=x_offset + grid_width / 2, y=summary_y)
        text_node.set("text-anchor", "middle")
        text_node.set("fill", "#333333")
        text_node.set("style", f"font-size:{summary_font_size}px;font-weight:bold;font-family:sans-serif")
        text_node.text = summary_text

        # Secondary stats line
        stats_y = summary_y + 90
        stats_text = f"{active_days} active days · Longest streak: {max_streak} days · Avg: {total_contributions / max(active_days, 1):.1f} per active day"
        text_node = self.svg.node(cal_group, "text", x=x_offset + grid_width / 2, y=stats_y)
        text_node.set("text-anchor", "middle")
        text_node.set("fill", "#666666")
        text_node.set("style", f"font-size:{int(summary_font_size * 0.85)}px;font-family:sans-serif")
        text_node.text = stats_text

    def _calculate_streak(self):
        """Calculate longest consecutive active days streak."""
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
        """Compute the box for rendering."""
        self._box.xmin = 0
        self._box.xmax = 53  # Max weeks in a year
        self._box.ymin = 0
        self._box.ymax = 7  # Days in a week


# Generate data - GitHub-style contribution data for a year
np.random.seed(42)
start_date = datetime(2024, 1, 1)
end_date = datetime(2024, 12, 31)

dates = []
values = []
current = start_date

while current <= end_date:
    dates.append(current)

    # Simulate contribution pattern: weekdays more active, weekends less
    weekday = current.weekday()
    base = 0 if weekday >= 5 else np.random.choice([0, 0, 1, 2, 3], p=[0.3, 0.2, 0.25, 0.15, 0.1])

    # Random spike days
    if np.random.random() < 0.05:
        base = np.random.randint(5, 15)

    # Some days have no activity
    if np.random.random() < 0.25:
        base = 0

    values.append(base)
    current += timedelta(days=1)

# Custom style for 4800x2700 canvas
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998",),
    title_font_size=72,
    legend_font_size=48,
    label_font_size=42,
    value_font_size=36,
    font_family="sans-serif",
)

# GitHub-style green colors
github_colors = ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"]

# Create calendar heatmap on 4800×2700 canvas
# Calendar has inherent ~7.5:1 aspect ratio - layout optimized for visual balance
chart = CalendarHeatmap(
    width=4800,
    height=2700,
    style=custom_style,
    title="heatmap-calendar · pygal · pyplots.ai",
    dates=dates,
    values=values,
    cell_colors=github_colors,
    show_legend=False,
    margin=20,
    margin_top=280,
    margin_bottom=100,
    show_x_labels=False,
    show_y_labels=False,
)

# Add a dummy series to trigger _plot (pygal requires at least one series)
chart.add("", [0])

# Save output
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")
