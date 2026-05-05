""" anyplot.ai
treemap-basic: Basic Treemap
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-05
"""

import os
import time
from pathlib import Path

import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, LabelSet
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9"]

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

# Create dataframe
df = pd.DataFrame(data)

# Sort by value descending for better layout
df = df.sort_values("value", ascending=False).reset_index(drop=True)

# Map categories to colors using Okabe-Ito palette
unique_categories = df["category"].unique()
category_color_map = {cat: OKABE_ITO[i % len(OKABE_ITO)] for i, cat in enumerate(unique_categories)}

# Extract values and labels
values = df["value"].values
labels = df["subcategory"].values
categories = df["category"].values

# Normalize sizes to fit in 100x100 area
total_value = sum(values)
normalized = [v * 10000 / total_value for v in values]


# Squarify algorithm for treemap layout
def squarify(sizes, x=0, y=0, w=100, h=100):
    """Layout rectangles using squarify algorithm."""
    rects = []
    if not sizes:
        return rects

    remaining = list(enumerate(sizes))

    while remaining:
        if w >= h:
            # Horizontal layout
            row = []
            row_area = 0
            best_ratio = float("inf")

            for _i, (idx, size) in enumerate(remaining):
                test_row = row + [(idx, size)]
                test_area = row_area + size
                col_width = test_area / h if h > 0 else 0

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
            # Vertical layout
            row = []
            row_area = 0
            best_ratio = float("inf")

            for _i, (idx, size) in enumerate(remaining):
                test_row = row + [(idx, size)]
                test_area = row_area + size
                row_height = test_area / w if w > 0 else 0

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

            row_height = row_area / w if w > 0 else 0
            rect_x = x
            for idx, size in row:
                rect_w = size / row_height if row_height > 0 else 0
                rects.append({"idx": idx, "x": rect_x, "y": y, "dx": rect_w, "dy": row_height})
                rect_x += rect_w

            y += row_height
            h -= row_height
            remaining = remaining[len(row) :]

    return rects


rects = squarify(normalized)
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
    colors.append(category_color_map[categories[idx]])

    if rw > 10 and rh > 8:
        display_labels.append(f"{labels[idx]}\n${int(values[idx])}K")
    elif rw > 6 or rh > 6:
        display_labels.append(labels[idx])
    else:
        display_labels.append("")

# Create data source
source = ColumnDataSource(
    data={"x": x_centers, "y": y_centers, "width": widths, "height": heights, "color": colors, "label": display_labels}
)

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="treemap-basic · bokeh · anyplot.ai",
    x_range=(-2, 102),
    y_range=(-2, 102),
    tools="",
    toolbar_location=None,
)

# Style figure background
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

# Draw rectangles
p.rect(
    x="x",
    y="y",
    width="width",
    height="height",
    source=source,
    fill_color="color",
    fill_alpha=0.90,
    line_color=PAGE_BG,
    line_width=2,
)

# Add labels
labels_set = LabelSet(
    x="x",
    y="y",
    text="label",
    source=source,
    text_align="center",
    text_baseline="middle",
    text_font_size="20pt",
    text_color=INK,
)
p.add_layout(labels_set)

# Style title
p.title.text_font_size = "28pt"
p.title.text_color = INK
p.title.align = "center"

# Hide axes for cleaner look
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False

# Add legend
legend_categories = list(category_color_map.keys())
legend_x = 86
legend_y_start = 96
legend_spacing = 5

for i, cat in enumerate(legend_categories):
    y_pos = legend_y_start - i * legend_spacing

    legend_source = ColumnDataSource(data={"x": [legend_x], "y": [y_pos], "text": [cat]})

    legend_label = LabelSet(
        x="x",
        y="y",
        text="text",
        source=legend_source,
        text_align="left",
        text_baseline="middle",
        text_font_size="16pt",
        text_color=INK_SOFT,
    )
    p.add_layout(legend_label)

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome
W, H = 4800, 2700
opts = Options()
for arg in (
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    f"--window-size={W},{H}",
    "--hide-scrollbars",
):
    opts.add_argument(arg)

driver = webdriver.Chrome(options=opts)
driver.set_window_size(W, H)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
