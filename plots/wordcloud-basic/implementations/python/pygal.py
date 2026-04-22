""" pyplots.ai
wordcloud-basic: Basic Word Cloud
Library: pygal 3.1.0 | Python 3.13.11
Quality: 86/100 | Created: 2025-12-24
"""

import xml.etree.ElementTree as ET

import cairosvg
import numpy as np
import pygal
from pygal.style import Style


# Data: Tech industry buzzwords with frequencies
np.random.seed(42)
word_frequencies = {
    "Python": 100,
    "Data": 95,
    "Machine": 90,
    "Learning": 88,
    "Analytics": 82,
    "Cloud": 78,
    "API": 75,
    "DevOps": 72,
    "Docker": 68,
    "Security": 65,
    "Database": 62,
    "Kubernetes": 58,
    "AI": 55,
    "Automation": 52,
    "Microservices": 48,
    "Agile": 45,
    "Testing": 42,
    "Git": 38,
    "Linux": 35,
    "Scalability": 32,
    "AWS": 30,
    "React": 28,
    "Azure": 26,
    "Terraform": 24,
    "GraphQL": 22,
}

# Canvas dimensions
canvas_w = 4800
canvas_h = 2700

# Scale frequencies to font sizes - increased for better canvas utilization
min_freq = min(word_frequencies.values())
max_freq = max(word_frequencies.values())
min_size = 72  # Larger minimum to ensure small words are visible at canvas scale
max_size = 240  # Larger maximum to fill more canvas space

# Sort by frequency (largest first for better placement)
sorted_words = sorted(word_frequencies.items(), key=lambda x: x[1], reverse=True)

# Color palette based on pyplots primary colors
color_palette = ["#306998", "#FFD43B", "#4B8BBE", "#646464", "#3776AB", "#FFE873"]

# Build word positions using spiral algorithm with better distribution
word_data = []
placed_boxes = []

for i, (word, freq) in enumerate(sorted_words):
    # Scale frequency to font size
    size = int(min_size + (freq - min_freq) / (max_freq - min_freq) * (max_size - min_size))

    # Estimate dimensions
    w = len(word) * size * 0.55
    h = size * 1.2

    # Spiral placement - centered for maximum canvas utilization
    cx, cy = canvas_w / 2, canvas_h / 2 + 100
    angle = 0
    radius = 0
    x, y = cx, cy
    box = (cx - w / 2, cy - h / 2, w, h)

    for _ in range(30000):
        # Elliptical spiral - stretched to fill 16:9 canvas (wider horizontal)
        test_x = cx + radius * 2.6 * np.cos(angle) - w / 2
        test_y = cy + radius * 1.6 * np.sin(angle) - h / 2

        # Check bounds (leave margin for edges and title, use more vertical space)
        if 80 < test_x < canvas_w - w - 80 and 180 < test_y < canvas_h - h - 80:
            test_box = (test_x, test_y, w, h)
            # Check for overlap with placed words
            overlap = False
            for pb in placed_boxes:
                x1, y1, w1, h1 = test_box
                x2, y2, w2, h2 = pb
                padding = 30  # Tighter padding to fit larger words
                if not (
                    x1 + w1 + padding < x2 or x2 + w2 + padding < x1 or y1 + h1 + padding < y2 or y2 + h2 + padding < y1
                ):
                    overlap = True
                    break
            if not overlap:
                x = test_x + w / 2
                y = test_y + h / 2
                box = test_box
                break

        angle += 0.08  # Slower angle for more positions to try
        radius += 4.0  # Faster radius growth to spread outward and fill canvas

    placed_boxes.append(box)
    word_data.append({"word": word, "x": x, "y": y, "size": size, "color": color_palette[i % len(color_palette)]})

# Create minimal pygal chart as canvas
custom_style = Style(background="white", plot_background="white")

chart = pygal.XY(
    style=custom_style,
    width=canvas_w,
    height=canvas_h,
    show_legend=False,
    show_x_labels=False,
    show_y_labels=False,
    show_x_guides=False,
    show_y_guides=False,
    show_dots=False,
    stroke=False,
    margin=0,
)

# Add dummy data (required for chart to render)
chart.add("", [(0, 0)])

# Render SVG and manually inject word cloud elements (KISS: no function wrapper)
svg_string = chart.render(is_unicode=True)
root = ET.fromstring(svg_string)

# Add title
title = ET.SubElement(root, "text")
title.set("x", "2400")
title.set("y", "110")
title.set("font-size", "84")
title.set("font-weight", "bold")
title.set("fill", "#333")
title.set("text-anchor", "middle")
title.set("font-family", "sans-serif")
title.text = "wordcloud-basic · pygal · pyplots.ai"

# Add word cloud text elements
for item in word_data:
    text_elem = ET.SubElement(root, "text")
    text_elem.set("x", str(int(item["x"])))
    text_elem.set("y", str(int(item["y"])))
    text_elem.set("font-size", str(item["size"]))
    text_elem.set("font-weight", "bold")
    text_elem.set("fill", item["color"])
    text_elem.set("text-anchor", "middle")
    text_elem.set("dominant-baseline", "middle")
    text_elem.set("font-family", "sans-serif")
    text_elem.text = item["word"]

# Write modified SVG
modified_svg = ET.tostring(root, encoding="unicode")
with open("plot.svg", "w") as f:
    f.write(modified_svg)

# Render PNG using cairosvg
cairosvg.svg2png(bytestring=modified_svg.encode(), write_to="plot.png")

# Save as HTML for interactive viewing
with open("plot.html", "w") as f:
    f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>wordcloud-basic · pygal · pyplots.ai</title>
    <style>
        body {{ margin: 0; display: flex; justify-content: center; align-items: center; min-height: 100vh; background: #f5f5f5; }}
        svg {{ max-width: 100%; height: auto; }}
    </style>
</head>
<body>
{modified_svg}
</body>
</html>""")
