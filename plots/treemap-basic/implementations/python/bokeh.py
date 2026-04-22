""" pyplots.ai
treemap-basic: Basic Treemap
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-24
"""

from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource, LabelSet
from bokeh.plotting import figure


# Data - budget allocation by department and project
data = [
    {"category": "Engineering", "subcategory": "Backend", "value": 220},
    {"category": "Engineering", "subcategory": "Frontend", "value": 180},
    {"category": "Sales", "subcategory": "Enterprise", "value": 200},
    {"category": "Marketing", "subcategory": "Digital", "value": 150},
    {"category": "Sales", "subcategory": "SMB", "value": 120},
    {"category": "Engineering", "subcategory": "DevOps", "value": 90},
    {"category": "Marketing", "subcategory": "Brand", "value": 80},
    {"category": "HR", "subcategory": "Recruiting", "value": 70},
    {"category": "Marketing", "subcategory": "Events", "value": 60},
    {"category": "Finance", "subcategory": "Accounting", "value": 60},
    {"category": "HR", "subcategory": "Training", "value": 50},
    {"category": "Finance", "subcategory": "Planning", "value": 40},
]

# Sort by value descending for better layout
data = sorted(data, key=lambda x: x["value"], reverse=True)

# Extract values and labels
values = [d["value"] for d in data]
labels = [d["subcategory"] for d in data]
categories = [d["category"] for d in data]

# Category color mapping using Python colors + colorblind-safe palette
category_colors = {
    "Engineering": "#306998",  # Python Blue
    "Marketing": "#FFD43B",  # Python Yellow
    "Sales": "#4ECDC4",  # Teal
    "HR": "#E07A5F",  # Terra cotta
    "Finance": "#81B29A",  # Sage green
}

# Calculate treemap layout using squarify algorithm
# Normalize sizes to fit in 100x100 area
total_value = sum(values)
normalized = [v * 10000 / total_value for v in values]

# Squarify algorithm - place rectangles with good aspect ratios
rects = []
remaining = list(enumerate(normalized))
x, y, w, h = 0, 0, 100, 100

while remaining:
    # Lay out along shorter dimension
    if w >= h:
        # Horizontal layout: fill from left, stack vertically in each column
        row = []
        row_area = 0
        best_ratio = float("inf")

        for _i, (idx, size) in enumerate(remaining):
            test_row = row + [(idx, size)]
            test_area = row_area + size
            col_width = test_area / h if h > 0 else 0

            # Calculate worst aspect ratio for test row
            ratios = []
            for _, s in test_row:
                rect_h = s / col_width if col_width > 0 else 0
                ratio = max(col_width / rect_h, rect_h / col_width) if rect_h > 0 else float("inf")
                ratios.append(ratio)
            test_ratio = max(ratios) if ratios else float("inf")

            if test_ratio <= best_ratio:
                row = test_row
                row_area = test_area
                best_ratio = test_ratio
            else:
                break

        # Place row rectangles
        col_width = row_area / h if h > 0 else 0
        rect_y = y
        for idx, size in row:
            rect_h = size / col_width if col_width > 0 else 0
            rects.append({"idx": idx, "x": x, "y": rect_y, "dx": col_width, "dy": rect_h})
            rect_y += rect_h

        x += col_width
        w -= col_width
        remaining = remaining[len(row) :]
    else:
        # Vertical layout: fill from bottom, stack horizontally in each row
        row = []
        row_area = 0
        best_ratio = float("inf")

        for _i, (idx, size) in enumerate(remaining):
            test_row = row + [(idx, size)]
            test_area = row_area + size
            row_height = test_area / w if w > 0 else 0

            # Calculate worst aspect ratio for test row
            ratios = []
            for _, s in test_row:
                rect_w = s / row_height if row_height > 0 else 0
                ratio = max(rect_w / row_height, row_height / rect_w) if rect_w > 0 else float("inf")
                ratios.append(ratio)
            test_ratio = max(ratios) if ratios else float("inf")

            if test_ratio <= best_ratio:
                row = test_row
                row_area = test_area
                best_ratio = test_ratio
            else:
                break

        # Place row rectangles
        row_height = row_area / w if w > 0 else 0
        rect_x = x
        for idx, size in row:
            rect_w = size / row_height if row_height > 0 else 0
            rects.append({"idx": idx, "x": rect_x, "y": y, "dx": rect_w, "dy": row_height})
            rect_x += rect_w

        y += row_height
        h -= row_height
        remaining = remaining[len(row) :]

# Sort rects by original index to match data order
rects = sorted(rects, key=lambda r: r["idx"])

# Extract rectangle data for plotting
x_centers = []
y_centers = []
widths = []
heights = []
colors = []
display_labels = []

for r in rects:
    idx = r["idx"]
    rx, ry = r["x"], r["y"]
    rw, rh = r["dx"], r["dy"]

    x_centers.append(rx + rw / 2)
    y_centers.append(ry + rh / 2)
    widths.append(rw)
    heights.append(rh)
    colors.append(category_colors[categories[idx]])

    # Only show labels for rectangles large enough
    if rw > 10 and rh > 8:
        display_labels.append(f"{labels[idx]}\n${values[idx]}K")
    elif rw > 6 or rh > 6:
        display_labels.append(labels[idx])
    else:
        display_labels.append("")

# Create data source
source = ColumnDataSource(
    data={"x": x_centers, "y": y_centers, "width": widths, "height": heights, "color": colors, "label": display_labels}
)

# Create figure (4800 × 2700 px)
p = figure(
    width=4800,
    height=2700,
    title="treemap-basic · bokeh · pyplots.ai",
    x_range=(-2, 102),
    y_range=(-2, 102),
    tools="",
    toolbar_location=None,
)

# Draw rectangles
p.rect(
    x="x",
    y="y",
    width="width",
    height="height",
    source=source,
    fill_color="color",
    fill_alpha=0.85,
    line_color="white",
    line_width=3,
)

# Add labels
labels_set = LabelSet(
    x="x",
    y="y",
    text="label",
    source=source,
    text_align="center",
    text_baseline="middle",
    text_font_size="24pt",
    text_color="#333333",
)
p.add_layout(labels_set)

# Style
p.title.text_font_size = "32pt"
p.title.align = "center"

# Hide axes for cleaner look (treemaps don't need axes)
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False
p.outline_line_color = None

# Add legend manually using rectangles in corner
legend_categories = list(category_colors.keys())
legend_x = 85
legend_y_start = 95
legend_spacing = 6

for i, cat in enumerate(legend_categories):
    y_pos = legend_y_start - i * legend_spacing
    # Legend color box
    p.rect(
        x=legend_x,
        y=y_pos,
        width=3,
        height=3,
        fill_color=category_colors[cat],
        fill_alpha=0.85,
        line_color="white",
        line_width=1,
    )
    # Legend text
    legend_source = ColumnDataSource(data={"x": [legend_x + 3], "y": [y_pos], "text": [cat]})
    legend_label = LabelSet(
        x="x",
        y="y",
        text="text",
        source=legend_source,
        text_align="left",
        text_baseline="middle",
        text_font_size="20pt",
        text_color="#333333",
    )
    p.add_layout(legend_label)

# Save outputs
export_png(p, filename="plot.png")
save(p, filename="plot.html")
