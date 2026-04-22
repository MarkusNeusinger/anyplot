""" pyplots.ai
bar-basic: Basic Bar Chart
Library: pygal 3.1.0 | Python 3.14
Quality: 88/100 | Created: 2025-12-23
"""

import pygal
from pygal.style import Style


# Data - Quarterly website traffic by channel (non-monotonic for diversity)
categories = ["Organic Search", "Direct", "Social Media", "Email", "Referral", "Paid Ads", "Affiliates"]
values = [142500, 98700, 87300, 53200, 41800, 72600, 18900]

# Identify the leader for emphasis
max_idx = values.index(max(values))
total = sum(values)
highlight_color = "#306998"
base_color = "#A8C4D8"

# Build per-bar data — highlight leader, muted for the rest
# Add percentage share as label for the leader bar to tell the data story
bar_data = []
for i, v in enumerate(values):
    entry = {"value": v, "color": highlight_color if i == max_idx else base_color}
    if i == max_idx:
        entry["formatter"] = lambda x: f"★ {x:,.0f} ({x / total:.0%} of total)"
    bar_data.append(entry)

# Custom style — refined for publication quality
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#2C3E50",
    foreground_strong="#2C3E50",
    foreground_subtle="#E8E8E8",
    colors=(highlight_color,),
    title_font_size=52,
    label_font_size=34,
    major_label_font_size=34,
    value_font_size=32,
    value_label_font_size=32,
    legend_font_size=34,
    title_font_family="sans-serif",
    label_font_family="sans-serif",
    value_font_family="sans-serif",
)

# Create chart with tighter margins for better canvas utilization
chart = pygal.Bar(
    width=4800,
    height=2700,
    title="bar-basic · pygal · pyplots.ai\nOrganic Search dominates Q4 2025 traffic at 28% share",
    x_title="Channel",
    y_title="Visits (Q4 2025)",
    style=custom_style,
    show_legend=False,
    print_values=True,
    print_values_position="top",
    value_formatter=lambda x: f"{x:,.0f}",
    show_y_guides=True,
    show_x_guides=False,
    margin=20,
    margin_bottom=80,
    margin_left=30,
    margin_right=30,
    spacing=18,
    rounded_bars=6,
    truncate_label=-1,
    x_label_rotation=0,
    show_minor_y_labels=False,
    y_labels_major_every=1,
)

# Y-axis ticks
chart.y_labels = [0, 30000, 60000, 90000, 120000, 150000]

# Add data
chart.x_labels = categories
chart.add("Visits", bar_data)

# Save
chart.render_to_png("plot.png")
