""" pyplots.ai
coefficient-confidence: Coefficient Plot with Confidence Intervals
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 90/100 | Created: 2026-01-09
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Legend, LegendItem, Span
from bokeh.plotting import figure


# Data - Regression coefficients for housing price prediction model
np.random.seed(42)

variables = [
    "Square Footage",
    "Number of Bedrooms",
    "Number of Bathrooms",
    "Age of House",
    "Distance to City Center",
    "Lot Size",
    "Garage Size",
    "School Rating",
    "Crime Rate Index",
    "Property Tax Rate",
]

# Generate realistic regression coefficients (some significant, some not)
coefficients = np.array([0.45, 0.12, 0.18, -0.08, -0.22, 0.15, 0.09, 0.28, -0.35, -0.05])
std_errors = np.array([0.05, 0.08, 0.06, 0.03, 0.07, 0.04, 0.06, 0.05, 0.09, 0.07])

# Calculate 95% confidence intervals
ci_lower = coefficients - 1.96 * std_errors
ci_upper = coefficients + 1.96 * std_errors

# Determine significance (CI does not cross zero)
significant = ~((ci_lower < 0) & (ci_upper > 0))

# Sort by coefficient magnitude for better visualization
sort_idx = np.argsort(np.abs(coefficients))
variables = [variables[i] for i in sort_idx]
coefficients = coefficients[sort_idx]
ci_lower = ci_lower[sort_idx]
ci_upper = ci_upper[sort_idx]
significant = significant[sort_idx]

# Strong color contrast for significant vs non-significant distinction
# Using vivid blue (#2171b5) for significant vs muted gray (#969696) for non-significant
SIG_COLOR = "#2171b5"
NONSIG_COLOR = "#969696"

colors = [SIG_COLOR if sig else NONSIG_COLOR for sig in significant]

# Create figure with categorical y-axis
p = figure(
    width=4800,
    height=2700,
    y_range=variables,
    title="coefficient-confidence · bokeh · pyplots.ai",
    x_axis_label="Coefficient Estimate (Standardized)",
    y_axis_label="Predictor Variable",
)

# Add vertical reference line at zero
zero_line = Span(location=0, dimension="height", line_color="#333333", line_width=3, line_dash="dashed")
p.add_layout(zero_line)

# Draw confidence interval segments (error bars) with distinct colors
for i, var in enumerate(variables):
    color = colors[i]
    # Main confidence interval line
    p.line(x=[ci_lower[i], ci_upper[i]], y=[var, var], line_width=6, line_color=color, line_alpha=0.85)

# Plot coefficient points - separate renderers for legend with distinct colors
sig_indices = [i for i, s in enumerate(significant) if s]
nonsig_indices = [i for i, s in enumerate(significant) if not s]

# Create separate data sources for legend
sig_source = ColumnDataSource(
    data={
        "variables": [variables[i] for i in sig_indices],
        "coefficients": [coefficients[i] for i in sig_indices],
        "ci_lower_fmt": [f"{ci_lower[i]:.3f}" for i in sig_indices],
        "ci_upper_fmt": [f"{ci_upper[i]:.3f}" for i in sig_indices],
        "coef_fmt": [f"{coefficients[i]:.3f}" for i in sig_indices],
        "significance": ["Significant (p < 0.05)"] * len(sig_indices),
    }
)

nonsig_source = ColumnDataSource(
    data={
        "variables": [variables[i] for i in nonsig_indices],
        "coefficients": [coefficients[i] for i in nonsig_indices],
        "ci_lower_fmt": [f"{ci_lower[i]:.3f}" for i in nonsig_indices],
        "ci_upper_fmt": [f"{ci_upper[i]:.3f}" for i in nonsig_indices],
        "coef_fmt": [f"{coefficients[i]:.3f}" for i in nonsig_indices],
        "significance": ["Not Significant"] * len(nonsig_indices),
    }
)

# Render significant points with vivid blue
sig_renderer = p.scatter(
    x="coefficients", y="variables", source=sig_source, size=30, color=SIG_COLOR, line_color="white", line_width=3
)

# Render non-significant points with muted gray
nonsig_renderer = p.scatter(
    x="coefficients", y="variables", source=nonsig_source, size=30, color=NONSIG_COLOR, line_color="white", line_width=3
)

# Add HoverTool for interactive tooltips (Bokeh distinctive feature)
hover = HoverTool(
    tooltips=[
        ("Variable", "@variables"),
        ("Coefficient", "@coef_fmt"),
        ("95% CI", "[@ci_lower_fmt, @ci_upper_fmt]"),
        ("Status", "@significance"),
    ],
    renderers=[sig_renderer, nonsig_renderer],
)
p.add_tools(hover)

# Create legend inside the plot area (top right corner within plot bounds)
legend = Legend(
    items=[
        LegendItem(label="Significant (p < 0.05)", renderers=[sig_renderer]),
        LegendItem(label="Not Significant", renderers=[nonsig_renderer]),
    ],
    location="top_right",
    label_text_font_size="24pt",
    glyph_width=40,
    glyph_height=40,
    border_line_color="#666666",
    border_line_width=2,
    background_fill_color="white",
    background_fill_alpha=0.95,
    padding=20,
    margin=30,
)
p.add_layout(legend)

# Style text sizes for large canvas (increased for better readability)
p.title.text_font_size = "36pt"
p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_font_size = "22pt"
p.yaxis.major_label_text_font_size = "22pt"

# Grid styling
p.xgrid.grid_line_alpha = 0.3
p.xgrid.grid_line_dash = "dashed"
p.ygrid.grid_line_alpha = 0.3
p.ygrid.grid_line_dash = "dashed"

# Background styling
p.background_fill_color = "#fafafa"
p.border_fill_color = "white"

# Increase axis line width for visibility
p.xaxis.axis_line_width = 2
p.yaxis.axis_line_width = 2
p.xaxis.major_tick_line_width = 2
p.yaxis.major_tick_line_width = 2

# Save plot (PNG and HTML for interactive)
export_png(p, filename="plot.png")
output_file("plot.html", title="Coefficient Plot with Confidence Intervals")
save(p)
