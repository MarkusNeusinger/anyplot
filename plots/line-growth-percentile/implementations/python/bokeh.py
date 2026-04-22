""" pyplots.ai
line-growth-percentile: Pediatric Growth Chart with Percentile Curves
Library: bokeh 3.9.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-19
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Label, Legend
from bokeh.plotting import figure


# Data - WHO-style weight-for-age reference for boys (0-36 months)
np.random.seed(42)
age_months = np.linspace(0, 36, 73)

# Approximate WHO weight-for-age percentile curves for boys (kg)
# Realistic growth: rapid early gain tapering off
median_weight = 3.3 + 0.7 * age_months - 0.012 * age_months**2 + 0.00012 * age_months**3
sd_factor = 0.35 + 0.03 * age_months

percentile_97 = median_weight + 1.88 * sd_factor
percentile_90 = median_weight + 1.28 * sd_factor
percentile_75 = median_weight + 0.67 * sd_factor
percentile_50 = median_weight
percentile_25 = median_weight - 0.67 * sd_factor
percentile_10 = median_weight - 1.28 * sd_factor
percentile_3 = median_weight - 1.88 * sd_factor

# Individual patient data - a healthy boy tracked at well-child visits
patient_age = np.array([0, 1, 2, 4, 6, 9, 12, 15, 18, 24, 30, 36])
patient_weight = np.array([3.4, 4.3, 5.4, 6.8, 7.8, 9.0, 10.0, 10.8, 11.5, 12.6, 13.8, 14.8])

# Plot
p = figure(
    width=4800,
    height=2700,
    title="Boys Weight-for-Age (0–36 months) · line-growth-percentile · bokeh · pyplots.ai",
    x_axis_label="Age (months)",
    y_axis_label="Weight (kg)",
    toolbar_location=None,
)

# Percentile band colors - blue tones for boys (darker at extremes, lighter near median)
band_colors = [
    "#1a5276",  # P3-P10
    "#2980b9",  # P10-P25
    "#85c1e9",  # P25-P50
    "#85c1e9",  # P50-P75
    "#2980b9",  # P75-P90
    "#1a5276",  # P90-P97
]
band_alphas = [0.55, 0.45, 0.40, 0.40, 0.45, 0.55]

# Draw filled percentile bands (from outer to inner)
bands = [
    (percentile_3, percentile_10),
    (percentile_10, percentile_25),
    (percentile_25, percentile_50),
    (percentile_50, percentile_75),
    (percentile_75, percentile_90),
    (percentile_90, percentile_97),
]

renderers = []
for i, (lower, upper) in enumerate(bands):
    source = ColumnDataSource(data={"x": age_months, "y1": lower, "y2": upper})
    r = p.varea(x="x", y1="y1", y2="y2", source=source, fill_color=band_colors[i], fill_alpha=band_alphas[i])
    renderers.append(r)

# Draw percentile lines
percentile_data = [
    (percentile_3, "P3", 2, 0.5),
    (percentile_10, "P10", 2, 0.5),
    (percentile_25, "P25", 2, 0.5),
    (percentile_50, "P50", 5, 0.9),
    (percentile_75, "P75", 2, 0.5),
    (percentile_90, "P90", 2, 0.5),
    (percentile_97, "P97", 2, 0.5),
]

for values, label, width, alpha in percentile_data:
    source = ColumnDataSource(data={"x": age_months, "y": values})
    p.line(x="x", y="y", source=source, line_color="#1a5276", line_width=width, line_alpha=alpha)
    # Percentile label on right margin
    lbl = Label(
        x=age_months[-1] + 0.5,
        y=values[-1],
        text=label,
        text_font_size="20pt",
        text_color="#1a5276",
        text_alpha=0.8,
        text_baseline="middle",
    )
    p.add_layout(lbl)

# Patient data overlay
patient_source = ColumnDataSource(data={"x": patient_age, "y": patient_weight})
r_line = p.line(x="x", y="y", source=patient_source, line_color="#e74c3c", line_width=4)
r_scatter = p.scatter(x="x", y="y", source=patient_source, size=18, color="#e74c3c", line_color="white", line_width=2)

# HoverTool for patient data points (interactive in HTML export)
hover = HoverTool(renderers=[r_scatter], tooltips=[("Age", "@x months"), ("Weight", "@y kg")], mode="mouse")
p.add_tools(hover)

# Legend
legend = Legend(
    items=[("Patient", [r_line, r_scatter]), ("Percentile bands (P3–P97)", [renderers[0]])], location="top_left"
)
p.add_layout(legend)

# Style
p.title.text_font_size = "36pt"
p.title.text_font_style = "bold"
p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_font_size = "22pt"
p.yaxis.major_label_text_font_size = "22pt"
p.legend.label_text_font_size = "22pt"
p.legend.glyph_height = 35
p.legend.glyph_width = 35
p.legend.spacing = 12
p.legend.padding = 20
p.legend.background_fill_alpha = 0.85

p.xgrid.grid_line_color = "#cccccc"
p.xgrid.grid_line_alpha = 0.3
p.xgrid.grid_line_dash = "dashed"
p.ygrid.grid_line_color = "#cccccc"
p.ygrid.grid_line_alpha = 0.3
p.ygrid.grid_line_dash = "dashed"

# Refined axis styling - remove heavy default chrome
p.outline_line_color = None
p.axis.axis_line_color = "#666666"
p.axis.axis_line_width = 1.5
p.axis.major_tick_line_color = "#666666"
p.axis.major_tick_line_width = 1.5
p.axis.minor_tick_line_color = None

# Background styling
p.background_fill_color = "#f8f9fa"
p.border_fill_color = "white"

p.y_range.start = 0
p.x_range.end = 37.5

p.min_border_left = 100
p.min_border_right = 120
p.min_border_top = 50
p.min_border_bottom = 80

# Save
export_png(p, filename="plot.png")
output_file("plot.html", title="line-growth-percentile · bokeh · pyplots.ai")
save(p)
