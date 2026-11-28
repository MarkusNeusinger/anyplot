""" anyplot.ai
datamatrix-basic: Basic Data Matrix 2D Barcode
Library: pygal 3.1.3 | Python 3.14.10
Quality: 80/100 | Updated: 2026-11-28
"""

import os
import sys

import numpy as np


# This file is named pygal.py, which shadows the installed package.
# Temporarily remove the script directory from sys.path so the real package loads.
_script_dir = os.path.dirname(os.path.abspath(__file__))
_removed = [p for p in list(sys.path) if p in ("", ".") or os.path.abspath(p) == _script_dir]
for _p in _removed:
    sys.path.remove(_p)

try:
    from pygal.graph.graph import Graph
    from pygal.style import Style
finally:
    for _p in _removed:
        sys.path.insert(0, _p)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
TILE_BG = "#FFFDF6"  # light tile behind the symbol in both themes, for scan contrast

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
QUIET_ZONE = 2  # modules of blank margin around the symbol (the spec asks for at least 1)
# ECC 200 square symbols with one data region: (rows, cols, data codewords, error-correction codewords)
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
# Galois field GF(256) log tables, primitive polynomial 0x12D (ISO/IEC 16022)
GF_EXP = [0] * 512
GF_LOG = [0] * 256
_x = 1
for _i in range(255):
    GF_EXP[_i] = _x
    GF_LOG[_x] = _i
    _x <<= 1
    if _x & 0x100:
        _x ^= 0x12D
for _i in range(255, 512):
    GF_EXP[_i] = GF_EXP[_i - 255]

# Data: replace this block with your own text, for example CONTENT = "SERIAL:12345678"
# Pharmaceutical serialization: the NDC (National Drug Code) of a drug package
CONTENT = "NDC:0069-0069-20"

# Plot
# ASCII encoding: each character becomes its code point + 1
codewords = [ord(ch) + 1 for ch in CONTENT if ord(ch) < 128]

# Smallest symbol that holds the data
rows, cols, data_cap, ec_count = next((s for s in SYMBOL_SIZES if len(codewords) <= s[2]), SYMBOL_SIZES[-1])

# Pad to capacity: one 129, then the randomised 253-state padding (position is 1-based)
if len(codewords) < data_cap:
    codewords.append(129)
while len(codewords) < data_cap:
    pad = 129 + (149 * (len(codewords) + 1)) % 253 + 1
    codewords.append(pad - 254 if pad > 254 else pad)
codewords = codewords[:data_cap]

# Reed-Solomon check codewords: generator polynomial with roots alpha^1 .. alpha^n
generator = [1]
for i in range(1, ec_count + 1):
    nxt = [0] * (len(generator) + 1)
    for j, g in enumerate(generator):
        nxt[j] ^= g
        if g:
            nxt[j + 1] ^= GF_EXP[GF_LOG[g] + i]
    generator = nxt
remainder = [0] * ec_count
for cw in codewords:
    lead = cw ^ remainder[0]
    remainder = remainder[1:] + [0]
    if lead:
        for j in range(ec_count):
            if generator[j + 1]:
                remainder[j] ^= GF_EXP[GF_LOG[generator[j + 1]] + GF_LOG[lead]]
stream = iter(codewords + remainder)

# Module placement of ISO/IEC 16022 (Annex F) inside the data region, which is 2 modules smaller each way
nrow, ncol = rows - 2, cols - 2
bits = np.full((nrow, ncol), -1)
UTAH = [(-2, -2), (-2, -1), (-1, -2), (-1, -1), (-1, 0), (0, -2), (0, -1), (0, 0)]
CORNERS = [
    [
        (nrow - 1, 0),
        (nrow - 1, 1),
        (nrow - 1, 2),
        (0, ncol - 2),
        (0, ncol - 1),
        (1, ncol - 1),
        (2, ncol - 1),
        (3, ncol - 1),
    ],
    [
        (nrow - 3, 0),
        (nrow - 2, 0),
        (nrow - 1, 0),
        (0, ncol - 4),
        (0, ncol - 3),
        (0, ncol - 2),
        (0, ncol - 1),
        (1, ncol - 1),
    ],
    [
        (nrow - 3, 0),
        (nrow - 2, 0),
        (nrow - 1, 0),
        (0, ncol - 2),
        (0, ncol - 1),
        (1, ncol - 1),
        (2, ncol - 1),
        (3, ncol - 1),
    ],
    [
        (nrow - 1, 0),
        (nrow - 1, ncol - 1),
        (0, ncol - 3),
        (0, ncol - 2),
        (0, ncol - 1),
        (1, ncol - 3),
        (1, ncol - 2),
        (1, ncol - 1),
    ],
]


def place(cells):
    """Write the next codeword, most significant bit first, into 8 modules (wrapping past the edges)."""
    codeword = next(stream, 0)
    for bit, (r, c) in enumerate(cells):
        if r < 0:
            r, c = r + nrow, c + 4 - (nrow + 4) % 8
        if c < 0:
            r, c = r + 4 - (ncol + 4) % 8, c + ncol
        bits[r, c] = codeword >> (7 - bit) & 1


