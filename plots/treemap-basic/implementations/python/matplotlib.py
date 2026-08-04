""" anyplot.ai
treemap-basic: Basic Treemap
Library: matplotlib 3.11.1 | Python 3.13.14
Quality: 89/100 | Updated: 2026-08-04
"""

import colorsys
import os

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.colors import to_hex, to_rgb
from matplotlib.patches import Rectangle


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette for categories
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030"]

# Data - Budget allocation by department and project
data = [
    ("Engineering", "Product Dev", 45),
    ("Sales", "Enterprise", 35),
    ("Marketing", "Digital", 30),
    ("Engineering", "Infrastructure", 25),
    ("Sales", "SMB", 25),
    ("Marketing", "Events", 20),
    ("Operations", "Logistics", 20),
    ("Engineering", "QA", 15),
    ("Sales", "Partners", 15),
    ("Operations", "Support", 15),
    ("HR", "Recruiting", 12),
    ("HR", "Training", 8),
]

# Extract sorted data
categories = [d[0] for d in data]
subcategories = [d[1] for d in data]
values = [d[2] for d in data]

# Category to color mapping (canonical Imprint order)
unique_categories = ["Engineering", "Sales", "Marketing", "Operations", "HR"]
category_colors = {cat: IMPRINT[i % len(IMPRINT)] for i, cat in enumerate(unique_categories)}
category_max = {cat: max(v for c, _, v in data if c == cat) for cat in unique_categories}

# Normalize values to fill a 160x90 area (matching figsize aspect ratio)
total = sum(values)
width, height = 160, 90
normalized = [v / total * width * height for v in values]

# Squarify algorithm - compute rectangle positions
rects = []
remaining = list(zip(normalized, range(len(normalized)), strict=True))
x, y, w, h = 0, 0, width, height

while remaining:
    # Lay out items in current strip
    strip_items = []
    strip_area = 0

    if w >= h:
        # Vertical strip
        for area, idx in remaining:
            strip_items.append((area, idx))
            strip_area += area
            strip_width = strip_area / h
            # Check if aspect ratios are getting worse
            if len(strip_items) > 1:
                aspects = [
                    max(strip_width / (a / strip_width), (a / strip_width) / strip_width) for a, _ in strip_items
                ]
                prev_aspects = []
                prev_area = strip_area - area
                if prev_area > 0:
                    prev_width = prev_area / h
                    prev_aspects = [
                        max(prev_width / (a / prev_width), (a / prev_width) / prev_width) for a, _ in strip_items[:-1]
                    ]
                if prev_aspects and max(aspects) > max(prev_aspects):
                    strip_items.pop()
                    strip_area -= area
                    break
        # Layout strip vertically
        strip_width = strip_area / h if h > 0 else 0
        cy = y
        for area, idx in strip_items:
            rect_h = area / strip_width if strip_width > 0 else 0
            rects.append((x, cy, strip_width, rect_h, idx))
            cy += rect_h
        x += strip_width
        w -= strip_width
    else:
        # Horizontal strip
        for area, idx in remaining:
            strip_items.append((area, idx))
            strip_area += area
            strip_height = strip_area / w
            if len(strip_items) > 1:
                aspects = [
                    max(strip_height / (a / strip_height), (a / strip_height) / strip_height) for a, _ in strip_items
                ]
                prev_aspects = []
                prev_area = strip_area - area
                if prev_area > 0:
                    prev_height = prev_area / w
                    prev_aspects = [
                        max(prev_height / (a / prev_height), (a / prev_height) / prev_height)
                        for a, _ in strip_items[:-1]
                    ]
                if prev_aspects and max(aspects) > max(prev_aspects):
                    strip_items.pop()
                    strip_area -= area
                    break
        # Layout strip horizontally
        strip_height = strip_area / w if w > 0 else 0
        cx = x
        for area, idx in strip_items:
            rect_w = area / strip_height if strip_height > 0 else 0
            rects.append((cx, y, rect_w, strip_height, idx))
            cx += rect_w
        y += strip_height
        h -= strip_height

    # Remove placed items
    placed_indices = {idx for _, idx in strip_items}
    remaining = [(a, i) for a, i in remaining if i not in placed_indices]

# Create plot (3200x1800 px)
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Draw rectangles with labels. Fill lightness is value-driven within each
# category (largest item keeps the full-strength hue, smaller ones lighten
# toward a soft tint) so area and shade reinforce the same magnitude signal.
for rx, ry, rw, rh, idx in rects:
    cat = categories[idx]
    base_r, base_g, base_b = to_rgb(category_colors[cat])
    hue, lightness, sat = colorsys.rgb_to_hls(base_r, base_g, base_b)
    weight = values[idx] / category_max[cat]
    tint = to_hex(colorsys.hls_to_rgb(hue, min(0.92, lightness + (1 - weight) * 0.18), sat))

    rect = Rectangle((rx, ry), rw, rh, facecolor=tint, edgecolor=PAGE_BG, linewidth=1.5)
    ax.add_patch(rect)

    # Add labels for all visible rectangles
    area = rw * rh
    if area > 80:
        fontsize = min(9, max(6, round(area**0.35 * 0.5)))

        label = f"{subcategories[idx]}\n${values[idx]}M"
        ax.text(
            rx + rw / 2, ry + rh / 2, label, ha="center", va="center", fontsize=fontsize, fontweight="bold", color=INK
        )

# Set axis limits and remove axes
ax.set_xlim(0, width)
ax.set_ylim(0, height)
ax.axis("off")
ax.set_aspect("equal")

# Title
ax.set_title("treemap-basic · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=10)

# Legend for categories (canonical Imprint hue, unshaded, for brand fidelity)
legend_handles = [mpatches.Patch(color=category_colors[cat], label=cat) for cat in unique_categories]
leg = ax.legend(
    handles=legend_handles,
    loc="upper center",
    fontsize=8,
    framealpha=0.95,
    edgecolor=INK_SOFT,
    ncol=5,
    bbox_to_anchor=(0.5, -0.03),
)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
for text in leg.get_texts():
    text.set_color(INK_SOFT)

fig.subplots_adjust(left=0.02, right=0.98, top=0.90, bottom=0.13)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
