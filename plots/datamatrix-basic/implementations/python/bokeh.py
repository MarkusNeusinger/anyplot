""" pyplots.ai
datamatrix-basic: Basic Data Matrix 2D Barcode
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-16
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import ColumnDataSource, Title
from bokeh.plotting import figure


# Data Matrix encoding helper functions
# Implements basic ASCII encoding for Data Matrix ECC 200


def encode_ascii(text):
    """Encode text using ASCII encoding scheme."""
    codewords = []
    i = 0
    while i < len(text):
        c = ord(text[i])
        if i + 1 < len(text) and text[i].isdigit() and text[i + 1].isdigit():
            # Encode digit pairs (values 130-229)
            pair = int(text[i : i + 2])
            codewords.append(130 + pair)
            i += 2
        elif 0 <= c <= 127:
            # ASCII values 0-127 encoded as value + 1
            codewords.append(c + 1)
            i += 1
        else:
            # Extended ASCII (128-255) uses Upper Shift
            codewords.append(235)  # Upper Shift
            codewords.append(c - 127)
            i += 1
    return codewords


def get_symbol_size(data_len):
    """Get appropriate symbol size for data length."""
    # Data Matrix ECC 200 symbol sizes (data capacity, rows, cols, data regions)
    sizes = [
        (3, 10, 10),
        (5, 12, 12),
        (8, 14, 14),
        (12, 16, 16),
        (18, 18, 18),
        (22, 20, 20),
        (30, 22, 22),
        (36, 24, 24),
        (44, 26, 26),
    ]
    for capacity, rows, cols in sizes:
        if data_len <= capacity:
            return rows, cols, capacity
    return 26, 26, 44  # Maximum for this implementation


def reed_solomon_encode(data, nsym, gf_exp=8, prim=0x12D):
    """Simple Reed-Solomon encoder for error correction."""
    # GF(256) with primitive polynomial x^8 + x^5 + x^3 + x^2 + 1
    gf_size = 2**gf_exp

    # Build log and exp tables
    exp_table = [0] * gf_size * 2
    log_table = [0] * gf_size
    x = 1
    for i in range(gf_size - 1):
        exp_table[i] = x
        log_table[x] = i
        x <<= 1
        if x >= gf_size:
            x ^= prim
    for i in range(gf_size - 1, gf_size * 2):
        exp_table[i] = exp_table[i - (gf_size - 1)]

    def gf_mult(a, b):
        if a == 0 or b == 0:
            return 0
        return exp_table[(log_table[a] + log_table[b]) % (gf_size - 1)]

    # Build generator polynomial
    gen = [1]
    for i in range(nsym):
        new_gen = [0] * (len(gen) + 1)
        for j, g in enumerate(gen):
            new_gen[j] ^= g
            new_gen[j + 1] ^= gf_mult(g, exp_table[i])
        gen = new_gen

    # Encode
    remainder = data + [0] * nsym
    for i in range(len(data)):
        coef = remainder[i]
        if coef != 0:
            for j in range(1, len(gen)):
                remainder[i + j] ^= gf_mult(gen[j], coef)

    return remainder[len(data) :]


def create_datamatrix(text):
    """Create a Data Matrix barcode matrix."""
    # Encode the data
    codewords = encode_ascii(text)
    rows, cols, capacity = get_symbol_size(len(codewords))

    # Pad with 129 (pad codeword) if needed
    while len(codewords) < capacity:
        pos = len(codewords) + 1
        pad = 129 + ((149 * pos) % 253) + 1
        if pad > 254:
            pad -= 254
        codewords.append(pad)

    # Add error correction
    # ECC codewords count based on symbol size
    ecc_counts = {
        (10, 10): 5,
        (12, 12): 7,
        (14, 14): 10,
        (16, 16): 12,
        (18, 18): 14,
        (20, 20): 18,
        (22, 22): 20,
        (24, 24): 24,
        (26, 26): 28,
    }
    n_ecc = ecc_counts.get((rows, cols), 10)
    ecc = reed_solomon_encode(codewords, n_ecc)
    all_codewords = codewords + ecc

    # Create the matrix with finder and timing patterns
    matrix = np.ones((rows, cols), dtype=int)  # Start with white

    # L-shaped finder pattern (solid black on left and bottom)
    matrix[:, 0] = 0  # Left column solid black
    matrix[-1, :] = 0  # Bottom row solid black

    # Alternating timing pattern (top and right edges)
    for i in range(cols):
        matrix[0, i] = i % 2  # Top edge alternating
    for i in range(rows):
        matrix[i, -1] = (i + 1) % 2  # Right edge alternating

    # Place data in the inner region using simplified row-by-row placement
    # Simplified placement: fill inner region row by row
    bit_idx = 0
    total_bits = len(all_codewords) * 8

    for r in range(1, rows - 1):
        for c in range(1, cols - 1):
            if bit_idx < total_bits:
                cw_idx = bit_idx // 8
                bit_pos = 7 - (bit_idx % 8)
                bit = (all_codewords[cw_idx] >> bit_pos) & 1
                matrix[r, c] = 1 - bit  # 1 = white, 0 = black
                bit_idx += 1

    return matrix


# Generate Data Matrix for sample content
content = "SERIAL:12345678"
matrix = create_datamatrix(content)
rows, cols = matrix.shape

# Add quiet zone (1 module width border)
quiet_zone = 2
total_width = cols + 2 * quiet_zone
total_height = rows + 2 * quiet_zone

# Find black cell positions (value = 0)
black_rows, black_cols = np.where(matrix == 0)

# Add offset for quiet zone
offset_cols = black_cols + quiet_zone
offset_rows = black_rows + quiet_zone

# Flip row coordinates for Bokeh (origin at bottom-left)
flipped_rows = total_height - 1 - offset_rows

# Create ColumnDataSource
source = ColumnDataSource(
    data={"x": offset_cols + 0.5, "y": flipped_rows + 0.5}  # Center squares on grid
)

# Create figure - square aspect for Data Matrix
p = figure(
    width=3600,
    height=3600,
    title="datamatrix-basic · bokeh · pyplots.ai",
    x_range=(0, total_width),
    y_range=(0, total_height),
    tools="",
    toolbar_location=None,
)

# Draw black squares using rect glyph
cell_size = 0.95  # Slightly smaller than 1 to show grid structure
p.rect(x="x", y="y", width=cell_size, height=cell_size, source=source, fill_color="#000000", line_color=None)

# Style the plot
p.title.text_font_size = "36pt"
p.title.align = "center"

# Set background to white (quiet zone)
p.background_fill_color = "white"
p.border_fill_color = "white"

# Hide axes for clean barcode appearance
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False
p.outline_line_color = None

# Add subtitle showing encoded content
subtitle = Title(text=f'Content: "{content}"', text_font_size="24pt", align="center")
p.add_layout(subtitle, "below")

# Save as PNG
export_png(p, filename="plot.png")
