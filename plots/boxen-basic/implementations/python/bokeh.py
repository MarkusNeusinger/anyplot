""" pyplots.ai
boxen-basic: Basic Boxen Plot (Letter-Value Plot)
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-09
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import ColumnDataSource, Legend, LegendItem
from bokeh.plotting import figure


# Data - Server response times by endpoint (large datasets ideal for boxen)
np.random.seed(42)

# Generate 5000 points per category with different distributions
categories = ["API Auth", "API Users", "API Orders", "API Search"]
data = {
    "API Auth": np.concatenate(
        [np.random.exponential(50, 4000) + 20, np.random.normal(200, 30, 800), np.random.uniform(400, 600, 200)]
    ),
    "API Users": np.concatenate([np.random.normal(80, 25, 4500), np.random.uniform(180, 300, 500)]),
    "API Orders": np.concatenate([np.random.lognormal(4, 0.5, 4800), np.random.uniform(300, 500, 200)]),
    "API Search": np.concatenate([np.random.gamma(3, 30, 4600), np.random.uniform(350, 550, 400)]),
}


# Letter-value quantiles: median, fourths, eighths, sixteenths, 32nds, 64ths
def compute_letter_values(arr, depth=6):
    """Compute letter values (quantile levels) for boxen plot."""
    levels = []
    for i in range(depth):
        q_low = 0.5 ** (i + 1)
        q_high = 1 - q_low
        lower = np.percentile(arr, q_low * 100)
        upper = np.percentile(arr, q_high * 100)
        levels.append((lower, upper, i))
    return levels


# Create figure
p = figure(
    width=4800,
    height=2700,
    title="boxen-basic · bokeh · pyplots.ai",
    x_axis_label="API Endpoint",
    y_axis_label="Response Time (ms)",
    x_range=categories,
)

# Colors for quantile levels (gradient from light to dark blue)
colors = [
    "#a8d4f0",  # Lightest - median (50%)
    "#7bbce0",  # Fourths (25-75%)
    "#4da4d0",  # Eighths
    "#306998",  # Sixteenths - Python Blue
    "#1e4d6b",  # 32nds
    "#0d3048",  # 64ths - darkest
]

# Width factors for nested boxes (wider outer, narrower inner)
width_factors = [0.75, 0.65, 0.55, 0.45, 0.35, 0.25]

# Track renderers for legend
legend_items = []

# Plot boxen for each category
for cat_idx, category in enumerate(categories):
    values = data[category]
    letter_values = compute_letter_values(values, depth=6)

    # Plot from outer to inner (deepest quantile first, so inner boxes are on top)
    for level_idx in range(len(letter_values) - 1, -1, -1):
        lower, upper, _ = letter_values[level_idx]
        width = width_factors[level_idx]
        color = colors[level_idx]

        # Create box as a quad
        source = ColumnDataSource(
            data={"left": [cat_idx - width / 2], "right": [cat_idx + width / 2], "bottom": [lower], "top": [upper]}
        )

        renderer = p.quad(
            left="left",
            right="right",
            bottom="bottom",
            top="top",
            source=source,
            fill_color=color,
            line_color="#1a3a5c",
            line_width=2,
            fill_alpha=0.95,
        )

        # Add legend item only once per level (first category)
        if cat_idx == 0:
            level_names = ["Median (50%)", "Fourths (25-75%)", "Eighths (12.5-87.5%)", "Sixteenths", "32nds", "64ths"]
            legend_items.append(LegendItem(label=level_names[level_idx], renderers=[renderer]))

    # Add median line
    median = np.median(values)
    median_width = width_factors[0]
    p.line(
        x=[cat_idx - median_width / 2, cat_idx + median_width / 2],
        y=[median, median],
        line_color="#FFD43B",
        line_width=5,
    )

    # Add outliers (beyond 64th percentile level)
    deepest_lower, deepest_upper, _ = letter_values[-1]
    outliers = values[(values < deepest_lower) | (values > deepest_upper)]
    if len(outliers) > 0:
        # Jitter x positions for visibility
        jitter = np.random.uniform(-0.12, 0.12, len(outliers))
        outlier_source = ColumnDataSource(data={"x": [cat_idx + j for j in jitter], "y": outliers})
        p.scatter(
            x="x",
            y="y",
            source=outlier_source,
            size=10,
            fill_color="#FFD43B",
            line_color="#1a3a5c",
            line_width=1,
            alpha=0.7,
        )

# Add median line to legend first
median_renderer = p.line(x=[], y=[], line_color="#FFD43B", line_width=5)
legend_items.insert(0, LegendItem(label="Median Line", renderers=[median_renderer]))

# Add outlier to legend
outlier_renderer = p.scatter(x=[], y=[], size=12, fill_color="#FFD43B", line_color="#1a3a5c")
legend_items.append(LegendItem(label="Outliers", renderers=[outlier_renderer]))

# Create and add legend
legend = Legend(items=legend_items, location="top_right")
legend.label_text_font_size = "18pt"
legend.glyph_height = 30
legend.glyph_width = 30
legend.spacing = 12
legend.padding = 20
legend.background_fill_alpha = 0.8
p.add_layout(legend, "right")

# Styling
p.title.text_font_size = "32pt"
p.title.text_font_style = "bold"
p.xaxis.axis_label_text_font_size = "24pt"
p.yaxis.axis_label_text_font_size = "24pt"
p.xaxis.major_label_text_font_size = "20pt"
p.yaxis.major_label_text_font_size = "18pt"
p.xaxis.major_label_orientation = 0.0

# Grid
p.xgrid.grid_line_color = None
p.ygrid.grid_line_alpha = 0.3
p.ygrid.grid_line_dash = "dashed"

# Background
p.background_fill_color = "#fafafa"
p.border_fill_color = "#ffffff"

# Axis styling
p.xaxis.axis_line_width = 2
p.yaxis.axis_line_width = 2
p.outline_line_width = 2

# Save
export_png(p, filename="plot.png")
