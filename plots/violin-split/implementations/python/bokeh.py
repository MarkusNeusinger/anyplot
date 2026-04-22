""" pyplots.ai
violin-split: Split Violin Plot
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import HoverTool, Legend, LegendItem
from bokeh.plotting import figure


# Data - Employee satisfaction scores before/after training across departments
np.random.seed(42)

categories = ["Engineering", "Marketing", "Sales", "Support"]
split_groups = ["Before Training", "After Training"]
n_per_group = 150

# Generate realistic satisfaction data (1-10 scale)
data = []
for cat in categories:
    # Base satisfaction varies by department
    base = {"Engineering": 6.5, "Marketing": 5.8, "Sales": 5.2, "Support": 5.5}[cat]
    improvement = {"Engineering": 1.2, "Marketing": 1.5, "Sales": 2.0, "Support": 1.8}[cat]
    spread = {"Engineering": 1.2, "Marketing": 1.5, "Sales": 1.8, "Support": 1.4}[cat]

    # Before training - lower scores with some variation
    before = np.clip(np.random.normal(base, spread, n_per_group), 1, 10)
    for v in before:
        data.append({"category": cat, "value": v, "split_group": "Before Training"})

    # After training - higher scores
    after = np.clip(np.random.normal(base + improvement, spread * 0.9, n_per_group), 1, 10)
    for v in after:
        data.append({"category": cat, "value": v, "split_group": "After Training"})

# Organize data by category and split group
values_by_cat_group = {}
for cat in categories:
    values_by_cat_group[cat] = {}
    for sg in split_groups:
        values_by_cat_group[cat][sg] = [d["value"] for d in data if d["category"] == cat and d["split_group"] == sg]


# Gaussian kernel density estimation using numpy only
def gaussian_kde_numpy(values, n_points=100, y_min=1.0, y_max=10.0):
    """Compute kernel density estimate using Gaussian kernels with bounded domain."""
    values = np.array(values)
    n = len(values)

    # Scott's rule for bandwidth
    std = np.std(values, ddof=1)
    bandwidth = 1.06 * std * n ** (-1 / 5)

    # Grid for evaluation - bounded to data scale
    y_grid = np.linspace(y_min, y_max, n_points)

    # Compute KDE at each grid point
    density = np.zeros(n_points)
    for i, y in enumerate(y_grid):
        kernel_values = np.exp(-0.5 * ((y - values) / bandwidth) ** 2)
        density[i] = np.sum(kernel_values) / (n * bandwidth * np.sqrt(2 * np.pi))

    return y_grid, density


# Colors - Python Blue and Yellow
color_before = "#306998"  # Python Blue
color_after = "#FFD43B"  # Python Yellow

# Create figure with HoverTool enabled
p = figure(
    width=4800,
    height=2700,
    title="violin-split · bokeh · pyplots.ai",
    x_axis_label="Department",
    y_axis_label="Satisfaction Score (1-10)",
    x_range=categories,
    y_range=(0.5, 10.5),
    tools="pan,wheel_zoom,box_zoom,reset,save",
)

# Width of each violin half
violin_width = 0.35

# Store patches for legend
before_patch = None
after_patch = None

# Store statistics for hover tooltips
stats_data = {"x": [], "y": [], "group": [], "median": [], "q1": [], "q3": [], "n": []}

# Draw split violins for each category
for i, cat in enumerate(categories):
    cat_x = i

    for sg in split_groups:
        values = values_by_cat_group[cat][sg]
        # Use bounded KDE to keep distribution within 1-10 scale
        y_grid, density = gaussian_kde_numpy(values, y_min=1.0, y_max=10.0)

        # Normalize density to fit within violin width
        max_density = max(density)
        if max_density > 0:
            density_norm = density / max_density * violin_width
        else:
            density_norm = density

        # Build polygon coordinates
        if sg == "Before Training":
            # Left half - density goes negative (left)
            xs = np.concatenate([cat_x - density_norm, [cat_x], [cat_x]])
            ys = np.concatenate([y_grid, [y_grid[-1]], [y_grid[0]]])
            color = color_before
        else:
            # Right half - density goes positive (right)
            xs = np.concatenate([[cat_x], cat_x + density_norm, [cat_x]])
            ys = np.concatenate([[y_grid[0]], y_grid, [y_grid[-1]]])
            color = color_after

        # Draw violin patch
        patch = p.patch(xs.tolist(), ys.tolist(), fill_color=color, fill_alpha=0.7, line_color=color, line_width=2)

        # Store first patches for legend
        if sg == "Before Training" and before_patch is None:
            before_patch = patch
        elif sg == "After Training" and after_patch is None:
            after_patch = patch

        # Add quartile markers
        q1, median, q3 = np.percentile(values, [25, 50, 75])

        # Horizontal offset for quartile lines
        if sg == "Before Training":
            line_start = cat_x - violin_width * 0.6
            line_end = cat_x
        else:
            line_start = cat_x
            line_end = cat_x + violin_width * 0.6

        # Draw quartile lines
        p.segment(x0=[line_start], y0=[median], x1=[line_end], y1=[median], line_color="white", line_width=4)
        p.segment(
            x0=[line_start], y0=[q1], x1=[line_end], y1=[q1], line_color="white", line_width=2, line_dash="dashed"
        )
        p.segment(
            x0=[line_start], y0=[q3], x1=[line_end], y1=[q3], line_color="white", line_width=2, line_dash="dashed"
        )

        # Store hover data for this violin
        hover_x = cat_x - violin_width / 2 if sg == "Before Training" else cat_x + violin_width / 2
        stats_data["x"].append(hover_x)
        stats_data["y"].append(median)
        stats_data["group"].append(f"{cat} - {sg}")
        stats_data["median"].append(f"{median:.2f}")
        stats_data["q1"].append(f"{q1:.2f}")
        stats_data["q3"].append(f"{q3:.2f}")
        stats_data["n"].append(str(len(values)))

# Add invisible scatter points for hover tooltips
hover_circles = p.scatter(x=stats_data["x"], y=stats_data["y"], size=30, fill_alpha=0, line_alpha=0)

# Configure HoverTool with statistics
hover = HoverTool(
    renderers=[hover_circles],
    tooltips=[("Group", "@group"), ("Median", "@median"), ("Q1", "@q1"), ("Q3", "@q3"), ("Sample Size", "@n")],
)
hover_circles.data_source.data.update(stats_data)
p.add_tools(hover)

# Add legend with larger glyphs, positioned inside plot area
legend = Legend(
    items=[
        LegendItem(label="Before Training", renderers=[before_patch]),
        LegendItem(label="After Training", renderers=[after_patch]),
    ],
    location="top_left",
)
legend.label_text_font_size = "24pt"
legend.glyph_width = 60
legend.glyph_height = 40
legend.spacing = 15
legend.padding = 20
legend.background_fill_alpha = 0.85
legend.border_line_color = "#cccccc"
legend.border_line_width = 2
p.add_layout(legend)

# Style - large text for 4800x2700 canvas
p.title.text_font_size = "32pt"
p.title.align = "center"
p.xaxis.axis_label_text_font_size = "24pt"
p.yaxis.axis_label_text_font_size = "24pt"
p.xaxis.major_label_text_font_size = "20pt"
p.yaxis.major_label_text_font_size = "18pt"

# Grid styling
p.xgrid.grid_line_color = None
p.ygrid.grid_line_alpha = 0.3
p.ygrid.grid_line_dash = "dashed"

# Axis styling
p.xaxis.major_tick_line_color = None
p.outline_line_color = None

# Background
p.background_fill_color = "#fafafa"

# Save as PNG and HTML
export_png(p, filename="plot.png")
output_file("plot.html")
save(p)
