""" pyplots.ai
gain-curve: Cumulative Gains Chart
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-29
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, Legend
from bokeh.plotting import figure


# Data - Simulated customer response model
np.random.seed(42)
n_samples = 1000

# Generate realistic probability scores from a classification model
# Positive class has higher predicted probabilities on average
positive_ratio = 0.15
n_positive = int(n_samples * positive_ratio)
n_negative = n_samples - n_positive

# Scores for positive cases (skewed towards higher probabilities)
positive_scores = np.random.beta(5, 2, n_positive)
# Scores for negative cases (skewed towards lower probabilities)
negative_scores = np.random.beta(2, 5, n_negative)

y_true = np.concatenate([np.ones(n_positive), np.zeros(n_negative)])
y_score = np.concatenate([positive_scores, negative_scores])

# Shuffle to mix positives and negatives
shuffle_idx = np.random.permutation(n_samples)
y_true = y_true[shuffle_idx]
y_score = y_score[shuffle_idx]

# Calculate cumulative gains curve
# Sort by predicted probability (descending)
sorted_idx = np.argsort(y_score)[::-1]
y_true_sorted = y_true[sorted_idx]

# Cumulative gains
cumulative_positives = np.cumsum(y_true_sorted)
total_positives = np.sum(y_true)

# Percentages for axes
pct_population = np.arange(1, n_samples + 1) / n_samples * 100
pct_captured = cumulative_positives / total_positives * 100

# Add origin point for complete curve
pct_population = np.insert(pct_population, 0, 0)
pct_captured = np.insert(pct_captured, 0, 0)

# Random baseline (diagonal line)
baseline = np.array([0, 100])

# Perfect model curve
positive_pct = positive_ratio * 100
perfect_x = np.array([0, positive_pct, 100])
perfect_y = np.array([0, 100, 100])

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="gain-curve · bokeh · pyplots.ai",
    x_axis_label="Percentage of Population Targeted (%)",
    y_axis_label="Percentage of Positive Cases Captured (%)",
    x_range=(0, 100),
    y_range=(0, 105),
)

# Create data sources
source_model = ColumnDataSource(data={"x": pct_population, "y": pct_captured})
source_baseline = ColumnDataSource(data={"x": baseline, "y": baseline})
source_perfect = ColumnDataSource(data={"x": perfect_x, "y": perfect_y})

# Plot the curves
# Model gain curve
model_line = p.line(x="x", y="y", source=source_model, line_color="#306998", line_width=4, line_alpha=0.9)

# Random baseline
baseline_line = p.line(
    x="x", y="y", source=source_baseline, line_color="#888888", line_width=3, line_dash="dashed", line_alpha=0.7
)

# Perfect model
perfect_line = p.line(
    x="x", y="y", source=source_perfect, line_color="#FFD43B", line_width=3, line_dash="dotted", line_alpha=0.8
)

# Add legend
legend = Legend(
    items=[("Model Gain Curve", [model_line]), ("Random Baseline", [baseline_line]), ("Perfect Model", [perfect_line])],
    location="center",
)

legend.label_text_font_size = "20pt"
legend.glyph_height = 30
legend.glyph_width = 50
legend.spacing = 15
legend.padding = 20
legend.background_fill_alpha = 0.9
legend.border_line_color = "#cccccc"
legend.border_line_width = 2
p.add_layout(legend, "right")

# Styling
p.title.text_font_size = "28pt"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Grid styling
p.xgrid.grid_line_alpha = 0.3
p.ygrid.grid_line_alpha = 0.3
p.xgrid.grid_line_dash = "dashed"
p.ygrid.grid_line_dash = "dashed"

# Background
p.background_fill_color = "#fafafa"
p.border_fill_color = "#ffffff"

# Save
export_png(p, filename="plot.png")
output_file("plot.html")
save(p)
