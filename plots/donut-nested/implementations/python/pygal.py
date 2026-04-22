""" pyplots.ai
donut-nested: Nested Donut Chart
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-25
"""

import io

import pygal
from PIL import Image
from pygal.style import Style


# Data: Budget allocation by department (inner) and expense categories (outer)
data = {
    "Engineering": {"Salaries": 450, "Equipment": 180, "Training": 70},
    "Marketing": {"Advertising": 280, "Events": 120, "Content": 100},
    "Operations": {"Infrastructure": 200, "Utilities": 80, "Maintenance": 60},
    "Sales": {"Commissions": 220, "Travel": 90, "Tools": 50},
}

# Color families: each parent has a base color, children use lighter variations
color_families = {
    "Engineering": ["#306998", "#4A89B8", "#6BA3C8", "#8CBDD8"],  # Blue family
    "Marketing": ["#FFD43B", "#FFE066", "#FFEB99", "#FFF2B3"],  # Yellow family
    "Operations": ["#2ECC71", "#58D68D", "#82E0AA", "#ABEBC6"],  # Green family
    "Sales": ["#E74C3C", "#EC7063", "#F1948A", "#F5B7B1"],  # Red family
}

# Prepare data for outer ring (children - detailed breakdown)
outer_labels = []
outer_colors = []

for parent, children in data.items():
    family = color_families[parent]
    for i, child_name in enumerate(children.keys()):
        outer_labels.append(child_name)
        outer_colors.append(family[min(i + 1, len(family) - 1)])

# Prepare data for inner ring (parents - department totals)
inner_values = []
inner_labels = []
inner_colors = []

for parent, children in data.items():
    inner_values.append(sum(children.values()))
    inner_labels.append(parent)
    inner_colors.append(color_families[parent][0])

# Canvas size
width = 3600
height = 3600

# Style for outer ring (subcategories)
outer_style = Style(
    background="transparent",
    plot_background="transparent",
    foreground="#333",
    foreground_strong="#333",
    foreground_subtle="#666",
    colors=tuple(outer_colors),
    title_font_size=52,
    label_font_size=24,
    value_font_size=22,
    value_label_font_size=22,
)

# Style for inner ring (departments)
inner_style = Style(
    background="transparent",
    plot_background="transparent",
    foreground="#333",
    foreground_strong="#333",
    foreground_subtle="#666",
    colors=tuple(inner_colors),
    title_font_size=52,
    label_font_size=30,
    value_font_size=28,
    value_label_font_size=28,
)

# Create outer ring (subcategories)
outer_ring = pygal.Pie(
    width=width,
    height=height,
    style=outer_style,
    inner_radius=0.58,
    title="donut-nested · pygal · pyplots.ai",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    print_values=True,
    value_formatter=lambda x: f"${x}K",
    margin=50,
)

# Add outer ring data (subcategories)
for parent, children in data.items():
    for child_name, value in children.items():
        outer_ring.add(f"{parent}: {child_name}", [{"value": value, "label": child_name}])

# Create inner ring (departments) - smaller to fit inside
inner_ring = pygal.Pie(
    width=int(width * 0.56),
    height=int(height * 0.56),
    style=inner_style,
    inner_radius=0.5,
    show_legend=False,
    print_values=True,
    value_formatter=lambda x: f"${x}K",
)

for label, value in zip(inner_labels, inner_values, strict=True):
    inner_ring.add(label, [{"value": value, "label": label}])

# Render both to PNG bytes
outer_png = outer_ring.render_to_png()
inner_png = inner_ring.render_to_png()

# Load as PIL Images
outer_img = Image.open(io.BytesIO(outer_png)).convert("RGBA")
inner_img = Image.open(io.BytesIO(inner_png)).convert("RGBA")

# Create white background
combined = Image.new("RGBA", (width, height), (255, 255, 255, 255))

# Paste outer ring
combined.paste(outer_img, (0, 0), outer_img)

# Calculate position to center inner ring inside outer
inner_x = (width - inner_img.width) // 2
inner_y = (height - inner_img.height) // 2 - 80  # Adjust for legend at bottom

# Paste inner ring (centered)
combined.paste(inner_img, (inner_x, inner_y), inner_img)

# Convert to RGB and save as PNG
combined_rgb = combined.convert("RGB")
combined_rgb.save("plot.png")

# Save HTML version with interactive outer ring
html_style = Style(
    background="white",
    plot_background="white",
    foreground="#333",
    foreground_strong="#333",
    foreground_subtle="#666",
    colors=tuple(outer_colors),
    title_font_size=48,
    label_font_size=22,
    legend_font_size=20,
    value_font_size=18,
)

html_chart = pygal.Pie(
    width=width,
    height=height,
    style=html_style,
    inner_radius=0.4,
    title="donut-nested · pygal · pyplots.ai",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    print_values=True,
    value_formatter=lambda x: f"${x}K",
)

for parent, children in data.items():
    for child_name, value in children.items():
        html_chart.add(f"{parent}: {child_name}", [{"value": value}])

html_chart.render_to_file("plot.html")
