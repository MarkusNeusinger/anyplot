""" pyplots.ai
map-animated-temporal: Animated Map over Time
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-20
"""

from io import BytesIO

from PIL import Image, ImageDraw, ImageFont
from pygal.style import Style
from pygal_maps_world.maps import World


# Data: Simulated seismic activity spreading over time (6 time periods)
# Shows earthquake activity propagating across Pacific Ring of Fire regions
time_periods = ["T1: Initial", "T2: +6h", "T3: +12h", "T4: +24h", "T5: +48h", "T6: +72h"]

# Countries in Pacific Ring of Fire and nearby regions
# Activity spreads outward from initial epicenter (Japan region)
# Values represent seismic intensity index (0-100)
# Distribute activity levels to ensure all categories are visible in each panel
activity_by_time = {
    0: {"jp": 95, "kr": 15, "ph": 25, "id": 38},
    1: {"jp": 85, "kr": 55, "ph": 40, "id": 22, "nz": 15},
    2: {"jp": 75, "kr": 70, "ph": 65, "id": 50, "tw": 45, "my": 18},
    3: {"jp": 60, "kr": 55, "ph": 75, "id": 80, "tw": 50, "my": 35, "nz": 40, "au": 22},
    4: {"jp": 45, "kr": 40, "ph": 60, "id": 70, "tw": 40, "my": 50, "nz": 65, "au": 35, "cl": 30, "pe": 18},
    5: {
        "jp": 35,
        "kr": 30,
        "ph": 45,
        "id": 55,
        "tw": 30,
        "my": 45,
        "nz": 55,
        "au": 50,
        "cl": 60,
        "pe": 40,
        "mx": 35,
        "ec": 25,
    },
}

# Activity level labels and thresholds (for binning)
activity_bins = [
    ("Minimal (<20)", 0, 20),
    ("Low (20-35)", 20, 35),
    ("Moderate (35-50)", 35, 50),
    ("High (50-65)", 50, 65),
    ("Severe (65-80)", 65, 80),
    ("Extreme (80+)", 80, 101),
]

# Colorblind-friendly sequential palette (viridis-inspired: yellow to blue/purple)
colors = ("#fde725", "#7ad151", "#22a884", "#2a788e", "#414487", "#440154")

# Custom style for individual maps (no legend - will add shared legend to composite)
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#111111",
    foreground_subtle="#666666",
    colors=colors,
    title_font_size=64,
    label_font_size=32,
    legend_font_size=32,
    major_label_font_size=28,
    value_font_size=28,
    tooltip_font_size=28,
    no_data_font_size=28,
)

# Generate small multiples: 2 rows x 3 columns grid for 6 time periods
# Each individual map rendered without legend to avoid redundancy
individual_width = 1600
individual_height = 1100
grid_cols = 3
grid_rows = 2

map_images = []
for time_idx in range(6):
    data = activity_by_time[time_idx]

    # Inline binning: group countries by activity level
    binned = {label: {} for label, _, _ in activity_bins}
    for country, value in data.items():
        for label, low, high in activity_bins:
            if low <= value < high:
                binned[label][country] = value
                break

    worldmap = World(
        style=custom_style,
        width=individual_width,
        height=individual_height,
        title=time_periods[time_idx],
        show_legend=False,
    )

    # Add all categories (with or without data) to maintain consistent coloring
    for label, _, _ in activity_bins:
        category_data = binned.get(label, {})
        if category_data:
            worldmap.add(label, category_data)

    # Render to PNG bytes
    png_bytes = worldmap.render_to_png()
    map_images.append(Image.open(BytesIO(png_bytes)))

# Create combined image: target 4800x2700 with space for title and shared legend
title_height = 150
legend_height = 150
combined_width = 4800
combined_height = 2700
combined = Image.new("RGB", (combined_width, combined_height), "white")

# Calculate grid cell size
cell_width = combined_width // grid_cols
cell_height = (combined_height - title_height - legend_height) // grid_rows

# Load fonts for title and legend
try:
    title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
    legend_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 42)
except OSError:
    title_font = ImageFont.load_default()
    legend_font = ImageFont.load_default()

draw = ImageDraw.Draw(combined)

# Add title at top center
title_text = "Seismic Activity Temporal Progression · map-animated-temporal · pygal · pyplots.ai"
bbox = draw.textbbox((0, 0), title_text, font=title_font)
text_width = bbox[2] - bbox[0]
title_x = (combined_width - text_width) // 2
draw.text((title_x, 40), title_text, fill="#111111", font=title_font)

# Paste individual maps in grid
for idx, img in enumerate(map_images):
    row = idx // grid_cols
    col = idx % grid_cols
    img_resized = img.resize((cell_width, cell_height), Image.Resampling.LANCZOS)
    x = col * cell_width
    y = row * cell_height + title_height
    combined.paste(img_resized, (x, y))

# Draw single shared legend at bottom
legend_y = combined_height - legend_height + 30
legend_labels = [label for label, _, _ in activity_bins]
box_size = 40
spacing = 50
total_legend_width = sum(draw.textbbox((0, 0), lbl, font=legend_font)[2] for lbl in legend_labels)
total_legend_width += len(legend_labels) * (box_size + spacing + 20)
legend_x = (combined_width - total_legend_width) // 2

for label, color in zip(legend_labels, colors, strict=True):
    # Draw color box
    draw.rectangle([legend_x, legend_y, legend_x + box_size, legend_y + box_size], fill=color, outline="#333333")
    # Draw label text
    text_x = legend_x + box_size + 12
    draw.text((text_x, legend_y + 2), label, fill="#111111", font=legend_font)
    # Move to next position
    text_bbox = draw.textbbox((0, 0), label, font=legend_font)
    legend_x += box_size + 12 + (text_bbox[2] - text_bbox[0]) + spacing

combined.save("plot.png", dpi=(300, 300))

# Also save individual HTML for interactivity (final snapshot for web viewing)
final_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#111111",
    foreground_subtle="#666666",
    colors=colors,
    title_font_size=72,
    label_font_size=48,
    legend_font_size=48,
    major_label_font_size=40,
    value_font_size=40,
    tooltip_font_size=36,
    no_data_font_size=36,
)
final_map = World(
    style=final_style,
    width=4800,
    height=2700,
    title="Seismic Activity (T6: +72h) · map-animated-temporal · pygal · pyplots.ai",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=6,
    legend_box_size=48,
)
final_data = activity_by_time[5]
final_binned = {label: {} for label, _, _ in activity_bins}
for country, value in final_data.items():
    for label, low, high in activity_bins:
        if low <= value < high:
            final_binned[label][country] = value
            break
for label, _, _ in activity_bins:
    category_data = final_binned.get(label, {})
    if category_data:
        final_map.add(label, category_data)
final_map.render_to_file("plot.html")
