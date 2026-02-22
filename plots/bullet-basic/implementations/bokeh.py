""" pyplots.ai
bullet-basic: Basic Bullet Chart
Library: bokeh 3.8.2 | Python 3.14.3
Quality: 82/100 | Updated: 2026-02-22
"""

from bokeh.io import export_png, output_file, save
from bokeh.models import Label, Range1d
from bokeh.plotting import figure


# Data - Sales performance metrics with targets
metrics = [
    {"label": "Revenue", "unit": "$K", "actual": 275, "target": 250, "ranges": [150, 225, 300]},
    {"label": "Profit", "unit": "$K", "actual": 85, "target": 100, "ranges": [50, 75, 100]},
    {"label": "Orders", "unit": "", "actual": 320, "target": 350, "ranges": [200, 300, 400]},
    {"label": "Customers", "unit": "", "actual": 1450, "target": 1200, "ranges": [800, 1100, 1500]},
    {"label": "Satisfaction", "unit": "/5", "actual": 4.2, "target": 4.5, "ranges": [3.0, 4.0, 5.0]},
]

# Configuration
num_metrics = len(metrics)
bar_spacing = 1.5
bar_height = 0.8

# Qualitative range colors: lightest (widest, good) to darkest (narrowest, poor)
range_colors = ["#d4d4d4", "#a8a8a8", "#737373"]

# Create figure
p = figure(
    width=4800,
    height=2700,
    x_range=Range1d(-38, 118),
    y_range=Range1d(-0.8, num_metrics * bar_spacing + 0.2),
    title="bullet-basic · bokeh · pyplots.ai",
    x_axis_label="% of Maximum Range",
    toolbar_location=None,
)

# Remove y-axis ticks and gridlines
p.yaxis.visible = False
p.ygrid.grid_line_color = None
p.xgrid.grid_line_alpha = 0.15
p.xgrid.grid_line_dash = [6, 4]

# Draw bullets for each metric
for i, metric in enumerate(metrics):
    y_pos = (num_metrics - 1 - i) * bar_spacing
    actual = metric["actual"]
    target = metric["target"]
    ranges = metric["ranges"]
    max_range = ranges[-1]

    # Normalize values to percentage of max range
    norm_actual = (actual / max_range) * 100
    norm_target = (target / max_range) * 100
    norm_ranges = [(r / max_range) * 100 for r in ranges]

    # Draw qualitative ranges (background bands) - widest first (lightest = good)
    for j in range(len(norm_ranges) - 1, -1, -1):
        range_width = norm_ranges[j]
        height_factor = 1 - j * 0.2
        h = bar_height * height_factor
        p.rect(x=range_width / 2, y=y_pos, width=range_width, height=h, color=range_colors[j], line_color=None)

    # Draw actual value bar
    actual_bar_height = bar_height * 0.3
    p.rect(x=norm_actual / 2, y=y_pos, width=norm_actual, height=actual_bar_height, color="#306998", line_color=None)

    # Draw target marker (thin vertical line)
    target_marker_height = bar_height * 0.55
    p.rect(x=norm_target, y=y_pos, width=0.7, height=target_marker_height, color="#1a1a1a", line_color=None)

    # Add metric label with unit
    unit_text = f" ({metric['unit']})" if metric["unit"] else ""
    label = Label(
        x=-2,
        y=y_pos,
        text=f"{metric['label']}{unit_text}",
        text_font_size="28pt",
        text_color="#333333",
        text_align="right",
        text_baseline="middle",
        text_font_style="bold",
    )
    p.add_layout(label)

    # Add actual value as text
    value_text = str(int(actual)) if actual == int(actual) else str(actual)
    value_label = Label(
        x=norm_actual + 2,
        y=y_pos,
        text=value_text,
        text_font_size="22pt",
        text_color="#306998",
        text_align="left",
        text_baseline="middle",
        text_font_style="bold",
    )
    p.add_layout(value_label)

# Legend - positioned below the chart
legend_y = -0.5
legend_start_x = 10
legend_spacing = 22
range_labels = ["Poor", "Satisfactory", "Good"]
box_w = 4
box_h = 0.2

for k, (color, lbl) in enumerate(zip(range_colors[::-1], range_labels, strict=True)):
    lx = legend_start_x + k * legend_spacing
    p.rect(x=lx, y=legend_y, width=box_w, height=box_h, color=color, line_color="#999999", line_width=1)
    p.add_layout(
        Label(
            x=lx + box_w / 2 + 1,
            y=legend_y,
            text=lbl,
            text_font_size="20pt",
            text_color="#555555",
            text_align="left",
            text_baseline="middle",
        )
    )

# Target marker legend entry
target_lx = legend_start_x + len(range_labels) * legend_spacing
p.rect(x=target_lx, y=legend_y, width=1.0, height=box_h, color="#1a1a1a", line_color=None)
p.add_layout(
    Label(
        x=target_lx + box_w / 2 + 1,
        y=legend_y,
        text="Target",
        text_font_size="20pt",
        text_color="#555555",
        text_align="left",
        text_baseline="middle",
    )
)

# Style - scaled for 4800x2700 canvas
p.title.text_font_size = "36pt"
p.title.text_color = "#333333"
p.title.align = "center"
p.xaxis.axis_label_text_font_size = "24pt"
p.xaxis.major_label_text_font_size = "20pt"
p.xaxis.ticker = [0, 20, 40, 60, 80, 100]
p.xaxis.axis_line_color = "#666666"
p.outline_line_color = None

# Save as PNG
export_png(p, filename="plot.png")

# Save as HTML
output_file("plot.html")
save(p)
