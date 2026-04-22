""" pyplots.ai
bland-altman-basic: Bland-Altman Agreement Plot
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-25
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource, Label, Span
from bokeh.plotting import figure
from bokeh.resources import CDN


# Data: Blood pressure readings (mmHg) from two sphygmomanometers
np.random.seed(42)
n = 80

# Generate realistic blood pressure measurements (systolic, 100-160 mmHg)
true_bp = np.random.normal(125, 15, n)
method1 = true_bp + np.random.normal(0, 5, n)
method2 = true_bp + np.random.normal(2, 6, n)  # Slight bias and more variability

# Bland-Altman calculations
mean_values = (method1 + method2) / 2
diff_values = method1 - method2
mean_diff = np.mean(diff_values)
std_diff = np.std(diff_values, ddof=1)
upper_loa = mean_diff + 1.96 * std_diff
lower_loa = mean_diff - 1.96 * std_diff

# Create ColumnDataSource
source = ColumnDataSource(data={"mean": mean_values, "diff": diff_values})

# Create figure (4800 x 2700 px)
p = figure(
    width=4800,
    height=2700,
    title="bland-altman-basic · bokeh · pyplots.ai",
    x_axis_label="Mean of Two Methods (mmHg)",
    y_axis_label="Difference (Method 1 - Method 2) (mmHg)",
)

# Plot scatter points
p.scatter(x="mean", y="diff", source=source, size=18, color="#306998", alpha=0.7, legend_label="Observations")

# Mean difference line (bias)
mean_line = Span(location=mean_diff, dimension="width", line_color="#306998", line_width=3, line_dash="solid")
p.add_layout(mean_line)

# Upper limit of agreement
upper_line = Span(location=upper_loa, dimension="width", line_color="#FFD43B", line_width=3, line_dash="dashed")
p.add_layout(upper_line)

# Lower limit of agreement
lower_line = Span(location=lower_loa, dimension="width", line_color="#FFD43B", line_width=3, line_dash="dashed")
p.add_layout(lower_line)

# Calculate x position for labels (left side of plot, inside the data area)
x_min = np.min(mean_values)
x_label_pos = x_min + (np.max(mean_values) - x_min) * 0.02

# Add annotations for reference lines
mean_label = Label(
    x=x_label_pos,
    y=mean_diff,
    text=f"Mean Bias: {mean_diff:.2f} mmHg",
    text_font_size="20pt",
    text_color="#306998",
    text_baseline="bottom",
    y_offset=5,
)
p.add_layout(mean_label)

upper_label = Label(
    x=x_label_pos,
    y=upper_loa,
    text=f"+1.96 SD: {upper_loa:.2f} mmHg",
    text_font_size="20pt",
    text_color="#C4A000",
    text_baseline="bottom",
    y_offset=5,
)
p.add_layout(upper_label)

lower_label = Label(
    x=x_label_pos,
    y=lower_loa,
    text=f"−1.96 SD: {lower_loa:.2f} mmHg",
    text_font_size="20pt",
    text_color="#C4A000",
    text_baseline="top",
    y_offset=-5,
)
p.add_layout(lower_label)

# Styling for large canvas
p.title.text_font_size = "28pt"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Grid styling
p.grid.grid_line_alpha = 0.3
p.grid.grid_line_dash = "dashed"

# Legend styling
p.legend.label_text_font_size = "18pt"
p.legend.location = "top_left"
p.legend.background_fill_alpha = 0.8

# Output background
p.background_fill_color = "white"
p.border_fill_color = "white"

# Save as PNG and HTML
export_png(p, filename="plot.png")

# Also save HTML for interactive version
save(p, filename="plot.html", resources=CDN, title="Bland-Altman Agreement Plot")
