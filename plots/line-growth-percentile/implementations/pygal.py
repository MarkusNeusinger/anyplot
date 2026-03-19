"""pyplots.ai
line-growth-percentile: Pediatric Growth Chart with Percentile Curves
Library: pygal 3.1.0 | Python 3.14.3
Quality: 83/100 | Created: 2026-03-19
"""

import io
import xml.etree.ElementTree as ET

import cairosvg
import numpy as np
import pygal
from PIL import Image
from pygal.style import Style


# Data - WHO-style weight-for-age reference for boys, 0-36 months
np.random.seed(42)
age_months = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 15, 18, 21, 24, 27, 30, 33, 36])

# Synthetic percentile reference data approximating WHO weight-for-age (boys, kg)
percentile_50 = np.array(
    [3.3, 4.5, 5.6, 6.4, 7.0, 7.5, 7.9, 8.3, 8.6, 8.9, 9.2, 9.4, 9.6, 10.3, 10.9, 11.5, 12.2, 12.7, 13.3, 13.8, 14.3]
)
offsets = {
    3: np.linspace(1.1, 3.2, len(age_months)),
    10: np.linspace(0.85, 2.5, len(age_months)),
    25: np.linspace(0.55, 1.5, len(age_months)),
    75: np.linspace(0.55, 1.5, len(age_months)),
    90: np.linspace(0.85, 2.5, len(age_months)),
    97: np.linspace(1.1, 3.2, len(age_months)),
}

percentile_3 = percentile_50 - offsets[3]
percentile_10 = percentile_50 - offsets[10]
percentile_25 = percentile_50 - offsets[25]
percentile_75 = percentile_50 + offsets[75]
percentile_90 = percentile_50 + offsets[90]
percentile_97 = percentile_50 + offsets[97]

# Individual patient data - a boy tracking between 25th and 50th percentiles
patient_ages = np.array([0, 1, 2, 4, 6, 9, 12, 15, 18, 24, 30, 36])
patient_weights = np.array([3.2, 4.3, 5.3, 6.7, 7.5, 8.5, 9.3, 10.0, 10.5, 11.8, 12.8, 13.7])

# Percentile values at age 36 for right-margin labels
percentile_labels = [
    ("P3", float(percentile_3[-1])),
    ("P10", float(percentile_10[-1])),
    ("P25", float(percentile_25[-1])),
    ("P50", float(percentile_50[-1])),
    ("P75", float(percentile_75[-1])),
    ("P90", float(percentile_90[-1])),
    ("P97", float(percentile_97[-1])),
]

# Style - blue tones for boys chart
custom_style = Style(
    background="white",
    plot_background="#FAFCFF",
    foreground="#2C3E50",
    foreground_strong="#1A252F",
    foreground_subtle="#D5D8DC",
    guide_stroke_color="#E8EDF2",
    guide_stroke_dasharray="4,6",
    colors=(
        "#2E86C1",  # P3-P10 band (darkest blue - extremes)
        "#85C1E9",  # P10-P25 band (medium blue)
        "#D6EAF8",  # P25-P50 band (lightest blue - near median)
        "#D6EAF8",  # P50-P75 band (lightest blue - near median)
        "#85C1E9",  # P75-P90 band (medium blue)
        "#2E86C1",  # P90-P97 band (darkest blue - extremes)
        "#154360",  # P50 median line (dark navy)
        "#C0392B",  # Patient data (bold red)
    ),
    opacity=".55",
    opacity_hover=".80",
    stroke_opacity="1",
    stroke_opacity_hover="1",
    title_font_size=58,
    label_font_size=40,
    major_label_font_size=42,
    legend_font_size=36,
    value_font_size=36,
    value_colors=("transparent",),
    tooltip_font_size=32,
    font_family='Helvetica, Arial, "DejaVu Sans", sans-serif',
)

# Chart
chart = pygal.XY(
    style=custom_style,
    width=4800,
    height=2700,
    explicit_size=True,
    title="WHO Weight-for-Age (Boys) · line-growth-percentile · pygal · pyplots.ai",
    x_title="Age (months)",
    y_title="Weight (kg)",
    show_dots=True,
    dots_size=0,
    show_x_guides=False,
    show_y_guides=True,
    fill=True,
    stroke=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    legend_box_size=28,
    truncate_legend=-1,
    range=(0, 18),
    x_labels=[0, 3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36],
    x_labels_major=[0, 6, 12, 18, 24, 30, 36],
    show_minor_x_labels=True,
    show_minor_y_labels=False,
    y_labels=list(range(2, 19, 2)),
    print_values=False,
    x_value_formatter=lambda x: f"{x:.0f}",
    value_formatter=lambda x: f"{x:.1f}",
    tooltip_border_radius=8,
    margin_top=30,
    margin_bottom=50,
    margin_left=30,
    margin_right=60,
    spacing=18,
    js=[],
)

