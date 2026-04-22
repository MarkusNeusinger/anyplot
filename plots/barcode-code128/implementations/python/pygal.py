""" pyplots.ai
barcode-code128: Code 128 Barcode
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-19
"""

import pygal
from pygal.style import Style


# Code 128B character values (space to DEL mapped to 0-94)
CODE128B_CHARS = " !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~"

# All 107 patterns for Code 128 (values 0-106)
# Each pattern is (bar, space, bar, space, bar, space) with widths 1-4
CODE128_PATTERNS = [
    (2, 1, 2, 2, 2, 2),
    (2, 2, 2, 1, 2, 2),
    (2, 2, 2, 2, 2, 1),
    (1, 2, 1, 2, 2, 3),
    (1, 2, 1, 3, 2, 2),
    (1, 3, 1, 2, 2, 2),
    (1, 2, 2, 2, 1, 3),
    (1, 2, 2, 3, 1, 2),
    (1, 3, 2, 2, 1, 2),
    (2, 2, 1, 2, 1, 3),
    (2, 2, 1, 3, 1, 2),
    (2, 3, 1, 2, 1, 2),
    (1, 1, 2, 2, 3, 2),
    (1, 2, 2, 1, 3, 2),
    (1, 2, 2, 2, 3, 1),
    (1, 1, 3, 2, 2, 2),
    (1, 2, 3, 1, 2, 2),
    (1, 2, 3, 2, 2, 1),
    (2, 2, 3, 2, 1, 1),
    (2, 2, 1, 1, 3, 2),
    (2, 2, 1, 2, 3, 1),
    (2, 1, 3, 2, 1, 2),
    (2, 2, 3, 1, 1, 2),
    (3, 1, 2, 1, 3, 1),
    (3, 1, 1, 2, 2, 2),
    (3, 2, 1, 1, 2, 2),
    (3, 2, 1, 2, 2, 1),
    (3, 1, 2, 2, 1, 2),
    (3, 2, 2, 1, 1, 2),
    (3, 2, 2, 2, 1, 1),
    (2, 1, 2, 1, 2, 3),
    (2, 1, 2, 3, 2, 1),
    (2, 3, 2, 1, 2, 1),
    (1, 1, 1, 3, 2, 3),
    (1, 3, 1, 1, 2, 3),
    (1, 3, 1, 3, 2, 1),
    (1, 1, 2, 3, 1, 3),
    (1, 3, 2, 1, 1, 3),
    (1, 3, 2, 3, 1, 1),
    (2, 1, 1, 3, 1, 3),
    (2, 3, 1, 1, 1, 3),
    (2, 3, 1, 3, 1, 1),
    (1, 1, 2, 1, 3, 3),
    (1, 1, 2, 3, 3, 1),
    (1, 3, 2, 1, 3, 1),
    (1, 1, 3, 1, 2, 3),
    (1, 1, 3, 3, 2, 1),
    (1, 3, 3, 1, 2, 1),
    (3, 1, 3, 1, 2, 1),
    (2, 1, 1, 3, 3, 1),
    (2, 3, 1, 1, 3, 1),
    (2, 1, 3, 1, 1, 3),
    (2, 1, 3, 3, 1, 1),
    (2, 1, 3, 1, 3, 1),
    (3, 1, 1, 1, 2, 3),
    (3, 1, 1, 3, 2, 1),
    (3, 3, 1, 1, 2, 1),
    (3, 1, 2, 1, 1, 3),
    (3, 1, 2, 3, 1, 1),
    (3, 3, 2, 1, 1, 1),
    (3, 1, 4, 1, 1, 1),
    (2, 2, 1, 4, 1, 1),
    (4, 3, 1, 1, 1, 1),
    (1, 1, 1, 2, 2, 4),
    (1, 1, 1, 4, 2, 2),
    (1, 2, 1, 1, 2, 4),
    (1, 2, 1, 4, 2, 1),
    (1, 4, 1, 1, 2, 2),
    (1, 4, 1, 2, 2, 1),
    (1, 1, 2, 2, 1, 4),
    (1, 1, 2, 4, 1, 2),
    (1, 2, 2, 1, 1, 4),
    (1, 2, 2, 4, 1, 1),
    (1, 4, 2, 1, 1, 2),
    (1, 4, 2, 2, 1, 1),
    (2, 4, 1, 2, 1, 1),
    (2, 2, 1, 1, 1, 4),
    (4, 1, 3, 1, 1, 1),
    (2, 4, 1, 1, 1, 2),
    (1, 3, 4, 1, 1, 1),
    (1, 1, 1, 2, 4, 2),
    (1, 2, 1, 1, 4, 2),
    (1, 2, 1, 2, 4, 1),
    (1, 1, 4, 2, 1, 2),
    (1, 2, 4, 1, 1, 2),
    (1, 2, 4, 2, 1, 1),
    (4, 1, 1, 2, 1, 2),
    (4, 2, 1, 1, 1, 2),
    (4, 2, 1, 2, 1, 1),
    (2, 1, 2, 1, 4, 1),
    (2, 1, 4, 1, 2, 1),
    (4, 1, 2, 1, 2, 1),
    (1, 1, 1, 1, 4, 3),
    (1, 1, 1, 3, 4, 1),
    (1, 3, 1, 1, 4, 1),
    (1, 1, 4, 1, 1, 3),
    (1, 1, 4, 3, 1, 1),
    (4, 1, 1, 1, 1, 3),
    (4, 1, 1, 3, 1, 1),
    (1, 1, 3, 1, 4, 1),
    (1, 1, 4, 1, 3, 1),
    (3, 1, 1, 1, 4, 1),
    (4, 1, 1, 1, 3, 1),
    (2, 1, 1, 4, 1, 2),
    (2, 1, 1, 2, 1, 4),
    (2, 1, 1, 2, 3, 2),
    (2, 3, 3, 1, 1, 1, 2),  # STOP pattern (7 elements)
]


