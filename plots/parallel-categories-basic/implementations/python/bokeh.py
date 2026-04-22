""" pyplots.ai
parallel-categories-basic: Basic Parallel Categories Plot
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import numpy as np
import pandas as pd
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource, Label
from bokeh.plotting import figure
from bokeh.resources import CDN


# Data - Product purchase journey: Channel -> Category -> Outcome
np.random.seed(42)

# Create realistic product journey data
channels = ["Online", "Store", "Mobile"]
categories = ["Electronics", "Clothing", "Home"]
outcomes = ["Purchased", "Returned", "Exchanged"]

# Generate data with realistic patterns
data = []
for _ in range(500):
    channel = np.random.choice(channels, p=[0.45, 0.35, 0.20])
    # Category probabilities vary by channel
    if channel == "Online":
        category = np.random.choice(categories, p=[0.5, 0.3, 0.2])
    elif channel == "Store":
        category = np.random.choice(categories, p=[0.2, 0.5, 0.3])
    else:
        category = np.random.choice(categories, p=[0.6, 0.25, 0.15])
    # Outcome probabilities vary by category
    if category == "Electronics":
        outcome = np.random.choice(outcomes, p=[0.7, 0.2, 0.1])
    elif category == "Clothing":
        outcome = np.random.choice(outcomes, p=[0.6, 0.25, 0.15])
    else:
        outcome = np.random.choice(outcomes, p=[0.85, 0.1, 0.05])
    data.append({"Channel": channel, "Category": category, "Outcome": outcome})

df = pd.DataFrame(data)

# Aggregate the data to get counts for each path
path_counts = df.groupby(["Channel", "Category", "Outcome"]).size().reset_index(name="count")

# Define dimensions and their unique values (ordered)
dimensions = ["Channel", "Category", "Outcome"]
dim_values = {"Channel": channels, "Category": categories, "Outcome": outcomes}

# Calculate x positions for each dimension
x_positions = {dim: i * 1.5 for i, dim in enumerate(dimensions)}

# Calculate y positions for each category within each dimension
# Each dimension gets a vertical axis from 0 to total_count
total_count = len(df)

# Build category positions for each dimension
dim_cat_positions = {}
for dim in dimensions:
    # Count occurrences of each category
    if dim == dimensions[0]:
        counts = df[dim].value_counts()
    else:
        counts = df[dim].value_counts()

    positions = {}
    y_current = 0
    for cat in dim_values[dim]:
        count = counts.get(cat, 0)
        height = count / total_count
        positions[cat] = {"y_start": y_current, "height": height, "y_end": y_current + height}
        y_current += height
    dim_cat_positions[dim] = positions

# Create ribbons connecting categories between adjacent dimensions
# Track current fill position for each category
ribbon_patches_x = []
ribbon_patches_y = []
ribbon_colors = []

# Color by first dimension (Channel)
channel_colors = {
    "Online": "#306998",  # Python Blue
    "Store": "#FFD43B",  # Python Yellow
    "Mobile": "#4DAF4A",  # Green
}

# Track running position within each category box
running_positions = {dim: dict.fromkeys(dim_values[dim], 0) for dim in dimensions}

# Process each unique path
for _, row in path_counts.iterrows():
    count = row["count"]
    ribbon_height = count / total_count

    # Get color based on first dimension
    color = channel_colors[row["Channel"]]

    # Create ribbons between each pair of adjacent dimensions
    for i in range(len(dimensions) - 1):
        dim1 = dimensions[i]
        dim2 = dimensions[i + 1]
        cat1 = row[dim1]
        cat2 = row[dim2]

        # Get x positions
        x1 = x_positions[dim1]
        x2 = x_positions[dim2]

        # Get y positions
        y1_base = dim_cat_positions[dim1][cat1]["y_start"]
        y1_start = y1_base + running_positions[dim1][cat1]
        y1_end = y1_start + ribbon_height

        y2_base = dim_cat_positions[dim2][cat2]["y_start"]
        y2_start = y2_base + running_positions[dim2][cat2]
        y2_end = y2_start + ribbon_height

        # Create smooth ribbon using bezier-like path
        # Use intermediate points for smooth curves
        x_mid = (x1 + x2) / 2

        # Create patch coordinates (going clockwise)
        # Left edge (bottom to top), then curve to right edge (top to bottom)
        num_curve_points = 20
        t = np.linspace(0, 1, num_curve_points)

        # Top edge: bezier from (x1, y1_end) to (x2, y2_end)
        top_x = x1 * (1 - t) ** 3 + 3 * x_mid * t * (1 - t) ** 2 + 3 * x_mid * t**2 * (1 - t) + x2 * t**3
        top_y = y1_end * (1 - t) ** 3 + 3 * y1_end * t * (1 - t) ** 2 + 3 * y2_end * t**2 * (1 - t) + y2_end * t**3

        # Bottom edge: bezier from (x2, y2_start) to (x1, y1_start) (reversed)
        bottom_x = x2 * (1 - t) ** 3 + 3 * x_mid * t * (1 - t) ** 2 + 3 * x_mid * t**2 * (1 - t) + x1 * t**3
        bottom_y = (
            y2_start * (1 - t) ** 3 + 3 * y2_start * t * (1 - t) ** 2 + 3 * y1_start * t**2 * (1 - t) + y1_start * t**3
        )

        # Combine to form closed polygon
        patch_x = np.concatenate([top_x, bottom_x])
        patch_y = np.concatenate([top_y, bottom_y])

        ribbon_patches_x.append(patch_x.tolist())
        ribbon_patches_y.append(patch_y.tolist())
        ribbon_colors.append(color)

        # Update running positions only after processing the LAST segment for this path
        if i == len(dimensions) - 2:
            for j in range(len(dimensions)):
                dim = dimensions[j]
                cat = row[dim]
                running_positions[dim][cat] += ribbon_height

# Reset running positions for proper tracking
running_positions = {dim: dict.fromkeys(dim_values[dim], 0) for dim in dimensions}

# Process each unique path again to correctly update positions
for _, row in path_counts.iterrows():
    count = row["count"]
    ribbon_height = count / total_count
    for dim in dimensions:
        cat = row[dim]
        running_positions[dim][cat] += ribbon_height

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="parallel-categories-basic · bokeh · pyplots.ai",
    x_range=(-0.7, 4.0),
    y_range=(-0.05, 1.15),
    tools="",
    toolbar_location=None,
)

# Draw ribbons
for i in range(len(ribbon_patches_x)):
    source = ColumnDataSource(data={"x": [ribbon_patches_x[i]], "y": [ribbon_patches_y[i]]})
    p.patches(
        xs="x",
        ys="y",
        source=source,
        fill_color=ribbon_colors[i],
        fill_alpha=0.6,
        line_color=ribbon_colors[i],
        line_alpha=0.8,
        line_width=0.5,
    )

# Draw category boxes (rectangles for each category in each dimension)
box_width = 0.12
for dim in dimensions:
    x = x_positions[dim]
    for cat in dim_values[dim]:
        pos = dim_cat_positions[dim][cat]
        # Draw rectangle
        source = ColumnDataSource(
            data={
                "x": [[x - box_width / 2, x + box_width / 2, x + box_width / 2, x - box_width / 2]],
                "y": [[pos["y_start"], pos["y_start"], pos["y_end"], pos["y_end"]]],
            }
        )
        p.patches(xs="x", ys="y", source=source, fill_color="#333333", fill_alpha=0.9, line_color="white", line_width=2)

        # Add category label (to the side of the box for better readability)
        y_mid = (pos["y_start"] + pos["y_end"]) / 2
        # Place labels on left side for first two dimensions, right side for last
        if dim == dimensions[-1]:
            label_x = x + box_width / 2 + 0.05
            align = "left"
        else:
            label_x = x - box_width / 2 - 0.05
            align = "right"
        label = Label(
            x=label_x,
            y=y_mid,
            text=cat,
            text_font_size="28pt",
            text_color="#333333",
            text_align=align,
            text_baseline="middle",
        )
        p.add_layout(label)

# Add dimension labels at the top
for dim in dimensions:
    x = x_positions[dim]
    label = Label(
        x=x,
        y=1.08,
        text=dim,
        text_font_size="36pt",
        text_color="#333333",
        text_font_style="bold",
        text_align="center",
        text_baseline="bottom",
    )
    p.add_layout(label)

# Add legend manually
legend_items = [("Online", "#306998"), ("Store", "#FFD43B"), ("Mobile", "#4DAF4A")]
legend_y = 0.92
for i, (name, color) in enumerate(legend_items):
    # Legend box
    lx = 3.35
    ly = legend_y - i * 0.1
    source = ColumnDataSource(
        data={"x": [[lx - 0.05, lx + 0.05, lx + 0.05, lx - 0.05]], "y": [[ly - 0.03, ly - 0.03, ly + 0.03, ly + 0.03]]}
    )
    p.patches(xs="x", ys="y", source=source, fill_color=color, fill_alpha=0.8, line_color="#333333", line_width=2)
    # Legend label
    label = Label(
        x=lx + 0.1,
        y=ly,
        text=name,
        text_font_size="24pt",
        text_color="#333333",
        text_align="left",
        text_baseline="middle",
    )
    p.add_layout(label)

# Style the figure
p.title.text_font_size = "48pt"
p.title.text_color = "#333333"
p.title.align = "center"

# Hide axes and grid (parallel categories don't use traditional axes)
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False
p.outline_line_color = None

# Background color
p.background_fill_color = "#FAFAFA"
p.border_fill_color = "#FAFAFA"

# Save as PNG
export_png(p, filename="plot.png")

# Also save as HTML for interactivity
save(p, filename="plot.html", resources=CDN, title="Parallel Categories Plot")
