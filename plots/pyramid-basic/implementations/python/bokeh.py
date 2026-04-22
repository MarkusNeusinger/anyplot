""" pyplots.ai
pyramid-basic: Basic Pyramid Chart
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, Range1d
from bokeh.plotting import figure


# Data - Population by age group (in thousands)
age_groups = ["0-9", "10-19", "20-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80+"]
male_population = [45, 52, 68, 82, 75, 65, 48, 32, 15]
female_population = [43, 50, 72, 85, 78, 70, 55, 40, 22]

# Negate male values for left side of pyramid
male_negative = [-v for v in male_population]

# Create data sources
source_male = ColumnDataSource(data={"age": age_groups, "population": male_negative})
source_female = ColumnDataSource(data={"age": age_groups, "population": female_population})

# Create figure with categorical y-axis and symmetric x-range
p = figure(
    width=4800,
    height=2700,
    y_range=age_groups,
    x_range=Range1d(-100, 100),
    title="pyramid-basic · bokeh · pyplots.ai",
    x_axis_label="Population (thousands)",
    y_axis_label="Age Group",
)

# Draw horizontal bars - male (left, Python Blue) and female (right, coral pink)
bar_height = 0.7
p.hbar(
    y="age", right="population", height=bar_height, source=source_male, color="#306998", alpha=0.85, legend_label="Male"
)
p.hbar(
    y="age",
    right="population",
    height=bar_height,
    source=source_female,
    color="#E8888C",
    alpha=0.85,
    legend_label="Female",
)

# Text styling for 4800x2700 px canvas
p.title.text_font_size = "32pt"
p.xaxis.axis_label_text_font_size = "24pt"
p.yaxis.axis_label_text_font_size = "24pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Grid styling - subtle dashed lines
p.xgrid.grid_line_alpha = 0.3
p.ygrid.grid_line_alpha = 0.3
p.xgrid.grid_line_dash = [6, 4]
p.ygrid.grid_line_dash = [6, 4]

# Legend styling
p.legend.label_text_font_size = "18pt"
p.legend.location = "top_right"
p.legend.background_fill_alpha = 0.7

# Add center line at x=0 for visual reference
p.line([0, 0], [-0.5, len(age_groups) - 0.5], line_color="#333333", line_width=2, line_alpha=0.5)

# Save outputs
export_png(p, filename="plot.png")
output_file("plot.html")
save(p)
