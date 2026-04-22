""" pyplots.ai
calibration-curve: Calibration Curve
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource, Label
from bokeh.plotting import figure
from bokeh.resources import CDN


# Data - Simulate binary classification predictions with realistic calibration
np.random.seed(42)
n_samples = 5000

# Generate predicted probabilities uniformly across [0, 1]
y_prob = np.random.uniform(0, 1, n_samples)

# Generate true labels based on probabilities with slight miscalibration
# Simulating a model that's slightly overconfident (sigmoid distortion)
calibration_factor = 1.3  # >1 means overconfident
adjusted_prob = 1 / (1 + np.exp(-calibration_factor * (np.log(y_prob / (1 - y_prob + 1e-10)))))
adjusted_prob = np.clip(adjusted_prob, 0.01, 0.99)
y_true = (np.random.uniform(0, 1, n_samples) < adjusted_prob).astype(int)

# Calculate calibration curve (binned)
n_bins = 10
bin_edges = np.linspace(0, 1, n_bins + 1)
bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

fraction_of_positives = []
mean_predicted_value = []
bin_counts = []

for i in range(n_bins):
    mask = (y_prob >= bin_edges[i]) & (y_prob < bin_edges[i + 1])
    if i == n_bins - 1:  # Include right edge for last bin
        mask = (y_prob >= bin_edges[i]) & (y_prob <= bin_edges[i + 1])

    if mask.sum() > 0:
        fraction_of_positives.append(y_true[mask].mean())
        mean_predicted_value.append(y_prob[mask].mean())
        bin_counts.append(mask.sum())
    else:
        fraction_of_positives.append(np.nan)
        mean_predicted_value.append(bin_centers[i])
        bin_counts.append(0)

# Filter out empty bins for plotting
valid_mask = np.array(bin_counts) > 0
mean_pred_valid = np.array(mean_predicted_value)[valid_mask]
frac_pos_valid = np.array(fraction_of_positives)[valid_mask]
counts_valid = np.array(bin_counts)[valid_mask]

# Calculate Brier score
brier_score = np.mean((y_prob - y_true) ** 2)

# Calculate Expected Calibration Error (ECE)
ece = 0
total_samples = sum(bin_counts)
for i in range(len(bin_counts)):
    if bin_counts[i] > 0:
        ece += (bin_counts[i] / total_samples) * abs(fraction_of_positives[i] - mean_predicted_value[i])

# Create main calibration plot
p = figure(
    width=4800,
    height=2700,
    title="calibration-curve · bokeh · pyplots.ai",
    x_axis_label="Mean Predicted Probability",
    y_axis_label="Fraction of Positives",
    x_range=(-0.02, 1.02),
    y_range=(-0.02, 1.02),
)

# Add diagonal reference line (perfect calibration)
p.line([0, 1], [0, 1], line_color="#888888", line_dash="dashed", line_width=4, legend_label="Perfect Calibration")

# Create source for calibration curve
source = ColumnDataSource(data={"x": mean_pred_valid, "y": frac_pos_valid, "count": counts_valid})

# Plot calibration curve with markers
p.line("x", "y", source=source, line_color="#306998", line_width=5, legend_label="Classifier")
p.scatter("x", "y", source=source, size=25, color="#306998", fill_alpha=0.9, line_color="#1a3d5c", line_width=3)

# Add metrics annotation
metrics_text = f"Brier Score: {brier_score:.3f}\nECE: {ece:.3f}"
metrics_label = Label(
    x=0.05,
    y=0.88,
    x_units="data",
    y_units="data",
    text=metrics_text,
    text_font_size="28pt",
    text_color="#333333",
    background_fill_color="white",
    background_fill_alpha=0.9,
)
p.add_layout(metrics_label)

# Style the plot
p.title.text_font_size = "36pt"
p.title.text_font_style = "bold"
p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_font_size = "22pt"
p.yaxis.major_label_text_font_size = "22pt"

# Grid styling
p.xgrid.grid_line_alpha = 0.3
p.ygrid.grid_line_alpha = 0.3
p.xgrid.grid_line_dash = "dashed"
p.ygrid.grid_line_dash = "dashed"

# Legend styling
p.legend.label_text_font_size = "24pt"
p.legend.location = "bottom_right"
p.legend.background_fill_alpha = 0.9
p.legend.border_line_width = 2
p.legend.padding = 15
p.legend.spacing = 10

# Axis styling
p.xaxis.axis_line_width = 2
p.yaxis.axis_line_width = 2
p.xaxis.major_tick_line_width = 2
p.yaxis.major_tick_line_width = 2

# Background
p.background_fill_color = "#fafafa"
p.border_fill_color = "#ffffff"

# Save outputs
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="Calibration Curve")
