""" pyplots.ai
line-impurity-comparison: Gini Impurity vs Entropy Comparison
Library: bokeh 3.8.2 | Python 3.14.3
Quality: 91/100 | Created: 2026-02-17
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Label, Legend, NumeralTickFormatter, Span
from bokeh.plotting import figure


# Data
p_vals = np.linspace(0, 1, 200)

# Gini impurity: 2 * p * (1 - p), already in [0, 1]
gini = 2 * p_vals * (1 - p_vals)

# Entropy: -p * log2(p) - (1-p) * log2(1-p), normalized to [0, 1]
with np.errstate(divide="ignore", invalid="ignore"):
    entropy = -p_vals * np.log2(p_vals) - (1 - p_vals) * np.log2(1 - p_vals)
entropy = np.nan_to_num(entropy, nan=0.0)

source_gini = ColumnDataSource(data={"p": p_vals, "impurity": gini})
source_entropy = ColumnDataSource(data={"p": p_vals, "impurity": entropy})

# Area between curves to visually emphasize the difference
source_diff = ColumnDataSource(
    data={"p": np.concatenate([p_vals, p_vals[::-1]]), "fill": np.concatenate([entropy, gini[::-1]])}
)

# Plot
fig = figure(
    width=4800,
    height=2700,
    title="line-impurity-comparison · bokeh · pyplots.ai",
    x_axis_label="Probability (p)",
    y_axis_label="Impurity Measure (normalized)",
    x_range=(-0.02, 1.02),
    y_range=(-0.05, 1.10),
)

# Shaded area between curves shows the gap — both peak at p=0.5 but differ in scale
fig.patch(x="p", y="fill", source=source_diff, fill_color="#D4A017", fill_alpha=0.08, line_alpha=0)

# Vertical reference line at p=0.5 using Span
ref_line = Span(
    location=0.5, dimension="height", line_color="#888888", line_width=2, line_dash="dotted", line_alpha=0.5
)
fig.add_layout(ref_line)

# Lines
line_gini = fig.line(x="p", y="impurity", source=source_gini, line_width=7, line_color="#306998")
line_entropy = fig.line(
    x="p", y="impurity", source=source_entropy, line_width=7, line_color="#D4A017", line_dash=[14, 7]
)

# Annotate max points at p=0.5 with larger markers
fig.scatter(x=[0.5, 0.5], y=[0.5, 1.0], size=32, fill_color=["#306998", "#D4A017"], line_color="white", line_width=4)

# Connector line between the two max dots
fig.segment(x0=[0.5], y0=[0.5], x1=[0.5], y1=[1.0], line_color="#666666", line_width=3, line_dash="dotted")

# Annotation label with background for visual hierarchy
max_label = Label(
    x=0.53,
    y=1.00,
    text="p = 0.5  (maximum impurity)",
    text_font_size="32pt",
    text_font_style="bold",
    text_color="#333333",
    background_fill_color="white",
    background_fill_alpha=0.85,
    border_line_color="#cccccc",
    border_line_alpha=0.6,
    border_line_width=2,
)
fig.add_layout(max_label)

# Value labels at each maximum dot
gini_val_label = Label(
    x=0.18, y=0.44, text="Gini max = 0.5", text_font_size="24pt", text_color="#306998", text_font_style="italic"
)
fig.add_layout(gini_val_label)

entropy_val_label = Label(
    x=0.62, y=0.88, text="Entropy max = 1.0", text_font_size="24pt", text_color="#B8860B", text_font_style="italic"
)
fig.add_layout(entropy_val_label)

# Practical insight annotation — key educational takeaway
insight_label = Label(
    x=0.62,
    y=0.18,
    text="Both criteria agree on optimal splits →\nsimilar tree structures in practice",
    text_font_size="24pt",
    text_color="#555555",
    text_font_style="italic",
    text_line_height=1.4,
    background_fill_color="white",
    background_fill_alpha=0.85,
    border_line_color="#aaaaaa",
    border_line_alpha=0.5,
    border_line_width=1,
)
fig.add_layout(insight_label)

# HoverTool for interactive HTML export
hover = HoverTool(
    renderers=[line_gini, line_entropy], tooltips=[("p", "@p{0.00}"), ("Impurity", "@impurity{0.000}")], mode="vline"
)
fig.add_tools(hover)

# Legend with formulas
legend = Legend(
    items=[("Gini: 2p(1−p)", [line_gini]), ("Entropy: −p log₂p − (1−p) log₂(1−p)", [line_entropy])],
    location="top_left",
    label_text_font_size="30pt",
    glyph_width=70,
    glyph_height=35,
    spacing=18,
    padding=30,
    border_line_alpha=0,
    background_fill_color="#fafafa",
    background_fill_alpha=0.9,
    click_policy="hide",
)
fig.add_layout(legend)

# Style - text sizes scaled for 4800x2700 canvas
fig.title.text_font_size = "42pt"
fig.title.text_color = "#2a2a2a"
fig.xaxis.axis_label_text_font_size = "32pt"
fig.yaxis.axis_label_text_font_size = "32pt"
fig.xaxis.major_label_text_font_size = "24pt"
fig.yaxis.major_label_text_font_size = "24pt"
fig.xaxis.axis_label_text_color = "#444444"
fig.yaxis.axis_label_text_color = "#444444"

# Tick formatters for clean number display
fig.xaxis.formatter = NumeralTickFormatter(format="0.0")
fig.yaxis.formatter = NumeralTickFormatter(format="0.0")

# Grid - y-axis only, subtle
fig.xgrid.grid_line_alpha = 0
fig.ygrid.grid_line_alpha = 0.15
fig.ygrid.grid_line_color = "#999999"
fig.ygrid.grid_line_dash = [4, 4]

# Background
fig.background_fill_color = "#f8f8f8"
fig.border_fill_color = "white"
fig.outline_line_color = None

# Axis styling
fig.axis.axis_line_width = 2
fig.axis.axis_line_color = "#555555"
fig.axis.minor_tick_line_color = None
fig.axis.major_tick_line_color = "#888888"
fig.axis.major_tick_out = 8

# Remove toolbar for cleaner static image
fig.toolbar_location = None

# Save
export_png(fig, filename="plot.png")

output_file("plot.html")
save(fig)
