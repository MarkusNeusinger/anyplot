""" pyplots.ai
histogram-basic: Basic Histogram
Library: pygal 3.1.0 | Python 3.14.0
Quality: 90/100 | Created: 2025-12-23
"""

import io

import numpy as np
import pygal
from PIL import Image, ImageDraw, ImageFont
from pygal.style import Style


# Data - Exam scores with realistic left skew using beta distribution
np.random.seed(42)
n = 500
# Beta distribution (a=5, b=2) naturally skews left and tapers at both ends
raw = np.random.beta(a=5, b=2, size=n)
values = raw * 60 + 35  # Scale to ~35-95 range (realistic exam scores)

# Compute histogram bins — 20 bins balances detail and readability for n=500
n_bins = 20
counts, bin_edges = np.histogram(values, bins=n_bins)
hist_data = [(int(count), float(bin_edges[i]), float(bin_edges[i + 1])) for i, count in enumerate(counts)]

# Key statistics for storytelling
mean_val = float(np.mean(values))
median_val = float(np.median(values))
q1, q3 = float(np.percentile(values, 25)), float(np.percentile(values, 75))
peak_bin = int(np.argmax(counts))
peak_lo, peak_hi = float(bin_edges[peak_bin]), float(bin_edges[peak_bin + 1])
max_count = int(max(counts))

# Shared font family
font = "DejaVu Sans, Helvetica, Arial, sans-serif"

# Custom style — refined typography, subtle grid, polished chrome
custom_style = Style(
    background="white",
    plot_background="#fafafa",
    foreground="#2d2d2d",
    foreground_strong="#2d2d2d",
    foreground_subtle="#e8e8e8",
    colors=("#306998",),
    font_family=font,
    title_font_family=font,
    title_font_size=56,
    label_font_size=40,
    major_label_font_size=36,
    legend_font_size=32,
    legend_font_family=font,
    value_font_size=30,
    opacity=0.85,
    opacity_hover=0.95,
    guide_stroke_color="#e0e0e0",
    guide_stroke_dasharray="4,4",
    major_guide_stroke_color="#d0d0d0",
    major_guide_stroke_dasharray="6,3",
    stroke_opacity=1.0,
    tooltip_font_size=28,
    tooltip_font_family=font,
    tooltip_border_radius=10,
)

# Chart dimensions
W, H = 4800, 2700

# Create histogram chart
chart = pygal.Histogram(
    width=W,
    height=H,
    style=custom_style,
    title="histogram-basic \u00b7 pygal \u00b7 pyplots.ai",
    x_title="Exam Score (points)",
    y_title="Number of Students",
    show_legend=True,
    legend_at_bottom=True,
    legend_box_size=24,
    show_y_guides=True,
    show_x_guides=False,
    value_formatter=lambda x: f"{x:,.0f}",
    tooltip_fancy_mode=True,
    min_scale=4,
    max_scale=8,
    margin_bottom=100,
    margin_left=80,
    margin_right=60,
    margin_top=80,
    spacing=12,
    print_values=False,
)

# Single histogram series — clean and uncluttered
chart.add("Score Distribution (n=500)", hist_data)

# Render chart to PNG in memory for annotation overlay
chart_png = chart.render_to_png()
img = Image.open(io.BytesIO(chart_png))
draw = ImageDraw.Draw(img)

# Load fonts for annotations
try:
    ann_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
    ann_bold = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 38)
    ann_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
except OSError:
    ann_font = ImageFont.load_default()
    ann_bold = ann_font
    ann_small = ann_font

# Derive plot area bounds proportionally from image dimensions
img_w, img_h = img.size
plot_x0 = int(img_w * 0.073)
plot_x1 = int(img_w * 0.969)
plot_y_top = int(img_h * 0.065)
plot_y_bot = int(img_h * 0.83)

data_min, data_max = float(bin_edges[0]), float(bin_edges[-1])


def data_to_px(val):
    """Convert a data x-value to pixel x-coordinate."""
    return plot_x0 + (val - data_min) / (data_max - data_min) * (plot_x1 - plot_x0)


# Draw mean vertical dashed line — subtle reference that doesn't compete with bars
mean_px = int(data_to_px(mean_val))
dash_len, gap_len = 18, 12
y = plot_y_top
while y < plot_y_bot:
    y_end = min(y + dash_len, plot_y_bot)
    draw.line([(mean_px, y), (mean_px, y_end)], fill="#c0392b", width=4)
    y += dash_len + gap_len

# Mean label — placed at bottom of dashed line, near x-axis, to avoid crowding peak area
mean_tag = f"Mean ({mean_val:.1f}) \u2192"
mtbox = draw.textbbox((0, 0), mean_tag, font=ann_small)
mt_w = mtbox[2] - mtbox[0]
draw.text((mean_px - mt_w - 12, plot_y_bot + 6), mean_tag, fill="#c0392b", font=ann_small)

# Annotation: summary statistics box in upper-left area
box_x, box_y = plot_x0 + 100, plot_y_top + 30
box_w, box_h = 1020, 380
draw.rounded_rectangle(
    [(box_x, box_y), (box_x + box_w, box_y + box_h)], radius=18, fill="#ffffffd9", outline="#b0b0b0", width=2
)
draw.text((box_x + 30, box_y + 22), "Distribution Summary", fill="#2d2d2d", font=ann_bold)
draw.line([(box_x + 30, box_y + 72), (box_x + box_w - 30, box_y + 72)], fill="#d0d0d0", width=2)
stats_lines = [
    f"Mean: {mean_val:.1f}  |  Median: {median_val:.1f}",
    f"Spread (IQR): {q1:.0f} \u2013 {q3:.0f} pts",
    f"Peak bin: {peak_lo:.0f}\u2013{peak_hi:.0f} pts ({int(counts[peak_bin])} students)",
    "Skew: left-skewed (mean < median)",
]
ly = box_y + 88
for line in stats_lines:
    draw.text((box_x + 30, ly), line, fill="#444444", font=ann_font)
    ly += 62

# Annotation: peak callout above the tallest bar — well clear of mean label
peak_mid = (peak_lo + peak_hi) / 2
peak_px = data_to_px(peak_mid)
label_text = f"\u25bc Peak: {peak_lo:.0f}\u2013{peak_hi:.0f} pts"
bbox = draw.textbbox((0, 0), label_text, font=ann_bold)
label_w = bbox[2] - bbox[0]
peak_label_x = int(peak_px - label_w / 2)
draw.text((peak_label_x, plot_y_top - 50), label_text, fill="#306998", font=ann_bold)

# Save annotated image
img.save("plot.png", "PNG")

# Save interactive HTML version (without PIL annotations)
chart.render_to_file("plot.html")
