""" anyplot.ai
box-notched: Notched Box Plot
Library: pygal 3.1.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-07
"""

import os
import xml.etree.ElementTree as ET

import cairosvg
import numpy as np
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
IMPRINT = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030")

# Data - Generate response times for different server configurations
np.random.seed(42)
categories = ["Baseline", "Config A", "Config B", "Config C", "Config D"]
data = {
    "Baseline": np.random.normal(120, 25, 80),
    "Config A": np.random.normal(95, 20, 80),
    "Config B": np.random.normal(115, 22, 80),
    "Config C": np.random.normal(85, 18, 80),
    "Config D": np.random.normal(110, 30, 80),
}
data["Baseline"] = np.append(data["Baseline"], [200, 210, 45])
data["Config D"] = np.append(data["Config D"], [190, 35])

# Calculate notched box plot statistics (inlined)
stats = {}
for cat in categories:
    values = data[cat]
    q1 = np.percentile(values, 25)
    median = np.percentile(values, 50)
    q3 = np.percentile(values, 75)
    iqr = q3 - q1
    n = len(values)

    notch_width = 1.57 * iqr / np.sqrt(n)
    notch_low = median - notch_width
    notch_high = median + notch_width

    whisker_low = max(q1 - 1.5 * iqr, np.min(values))
    whisker_high = min(q3 + 1.5 * iqr, np.max(values))

    outliers = values[(values < q1 - 1.5 * iqr) | (values > q3 + 1.5 * iqr)]

    stats[cat] = {
        "q1": q1,
        "median": median,
        "q3": q3,
        "notch_low": notch_low,
        "notch_high": notch_high,
        "whisker_low": whisker_low,
        "whisker_high": whisker_high,
        "outliers": outliers.tolist(),
    }

# Custom style
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT,
    title_font_size=28,
    label_font_size=22,
    major_label_font_size=18,
    legend_font_size=16,
    value_font_size=14,
)

# Create base chart
all_values = np.concatenate([data[cat] for cat in categories])
y_min = np.floor(np.min(all_values) / 10) * 10 - 10
y_max = np.ceil(np.max(all_values) / 10) * 10 + 10

chart = pygal.Line(
    width=4800,
    height=2700,
    style=custom_style,
    title="box-notched · pygal · anyplot.ai",
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
    no_data_text="",
)

chart.x_labels = categories

for category in categories:
    chart.add(category, [{"value": y_min, "label": ""}])

# Render base SVG
svg_string = chart.render()

# Parse and modify SVG
ET.register_namespace("", "http://www.w3.org/2000/svg")
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
root = ET.fromstring(svg_string)

# Plot area boundaries
plot_left = 350
plot_right = 4600
plot_top = 200
plot_bottom = 2350
plot_width = plot_right - plot_left
plot_height = plot_bottom - plot_top

boxes_group = ET.Element("{http://www.w3.org/2000/svg}g", attrib={"class": "notched-boxes"})

n_cats = len(categories)
box_spacing = plot_width / n_cats
box_width = box_spacing * 0.6
notch_indent = box_width * 0.15

# Draw each notched box
for i, category in enumerate(categories):
    s = stats[category]
    color = IMPRINT[i % len(IMPRINT)]
    x_center = plot_left + box_spacing * (i + 0.5)
    x_left = x_center - box_width / 2
    x_right = x_center + box_width / 2

    y_q1 = plot_bottom - (s["q1"] - y_min) / (y_max - y_min) * plot_height
    y_q3 = plot_bottom - (s["q3"] - y_min) / (y_max - y_min) * plot_height
    y_med = plot_bottom - (s["median"] - y_min) / (y_max - y_min) * plot_height
    y_notch_low = plot_bottom - (s["notch_low"] - y_min) / (y_max - y_min) * plot_height
    y_notch_high = plot_bottom - (s["notch_high"] - y_min) / (y_max - y_min) * plot_height
    y_whisker_low = plot_bottom - (s["whisker_low"] - y_min) / (y_max - y_min) * plot_height
    y_whisker_high = plot_bottom - (s["whisker_high"] - y_min) / (y_max - y_min) * plot_height

    notch_x_left = x_left + notch_indent
    notch_x_right = x_right - notch_indent

    path_d = (
        f"M {x_left} {y_q3} "
        f"L {x_right} {y_q3} "
        f"L {x_right} {y_notch_high} "
        f"L {notch_x_right} {y_med} "
        f"L {x_right} {y_notch_low} "
        f"L {x_right} {y_q1} "
        f"L {x_left} {y_q1} "
        f"L {x_left} {y_notch_low} "
        f"L {notch_x_left} {y_med} "
        f"L {x_left} {y_notch_high} "
        f"Z"
    )

    box_path = ET.SubElement(
        boxes_group,
        "{http://www.w3.org/2000/svg}path",
        attrib={"d": path_d, "fill": color, "fill-opacity": "0.4", "stroke": color, "stroke-width": "4"},
    )

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

    for outlier in s["outliers"]:
        y_outlier = plot_bottom - (outlier - y_min) / (y_max - y_min) * plot_height
        ET.SubElement(
            boxes_group,
            "{http://www.w3.org/2000/svg}circle",
            attrib={
                "cx": str(x_center),
                "cy": str(y_outlier),
                "r": "12",
                "fill": PAGE_BG,
                "stroke": color,
                "stroke-width": "3",
            },
        )

root.append(boxes_group)
modified_svg = ET.tostring(root, encoding="unicode")

# Save as PNG and HTML
with open(f"plot-{THEME}.html", "w") as f:
    f.write(modified_svg)

cairosvg.svg2png(
    bytestring=modified_svg.encode("utf-8"), write_to=f"plot-{THEME}.png", output_width=4800, output_height=2700
)
