""" anyplot.ai
donut-nested: Nested Donut Chart
Library: pygal 3.1.0 | Python 3.13.13
Quality: 81/100 | Updated: 2026-05-08
"""

import io
import os

import pygal
from PIL import Image
from pygal.style import Style


# Theme tokens (light/dark adaptive)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
BRAND = "#009E73"  # Okabe-Ito position 1 (first series)

# Data: Market share by region (inner) and product lines within each region (outer)
# Using market share domain per spec's library independence requirement
data = {
    "North America": {"Premium": 320, "Standard": 480, "Budget": 200},
    "Europe": {"Premium": 280, "Standard": 420, "Budget": 150},
    "Asia-Pacific": {"Premium": 450, "Standard": 590, "Budget": 320},
    "LATAM": {"Premium": 140, "Standard": 210, "Budget": 90},
}

# Okabe-Ito color families: each region gets a base hue with lighter shades for product lines
# Position 1 (green) for first region, then positions 2-7 for others
oi_base_colors = (
    "#009E73",  # 1: bluish green
    "#C475FD",  # 2: vermillion
    "#4467A3",  # 3: blue
    "#BD8233",  # 4: reddish purple
)

color_families = {}
for i, region in enumerate(data.keys()):
    base = oi_base_colors[i % len(oi_base_colors)]
    # Generate lighter shades of the base color for child categories
    if THEME == "light":
        # Light versions for light theme
        shades = [base, base + "CC", base + "99", base + "66"]
    else:
        # Slightly brighter for dark theme visibility
        shades = [base, base + "DD", base + "BB", base + "99"]
    color_families[region] = shades

# Prepare data for outer ring (product lines per region)
outer_labels = []
outer_colors = []
for region, products in data.items():
    family = color_families[region]
    for i, product_name in enumerate(products.keys()):
        outer_labels.append(product_name)
        outer_colors.append(family[min(i + 1, len(family) - 1)])

# Prepare data for inner ring (region totals)
inner_values = []
inner_labels = []
inner_colors = []
for region, products in data.items():
    inner_values.append(sum(products.values()))
    inner_labels.append(region)
    inner_colors.append(color_families[region][0])

# Canvas size (square format for symmetric donut)
width = 3600
height = 3600

# Style for outer ring (product lines)
outer_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=tuple(outer_colors),
    title_font_size=32,
    label_font_size=20,
    legend_font_size=18,  # Increased from previous for better readability
    value_font_size=16,
    value_label_font_size=16,
)

# Style for inner ring (regions)
inner_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=tuple(inner_colors),
    title_font_size=32,
    label_font_size=22,
    value_font_size=18,
    value_label_font_size=18,
)

# Create outer ring (product lines per region)
# This renders as a transparent SVG that will be composited with the inner ring
outer_ring = pygal.Pie(
    width=width,
    height=height,
    style=outer_style,
    inner_radius=0.55,
    title="donut-nested · pygal · anyplot.ai",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    print_values=True,
    value_formatter=lambda x: f"${x}M",
    margin=80,
)

# Add outer ring data (product lines with parent region labels)
for region, products in data.items():
    for product_name, value in products.items():
        outer_ring.add(f"{region}: {product_name}", [{"value": value, "label": product_name}])

# Create inner ring (region totals)
# This is a separate pie chart that will be composited on top of the outer ring
inner_ring = pygal.Pie(
    width=int(width * 0.50),
    height=int(height * 0.50),
    style=inner_style,
    inner_radius=0.45,
    show_legend=False,
    print_values=True,
    value_formatter=lambda x: f"${x}M",
)

for label, value in zip(inner_labels, inner_values, strict=True):
    inner_ring.add(label, [{"value": value, "label": label}])

# Render both rings to PNG bytes
# This is a creative compositing technique to achieve nested donuts in pygal
outer_png = outer_ring.render_to_png()
inner_png = inner_ring.render_to_png()

# Load rendered PNGs as PIL Images with transparency support
outer_img = Image.open(io.BytesIO(outer_png)).convert("RGBA")
inner_img = Image.open(io.BytesIO(inner_png)).convert("RGBA")

# Create background with the appropriate theme color
bg_color = (250, 248, 241, 255) if THEME == "light" else (26, 26, 23, 255)
combined = Image.new("RGBA", (width, height), bg_color)

# Paste outer ring (the full-sized pie chart with inner_radius cutout)
combined.paste(outer_img, (0, 0), outer_img)

# Calculate position to center inner ring inside the outer ring's cutout
inner_x = (width - inner_img.width) // 2
inner_y = (height - inner_img.height) // 2 - 40

# Paste inner ring (centered, composited on top)
combined.paste(inner_img, (inner_x, inner_y), inner_img)

# Convert to RGB and save as PNG with theme suffix
combined_rgb = combined.convert("RGB")
combined_rgb.save(f"plot-{THEME}.png")

# Save HTML version with interactive outer ring
html_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=tuple(outer_colors),
    title_font_size=32,
    label_font_size=20,
    legend_font_size=18,
    value_font_size=16,
)

html_chart = pygal.Pie(
    width=width,
    height=height,
    style=html_style,
    inner_radius=0.4,
    title="donut-nested · pygal · anyplot.ai",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    print_values=True,
    value_formatter=lambda x: f"${x}M",
)

for region, products in data.items():
    for product_name, value in products.items():
        html_chart.add(f"{region}: {product_name}", [{"value": value}])

html_chart.render_to_file(f"plot-{THEME}.html")
