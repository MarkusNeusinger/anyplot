""" anyplot.ai
wordcloud-basic: Basic Word Cloud
Library: altair 6.1.0 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-06
"""

import os
import sys


# Prevent local file from shadowing the altair package
script_dir = os.path.dirname(os.path.abspath(__file__)) if __file__ else os.getcwd()
if script_dir in sys.path:
    sys.path.remove(script_dir)

import altair as alt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (first series always #009E73)
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442"]

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
canvas_w = 1600
canvas_h = 900

# Scale frequencies to font sizes (24-80 for Altair text marks)
min_freq = min(word_frequencies.values())
max_freq = max(word_frequencies.values())
min_size = 24
max_size = 80

# Build data with spiral positioning
words_list = []
x_positions = []
y_positions = []
font_sizes = []
colors = []
placed_boxes = []

# Sort by frequency (largest first for better placement)
sorted_words = sorted(word_frequencies.items(), key=lambda x: x[1], reverse=True)

for i, (word, freq) in enumerate(sorted_words):
    # Scale frequency to font size
    size = int(min_size + (freq - min_freq) / (max_freq - min_freq) * (max_size - min_size))

    # Estimate word dimensions
    word_width = len(word) * size * 0.6
    word_height = size * 1.3
    padding = 30

    # Find position using spiral algorithm
    cx, cy = canvas_w / 2, canvas_h / 2
    angle = 0
    radius = 0
    found_x, found_y = cx, cy
    found_box = (cx - word_width / 2, cy - word_height / 2, word_width, word_height)

    for _ in range(8000):
        # Elliptical spiral for 16:9 aspect ratio
        x = cx + radius * 1.6 * np.cos(angle) - word_width / 2
        y = cy + radius * np.sin(angle) - word_height / 2

        # Check bounds (leave margin for title and edges)
        if 50 < x < canvas_w - word_width - 50 and 80 < y < canvas_h - word_height - 50:
            box = (x, y, word_width, word_height)

            # Check for overlaps with placed words
            has_overlap = False
            for pb in placed_boxes:
                px, py, pw, ph = pb
                if not (
                    x + word_width + padding < px
                    or px + pw + padding < x
                    or y + word_height + padding < py
                    or py + ph + padding < y
                ):
                    has_overlap = True
                    break

            if not has_overlap:
                found_x = x + word_width / 2
                found_y = y + word_height / 2
                found_box = box
                break

        angle += 0.25
        radius += 2

    placed_boxes.append(found_box)
    words_list.append(word)
    x_positions.append(found_x)
    y_positions.append(found_y)
    font_sizes.append(size)
    colors.append(OKABE_ITO[i % len(OKABE_ITO)])

# Create DataFrame
df = pd.DataFrame({"word": words_list, "x": x_positions, "y": y_positions, "size": font_sizes, "color": colors})

# Create selection for interactivity
selection = alt.selection_point(fields=["word"], on="mouseover")

# Create Altair chart with enhanced styling and interactivity
chart = (
    alt.Chart(df)
    .mark_text(fontWeight="bold", align="center", baseline="middle")
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[0, canvas_w]), axis=None),
        y=alt.Y("y:Q", scale=alt.Scale(domain=[0, canvas_h]), axis=None),
        text="word:N",
        size=alt.Size("size:Q", scale=None, legend=None),
        color=alt.Color("color:N", scale=None, legend=None),
        opacity=alt.condition(selection, alt.value(1), alt.value(0.4)),
        tooltip=["word:N", alt.Tooltip("size:Q", title="Size (freq)")],
    )
    .add_params(selection)
    .properties(
        width=canvas_w,
        height=canvas_h,
        background=PAGE_BG,
        title=alt.Title("wordcloud-basic · altair · anyplot.ai", fontSize=28, anchor="middle", color=INK),
    )
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .configure_title(color=INK)
    .configure_axis(labelFontSize=14, titleFontSize=16, labelColor=INK_SOFT, titleColor=INK)
)

# Save outputs
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
