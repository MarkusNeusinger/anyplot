""" pyplots.ai
box-notched: Notched Box Plot
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-25
"""

import xml.etree.ElementTree as ET

import cairosvg
import numpy as np
import pygal
from pygal.style import Style


# Data - Generate response times for different server configurations
np.random.seed(42)
categories = ["Baseline", "Config A", "Config B", "Config C", "Config D"]

# Create datasets with different distributions to show statistical differences
data = {
    "Baseline": np.random.normal(120, 25, 80),
    "Config A": np.random.normal(95, 20, 80),  # Significantly different from baseline
    "Config B": np.random.normal(115, 22, 80),  # Not significantly different
    "Config C": np.random.normal(85, 18, 80),  # Significantly different
    "Config D": np.random.normal(110, 30, 80),  # Higher variance
}

# Add some outliers to demonstrate whisker/outlier handling
data["Baseline"] = np.append(data["Baseline"], [200, 210, 45])
data["Config D"] = np.append(data["Config D"], [190, 35])


# Calculate notched box plot statistics
def calc_box_stats(values):
    q1 = np.percentile(values, 25)
    median = np.percentile(values, 50)
    q3 = np.percentile(values, 75)
    iqr = q3 - q1
    n = len(values)

    # Notch bounds (95% CI): median ± 1.57 * IQR / sqrt(n)
    notch_width = 1.57 * iqr / np.sqrt(n)
    notch_low = median - notch_width
    notch_high = median + notch_width

    # Whiskers at 1.5 * IQR
    whisker_low = max(q1 - 1.5 * iqr, np.min(values))
    whisker_high = min(q3 + 1.5 * iqr, np.max(values))

    # Outliers
    outliers = values[(values < q1 - 1.5 * iqr) | (values > q3 + 1.5 * iqr)]

    return {
        "q1": q1,
        "median": median,
        "q3": q3,
        "notch_low": notch_low,
        "notch_high": notch_high,
        "whisker_low": whisker_low,
        "whisker_high": whisker_high,
        "outliers": outliers.tolist(),
    }


# Calculate statistics for all categories
stats = {cat: calc_box_stats(data[cat]) for cat in categories}

# Custom style
colors = ("#306998", "#FFD43B", "#4CAF50", "#FF5722", "#9C27B0")
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=colors,
    title_font_size=60,
    label_font_size=40,
    major_label_font_size=36,
    legend_font_size=36,
    value_font_size=32,
)

# We'll create a custom SVG-based notched box plot using pygal's XY chart as base
# This allows us to draw the notched boxes manually

# First, find the data range for Y axis
all_values = np.concatenate([data[cat] for cat in categories])
y_min = np.floor(np.min(all_values) / 10) * 10 - 10
y_max = np.ceil(np.max(all_values) / 10) * 10 + 10

# Create base chart using Line for coordinate system
chart = pygal.Line(
    width=4800,
    height=2700,
    style=custom_style,
    title="box-notched · pygal · pyplots.ai",
    x_title="Server Configuration",
    y_title="Response Time (ms)",
    show_legend=True,
    legend_at_bottom=True,
    legend_box_size=24,
    show_y_guides=True,
    show_x_guides=False,
    margin=50,
    range=(y_min, y_max),
    show_dots=False,
    stroke=False,
    fill=False,
    no_data_text="",  # Remove "No data" text
)

# Set x labels
chart.x_labels = categories

# Add invisible series just for legend (use a single valid point outside visible range)
for category in categories:
    # Add a single point at bottom of range to create legend entry without visible data
    chart.add(category, [{"value": y_min, "label": ""}])

# Render the base SVG
svg_string = chart.render()

# Parse SVG and add notched box elements
# Register the SVG namespace
ET.register_namespace("", "http://www.w3.org/2000/svg")
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
root = ET.fromstring(svg_string)
ns = {"svg": "http://www.w3.org/2000/svg"}

# Calculate plot area from viewBox or chart dimensions
# Approximate plot area based on typical pygal layout
plot_left = 350
plot_right = 4600
plot_top = 200
plot_bottom = 2350
plot_width = plot_right - plot_left
plot_height = plot_bottom - plot_top

# Create a group for the boxes
boxes_group = ET.Element("{http://www.w3.org/2000/svg}g", attrib={"class": "notched-boxes"})

# Calculate positions
n_cats = len(categories)
box_spacing = plot_width / n_cats
box_width = box_spacing * 0.6
notch_indent = box_width * 0.15  # How much the notch indents


def y_to_svg(val):
    """Convert data Y value to SVG Y coordinate."""
    return plot_bottom - (val - y_min) / (y_max - y_min) * plot_height


