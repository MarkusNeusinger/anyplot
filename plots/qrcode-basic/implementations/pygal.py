""" pyplots.ai
qrcode-basic: Basic QR Code Generator
Library: pygal 3.1.0 | Python 3.14.3
Quality: 81/100 | Updated: 2026-04-07
"""

import sys

import qrcode


# Avoid name collision: this file is named pygal.py, which shadows the package
_cwd = sys.path[0] if sys.path[0] else "."
if _cwd in sys.path:
    sys.path.remove(_cwd)

import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


sys.path.insert(0, _cwd)

# Data - URL to encode in QR code
qr_content = "https://pyplots.ai"

# Generate QR code matrix using qrcode library (real, scannable)
qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=1, border=0)
qr.add_data(qr_content)
qr.make(fit=True)
qr_matrix = qr.get_matrix()

matrix_size = len(qr_matrix)
quiet_zone = 4

# Build row data for StackedBar (each row becomes a stacked layer)
# Rows go bottom-to-top in StackedBar, so reverse the matrix
total_cols = matrix_size + 2 * quiet_zone

# Style
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#000000",),
    title_font_size=72,
    label_font_size=42,
    major_label_font_size=42,
    legend_font_size=0,
    value_font_size=0,
    font_family="sans-serif",
    opacity=1.0,
    opacity_hover=1.0,
    transition="0s",
)

# Chart - square canvas, stacked bar to render QR grid
chart = pygal.StackedBar(
    width=3600,
    height=3600,
    style=custom_style,
    title="qrcode-basic \u00b7 pygal \u00b7 pyplots.ai",
    show_legend=False,
    show_x_labels=False,
    show_y_labels=False,
    show_x_guides=False,
    show_y_guides=False,
    spacing=0,
    margin=180,
    margin_top=250,
    margin_bottom=400,
    print_values=False,
    range=(0, matrix_size + 2 * quiet_zone),
    x_title=f"{qr_content}  \u00b7  Error Correction: M (15%)  \u00b7  {matrix_size}\u00d7{matrix_size} modules",
)

# Add quiet zone rows at bottom
for _ in range(quiet_zone):
    row_data = [{"value": 1, "color": "#FFFFFF"} for _ in range(total_cols)]
    chart.add("", row_data)

# Add QR matrix rows (bottom to top, since StackedBar stacks upward)
for row_idx in reversed(range(matrix_size)):
    row_data = []
    # Left quiet zone
    for _ in range(quiet_zone):
        row_data.append({"value": 1, "color": "#FFFFFF"})
    # QR modules
    for col_idx in range(matrix_size):
        color = "#000000" if qr_matrix[row_idx][col_idx] else "#FFFFFF"
        row_data.append({"value": 1, "color": color})
    # Right quiet zone
    for _ in range(quiet_zone):
        row_data.append({"value": 1, "color": "#FFFFFF"})
    chart.add("", row_data)

# Add quiet zone rows at top
for _ in range(quiet_zone):
    row_data = [{"value": 1, "color": "#FFFFFF"} for _ in range(total_cols)]
    chart.add("", row_data)

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
