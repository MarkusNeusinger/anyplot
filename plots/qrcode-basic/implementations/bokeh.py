"""pyplots.ai
qrcode-basic: Basic QR Code Generator
Library: bokeh 3.8.2 | Python 3.14.3
Quality: /100 | Updated: 2026-04-07
"""

import numpy as np
import qrcode
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, Label
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

# Create coordinates for black modules
black_x = []
black_y = []
for row in range(size):
    for col in range(size):
        if qr_matrix[row, col]:
            black_x.append(col + quiet_zone + 0.5)
            black_y.append(size - row - 1 + quiet_zone + 0.5)

source = ColumnDataSource(data={"x": black_x, "y": black_y})

total_size = size + 2 * quiet_zone

# Plot - square format for QR code (3600x3600)
p = figure(
    width=3600,
    height=3600,
    title="qrcode-basic \u00b7 bokeh \u00b7 pyplots.ai",
    x_range=(-1, total_size + 1),
    y_range=(-3, total_size + 1),
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

# Draw QR code modules as unit squares
p.rect(x="x", y="y", width=1, height=1, source=source, fill_color="#000000", line_color=None)

# Footer with encoded content and version info
encoded_label = Label(
    x=total_size / 2,
    y=-1.5,
    text=f"Encoded: {content}",
    text_font_size="20pt",
    text_color="#555555",
    text_font="monospace",
    text_align="center",
)
p.add_layout(encoded_label)

version_label = Label(
    x=total_size / 2,
    y=-3,
    text=f"Version {qr.version} ({size}\u00d7{size}) \u00b7 Error Correction Level M (15%)",
    text_font_size="14pt",
    text_color="#888888",
    text_align="center",
)
p.add_layout(version_label)

# Save
export_png(p, filename="plot.png")

output_file("plot.html", title="QR Code - pyplots.ai")
save(p)
