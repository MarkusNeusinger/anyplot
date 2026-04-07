""" pyplots.ai
qrcode-basic: Basic QR Code Generator
Library: pygal 3.1.0 | Python 3.14.3
Quality: 86/100 | Updated: 2026-04-07
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

# --- Data ---
qr_content = "https://pyplots.ai"

qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=1, border=0)
qr.add_data(qr_content)
qr.make(fit=True)
qr_matrix = qr.get_matrix()
matrix_size = len(qr_matrix)
quiet_zone = 4
total_cols = matrix_size + 2 * quiet_zone

# --- Color mapping for QR structural elements ---
FINDER_DARK = "#1a237e"  # Deep indigo for finder patterns
DATA_DARK = "#000000"  # Black for data modules
WHITE = "#FFFFFF"


def is_finder(row, col, size):
    """Check if cell belongs to a finder pattern (three 7x7 corner squares)."""
    if row < 7 and col < 7:
        return True
    if row < 7 and col >= size - 7:
        return True
    if row >= size - 7 and col < 7:
        return True
    return False


# --- Style ---
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

# --- Chart ---
# Inject CSS to remove strokes between bars (pygal's SVG/CSS capability)
no_gap_css = (
    "inline:rect { stroke-width: 0 !important; stroke: none !important; shape-rendering: crispEdges !important; }"
)

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
    range=(0, total_cols),
    x_title=(
        f"{qr_content}  \u00b7  Error Correction: M (15%)"
        f"  \u00b7  {matrix_size}\u00d7{matrix_size} modules"
        f"  \u00b7  Finder patterns highlighted in indigo"
    ),
    css=["file://style.css", "file://graph.css", no_gap_css],
)

# --- Build rows ---
# Slight oversize (1.03) makes rows overlap, eliminating SVG rendering seams
CELL = 1.03
white_row = [{"value": CELL, "color": WHITE} for _ in range(total_cols)]

# Bottom quiet zone
for _ in range(quiet_zone):
    chart.add("", white_row)

# QR matrix rows (bottom to top for StackedBar stacking)
for row_idx in reversed(range(matrix_size)):
    row_data = []
    for col_idx in range(-quiet_zone, matrix_size + quiet_zone):
        if col_idx < 0 or col_idx >= matrix_size:
            row_data.append({"value": CELL, "color": WHITE})
        elif qr_matrix[row_idx][col_idx]:
            color = FINDER_DARK if is_finder(row_idx, col_idx, matrix_size) else DATA_DARK
            row_data.append({"value": CELL, "color": color})
        else:
            row_data.append({"value": CELL, "color": WHITE})
    chart.add("", row_data)

# Top quiet zone
for _ in range(quiet_zone):
    chart.add("", white_row)

# --- Save ---
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