# Draw each notched box
for i, category in enumerate(categories):
    s = stats[category]
    color = colors[i % len(colors)]
    x_center = plot_left + box_spacing * (i + 0.5)
    x_left = x_center - box_width / 2
    x_right = x_center + box_width / 2

    # SVG Y coordinates (inverted)
    y_q1 = y_to_svg(s["q1"])
    y_q3 = y_to_svg(s["q3"])
    y_med = y_to_svg(s["median"])
    y_notch_low = y_to_svg(s["notch_low"])
    y_notch_high = y_to_svg(s["notch_high"])
    y_whisker_low = y_to_svg(s["whisker_low"])
    y_whisker_high = y_to_svg(s["whisker_high"])

    # Draw notched box as a polygon path
    # Path: start at top-left, go clockwise with notch indents at median level
    notch_x_left = x_left + notch_indent
    notch_x_right = x_right - notch_indent

    path_d = (
        f"M {x_left} {y_q3} "  # Top-left corner
        f"L {x_right} {y_q3} "  # Top-right corner
        f"L {x_right} {y_notch_high} "  # Right side down to notch top
        f"L {notch_x_right} {y_med} "  # Notch indent to median
        f"L {x_right} {y_notch_low} "  # Notch indent back out
        f"L {x_right} {y_q1} "  # Right side down to Q1
        f"L {x_left} {y_q1} "  # Bottom edge
        f"L {x_left} {y_notch_low} "  # Left side up to notch bottom
        f"L {notch_x_left} {y_med} "  # Notch indent to median
        f"L {x_left} {y_notch_high} "  # Notch indent back out
        f"Z"  # Close path
    )

    # Box fill
    box_path = ET.SubElement(
        boxes_group,
        "{http://www.w3.org/2000/svg}path",
        attrib={"d": path_d, "fill": color, "fill-opacity": "0.4", "stroke": color, "stroke-width": "4"},
    )

    # Median line (horizontal line at median across the notch)
    med_line = ET.SubElement(
        boxes_group,
        "{http://www.w3.org/2000/svg}line",
        attrib={
            "x1": str(notch_x_left),
            "y1": str(y_med),
            "x2": str(notch_x_right),
            "y2": str(y_med),
            "stroke": color,
            "stroke-width": "6",
        },
    )

    # Upper whisker (vertical line)
    upper_whisker = ET.SubElement(
        boxes_group,
        "{http://www.w3.org/2000/svg}line",
        attrib={
            "x1": str(x_center),
            "y1": str(y_q3),
            "x2": str(x_center),
            "y2": str(y_whisker_high),
            "stroke": color,
            "stroke-width": "3",
        },
    )

    # Upper whisker cap
    cap_width = box_width * 0.3
    upper_cap = ET.SubElement(
        boxes_group,
        "{http://www.w3.org/2000/svg}line",
        attrib={
            "x1": str(x_center - cap_width / 2),
            "y1": str(y_whisker_high),
            "x2": str(x_center + cap_width / 2),
            "y2": str(y_whisker_high),
            "stroke": color,
            "stroke-width": "3",
        },
    )

    # Lower whisker (vertical line)
    lower_whisker = ET.SubElement(
        boxes_group,
        "{http://www.w3.org/2000/svg}line",
        attrib={
            "x1": str(x_center),
            "y1": str(y_q1),
            "x2": str(x_center),
            "y2": str(y_whisker_low),
            "stroke": color,
            "stroke-width": "3",
        },
    )

    # Lower whisker cap
    lower_cap = ET.SubElement(
        boxes_group,
        "{http://www.w3.org/2000/svg}line",
        attrib={
            "x1": str(x_center - cap_width / 2),
            "y1": str(y_whisker_low),
            "x2": str(x_center + cap_width / 2),
            "y2": str(y_whisker_low),
            "stroke": color,
            "stroke-width": "3",
        },
    )

    # Draw outliers as circles
    for outlier in s["outliers"]:
        y_outlier = y_to_svg(outlier)
        outlier_circle = ET.SubElement(
            boxes_group,
            "{http://www.w3.org/2000/svg}circle",
            attrib={
                "cx": str(x_center),
                "cy": str(y_outlier),
                "r": "12",
                "fill": "white",
                "stroke": color,
                "stroke-width": "3",
            },
        )

# Insert the boxes group into the SVG - just append to root since ET doesn't have getparent()
root.append(boxes_group)

# Save the modified SVG
modified_svg = ET.tostring(root, encoding="unicode")

# Save as HTML (SVG inline)
with open("plot.html", "w") as f:
    f.write(modified_svg)

# Convert to PNG using cairosvg
cairosvg.svg2png(
    bytestring=modified_svg.encode("utf-8"), write_to="plot.png", output_width=4800, output_height=2700
)
