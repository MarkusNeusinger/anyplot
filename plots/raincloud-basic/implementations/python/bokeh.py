"""pyplots.ai
raincloud-basic: Basic Raincloud Plot
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-25
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import ColumnDataSource, HoverTool, Legend, LegendItem
from bokeh.plotting import figure, output_file, save


# Data - Reaction times (ms) for different treatment groups
np.random.seed(42)
categories = ["Control", "Treatment A", "Treatment B", "Treatment C"]
n_points = [80, 75, 85, 70]

# Generate realistic reaction time data with different distributions
data = {
    "Control": np.random.normal(450, 80, n_points[0]),
    "Treatment A": np.random.normal(380, 60, n_points[1]),
    "Treatment B": np.concatenate(
        [np.random.normal(350, 40, n_points[2] // 2), np.random.normal(450, 50, n_points[2] - n_points[2] // 2)]
    ),  # Bimodal
    "Treatment C": np.random.normal(320, 50, n_points[3]),
}

# Color palette - Python Blue and Yellow first, then accessible colors
colors = ["#306998", "#FFD43B", "#2E8B57", "#E07B53"]

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="raincloud-basic · bokeh · pyplots.ai",
    x_axis_label="Reaction Time (ms)",
    y_axis_label="Treatment Group",
    y_range=[-0.5, len(categories) - 0.5],
    x_range=[150, 650],
    tools="pan,box_zoom,wheel_zoom,reset,save",
)

# Style settings
p.title.text_font_size = "32pt"
p.xaxis.axis_label_text_font_size = "24pt"
p.yaxis.axis_label_text_font_size = "24pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.grid.grid_line_alpha = 0.3
p.grid.grid_line_dash = [6, 4]

# Custom y-axis ticks for categories
p.yaxis.ticker = list(range(len(categories)))
p.yaxis.major_label_overrides = dict(enumerate(categories))

# Legend items
legend_items = []

# Plot each category
for idx, (cat, values) in enumerate(data.items()):
    color = colors[idx]
    y_base = idx

    # Calculate KDE for half-violin (cloud) using Silverman's rule
    n = len(values)
    std = np.std(values)
    bw = 1.06 * std * n ** (-1 / 5)  # Silverman bandwidth

    x_min, x_max = values.min() - 20, values.max() + 20
    x_kde = np.linspace(x_min, x_max, 200)

    # Gaussian kernel density estimation
    y_kde = np.zeros_like(x_kde)
    for point in values:
        y_kde += np.exp(-0.5 * ((x_kde - point) / bw) ** 2) / (bw * np.sqrt(2 * np.pi))
    y_kde /= n

    # Normalize and scale KDE to fit in 0.35 height above the center line
    y_kde_scaled = y_kde / y_kde.max() * 0.35

    # Create half-violin patch (cloud) - above center
    violin_x = np.concatenate([x_kde, x_kde[::-1]])
    violin_y = np.concatenate([y_base + y_kde_scaled, np.full(len(x_kde), y_base)])

    source_violin = ColumnDataSource(data={"x": violin_x, "y": violin_y})
    p.patch(x="x", y="y", source=source_violin, fill_color=color, fill_alpha=0.6, line_color=color, line_width=2)

    # Jittered points (rain) - below center
    jitter = np.random.uniform(-0.25, -0.05, len(values))

    # Calculate statistics for tooltip
    q1 = np.percentile(values, 25)
    q2 = np.percentile(values, 50)  # median
    q3 = np.percentile(values, 75)
    mean_val = np.mean(values)
    std_val = np.std(values)

    source_points = ColumnDataSource(
        data={
            "x": values,
            "y": y_base + jitter,
            "category": [cat] * len(values),
            "value": values,
            "mean": [f"{mean_val:.1f}"] * len(values),
            "median": [f"{q2:.1f}"] * len(values),
            "std": [f"{std_val:.1f}"] * len(values),
        }
    )
    scatter_glyph = p.scatter(
        x="x",
        y="y",
        source=source_points,
        size=12,
        color=color,
        alpha=0.6,
        line_color="white",
        line_width=1,
        name=f"points_{idx}",
    )

    # Add legend item (only one per category, using the scatter points)
    legend_items.append(LegendItem(label=cat, renderers=[scatter_glyph]))

    # Box plot elements - at center
    iqr = q3 - q1
    whisker_low = max(min(values), q1 - 1.5 * iqr)
    whisker_high = min(max(values), q3 + 1.5 * iqr)

    box_height = 0.08

    # Whiskers
    p.line(x=[whisker_low, q1], y=[y_base, y_base], line_color="#333333", line_width=3)
    p.line(x=[q3, whisker_high], y=[y_base, y_base], line_color="#333333", line_width=3)

    # Whisker caps
    p.line(
        x=[whisker_low, whisker_low],
        y=[y_base - box_height / 2, y_base + box_height / 2],
        line_color="#333333",
        line_width=3,
    )
    p.line(
        x=[whisker_high, whisker_high],
        y=[y_base - box_height / 2, y_base + box_height / 2],
        line_color="#333333",
        line_width=3,
    )

    # Box (IQR)
    box_source = ColumnDataSource(
        data={
            "x": [q1, q3, q3, q1],
            "y": [y_base - box_height, y_base - box_height, y_base + box_height, y_base + box_height],
        }
    )
    p.patch(x="x", y="y", source=box_source, fill_color="white", fill_alpha=0.9, line_color="#333333", line_width=3)

    # Median line
    p.line(x=[q2, q2], y=[y_base - box_height, y_base + box_height], line_color="#333333", line_width=4)

# Collect scatter renderers for HoverTool
scatter_renderers = [r for r in p.renderers if hasattr(r, "name") and r.name and r.name.startswith("points_")]

# Add HoverTool for interactive exploration
hover = HoverTool(
    renderers=scatter_renderers,
    tooltips=[
        ("Group", "@category"),
        ("Value", "@value{0.1f} ms"),
        ("Mean", "@mean ms"),
        ("Median", "@median ms"),
        ("Std Dev", "@std ms"),
    ],
    mode="mouse",
)
p.add_tools(hover)

# Create legend and position it outside the plot area (right side)
legend = Legend(
    items=legend_items,
    location="center",
    label_text_font_size="18pt",
    glyph_width=30,
    glyph_height=30,
    spacing=10,
    padding=15,
    background_fill_alpha=0.9,
    border_line_color="#cccccc",
)
p.add_layout(legend, "right")
p.legend.click_policy = "hide"

# Save outputs
export_png(p, filename="plot.png")
output_file("plot.html", title="raincloud-basic · bokeh · pyplots.ai")
save(p)