row, col = 4, 0
while True:
    if row == nrow and col == 0:
        place(CORNERS[0])
    if row == nrow - 2 and col == 0 and ncol % 4:
        place(CORNERS[1])
    if row == nrow - 2 and col == 0 and ncol % 8 == 4:
        place(CORNERS[2])
    if row == nrow + 4 and col == 2 and ncol % 8 == 0:
        place(CORNERS[3])
    while True:  # diagonal sweep up and to the right
        if row < nrow and col >= 0 and bits[row, col] < 0:
            place([(row + dr, col + dc) for dr, dc in UTAH])
        row, col = row - 2, col + 2
        if row < 0 or col >= ncol:
            break
    row, col = row + 1, col + 3
    while True:  # diagonal sweep down and to the left
        if row >= 0 and col < ncol and bits[row, col] < 0:
            place([(row + dr, col + dc) for dr, dc in UTAH])
        row, col = row + 2, col - 2
        if row >= nrow or col < 0:
            break
    row, col = row + 3, col + 1
    if row >= nrow and col >= ncol:
        break
if bits[nrow - 1, ncol - 1] < 0:  # fixed pattern when the bit count leaves the corner unused
    bits[nrow - 1, ncol - 1] = bits[nrow - 2, ncol - 2] = 1

# Full symbol: L-shaped finder (left column, bottom row), clock track (top row, right column), data inside
modules = np.zeros((rows, cols), dtype=bool)
modules[1:-1, 1:-1] = bits == 1
modules[0, :] = np.arange(cols) % 2 == 0
modules[:, -1] = (rows - 1 - np.arange(rows)) % 2 == 0
modules[:, 0] = True
modules[-1, :] = True

# Captions below the symbol, derived from the encoded symbol
caption = f"Encoded: {CONTENT}"
caption_detail = (
    f"Matrix: {rows} × {cols} | ECC 200 | {ec_count} of {data_cap + ec_count} codewords for error correction"
)


class DataMatrixChart(Graph):
    """pygal draws no barcodes: this Graph subclass paints the symbol as SVG in the plot area."""

    def _plot(self):
        total = max(rows, cols) + 2 * QUIET_ZONE
        # Whole-pixel module size and offsets, so adjacent modules meet without seams
        cell = int((min(self.view.width, self.view.height) - 2 * 160) / total)
        side = total * cell
        x0 = round(self.view.x(0) + (self.view.width - side) / 2)
        y0 = round(self.view.y(total) + (self.view.height - side) / 2)

        group = self.svg.node(self.nodes["plot"], class_="datamatrix")
        group.set("shape-rendering", "crispEdges")
        tile = self.svg.node(group, "rect", x=x0, y=y0, width=side, height=side)
        tile.set("fill", TILE_BG)
        tile.set("stroke", INK_SOFT)
        tile.set("stroke-width", "2")

        # All dark modules in one path, so they merge into solid edges
        r_idx, c_idx = np.nonzero(modules)
        outline = "".join(
            f"M{x0 + (c + QUIET_ZONE) * cell} {y0 + (r + QUIET_ZONE) * cell}h{cell}v{cell}h-{cell}z"
            for r, c in zip(r_idx, c_idx, strict=True)
        )
        symbol = self.svg.node(group, "path", d=outline)
        symbol.set("fill", "#1A1A17")

        label_x = x0 + side / 2
        label_y = y0 + side + 70
        title_node = self.svg.node(group, "text", x=label_x, y=label_y)
        title_node.set("text-anchor", "middle")
        title_node.set("fill", INK)
        title_node.set("style", "font-size:44px;font-weight:bold;font-family:sans-serif")
        title_node.text = caption
        detail_node = self.svg.node(group, "text", x=label_x, y=label_y + 58)
        detail_node.set("text-anchor", "middle")
        detail_node.set("fill", INK_SOFT)
        detail_node.set("style", "font-size:36px;font-family:sans-serif")
        detail_node.text = caption_detail

    def _compute(self):
        total = max(rows, cols) + 2 * QUIET_ZONE
        self._box.xmin = 0
        self._box.xmax = total
        self._box.ymin = 0
        self._box.ymax = total


# Style
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_SOFT,
    guide_stroke_color=INK_SOFT,
    major_guide_stroke_color=INK_SOFT,
    colors=tuple(IMPRINT_PALETTE),
    title_font_size=66,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
)

chart = DataMatrixChart(
    width=2400,
    height=2400,
    style=custom_style,
    title="datamatrix-basic · python · pygal · anyplot.ai",
    show_legend=False,
    margin=100,
    margin_top=180,
    margin_bottom=180,
    show_x_labels=False,
    show_y_labels=False,
)

# Required: pygal's Graph._draw() only calls _plot() when series data is present
chart.add("", [0])

# Save
chart.render_to_png(f"plot-{THEME}.png")

svg_content = chart.render(is_unicode=True)
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>datamatrix-basic - python - pygal - anyplot.ai</title>
    <style>
        body {{
            margin: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            background: {PAGE_BG};
        }}
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

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)
