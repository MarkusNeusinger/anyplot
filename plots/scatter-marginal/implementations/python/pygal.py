""" pyplots.ai
scatter-marginal: Scatter Plot with Marginal Distributions
Library: pygal 3.1.0 | Python 3.13.11
Quality: 88/100 | Created: 2025-12-26
"""

import io

import numpy as np
import pygal
from PIL import Image, ImageDraw, ImageFont
from pygal.style import Style


# Data - correlated bivariate data with realistic measurement context
np.random.seed(42)
n_points = 150
x = np.random.randn(n_points) * 15 + 50  # Measurement A in range ~10-90
y = x * 0.6 + np.random.randn(n_points) * 12 + 20  # Measurement B correlated

# Calculate correlation for annotation
correlation = np.corrcoef(x, y)[0, 1]

# Calculate histogram data for marginals
# Use same number of bins and explicit ranges for better alignment
n_bins = 10
x_min, x_max = np.floor(x.min() / 5) * 5, np.ceil(x.max() / 5) * 5
y_min, y_max = np.floor(y.min() / 5) * 5, np.ceil(y.max() / 5) * 5

x_hist, x_edges = np.histogram(x, bins=n_bins, range=(x_min, x_max))
y_hist, y_edges = np.histogram(y, bins=n_bins, range=(y_min, y_max))

# Dimensions for layout - optimized spacing
total_width = 4800
total_height = 2700
margin_plot_size = 450  # Slightly smaller marginals
title_height = 100
gap = 15
corner_size = margin_plot_size  # Size for corner annotation

# Calculate main scatter dimensions
scatter_width = total_width - margin_plot_size - gap * 3
scatter_height = total_height - margin_plot_size - title_height - gap * 3

# Shared margins for alignment
left_margin = 100
bottom_margin = 80
top_margin = 20
right_margin = 20

# Custom style for main scatter
scatter_style = Style(
    background="#ffffff",
    plot_background="#fafafa",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998",),
    title_font_size=48,
    label_font_size=36,
    major_label_font_size=32,
    legend_font_size=32,
    tooltip_font_size=24,
    opacity=0.65,
    opacity_hover=0.9,
    guide_stroke_color="#e0e0e0",
    major_guide_stroke_color="#cccccc",
)

# Custom style for marginal histograms - subtle color to not distract from main scatter
marginal_style = Style(
    background="#ffffff",
    plot_background="#f8f8f8",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#a8c5db",),  # Subtle, lighter blue for marginals
    title_font_size=32,
    label_font_size=32,
    major_label_font_size=30,
    legend_font_size=28,
    opacity=0.6,  # More transparency for subtle appearance
    guide_stroke_color="#e0e0e0",
)

# Create main scatter plot with explicit axis ranges matching marginal histograms
scatter = pygal.XY(
    width=scatter_width,
    height=scatter_height,
    style=scatter_style,
    x_title="Measurement A (units)",
    y_title="Measurement B (units)",
    show_legend=False,
    stroke=False,
    dots_size=10,
    show_x_guides=True,
    show_y_guides=True,
    x_label_rotation=0,
    truncate_label=-1,
    explicit_size=True,
    margin_top=top_margin,
    margin_right=right_margin,
    margin_bottom=bottom_margin,
    margin_left=left_margin,
    range=(y_min - 5, y_max + 5),  # Y range with slight padding
    xrange=(x_min - 5, x_max + 5),  # X range with slight padding
)

# Add scatter data
scatter_points = [(float(xi), float(yi)) for xi, yi in zip(x, y, strict=True)]
scatter.add("Data", scatter_points)

# Create top marginal histogram (X distribution)
# Use bar chart with x_labels matching scatter X range bins
x_margin = pygal.Bar(
    width=scatter_width,
    height=margin_plot_size,
    style=marginal_style,
    show_legend=False,
    show_x_labels=False,  # Hide to avoid clutter
    show_y_labels=True,
    show_y_guides=True,
    show_x_guides=False,
    margin_top=top_margin,
    margin_right=right_margin,
    margin_bottom=20,
    margin_left=left_margin,
    explicit_size=True,
    spacing=2,  # Tighter spacing for better visual continuity
)
x_margin.add("X Distribution", [float(h) for h in x_hist])

