""" pyplots.ai
bullet-basic: Basic Bullet Chart
Library: bokeh 3.8.2 | Python 3.14.3
Quality: 88/100 | Updated: 2026-02-22
"""

from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Label, Range1d
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

# Qualitative range colors: index 0=poor (darkest) → index 2=good (lightest)
# Following Stephen Few's bullet chart convention
range_colors = ["#737373", "#a8a8a8", "#d4d4d4"]

# Actual bar colors: distinguish above-target (strong blue) vs below-target (muted)
color_above = "#306998"
color_below = "#7a9bb5"

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

# Prepare data for actual bars via ColumnDataSource (for HoverTool)
bar_x = []
bar_y = []
bar_w = []
bar_h_list = []
bar_colors = []
hover_labels = []
hover_actuals = []
hover_targets = []
hover_pcts = []

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

    # Draw qualitative ranges (background bands)
    # j=0 is poor (darkest, shortest height), j=2 is good (lightest, tallest height)
    # Draw from widest (j=2) to narrowest (j=0) so narrower bands overlay wider ones
    for j in range(len(norm_ranges) - 1, -1, -1):
        range_width = norm_ranges[j]
        height_factor = 0.6 + j * 0.2  # j=0 shortest (0.6), j=2 tallest (1.0)
        h = bar_height * height_factor
        p.rect(x=range_width / 2, y=y_pos, width=range_width, height=h, color=range_colors[j], line_color=None)

    # Determine bar color based on actual vs target
    bar_color = color_above if actual >= target else color_below
    actual_bar_height = bar_height * 0.3

    # Collect data for ColumnDataSource
    bar_x.append(norm_actual / 2)
    bar_y.append(y_pos)
    bar_w.append(norm_actual)
    bar_h_list.append(actual_bar_height)
    bar_colors.append(bar_color)

    unit_text = f" {metric['unit']}" if metric["unit"] else ""
    hover_labels.append(f"{metric['label']}{unit_text}")
    hover_actuals.append(f"{actual}{unit_text}")
    hover_targets.append(f"{target}{unit_text}")
    hover_pcts.append(f"{norm_actual:.0f}%")

    # Draw target marker (thin vertical line)
    target_marker_height = bar_height * 0.55
    p.rect(x=norm_target, y=y_pos, width=0.7, height=target_marker_height, color="#1a1a1a", line_color=None)

    # Add metric label with unit
    label_unit = f" ({metric['unit']})" if metric["unit"] else ""
    label = Label(
        x=-2,
        y=y_pos,
        text=f"{metric['label']}{label_unit}",
        text_font_size="28pt",
        text_color="#333333",
        text_align="right",
        text_baseline="middle",
        text_font_style="bold",
    )
    p.add_layout(label)

    # Add actual value as text — color-coded to match bar
    value_text = str(int(actual)) if actual == int(actual) else str(actual)
    value_label = Label(
        x=norm_actual + 2,
        y=y_pos,
        text=value_text,
        text_font_size="22pt",
        text_color=bar_color,
        text_align="left",
        text_baseline="middle",
        text_font_style="bold",
    )
    p.add_layout(value_label)

# Draw actual bars using ColumnDataSource for interactivity
source = ColumnDataSource(
    data={
        "x": bar_x,
        "y": bar_y,
        "width": bar_w,
        "height": bar_h_list,
        "color": bar_colors,
        "label": hover_labels,
        "actual": hover_actuals,
        "target": hover_targets,
        "pct": hover_pcts,
    }
)
actual_renderer = p.rect(x="x", y="y", width="width", height="height", color="color", line_color=None, source=source)

# Add HoverTool for interactivity (in HTML export)
hover = HoverTool(
    renderers=[actual_renderer],
    tooltips=[("Metric", "@label"), ("Actual", "@actual"), ("Target", "@target"), ("% of Range", "@pct")],
)
p.add_tools(hover)

# Legend - positioned below the chart
legend_y = -0.5
legend_start_x = 10
legend_spacing = 22
range_labels = ["Poor", "Satisfactory", "Good"]
box_w = 4
box_h = 0.2

for k, (color, lbl) in enumerate(zip(range_colors, range_labels, strict=True)):
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

# Save as HTML (with interactive HoverTool)
output_file("plot.html")
save(p)
