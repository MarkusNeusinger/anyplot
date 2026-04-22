""" pyplots.ai
wordcloud-basic: Basic Word Cloud
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 78/100 | Created: 2025-12-24
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, HoverTool, LabelSet
from bokeh.plotting import figure


# Data: Technology terms with frequencies (40 words for good density)
np.random.seed(42)
words_data = [
    ("Python", 100),
    ("Data", 95),
    ("Machine", 92),
    ("Learning", 88),
    ("Analytics", 85),
    ("Visualization", 82),
    ("Statistics", 78),
    ("Algorithm", 75),
    ("Model", 72),
    ("Neural", 70),
    ("Network", 68),
    ("Cloud", 65),
    ("API", 62),
    ("Framework", 60),
    ("Library", 58),
    ("Code", 55),
    ("Science", 52),
    ("Analysis", 50),
    ("Deep", 48),
    ("Tensor", 46),
    ("Deploy", 44),
    ("Pipeline", 42),
    ("Training", 40),
    ("Metrics", 38),
    ("Dataset", 36),
    ("Vector", 34),
    ("Graph", 32),
    ("Batch", 30),
    ("Query", 28),
    ("Cache", 26),
    ("Index", 24),
    ("Schema", 22),
    ("Token", 20),
    ("Epoch", 18),
    ("Layer", 16),
    ("Cluster", 14),
    ("Stream", 12),
    ("Config", 10),
    ("Debug", 8),
    ("Stack", 6),
]

# Canvas dimensions
canvas_width = 4800
canvas_height = 2700

# Scale frequencies to font sizes (45-220 pt for better readability and canvas fill)
min_freq = min(f for _, f in words_data)
max_freq = max(f for _, f in words_data)
min_size, max_size = 45, 220

# Rotation angles for visual interest (0, 90, -90 degrees)
rotations = [0, 0, 90, -90]  # 50% horizontal, 50% rotated for variety

# Build word positions using Archimedean spiral placement with rotation
words = []
x_pos = []
y_pos = []
sizes = []
colors = []
angles = []
frequencies = []
placed_boxes = []

for i, (word, freq) in enumerate(words_data):
    # Scale frequency to font size
    size = int(min_size + (freq - min_freq) / (max_freq - min_freq) * (max_size - min_size))

    # Assign rotation based on pattern (top 5 words stay horizontal for readability)
    if i < 5:
        angle_deg = 0  # Keep top words horizontal for readability
    else:
        angle_deg = rotations[i % len(rotations)]
    angle_rad = np.radians(angle_deg)

    # Estimate word dimensions for collision detection (swap for rotated words)
    base_width = len(word) * size * 0.58
    base_height = size * 1.2
    if angle_deg != 0:
        word_width = base_height
        word_height = base_width
    else:
        word_width = base_width
        word_height = base_height

    # Find non-overlapping position using Archimedean spiral
    cx, cy = canvas_width / 2, canvas_height / 2
    spiral_angle = 0
    radius = 0
    padding = 10  # Tighter packing for better density
    found_x, found_y = cx, cy
    found_box = (cx - word_width / 2, cy - word_height / 2, word_width, word_height)

    for _ in range(25000):
        # Elliptical spiral to better fill 16:9 canvas
        test_x = cx + radius * 2.0 * np.cos(spiral_angle) - word_width / 2
        test_y = cy + radius * np.sin(spiral_angle) - word_height / 2

        # Check bounds - minimal margins to maximize canvas usage
        margin_x = 30
        margin_y = 50
        if (
            margin_x < test_x < canvas_width - word_width - margin_x
            and margin_y < test_y < canvas_height - word_height - margin_y
        ):
            test_box = (test_x, test_y, word_width, word_height)

            # Check for overlaps with placed words
            overlap = False
            for pb in placed_boxes:
                px, py, pw, ph = pb
                if not (
                    test_x + word_width + padding < px
                    or px + pw + padding < test_x
                    or test_y + word_height + padding < py
                    or py + ph + padding < test_y
                ):
                    overlap = True
                    break

            if not overlap:
                found_x = test_x + word_width / 2
                found_y = test_y + word_height / 2
                found_box = test_box
                break

        spiral_angle += 0.08  # Finer spiral steps for tighter packing
        radius += 0.8  # Slower radius growth keeps words closer together

    placed_boxes.append(found_box)
    words.append(word)
    x_pos.append(found_x)
    y_pos.append(found_y)
    sizes.append(size)
    angles.append(angle_rad)
    frequencies.append(freq)
    # Color by frequency range (semantic coloring)
    if freq >= 80:
        colors.append("#306998")  # Python Blue - highest frequency
    elif freq >= 50:
        colors.append("#4B8BBE")  # Lighter blue - medium-high
    elif freq >= 25:
        colors.append("#FFD43B")  # Python Yellow - medium-low
    else:
        colors.append("#FFE873")  # Lighter yellow - lowest

# Create Bokeh figure with hover tool
p = figure(
    width=4800,
    height=2700,
    title="wordcloud-basic · bokeh · pyplots.ai",
    x_range=(0, canvas_width),
    y_range=(0, canvas_height),
    tools="hover",
    toolbar_location=None,
)

# Calculate hit area sizes (proportional to font size)
hit_sizes = [s * 0.8 for s in sizes]

# Create data source with all attributes for hover
source = ColumnDataSource(
    data={
        "x": x_pos,
        "y": y_pos,
        "text": words,
        "size": sizes,
        "hit_size": hit_sizes,
        "color": colors,
        "angle": angles,
        "frequency": frequencies,
    }
)

# Add invisible scatter points for hover detection
p.scatter(x="x", y="y", size="hit_size", source=source, fill_alpha=0, line_alpha=0)

# Configure hover tool to show word frequency
hover = p.select_one(HoverTool)
hover.tooltips = [("Word", "@text"), ("Frequency", "@frequency")]
hover.mode = "mouse"

# Convert sizes to string format for LabelSet
source.data["size"] = [f"{s}pt" for s in sizes]

# Add words as labels with rotation
labels = LabelSet(
    x="x",
    y="y",
    text="text",
    text_font_size="size",
    text_color="color",
    text_align="center",
    text_baseline="middle",
    text_font_style="bold",
    angle="angle",
    source=source,
)
p.add_layout(labels)

# Clean appearance - no axes or grid
p.axis.visible = False
p.grid.visible = False
p.outline_line_color = None

# Style title
p.title.text_font_size = "36pt"
p.title.align = "center"

# Light background
p.background_fill_color = "#FAFAFA"

# Save outputs
export_png(p, filename="plot.png")
output_file("plot.html")
save(p)
