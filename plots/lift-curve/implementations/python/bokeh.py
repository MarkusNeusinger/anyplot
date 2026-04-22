""" pyplots.ai
lift-curve: Model Lift Chart
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-27
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, Span
from bokeh.plotting import figure


# Data - Simulated customer response data for marketing campaign
np.random.seed(42)
n_samples = 1000

# Create realistic model predictions with reasonable discrimination
# Mix of responders and non-responders
y_true = np.random.binomial(1, 0.15, n_samples)  # 15% baseline response rate

# Generate scores that correlate with true outcomes but imperfectly
noise = np.random.normal(0, 0.3, n_samples)
y_score = 0.3 + 0.5 * y_true + noise
y_score = np.clip(y_score, 0, 1)  # Keep scores in valid range

# Calculate lift curve data
# Sort by predicted score descending
sorted_indices = np.argsort(y_score)[::-1]
y_true_sorted = y_true[sorted_indices]

# Calculate cumulative lift at each percentage
n_positives = y_true.sum()
baseline_rate = n_positives / n_samples

# Create percentile bins (0% to 100%)
percentiles = np.arange(1, 101)
cumulative_lift = []
cumulative_response_rate = []

for pct in percentiles:
    n_selected = int(n_samples * pct / 100)
    n_positives_selected = y_true_sorted[:n_selected].sum()
    response_rate = n_positives_selected / n_selected if n_selected > 0 else 0
    lift = response_rate / baseline_rate if baseline_rate > 0 else 0
    cumulative_lift.append(lift)
    cumulative_response_rate.append(response_rate)

# Create data source
source = ColumnDataSource(
    data={"percentile": percentiles, "lift": cumulative_lift, "response_rate": cumulative_response_rate}
)

# Create figure - 4800 × 2700 px for large canvas
p = figure(
    width=4800,
    height=2700,
    title="lift-curve · bokeh · pyplots.ai",
    x_axis_label="Population Targeted (%)",
    y_axis_label="Cumulative Lift Ratio",
    x_range=(0, 105),
    y_range=(0, max(cumulative_lift) * 1.15),
)

# Add horizontal reference line at y=1 (random selection baseline)
baseline = Span(location=1, dimension="width", line_color="#888888", line_width=3, line_dash="dashed")
p.add_layout(baseline)

# Plot the lift curve
lift_line = p.line(
    x="percentile", y="lift", source=source, line_width=5, line_color="#306998", legend_label="Model Lift"
)

# Add scatter points at deciles for emphasis
decile_indices = [9, 19, 29, 39, 49, 59, 69, 79, 89, 99]  # 10%, 20%, ... 100%
decile_source = ColumnDataSource(
    data={"percentile": [percentiles[i] for i in decile_indices], "lift": [cumulative_lift[i] for i in decile_indices]}
)

p.scatter(
    x="percentile",
    y="lift",
    source=decile_source,
    size=20,
    fill_color="#FFD43B",
    line_color="#306998",
    line_width=3,
    legend_label="Decile Markers",
)

# Styling for large canvas (4800x2700 px)
p.title.text_font_size = "42pt"
p.title.text_font_style = "bold"
p.xaxis.axis_label_text_font_size = "32pt"
p.yaxis.axis_label_text_font_size = "32pt"
p.xaxis.major_label_text_font_size = "24pt"
p.yaxis.major_label_text_font_size = "24pt"
p.xaxis.axis_label_standoff = 25
p.yaxis.axis_label_standoff = 25

# Grid styling
p.xgrid.grid_line_alpha = 0.3
p.ygrid.grid_line_alpha = 0.3
p.xgrid.grid_line_dash = [6, 4]
p.ygrid.grid_line_dash = [6, 4]

# Legend styling
p.legend.location = "top_right"
p.legend.label_text_font_size = "24pt"
p.legend.background_fill_alpha = 0.8
p.legend.border_line_width = 2
p.legend.padding = 20
p.legend.spacing = 15

# Background
p.background_fill_color = "#fafafa"
p.border_fill_color = "white"

# Save as PNG
export_png(p, filename="plot.png")

# Save as HTML for interactivity
output_file("plot.html")
save(p)
