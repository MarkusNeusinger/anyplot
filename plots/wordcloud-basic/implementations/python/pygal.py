"""anyplot.ai
wordcloud-basic: Basic Word Cloud
Library: pygal | Python 3.13
Quality: pending | Created: 2025-12-21
"""

import os
import sys
import xml.etree.ElementTree as ET


# Avoid naming conflict with pygal.py script name
# Remove current directory from path temporarily
cwd = os.getcwd()
sys.path = [p for p in sys.path if p not in ("", ".", cwd)]

import cairosvg  # noqa: E402
import numpy as np  # noqa: E402
import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"

# Okabe-Ito palette (first series = #009E73)
OKABE_ITO = ("#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442")

# Data: Tech industry buzzwords with frequencies
word_frequencies = {
    "Python": 180,
    "Data": 165,
    "Machine": 150,
    "Learning": 145,
    "Analytics": 135,
    "Cloud": 128,
    "API": 120,
    "DevOps": 110,
    "Docker": 105,
    "Security": 98,
    "Database": 92,
    "Kubernetes": 85,
    "AI": 78,
    "Automation": 70,
    "Microservices": 62,
    "Agile": 55,
    "Testing": 48,
    "Git": 42,
    "Linux": 38,
    "Scalability": 32,
    "AWS": 28,
    "React": 25,
    "Azure": 22,
    "Terraform": 20,
    "GraphQL": 18,
    "Pipeline": 16,
    "Deploy": 15,
    "Build": 14,
}

# Canvas dimensions
canvas_w = 4800
canvas_h = 2700

# Scale frequencies to font sizes for large canvas
min_freq = min(word_frequencies.values())
max_freq = max(word_frequencies.values())
min_size = 60
max_size = 280

# Sort by frequency (largest first for better placement)
sorted_words = sorted(word_frequencies.items(), key=lambda x: x[1], reverse=True)

# Build word positions using improved spiral algorithm
word_data = []
placed_boxes = []

for i, (word, freq) in enumerate(sorted_words):
    # Scale frequency to font size
    size = int(min_size + (freq - min_freq) / (max_freq - min_freq) * (max_size - min_size))

    # Estimate dimensions
    w = len(word) * size * 0.55
    h = size * 1.2

    # Improved spiral placement - centered with balanced distribution
    cx, cy = canvas_w / 2, canvas_h / 2 + 50
    angle = 0
    radius = 0
    x, y = cx, cy
    box = (cx - w / 2, cy - h / 2, w, h)

    for _ in range(50000):
        # Elliptical spiral - stretched for 16:9 canvas
        test_x = cx + radius * 2.8 * np.cos(angle) - w / 2
        test_y = cy + radius * 1.8 * np.sin(angle) - h / 2

        # Check bounds with margins for title and edges
        if 100 < test_x < canvas_w - w - 100 and 200 < test_y < canvas_h - h - 100:
            test_box = (test_x, test_y, w, h)
            # Check for overlap with placed words
            overlap = False
            for pb in placed_boxes:
                x1, y1, w1, h1 = test_box
                x2, y2, w2, h2 = pb
                padding = 50  # Increased padding to prevent clustering
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

        angle += 0.06  # Slower angle progression for better spacing
        radius += 3.5  # Moderate radius growth

    placed_boxes.append(box)
    word_data.append({"word": word, "x": x, "y": y, "size": size, "color": OKABE_ITO[i % len(OKABE_ITO)]})

# Create minimal pygal chart as canvas
custom_style = Style(background=PAGE_BG, plot_background=PAGE_BG)

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

# Render SVG and manually inject word cloud elements
svg_string = chart.render(is_unicode=True)
root = ET.fromstring(svg_string)

# Add title
title = ET.SubElement(root, "text")
title.set("x", "2400")
title.set("y", "130")
title.set("font-size", "84")
title.set("font-weight", "bold")
title.set("fill", INK)
title.set("text-anchor", "middle")
title.set("font-family", "sans-serif")
title.text = "wordcloud-basic · pygal · anyplot.ai"

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
with open(f"plot-{THEME}.svg", "w") as f:
    f.write(modified_svg)

# Render PNG using cairosvg
cairosvg.svg2png(bytestring=modified_svg.encode(), write_to=f"plot-{THEME}.png")

# Save as HTML for interactive viewing
with open(f"plot-{THEME}.html", "w") as f:
    f.write(
        f"""<!DOCTYPE html>
<html>
<head>
    <title>wordcloud-basic · pygal · anyplot.ai</title>
    <style>
        body {{ margin: 0; display: flex; justify-content: center; align-items: center; min-height: 100vh; background: {PAGE_BG}; }}
        svg {{ max-width: 100%; height: auto; }}
    </style>
</head>
<body>
{modified_svg}
</body>
</html>"""
    )
