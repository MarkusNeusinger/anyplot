""" pyplots.ai
histogram-returns-distribution: Returns Distribution Histogram
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-16
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import BoxAnnotation, ColumnDataSource, Label
from bokeh.plotting import figure


# Data - Generate synthetic daily returns for 1 year
np.random.seed(42)
n_days = 252
daily_returns = np.random.normal(loc=0.0005, scale=0.015, size=n_days) * 100  # Convert to percentage

# Calculate statistics manually
mean_return = np.mean(daily_returns)
std_return = np.std(daily_returns)
n = len(daily_returns)
# Skewness: measure of asymmetry
skewness = np.sum(((daily_returns - mean_return) / std_return) ** 3) / n
# Excess kurtosis: measure of tail heaviness (0 for normal distribution)
kurtosis = np.sum(((daily_returns - mean_return) / std_return) ** 4) / n - 3

# Create histogram bins
n_bins = 30
hist, edges = np.histogram(daily_returns, bins=n_bins, density=True)

# Create normal distribution overlay (PDF calculated manually)
x_norm = np.linspace(daily_returns.min() - std_return, daily_returns.max() + std_return, 200)
y_norm = (1 / (std_return * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x_norm - mean_return) / std_return) ** 2)

# Prepare data for histogram bars
hist_source = ColumnDataSource(data={"x": edges[:-1], "top": hist, "width": np.diff(edges)})

# Prepare data for normal curve
norm_source = ColumnDataSource(data={"x": x_norm, "y": y_norm})

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="histogram-returns-distribution · bokeh · pyplots.ai",
    x_axis_label="Daily Returns (%)",
    y_axis_label="Density",
)

# Define tail regions (beyond 2 standard deviations)
lower_tail = mean_return - 2 * std_return
upper_tail = mean_return + 2 * std_return

# Add tail region highlights
left_tail_box = BoxAnnotation(left=None, right=lower_tail, fill_alpha=0.15, fill_color="#E74C3C")
right_tail_box = BoxAnnotation(left=upper_tail, right=None, fill_alpha=0.15, fill_color="#E74C3C")
p.add_layout(left_tail_box)
p.add_layout(right_tail_box)

# Plot histogram bars
for i in range(len(hist)):
    left_edge = edges[i]
    right_edge = edges[i + 1]
    is_tail = (left_edge < lower_tail) or (right_edge > upper_tail)
    color = "#E74C3C" if is_tail else "#306998"
    p.quad(
        top=[hist[i]],
        bottom=[0],
        left=[left_edge],
        right=[right_edge],
        fill_color=color,
        line_color="white",
        fill_alpha=0.7,
        line_width=1,
    )

# Plot normal distribution curve
p.line(x="x", y="y", source=norm_source, line_color="#FFD43B", line_width=4, legend_label="Normal Distribution")

# Add statistics text box
stats_text = f"Mean: {mean_return:.3f}%\nStd Dev: {std_return:.3f}%\nSkewness: {skewness:.3f}\nKurtosis: {kurtosis:.3f}"

# Add label for statistics
stats_label = Label(
    x=70,
    y=570,
    x_units="screen",
    y_units="screen",
    text=stats_text,
    text_font_size="24pt",
    text_color="#333333",
    background_fill_color="white",
    background_fill_alpha=0.8,
    border_line_color="#CCCCCC",
    border_line_width=2,
)
p.add_layout(stats_label)

# Add legend label for tail regions
tail_label = Label(
    x=70,
    y=420,
    x_units="screen",
    y_units="screen",
    text="Red: Beyond 2σ (tail risk)",
    text_font_size="18pt",
    text_color="#E74C3C",
    background_fill_color="white",
    background_fill_alpha=0.8,
)
p.add_layout(tail_label)

# Styling
p.title.text_font_size = "32pt"
p.xaxis.axis_label_text_font_size = "24pt"
p.yaxis.axis_label_text_font_size = "24pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Grid styling
p.xgrid.grid_line_alpha = 0.3
p.ygrid.grid_line_alpha = 0.3
p.xgrid.grid_line_dash = "dashed"
p.ygrid.grid_line_dash = "dashed"

# Legend styling
p.legend.location = "top_right"
p.legend.label_text_font_size = "18pt"
p.legend.background_fill_alpha = 0.8

# Save as PNG and HTML
export_png(p, filename="plot.png")

# Also save as HTML for interactive version
output_file("plot.html")
save(p)
