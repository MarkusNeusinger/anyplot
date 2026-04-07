"""pyplots.ai
qrcode-basic: Basic QR Code Generator
Library: pygal 3.1.0 | Python 3.14.3
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

# --- Color palette for QR structural elements ---
FINDER_DARK = "#1a237e"  # Deep indigo — finder patterns
TIMING_DARK = "#6a1b9a"  # Purple — timing strips
ALIGN_DARK = "#00695c"  # Teal — alignment pattern
DATA_DARK = "#212121"  # Near-black — data modules
WHITE = "#FFFFFF"

# --- Identify structural elements inline (KISS: no helper functions) ---
finder_cells = set()
for r in range(7):
    for c in range(7):
        finder_cells.add((r, c))  # Top-left
        finder_cells.add((r, matrix_size - 7 + c))  # Top-right
        finder_cells.add((matrix_size - 7 + r, c))  # Bottom-left

timing_cells = set()
for i in range(7, matrix_size - 7):
    timing_cells.add((6, i))  # Horizontal timing strip
    timing_cells.add((i, 6))  # Vertical timing strip

align_cells = set()
if matrix_size >= 25:
    ax, ay = matrix_size - 7, matrix_size - 7
    for dr in range(-2, 3):
        for dc in range(-2, 3):
            align_cells.add((ax + dr, ay + dc))

# --- Style ---
custom_style = Style(
    background="white",
    plot_background="#fafafa",
    foreground="#333333",
    foreground_strong="#222222",
    foreground_subtle="#666666",
    colors=("#000000",),
    title_font_size=64,
    label_font_size=36,
    major_label_font_size=36,
    legend_font_size=0,
    value_font_size=0,
    font_family="'Helvetica Neue', Helvetica, Arial, sans-serif",
    opacity=1.0,
    opacity_hover=1.0,
    transition="0s",
)

# --- Chart ---
# CSS: remove bar strokes for seamless pixel grid; add subtle border to plot area
custom_css = (
    "inline:"
    "rect { stroke-width: 0 !important; stroke: none !important;"
    " shape-rendering: crispEdges !important; }"
    " .plot_background { stroke: #bdbdbd !important; stroke-width: 2 !important;"
    " rx: 6 !important; ry: 6 !important; }"
    " .title { font-weight: 600 !important; letter-spacing: 1px !important; }"
)

chart = pygal.StackedBar(
    width=3600,
    height=3600,
    style=custom_style,
    title="qrcode-basic · pygal · pyplots.ai",
    show_legend=False,
    show_x_labels=False,
    show_y_labels=False,
    show_x_guides=False,
    show_y_guides=False,
    spacing=0,
    margin=100,
    margin_top=160,
    margin_bottom=300,
    print_values=False,
    range=(0, total_cols),
    x_title=(
        f"{qr_content}  ·  Error Correction: M (15%)"
        f"  ·  {matrix_size}×{matrix_size} modules\n"
        f"■ Finder (indigo)   ■ Timing (purple)"
        f"   ■ Alignment (teal)   ■ Data (black)"
    ),
    css=["file://style.css", "file://graph.css", custom_css],
)

# --- Build rows ---
# Slight oversize (1.03) ensures rows overlap, eliminating SVG rendering seams
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
            pos = (row_idx, col_idx)
            if pos in finder_cells:
                color = FINDER_DARK
            elif pos in align_cells:
                color = ALIGN_DARK
            elif pos in timing_cells:
                color = TIMING_DARK
            else:
                color = DATA_DARK
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