# Create right marginal histogram (Y distribution) - horizontal bars
# Use same margin settings as scatter for better alignment
y_margin = pygal.HorizontalBar(
    width=margin_plot_size,
    height=scatter_height,
    style=marginal_style,
    show_legend=False,
    show_x_labels=False,
    show_y_labels=False,
    show_y_guides=False,
    show_x_guides=False,
    margin_top=top_margin,
    margin_right=30,
    margin_bottom=bottom_margin,  # Match scatter bottom margin
    margin_left=10,
    explicit_size=True,
    spacing=2,  # Tighter spacing matching X marginal
)
# Reverse order to match scatter Y axis orientation (pygal HorizontalBar goes top-to-bottom)
y_margin.add("Y Distribution", [float(h) for h in y_hist[::-1]])

# Render each chart to PNG in memory
scatter_png = scatter.render_to_png()
x_margin_png = x_margin.render_to_png()
y_margin_png = y_margin.render_to_png()

# Open images
scatter_img = Image.open(io.BytesIO(scatter_png))
x_margin_img = Image.open(io.BytesIO(x_margin_png))
y_margin_img = Image.open(io.BytesIO(y_margin_png))

# Create final composite image
final_img = Image.new("RGB", (total_width, total_height), "white")

# Calculate positions - aligned for better visual coherence
scatter_x = gap
scatter_y = title_height + margin_plot_size + gap
x_margin_x = gap
x_margin_y = title_height
y_margin_x = gap + scatter_width + gap
y_margin_y = title_height + margin_plot_size + gap

# Paste images
final_img.paste(x_margin_img, (x_margin_x, x_margin_y))
final_img.paste(y_margin_img, (y_margin_x, y_margin_y))
final_img.paste(scatter_img, (scatter_x, scatter_y))

# Add title and corner annotation
draw = ImageDraw.Draw(final_img)
title_text = "scatter-marginal · pygal · pyplots.ai"
try:
    title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
    stats_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
    stats_font_bold = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 42)
except OSError:
    title_font = ImageFont.load_default()
    stats_font = ImageFont.load_default()
    stats_font_bold = ImageFont.load_default()

# Get text bounding box for centering title
bbox = draw.textbbox((0, 0), title_text, font=title_font)
text_width = bbox[2] - bbox[0]
text_x = (total_width - text_width) // 2
text_y = 30
draw.text((text_x, text_y), title_text, fill="#333333", font=title_font)

# Add statistics in the corner space (top-right empty area)
# This corner is at: x = right of top marginal, y = below title and above right marginal
corner_x = y_margin_x + 30  # Right side where y_margin is
corner_y = title_height + 30  # Just below title area
corner_width = margin_plot_size - 60
corner_height = margin_plot_size - 80

# Draw subtle background for stats box
stats_box = [(corner_x, corner_y), (corner_x + corner_width, corner_y + corner_height)]
draw.rounded_rectangle(stats_box, radius=15, fill="#f5f5f5", outline="#c0c0c0", width=2)

# Add statistics text - centered in box
stats_title = "Summary"
draw.text((corner_x + 35, corner_y + 25), stats_title, fill="#333333", font=stats_font_bold)

stats_lines = [f"n = {n_points}", f"r = {correlation:.3f}", f"A̅ = {np.mean(x):.1f}", f"B̅ = {np.mean(y):.1f}"]
line_y = corner_y + 85
for line in stats_lines:
    draw.text((corner_x + 35, line_y), line, fill="#555555", font=stats_font)
    line_y += 50

# Save final image
final_img.save("plot.png", "PNG")

# Also save the scatter SVG as HTML for interactivity
scatter_svg_full = scatter.render().decode("utf-8")
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(scatter_svg_full)
