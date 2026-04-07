""" pyplots.ai
qrcode-basic: Basic QR Code Generator
Library: bokeh 3.8.2 | Python 3.14.3
Quality: 86/100 | Updated: 2026-04-07
"""

import numpy as np
import qrcode
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Label
from bokeh.plotting import figure


# Data - Generate a real, scannable QR code encoding "https://pyplots.ai"
content = "https://pyplots.ai"

qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=1, border=0)
qr.add_data(content)
qr.make(fit=True)

# Convert QR matrix to numpy array (True = black module)
qr_matrix = np.array(qr.get_matrix(), dtype=bool)
size = qr_matrix.shape[0]

# Add quiet zone for reliable scanning
quiet_zone = 4

# Classify QR code regions for visual storytelling
finder_size = 7
alignment_pos = qrcode.util.pattern_position(qr.version)

# Build sets of finder pattern coordinates for fast lookup
finder_corners = set()
for r in range(finder_size):
    for c in range(finder_size):
        finder_corners.add((r, c))  # Top-Left
        finder_corners.add((r, size - finder_size + c))  # Top-Right
        finder_corners.add((size - finder_size + r, c))  # Bottom-Left

# Build set of alignment pattern coordinates
alignment_cells = set()
if alignment_pos:
    for ar in alignment_pos:
        for ac in alignment_pos:
            if (
                (ar, ac) not in {(r, c) for r in range(finder_size) for c in range(finder_size)}
                and (ar, ac)
                not in {(r, size - finder_size + c) for r in range(finder_size) for c in range(finder_size)}
                and (ar, ac)
                not in {(size - finder_size + r, c) for r in range(finder_size) for c in range(finder_size)}
            ):
                for dr in range(-2, 3):
                    for dc in range(-2, 3):
                        alignment_cells.add((ar + dr, ac + dc))

# Create coordinates with region classification
mod_x, mod_y, mod_region, mod_color = [], [], [], []
color_map = {
    "Finder Pattern": "#306998",
    "Timing Pattern": "#4A8BBE",
    "Alignment Pattern": "#4A8BBE",
    "Data & Error Correction": "#1a1a1a",
}

for row in range(size):
    for col in range(size):
        if qr_matrix[row, col]:
            if (row, col) in finder_corners:
                region = "Finder Pattern"
            elif (row == 6 and finder_size <= col <= size - finder_size - 1) or (
                col == 6 and finder_size <= row <= size - finder_size - 1
            ):
                region = "Timing Pattern"
            elif (row, col) in alignment_cells:
                region = "Alignment Pattern"
            else:
                region = "Data & Error Correction"
            mod_x.append(col + quiet_zone + 0.5)
            mod_y.append(size - row - 1 + quiet_zone + 0.5)
            mod_region.append(region)
            mod_color.append(color_map[region])

source = ColumnDataSource(data={"x": mod_x, "y": mod_y, "region": mod_region, "color": mod_color})

total_size = size + 2 * quiet_zone

# Plot - square format for QR code (3600x3600)
p = figure(
    width=3600,
    height=3600,
    title="qrcode-basic · bokeh · pyplots.ai",
    x_range=(-1, total_size + 1),
    y_range=(-3.5, total_size + 1),
    tools="",
    toolbar_location=None,
    match_aspect=True,
)

# Style - clean white background
p.background_fill_color = "white"
p.border_fill_color = "white"
p.outline_line_color = None

# Hide axes for clean QR code appearance
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False

# Title styling
p.title.text_font_size = "36pt"
p.title.align = "center"
p.title.text_color = "#306998"
p.title.offset = 10

# Draw QR code modules color-coded by region
renderer = p.rect(x="x", y="y", width=1, height=1, source=source, fill_color="color", line_color=None)

# HoverTool - distinctive Bokeh feature for interactive HTML output
hover = HoverTool(renderers=[renderer], tooltips=[("Region", "@region"), ("Position", "(@x, @y)")], mode="mouse")
p.add_tools(hover)

# Footer with encoded content and version info - balanced spacing
encoded_label = Label(
    x=total_size / 2,
    y=-1.0,
    text=f"Encoded: {content}",
    text_font_size="22pt",
    text_color="#555555",
    text_font="monospace",
    text_align="center",
)
p.add_layout(encoded_label)

version_label = Label(
    x=total_size / 2,
    y=-2.5,
    text=f"Version {qr.version} ({size}×{size}) · Error Correction Level M (15%)",
    text_font_size="18pt",
    text_color="#888888",
    text_align="center",
)
p.add_layout(version_label)

# Save
export_png(p, filename="plot.png")

output_file("plot.html", title="QR Code - pyplots.ai")
save(p)