def encode_code128b(text):
    """Encode text using Code 128B and return list of values"""
    values = [104]  # START_B
    for char in text:
        if char in CODE128B_CHARS:
            values.append(CODE128B_CHARS.index(char))
        else:
            values.append(0)  # Space for unsupported chars

    # Calculate checksum (modulo 103)
    checksum = values[0]
    for i, val in enumerate(values[1:], 1):
        checksum += i * val
    checksum = checksum % 103
    values.append(checksum)
    values.append(106)  # STOP
    return values


def values_to_bars(values):
    """Convert encoded values to bar pattern (list of bar widths)"""
    bars = []
    for val in values:
        pattern = CODE128_PATTERNS[val]
        bars.extend(pattern)
    return bars


# Data - encode sample shipping label text
content = "SHIP-2024-ABC123"
encoded_values = encode_code128b(content)
bar_pattern = values_to_bars(encoded_values)

# Calculate total width of barcode
unit_width = 1
total_barcode_width = sum(bar_pattern) * unit_width
quiet_zone = 10  # Quiet zone modules on each side

# Create bar heights - all bars at 100 (full height), spaces at 0
bar_heights = []
for i, width in enumerate(bar_pattern):
    is_bar = i % 2 == 0  # Even indices are bars (black)
    for _ in range(width):
        bar_heights.append(100 if is_bar else 0)

# Add quiet zones (white space)
bar_heights = [0] * quiet_zone + bar_heights + [0] * quiet_zone

# Custom style for barcode visualization
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#000000",
    foreground_strong="#000000",
    foreground_subtle="#333333",
    colors=("#000000",),  # Black bars
    title_font_size=56,
    label_font_size=48,
    major_label_font_size=40,
    legend_font_size=0,
    value_font_size=0,
    tooltip_font_size=0,
)

# Create vertical bar chart for barcode
chart = pygal.Bar(
    width=4800,
    height=2700,
    style=custom_style,
    show_legend=False,
    show_x_labels=False,
    show_y_labels=False,
    show_x_guides=False,
    show_y_guides=False,
    spacing=0,
    margin_top=300,
    margin_bottom=500,
    margin_left=600,
    margin_right=600,
    title="barcode-code128 · pygal · pyplots.ai",
    print_values=False,
    range=(0, 100),
)

# Add barcode pattern as single series
chart.add("", bar_heights)

# Add human-readable text as x_title (below the barcode)
chart.x_title = content

# Save outputs
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
