""" pyplots.ai
funnel-basic: Basic Funnel Chart
Library: pygal 3.1.0 | Python 3.13.11
Quality: 90/100 | Created: 2025-12-23
"""

import pygal
from pygal.style import Style


# Data - Sales funnel stages with progressively decreasing values
# Deterministic data - no random seed needed
stages = ["Awareness", "Interest", "Consideration", "Intent", "Purchase"]
values = [1000, 600, 400, 200, 100]
base_value = values[0]

# Custom style for visibility at 4800x2700
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998", "#FFD43B", "#4A90A4", "#F4A261", "#6B8E23"),
    title_font_size=36,
    label_font_size=24,
    major_label_font_size=22,
    value_font_size=28,
    value_label_font_size=28,
    legend_font_size=24,
    tooltip_font_size=20,
)


# Create funnel chart with enhanced interactivity
chart = pygal.Funnel(
    width=4800,
    height=2700,
    title="funnel-basic · pygal · pyplots.ai",
    style=custom_style,
    print_values=True,
    value_formatter=lambda x: f"{x:,.0f} ({x / base_value * 100:.0f}%)",
    margin=80,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=5,
    show_y_labels=False,
    show_y_guides=False,
    show_x_labels=False,
    truncate_legend=-1,
    spacing=20,
)

# Add each stage as a separate series for distinct colors and legend labels
for stage, value in zip(stages, values, strict=True):
    chart.add(stage, [{"value": value, "label": f"{stage}: {value:,.0f} ({value / base_value * 100:.0f}%)"}])

# Save outputs
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
