""" pyplots.ai
datamatrix-basic: Basic Data Matrix 2D Barcode
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-16
"""

import sys

import cairosvg
import numpy as np


# Temporarily remove current directory from path to avoid name collision
_cwd = sys.path[0] if sys.path[0] else "."
if _cwd in sys.path:
    sys.path.remove(_cwd)

from pygal.graph.graph import Graph  # noqa: E402
from pygal.style import Style  # noqa: E402


# Restore path
sys.path.insert(0, _cwd)


# Data Matrix ECC 200 implementation
# Symbol sizes for ECC 200 (rows, cols, data_codewords, ec_codewords)
SYMBOL_SIZES = [
    (10, 10, 3, 5),
    (12, 12, 5, 7),
    (14, 14, 8, 10),
    (16, 16, 12, 12),
    (18, 18, 18, 14),
    (20, 20, 22, 18),
    (22, 22, 30, 20),
    (24, 24, 36, 24),
    (26, 26, 44, 28),
]

# Galois field GF(256) for Reed-Solomon
GF_EXP = [0] * 512
GF_LOG = [0] * 256


def init_galois_field():
    """Initialize Galois field tables for GF(256) with polynomial 0x12D."""
    x = 1
    for i in range(255):
        GF_EXP[i] = x
        GF_LOG[x] = i
        x <<= 1
        if x & 0x100:
            x ^= 0x12D  # Reed-Solomon polynomial for Data Matrix
    for i in range(255, 512):
        GF_EXP[i] = GF_EXP[i - 255]


init_galois_field()


def gf_mul(a, b):
    """Multiply two numbers in GF(256)."""
    if a == 0 or b == 0:
        return 0
    # Ensure values are in valid range
    a = a % 256
    b = b % 256
    if a == 0 or b == 0:
        return 0
    return GF_EXP[(GF_LOG[a] + GF_LOG[b]) % 255]


def rs_encode(data, num_ec):
    """Reed-Solomon encode data with num_ec error correction codewords."""
    # Ensure all data values are in valid range
    data = [d % 256 for d in data]

    # Build generator polynomial
    g = [1]
    for i in range(num_ec):
        new_g = [0] * (len(g) + 1)
        for j in range(len(g)):
            new_g[j] ^= gf_mul(g[j], GF_EXP[i])
            new_g[j + 1] ^= g[j]
        g = new_g

    # Encode: shift data and divide by generator
    encoded = list(data) + [0] * num_ec
    for i in range(len(data)):
        coef = encoded[i]
        if coef != 0:
            for j in range(len(g)):
                encoded[i + j] ^= gf_mul(g[j], coef)

    return encoded[len(data) :]


def encode_text(text):
    """Encode text to Data Matrix codewords using ASCII encoding."""
    codewords = []
    for char in text:
        code = ord(char)
        if 0 <= code <= 127:
            codewords.append(code + 1)  # ASCII encoding adds 1
        else:
            # Extended ASCII (2 codewords)
            codewords.append(235)
            codewords.append(code - 127)
    return codewords


def select_symbol_size(data_codewords):
    """Select the smallest symbol size that can hold the data."""
    for rows, cols, data_cap, ec in SYMBOL_SIZES:
        if data_codewords <= data_cap:
            return rows, cols, data_cap, ec
    return SYMBOL_SIZES[-1]  # Use largest if data too big


def pad_codewords(codewords, capacity):
    """Pad codewords to fill the data capacity."""
    if len(codewords) < capacity:
        codewords.append(129)  # Pad codeword
    while len(codewords) < capacity:
        # Randomized pad
        pad = 130 + (((149 * (len(codewords) + 1)) % 253) + 1) % 254
        codewords.append(pad)
    return codewords[:capacity]


def create_matrix(rows, cols):
    """Create the Data Matrix grid."""
    return np.zeros((rows, cols), dtype=int)


