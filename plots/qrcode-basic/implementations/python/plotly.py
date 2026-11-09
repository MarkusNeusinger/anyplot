"""anyplot.ai
qrcode-basic: Basic QR Code Generator
Library: plotly 6.8.0 | Python 3.13.14
Quality: pending | Updated: 2026-06-24
"""

import os
import sys


# Remove this script's directory from sys.path so `import plotly` finds the
# installed package rather than this file itself (plotly.py would shadow it).
_here = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _here]

import numpy as np
import plotly.graph_objects as go


# Theme-adaptive chrome tokens (Imprint palette)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette position 1 — brand green accent for chrome
ACCENT = "#009E73"

# QR code modules: dark on a white tile in both themes — scanners expect dark-on-light,
# so the code itself never inverts with the theme; only the surrounding chrome does
MODULE_DARK = "#1A1A17"
MODULE_LIGHT = "#FFFDF6"

# Constants — ISO/IEC 18004 byte-mode tables for versions 1–4. The runner has no
# QR package (qrcode, segno), so the standard encoding is written out here.
QUIET_ZONE = 4  # modules of blank border the standard requires
EC_SHARE = {"L": "7%", "M": "15%", "Q": "25%", "H": "30%"}
EC_FORMAT_BITS = {"L": 1, "M": 0, "Q": 3, "H": 2}
# version → total codewords, and per level (EC codewords per block, number of blocks)
VERSION_TABLE = {
    1: (26, {"L": (7, 1), "M": (10, 1), "Q": (13, 1), "H": (17, 1)}),
    2: (44, {"L": (10, 1), "M": (16, 1), "Q": (22, 1), "H": (28, 1)}),
    3: (70, {"L": (15, 1), "M": (26, 1), "Q": (18, 2), "H": (22, 2)}),
    4: (100, {"L": (20, 1), "M": (18, 2), "Q": (26, 2), "H": (16, 4)}),
}
MASKS = [
    lambda r, c: (r + c) % 2 == 0,
    lambda r, c: r % 2 == 0,
    lambda r, c: c % 3 == 0,
    lambda r, c: (r + c) % 3 == 0,
    lambda r, c: (r // 2 + c // 3) % 2 == 0,
    lambda r, c: (r * c) % 2 + (r * c) % 3 == 0,
    lambda r, c: ((r * c) % 2 + (r * c) % 3) % 2 == 0,
    lambda r, c: ((r + c) % 2 + (r * c) % 3) % 2 == 0,
]

# Data: the text to encode and the error correction level (L, M, Q or H)
CONTENT = "https://pyplots.ai"
ERROR_CORRECTION = "M"

# Plot: encode CONTENT into the module matrix, then draw it
payload = CONTENT.encode("utf-8")
version = next(
    v
    for v, (total, levels) in VERSION_TABLE.items()
    if total - levels[ERROR_CORRECTION][0] * levels[ERROR_CORRECTION][1] >= len(payload) + 2
)
total_codewords, levels = VERSION_TABLE[version]
ec_per_block, n_blocks = levels[ERROR_CORRECTION]
n_data = total_codewords - ec_per_block * n_blocks

# Bit stream: byte mode indicator, 8-bit length, payload, terminator, pad bytes
bits = "0100" + f"{len(payload):08b}" + "".join(f"{b:08b}" for b in payload)
bits += "0" * min(4, n_data * 8 - len(bits))
bits += "0" * (-len(bits) % 8)
data = [int(bits[i : i + 8], 2) for i in range(0, len(bits), 8)]
data += [0xEC, 0x11] * ((n_data - len(data)) // 2) + [0xEC] * ((n_data - len(data)) % 2)

# Reed–Solomon error correction over GF(256), polynomial 0x11D
gf_exp = [1] * 512
for i in range(1, 255):
    gf_exp[i] = (gf_exp[i - 1] << 1) ^ (0x11D if gf_exp[i - 1] & 0x80 else 0)
gf_exp[255:] = gf_exp[:257]
gf_log = {gf_exp[i]: i for i in range(255)}
generator = [1]
for i in range(ec_per_block):
    generator = [
        (generator[j] if j < len(generator) else 0)
        ^ (gf_exp[gf_log[generator[j - 1]] + i] if 0 < j <= len(generator) and generator[j - 1] else 0)
        for j in range(len(generator) + 1)
    ]
block_len = n_data // n_blocks
data_blocks = [data[k * block_len : (k + 1) * block_len] for k in range(n_blocks)]
ec_blocks = []
for block in data_blocks:
    remainder = list(block) + [0] * ec_per_block
    for i in range(len(block)):
        factor = remainder[i]
        if factor:
            for j, g in enumerate(generator):
                if g:
                    remainder[i + j] ^= gf_exp[gf_log[g] + gf_log[factor]]
    ec_blocks.append(remainder[len(block) :])
codewords = [b[i] for i in range(block_len) for b in data_blocks]
codewords += [b[i] for i in range(ec_per_block) for b in ec_blocks]

# Function patterns: finders with separators, timing lines, alignment, dark module
size = 4 * version + 17
modules = np.zeros((size, size), dtype=bool)
reserved = np.zeros((size, size), dtype=bool)
finder = np.ones((7, 7), dtype=bool)
finder[1:6, 1:6] = False
finder[2:5, 2:5] = True
for r0, c0 in [(0, 0), (0, size - 7), (size - 7, 0)]:
    modules[r0 : r0 + 7, c0 : c0 + 7] = finder
    reserved[max(r0 - 1, 0) : r0 + 8, max(c0 - 1, 0) : c0 + 8] = True
modules[6, 8 : size - 8] = np.arange(8, size - 8) % 2 == 0
modules[8 : size - 8, 6] = np.arange(8, size - 8) % 2 == 0
reserved[6, :] = reserved[:, 6] = True
if version > 1:
    centre = size - 7
    align = np.ones((5, 5), dtype=bool)
    align[1:4, 1:4] = False
    align[2, 2] = True
    modules[centre - 2 : centre + 3, centre - 2 : centre + 3] = align
    reserved[centre - 2 : centre + 3, centre - 2 : centre + 3] = True
reserved[8, :9] = reserved[:9, 8] = reserved[8, size - 8 :] = reserved[size - 8 :, 8] = True
modules[size - 8, 8] = True

# Codeword placement in the two-column zigzag, bottom-right to top-left
stream = "".join(f"{c:08b}" for c in codewords)
position = 0
for right in range(size - 1, 0, -2):
    right = right - 1 if right <= 6 else right
    upward = ((right + 1) & 2) == 0
    for step in range(size):
        r = size - 1 - step if upward else step
        for c in (right, right - 1):
            if not reserved[r, c]:
                modules[r, c] = position < len(stream) and stream[position] == "1"
                position += 1

# Mask choice by the standard's four penalty rules, format information written in
rows_idx, cols_idx = np.indices((size, size))
finder_like = [np.array([1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0]), np.array([0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 1])]
best_penalty, qr_core = None, None
for mask_id, mask_rule in enumerate(MASKS):
    candidate = modules ^ (mask_rule(rows_idx, cols_idx) & ~reserved)
    format_data = (EC_FORMAT_BITS[ERROR_CORRECTION] << 3) | mask_id
    remainder = format_data
    for _ in range(10):
        remainder = (remainder << 1) ^ ((remainder >> 9) * 0x537)
    format_bits = ((format_data << 10) | remainder) ^ 0x5412
    bit = [(format_bits >> i) & 1 == 1 for i in range(15)]
    for i in range(6):
        candidate[i, 8] = bit[i]
    candidate[7, 8], candidate[8, 8], candidate[8, 7] = bit[6], bit[7], bit[8]
    for i in range(9, 15):
        candidate[8, 14 - i] = bit[i]
    for i in range(8):
        candidate[8, size - 1 - i] = bit[i]
    for i in range(8, 15):
        candidate[size - 15 + i, 8] = bit[i]

    penalty = 0
    for line in list(candidate) + list(candidate.T):
        run_values = np.diff(np.flatnonzero(np.diff(np.r_[-1, line.astype(int), -1]) != 0))
        penalty += sum(run - 2 for run in run_values if run >= 5)
        as_int = line.astype(int)
        for pattern in finder_like:
            windows = np.lib.stride_tricks.sliding_window_view(as_int, len(pattern))
            penalty += 40 * int((windows == pattern).all(axis=1).sum())
    blocks_2x2 = candidate[:-1, :-1] + 0 + candidate[1:, :-1] + candidate[:-1, 1:] + candidate[1:, 1:]
    penalty += 3 * int(((blocks_2x2 == 0) | (blocks_2x2 == 4)).sum())
    penalty += 10 * (abs(candidate.mean() * 100 - 50) // 5)
    if best_penalty is None or penalty < best_penalty:
        best_penalty, qr_core = penalty, candidate

qr_matrix = np.pad(qr_core, QUIET_ZONE).astype(int)
n_modules = qr_matrix.shape[0]
frame_pad = n_modules * 0.01  # gap between the white tile and the accent frame

fig = go.Figure(
    data=go.Heatmap(
        z=qr_matrix,
        colorscale=[[0, MODULE_LIGHT], [1, MODULE_DARK]],
        showscale=False,
        hovertemplate="Module: (%{x}, %{y})<extra></extra>",
    )
)

fig.update_layout(
    autosize=False,
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    title={
        "text": "qrcode-basic · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK, "family": "Arial Black, sans-serif"},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.98,
    },
    xaxis={
        "showticklabels": False,
        "showgrid": False,
        "zeroline": False,
        "scaleanchor": "y",
        "scaleratio": 1,
        "constrain": "domain",
        "showline": False,
        "range": [-0.5 - frame_pad * 2, n_modules - 0.5 + frame_pad * 2],
    },
    yaxis={
        "showticklabels": False,
        "showgrid": False,
        "zeroline": False,
        "constrain": "domain",
        "showline": False,
        "range": [n_modules - 0.5 + frame_pad * 2, -0.5 - frame_pad * 2],
    },
    margin={"l": 40, "r": 40, "t": 80, "b": 150},
)

# Accent border framing the QR code area
fig.add_shape(
    type="rect",
    xref="x",
    yref="y",
    x0=-0.5 - frame_pad,
    y0=-0.5 - frame_pad,
    x1=n_modules - 0.5 + frame_pad,
    y1=n_modules - 0.5 + frame_pad,
    line={"color": ACCENT, "width": 1.5},
    fillcolor="rgba(0,0,0,0)",
    opacity=0.7,
)

# Dotted divider between QR code and annotation area
fig.add_shape(
    type="line",
    xref="paper",
    yref="paper",
    x0=0.25,
    y0=-0.06,
    x1=0.75,
    y1=-0.06,
    line={"color": ACCENT, "width": 1.5, "dash": "dot"},
    opacity=0.5,
)

# Encoded URL — prominent, just below the divider
fig.add_annotation(
    text=f"<b>{CONTENT}</b>",
    xref="paper",
    yref="paper",
    x=0.5,
    y=-0.14,
    showarrow=False,
    font={"size": 12, "color": ACCENT, "family": "Arial, sans-serif"},
    xanchor="center",
    yanchor="top",
)

# QR code metadata — version, error correction, module count
fig.add_annotation(
    text=(
        f"Error Correction: {ERROR_CORRECTION} ({EC_SHARE[ERROR_CORRECTION]})"
        f"  ·  Version {version}  ·  {size}×{size} modules"
    ),
    xref="paper",
    yref="paper",
    x=0.5,
    y=-0.27,
    showarrow=False,
    font={"size": 12, "color": INK_SOFT, "family": "Arial, sans-serif"},
    xanchor="center",
    yanchor="top",
)

# Save — square canvas: 600×600 logical → 2400×2400 px at scale=4
fig.write_image(f"plot-{THEME}.png", width=600, height=600, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