# Percentile bands as filled polygons (upper forward, lower reversed)
band_configs = [
    ("P3–P10", percentile_3, percentile_10),
    ("P10–P25", percentile_10, percentile_25),
    ("P25–P50", percentile_25, percentile_50),
    ("P50–P75", percentile_50, percentile_75),
    ("P75–P90", percentile_75, percentile_90),
    ("P90–P97", percentile_90, percentile_97),
]

for label, lower, upper in band_configs:
    polygon = [(float(a), float(u)) for a, u in zip(age_months, upper, strict=True)]
    for a, lo in zip(reversed(age_months), reversed(lower), strict=True):
        polygon.append((float(a), float(lo)))
    chart.add(label, polygon, stroke_style={"width": 0.5, "opacity": 0.1})

# P50 median line - strongly emphasized with dark navy, dashed for distinction
median_data = [(float(a), float(v)) for a, v in zip(age_months, percentile_50, strict=True)]
chart.add(
    "P50 (Median)",
    median_data,
    fill=False,
    stroke=True,
    dots_size=0,
    stroke_style={"width": 7, "linecap": "round", "linejoin": "round", "dasharray": "12,6"},
)

# Patient data - bold connected markers with prominent dots
patient_data = [(float(a), float(w)) for a, w in zip(patient_ages, patient_weights, strict=True)]
chart.add(
    "Patient",
    patient_data,
    fill=False,
    stroke=True,
    dots_size=12,
    stroke_style={"width": 5.5, "linecap": "round", "linejoin": "round"},
)

# Render SVG and inject percentile labels as native SVG text elements
svg_data = chart.render()

ET.register_namespace("", "http://www.w3.org/2000/svg")
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
tree = ET.ElementTree(ET.fromstring(svg_data))
root = tree.getroot()

# Locate the plot overlay group to find the chart area bounds
ns = {"svg": "http://www.w3.org/2000/svg"}
plot_group = root.find(".//{http://www.w3.org/2000/svg}g[@class='plot overlay']")

# Determine y-coordinate mapping from axis tick labels in the SVG
y_min_val, y_max_val = 0.0, 18.0
# Find axis guides to extract plot area coordinates
y_guides = root.findall(".//{http://www.w3.org/2000/svg}g[@class='guides']//{http://www.w3.org/2000/svg}line")
y_positions = []
for guide in y_guides:
    y1 = guide.get("y1")
    x1 = guide.get("x1")
    x2 = guide.get("x2")
    if y1 and x1 and x2 and x1 != x2:  # horizontal guides
        y_positions.append(float(y1))

if y_positions:
    plot_top_svg = min(y_positions)
    plot_bottom_svg = max(y_positions)
else:
    # Fallback: approximate from viewBox
    plot_top_svg = 80
    plot_bottom_svg = 2340

# Find the rightmost x of the plot area from horizontal guides
x_right_svg = 4700  # default
for guide in y_guides:
    x2 = guide.get("x2")
    if x2:
        x_right_svg = max(x_right_svg, float(x2))

# Add percentile labels as SVG text elements on the right margin
label_group = ET.SubElement(root, "{http://www.w3.org/2000/svg}g")
label_group.set("class", "percentile-labels")

for label, val in percentile_labels:
    frac = (val - y_min_val) / (y_max_val - y_min_val)
    y_svg = plot_bottom_svg - frac * (plot_bottom_svg - plot_top_svg)
    text_el = ET.SubElement(label_group, "{http://www.w3.org/2000/svg}text")
    text_el.set("x", str(x_right_svg + 15))
    text_el.set("y", str(y_svg + 10))
    text_el.set("font-size", "38")
    text_el.set("font-family", 'Helvetica, Arial, "DejaVu Sans", sans-serif')
    text_el.set("font-weight", "bold")
    text_el.set("fill", "#154360" if label == "P50" else "#5D6D7E")
    text_el.text = label

# Convert modified SVG to PNG
modified_svg = ET.tostring(root, encoding="unicode")
png_bytes = cairosvg.svg2png(bytestring=modified_svg.encode("utf-8"), output_width=4800, output_height=2700)
img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
img.save("plot.png", dpi=(150, 150))

# Also save HTML version
chart.render_to_file("plot.html")