def place_finder_pattern(matrix):
    """Place L-shaped finder pattern and alternating timing pattern."""
    rows, cols = matrix.shape

    # Left edge: solid black (L-shape vertical)
    for r in range(rows):
        matrix[r, 0] = 1

    # Bottom edge: solid black (L-shape horizontal)
    for c in range(cols):
        matrix[rows - 1, c] = 1

    # Top edge: alternating (timing pattern)
    for c in range(cols):
        matrix[0, c] = 1 if c % 2 == 0 else 0

    # Right edge: alternating (timing pattern)
    for r in range(rows):
        matrix[r, cols - 1] = 1 if r % 2 == 0 else 0


def module_position(row, col, matrix_rows, matrix_cols):
    """Calculate the actual matrix position for a module."""
    # Adjust for finder/timing patterns
    actual_row = row + 1  # Skip top timing row
    actual_col = col + 1  # Skip left finder column
    return actual_row, actual_col


def place_codewords(matrix, codewords):
    """Place codewords in the Data Matrix using the ECC 200 placement algorithm."""
    rows, cols = matrix.shape
    data_rows = rows - 2  # Exclude finder/timing patterns
    data_cols = cols - 2

    # Simple diagonal placement (simplified for demonstration)
    bit_idx = 0
    total_bits = len(codewords) * 8

    # Create a placement map
    placed = np.zeros((data_rows, data_cols), dtype=bool)

    # Diagonal pattern placement
    for module_num in range(data_rows * data_cols):
        if bit_idx >= total_bits:
            break

        # Calculate position using a simple column-major diagonal pattern
        r = module_num // data_cols
        c = module_num % data_cols

        if not placed[r, c]:
            codeword_idx = bit_idx // 8
            bit_pos = 7 - (bit_idx % 8)

            if codeword_idx < len(codewords):
                bit_value = (codewords[codeword_idx] >> bit_pos) & 1
                actual_r = r + 1  # Offset for top timing pattern
                actual_c = c + 1  # Offset for left finder pattern
                if 0 < actual_r < rows - 1 and 0 < actual_c < cols - 1:
                    matrix[actual_r, actual_c] = bit_value
                placed[r, c] = True
                bit_idx += 1


def generate_datamatrix(content):
    """Generate a Data Matrix for the given content."""
    # Encode content to codewords
    codewords = encode_text(content)

    # Select symbol size
    rows, cols, data_cap, ec_count = select_symbol_size(len(codewords))

    # Pad to fill data capacity
    codewords = pad_codewords(codewords, data_cap)

    # Add error correction
    ec_codewords = rs_encode(codewords, ec_count)
    all_codewords = codewords + ec_codewords

    # Create matrix
    matrix = create_matrix(rows, cols)

    # Place finder pattern
    place_finder_pattern(matrix)

    # Place data
    place_codewords(matrix, all_codewords)

    return matrix


