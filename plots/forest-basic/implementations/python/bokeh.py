""" pyplots.ai
forest-basic: Meta-Analysis Forest Plot
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-27
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource, Label, Span
from bokeh.plotting import figure


# Data - Meta-analysis of blood pressure reduction trials
np.random.seed(42)

studies = [
    "Smith et al. 2018",
    "Johnson et al. 2019",
    "Williams et al. 2019",
    "Brown et al. 2020",
    "Davis et al. 2020",
    "Miller et al. 2021",
    "Wilson et al. 2021",
    "Moore et al. 2022",
    "Taylor et al. 2022",
    "Anderson et al. 2023",
    "Thomas et al. 2023",
    "Pooled Estimate",
]

# Effect sizes (mean difference in mmHg) with confidence intervals
effect_sizes = np.array([-3.2, -5.1, -2.8, -4.5, -6.2, -3.9, -4.1, -5.8, -3.5, -4.7, -2.9, -4.2])
ci_lower = np.array([-5.8, -8.2, -5.1, -7.3, -9.1, -6.5, -6.8, -8.9, -6.2, -7.4, -5.6, -5.1])
ci_upper = np.array([-0.6, -2.0, -0.5, -1.7, -3.3, -1.3, -1.4, -2.7, -0.8, -2.0, -0.2, -3.3])

# Weights based on sample size (larger = more precise)
weights = np.array([8, 12, 6, 15, 10, 9, 11, 14, 7, 13, 5, 20])

# Y positions (reversed so first study is at top)
y_positions = list(range(len(studies) - 1, -1, -1))

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="forest-basic · bokeh · pyplots.ai",
    x_axis_label="Mean Difference in Blood Pressure (mmHg)",
    y_range=(-0.5, len(studies) - 0.5),
    x_range=(-12, 4),
    tools="",
    toolbar_location=None,
)

# Add vertical reference line at null effect (0)
null_line = Span(location=0, dimension="height", line_color="#666666", line_width=3, line_dash="dashed")
p.add_layout(null_line)

# Prepare data for individual studies (excluding pooled estimate)
study_source = ColumnDataSource(
    data={
        "study": studies[:-1],
        "effect": effect_sizes[:-1],
        "ci_lower": ci_lower[:-1],
        "ci_upper": ci_upper[:-1],
        "y": y_positions[:-1],
        "size": (weights[:-1] / weights[:-1].max() * 25 + 10).tolist(),
    }
)

# Draw confidence interval lines (whiskers)
for i in range(len(studies) - 1):
    p.line(x=[ci_lower[i], ci_upper[i]], y=[y_positions[i], y_positions[i]], line_width=4, line_color="#306998")
    # Add CI end caps
    p.line(
        x=[ci_lower[i], ci_lower[i]],
        y=[y_positions[i] - 0.15, y_positions[i] + 0.15],
        line_width=3,
        line_color="#306998",
    )
    p.line(
        x=[ci_upper[i], ci_upper[i]],
        y=[y_positions[i] - 0.15, y_positions[i] + 0.15],
        line_width=3,
        line_color="#306998",
    )

# Plot effect size points (size proportional to weight)
p.scatter(x="effect", y="y", source=study_source, size="size", color="#306998", alpha=0.9)

# Add study labels on the left
for i, study in enumerate(studies[:-1]):
    label = Label(
        x=-11.5,
        y=y_positions[i],
        text=study,
        text_font_size="18pt",
        text_align="left",
        text_baseline="middle",
        text_color="#333333",
    )
    p.add_layout(label)

# Draw pooled estimate as a diamond
pooled_y = y_positions[-1]
pooled_effect = effect_sizes[-1]
pooled_lower = ci_lower[-1]
pooled_upper = ci_upper[-1]

# Diamond vertices
diamond_x = [pooled_lower, pooled_effect, pooled_upper, pooled_effect, pooled_lower]
diamond_y = [pooled_y, pooled_y + 0.25, pooled_y, pooled_y - 0.25, pooled_y]

p.patch(x=diamond_x, y=diamond_y, fill_color="#FFD43B", line_color="#306998", line_width=3, alpha=0.9)

# Add pooled estimate label
pooled_label = Label(
    x=-11.5,
    y=pooled_y,
    text="Pooled Estimate",
    text_font_size="18pt",
    text_font_style="bold",
    text_align="left",
    text_baseline="middle",
    text_color="#333333",
)
p.add_layout(pooled_label)

# Add "Favors Treatment" and "Favors Control" labels
favors_treatment = Label(
    x=-6,
    y=-0.35,
    text="← Favors Treatment",
    text_font_size="16pt",
    text_align="center",
    text_baseline="top",
    text_color="#666666",
)
p.add_layout(favors_treatment)

favors_control = Label(
    x=2,
    y=-0.35,
    text="Favors Control →",
    text_font_size="16pt",
    text_align="center",
    text_baseline="top",
    text_color="#666666",
)
p.add_layout(favors_control)

# Styling
p.title.text_font_size = "28pt"
p.title.text_color = "#333333"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Hide y-axis ticks and labels (studies are labeled manually)
p.yaxis.visible = False

# Grid styling
p.xgrid.grid_line_color = "#cccccc"
p.xgrid.grid_line_alpha = 0.3
p.xgrid.grid_line_dash = "dashed"
p.ygrid.grid_line_color = None

# Background
p.background_fill_color = "#ffffff"
p.border_fill_color = "#ffffff"

# Save as PNG and HTML
export_png(p, filename="plot.png")
save(p, filename="plot.html", title="forest-basic · bokeh · pyplots.ai")