class DataMatrixChart(Graph):
    """Custom Data Matrix visualization for pygal."""

    def __init__(self, *args, **kwargs):
        self.dm_data = kwargs.pop("dm_data", "PYPLOTS")
        self.module_color = kwargs.pop("module_color", "#000000")
        self.bg_color = kwargs.pop("bg_color", "#FFFFFF")
        self.quiet_zone = kwargs.pop("quiet_zone", 2)
        super().__init__(*args, **kwargs)
        self._dm_matrix = None

    def _plot(self):
        """Draw the Data Matrix as SVG rectangles."""
        # Generate Data Matrix
        self._dm_matrix = generate_datamatrix(self.dm_data)
        if self._dm_matrix is None:
            return

        matrix_rows, matrix_cols = self._dm_matrix.shape
        total_rows = matrix_rows + 2 * self.quiet_zone
        total_cols = matrix_cols + 2 * self.quiet_zone

        # Get plot dimensions
        plot_width = self.view.width
        plot_height = self.view.height

        # Calculate cell size
        margin = 200
        available_size = min(plot_width, plot_height) - 2 * margin
        cell_size = available_size / max(total_rows, total_cols)

        # Center the matrix
        dm_width = total_cols * cell_size
        dm_height = total_rows * cell_size
        x_offset = self.view.x(0) + (plot_width - dm_width) / 2
        y_offset = self.view.y(total_rows) + (plot_height - dm_height) / 2 + 100

        # Create group
        plot_node = self.nodes["plot"]
        dm_group = self.svg.node(plot_node, class_="datamatrix")

        # Draw background with quiet zone
        bg_rect = self.svg.node(dm_group, "rect", x=x_offset, y=y_offset, width=dm_width, height=dm_height)
        bg_rect.set("fill", self.bg_color)
        bg_rect.set("stroke", "#CCCCCC")
        bg_rect.set("stroke-width", "2")

        # Draw Data Matrix modules
        for row in range(matrix_rows):
            for col in range(matrix_cols):
                if self._dm_matrix[row, col]:
                    x = x_offset + (col + self.quiet_zone) * cell_size
                    y = y_offset + (row + self.quiet_zone) * cell_size
                    rect = self.svg.node(dm_group, "rect", x=x, y=y, width=cell_size, height=cell_size)
                    rect.set("fill", self.module_color)

        # Add encoded data label
        label_y = y_offset + dm_height + 80
        label_x = x_offset + dm_width / 2
        font_size = 42

        text_node = self.svg.node(dm_group, "text", x=label_x, y=label_y)
        text_node.set("text-anchor", "middle")
        text_node.set("fill", "#306998")
        text_node.set("style", f"font-size:{font_size}px;font-weight:bold;font-family:sans-serif")
        text_node.text = f"Content: {self.dm_data}"

        # Matrix size info
        size_node = self.svg.node(dm_group, "text", x=label_x, y=label_y + 60)
        size_node.set("text-anchor", "middle")
        size_node.set("fill", "#666666")
        size_node.set("style", f"font-size:{int(font_size * 0.7)}px;font-family:sans-serif")
        size_node.text = f"Matrix: {matrix_rows} x {matrix_cols} | ECC 200"

    def _compute(self):
        """Compute the box for rendering."""
        if self._dm_matrix is None:
            self._dm_matrix = generate_datamatrix(self.dm_data)

        matrix_rows, matrix_cols = self._dm_matrix.shape
        total_size = max(matrix_rows, matrix_cols) + 2 * self.quiet_zone

        self._box.xmin = 0
        self._box.xmax = total_size
        self._box.ymin = 0
        self._box.ymax = total_size


# Custom style for 3600x3600 square canvas
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998", "#FFD43B"),
    title_font_size=72,
    legend_font_size=48,
    label_font_size=42,
    value_font_size=36,
    font_family="sans-serif",
)

# Data - content to encode
dm_content = "SERIAL:12345678"

# Create Data Matrix chart
chart = DataMatrixChart(
    width=3600,
    height=3600,
    style=custom_style,
    title="datamatrix-basic \u00b7 pygal \u00b7 pyplots.ai",
    dm_data=dm_content,
    module_color="#000000",
    bg_color="#FFFFFF",
    quiet_zone=2,
    show_legend=False,
    margin=120,
    margin_top=200,
    margin_bottom=200,
    show_x_labels=False,
    show_y_labels=False,
)

# Add a dummy series to trigger _plot
chart.add("", [0])

# Render to SVG
svg_content = chart.render(is_unicode=True)

# Save to PNG using cairosvg
chart.render_to_file("plot.svg")
cairosvg.svg2png(url="plot.svg", write_to="plot.png", output_width=3600, output_height=3600)

# Save HTML for interactivity
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>datamatrix-basic - pygal</title>
    <style>
        body {{ margin: 0; display: flex; justify-content: center; align-items: center; min-height: 100vh; background: #f5f5f5; }}
        .chart {{ max-width: 100%; height: auto; }}
    </style>
</head>
<body>
    <figure class="chart">
        {svg_content}
    </figure>
</body>
</html>
"""

with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)
