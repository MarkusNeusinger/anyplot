"""anyplot.ai
qrcode-basic: Basic QR Code Generator
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 83/100 | Updated: 2026-11-09
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_rect,
    element_text,
    geom_raster,
    gggrid,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_fill_identity,
    theme,
    theme_void,
)


LetsPlot.setup_html()

# Theme-adaptive chrome tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: no categorical series here, the code itself is black on white
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants: scanners need dark modules on a light field, so these stay the same in both themes
MODULE_DARK = "#1A1A17"
MODULE_LIGHT = "#FAF8F1"
QUIET_ZONE = 4  # modules of blank border the QR standard requires
# QR standard (ISO/IEC 18004) tables for versions 1-10: format bits, EC codewords per block, block count
ECC_FORMAT_BITS = {"L": 1, "M": 0, "Q": 3, "H": 2}
ECC_SHARE = {"L": "7%", "M": "15%", "Q": "25%", "H": "30%"}
EC_PER_BLOCK = {
    "L": [7, 10, 15, 20, 26, 18, 20, 24, 30, 18],
    "M": [10, 16, 26, 18, 24, 16, 18, 22, 22, 26],
    "Q": [13, 22, 18, 26, 18, 24, 18, 22, 20, 24],
    "H": [17, 28, 22, 16, 22, 28, 26, 26, 24, 28],
}
EC_BLOCKS = {
    "L": [1, 1, 1, 1, 1, 2, 2, 2, 2, 4],
    "M": [1, 1, 1, 2, 2, 4, 4, 4, 5, 5],
    "Q": [1, 1, 2, 2, 4, 4, 6, 6, 8, 8],
    "H": [1, 1, 2, 4, 4, 4, 5, 6, 8, 8],
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

# Data: replace these parameters with your own content and error correction level
content = "https://pyplots.ai"
error_correction = "M"

# Plot: encode the content as a byte-mode QR symbol, then draw one raster cell per module

# Galois field GF(256) with the QR polynomial 0x11D, for Reed-Solomon error correction
gf_exp = np.zeros(512, dtype=int)
gf_log = np.zeros(256, dtype=int)
value = 1
for power in range(255):
    gf_exp[power] = value
    gf_log[value] = power
    value <<= 1
    if value & 0x100:
        value ^= 0x11D
gf_exp[255:510] = gf_exp[:255]

# Smallest version (1-10) whose data capacity holds the content
payload = content.encode("utf-8")
for version in range(1, 11):
    side = 4 * version + 17
    align_count = version // 7 + 2 if version > 1 else 0
    raw_modules = (16 * version + 128) * version + 64
    raw_modules -= ((25 * align_count - 10) * align_count - 55) if version > 1 else 0
    raw_modules -= 36 if version >= 7 else 0
    raw_codewords = raw_modules // 8
    ec_len = EC_PER_BLOCK[error_correction][version - 1]
    n_blocks = EC_BLOCKS[error_correction][version - 1]
    data_capacity = raw_codewords - ec_len * n_blocks
    count_bits = 8 if version < 10 else 16
    if 4 + count_bits + 8 * len(payload) <= 8 * data_capacity:
        break
else:
    raise ValueError("content is too long for QR versions 1-10")

# Bit stream: byte-mode indicator, length, data, terminator, pad bytes
bits = "0100" + format(len(payload), f"0{count_bits}b") + "".join(format(b, "08b") for b in payload)
bits += "0" * min(4, 8 * data_capacity - len(bits))
bits += "0" * (-len(bits) % 8)
data_words = [int(bits[i : i + 8], 2) for i in range(0, len(bits), 8)]
data_words += [0xEC, 0x11] * ((data_capacity - len(data_words)) // 2 + 1)
data_words = data_words[:data_capacity]

# Reed-Solomon generator polynomial for ec_len error-correction codewords
generator = [1]
for i in range(ec_len):
    generator = [
        (generator[j] if j < len(generator) else 0)
        ^ (gf_exp[gf_log[generator[j - 1]] + i] if 0 < j <= len(generator) and generator[j - 1] else 0)
        for j in range(len(generator) + 1)
    ]

# Split into blocks, add each block's Reed-Solomon remainder, interleave
short_len = raw_codewords // n_blocks
n_short = n_blocks - raw_codewords % n_blocks
blocks, start = [], 0
for b in range(n_blocks):
    length = short_len - ec_len + (b >= n_short)
    chunk = data_words[start : start + length]
    start += length
    remainder = chunk + [0] * ec_len
    for i in range(length):
        lead = remainder[i]
        if lead:
            for j, coef in enumerate(generator):
                if coef:
                    remainder[i + j] ^= gf_exp[gf_log[coef] + gf_log[lead]]
    blocks.append((chunk + [None] if b < n_short else chunk) + remainder[length:])
codewords = [blk[i] for i in range(short_len + 1) for blk in blocks if blk[i] is not None]

# Function patterns: finders with separators, timing, alignment, reserved format/version areas
grid = np.zeros((side, side), dtype=bool)
reserved = np.zeros((side, side), dtype=bool)
grid[6, :] = grid[:, 6] = np.arange(side) % 2 == 0
reserved[6, :] = reserved[:, 6] = True
for r0, c0 in [(0, 0), (0, side - 7), (side - 7, 0)]:
    rr, cc = np.mgrid[-1:8, -1:8]
    dist = np.maximum(np.abs(rr - 3), np.abs(cc - 3))
    inside = (r0 + rr >= 0) & (r0 + rr < side) & (c0 + cc >= 0) & (c0 + cc < side)
    grid[r0 + rr[inside], c0 + cc[inside]] = (dist[inside] != 2) & (dist[inside] != 4)
    reserved[r0 + rr[inside], c0 + cc[inside]] = True
if version > 1:
    step = (version * 4 + align_count * 2 + 1) // (align_count * 2 - 2) * 2
    centers = [6] + [side - 7 - i * step for i in range(align_count - 1)][::-1]
    corners = {(centers[0], centers[0]), (centers[0], centers[-1]), (centers[-1], centers[0])}
    for ra in centers:
        for ca in centers:
            if (ra, ca) in corners:
                continue
            rr, cc = np.mgrid[-2:3, -2:3]
            grid[ra + rr, ca + cc] = np.maximum(np.abs(rr), np.abs(cc)) != 1
            reserved[ra + rr, ca + cc] = True
reserved[8, :9] = reserved[:9, 8] = reserved[8, side - 8 :] = reserved[side - 8 :, 8] = True
if version >= 7:
    reserved[:6, side - 11 : side - 8] = reserved[side - 11 : side - 8, :6] = True

# Data placement: two-column zigzag from the bottom right, skipping the vertical timing column
stream = [(word >> (7 - k)) & 1 for word in codewords for k in range(8)]
positions = []
right = side - 1
while right >= 1:
    if right == 6:
        right = 5
    upward = ((right + 1) & 2) == 0
    for vert in range(side):
        row = side - 1 - vert if upward else vert
        positions += [(row, right - j) for j in (0, 1) if not reserved[row, right - j]]
    right -= 2
for (row, col), bit in zip(positions, stream + [0] * (len(positions) - len(stream)), strict=True):
    grid[row, col] = bool(bit)


# Mask selection: apply each of the eight masks with its format bits, keep the lowest-penalty symbol
rr, cc = np.mgrid[0:side, 0:side]
first = [(i, 8) for i in range(6)] + [(7, 8), (8, 8), (8, 7)] + [(8, 14 - i) for i in range(9, 15)]
second = [(8, side - 1 - i) for i in range(8)] + [(side - 15 + i, 8) for i in range(8, 15)]
finder_like = [np.array([1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0]), np.array([0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 1])]
best_symbol, best_score = None, None
for mask_id, mask in enumerate(MASKS):
    candidate = grid ^ (mask(rr, cc) & ~reserved)
    fmt = ECC_FORMAT_BITS[error_correction] << 3 | mask_id
    rem = fmt
    for _ in range(10):
        rem = (rem << 1) ^ ((rem >> 9) * 0x537)
    fmt_bits = [((fmt << 10 | rem) ^ 0x5412) >> i & 1 for i in range(15)]
    for (r, c), bit in zip(first + second, fmt_bits * 2, strict=True):
        candidate[r, c] = bit
    candidate[side - 8, 8] = True
    if version >= 7:
        rem = version
        for _ in range(12):
            rem = (rem << 1) ^ ((rem >> 11) * 0x1F25)
        ver_bits = version << 12 | rem
        for i in range(18):
            a, b = side - 11 + i % 3, i // 3
            candidate[b, a] = candidate[a, b] = ver_bits >> i & 1

    # Penalty rules: long runs, finder-like sequences, 2×2 blocks, dark/light imbalance
    score = 0
    for lines in (candidate, candidate.T):
        for line in lines.astype(int):
            runs = np.diff(np.flatnonzero(np.diff(np.r_[-1, line, -1])))
            score += int(np.sum(runs[runs >= 5] - 2))
            windows = np.lib.stride_tricks.sliding_window_view(np.r_[np.zeros(4, int), line, np.zeros(4, int)], 11)
            score += 40 * sum(int(np.sum(np.all(windows == pattern, axis=1))) for pattern in finder_like)
    square = candidate[:-1, :-1] == candidate[1:, :-1]
    square &= (candidate[:-1, :-1] == candidate[:-1, 1:]) & (candidate[:-1, :-1] == candidate[1:, 1:])
    score += 3 * int(square.sum())
    total = candidate.size
    score += 10 * ((abs(int(candidate.sum()) * 20 - total * 10) + total - 1) // total - 1)
    if best_score is None or score < best_score:
        best_symbol, best_score = candidate, score

symbol = np.pad(best_symbol, QUIET_ZONE)

full = symbol.shape[0]
rr, cc = np.mgrid[0:full, 0:full]
modules = pd.DataFrame(
    {"x": cc.ravel(), "y": (full - 1 - rr).ravel(), "fill": np.where(symbol.ravel(), MODULE_DARK, MODULE_LIGHT)}
)

title = "qrcode-basic · python · letsplot · anyplot.ai"

plot = (
    ggplot(modules, aes(x="x", y="y", fill="fill"))
    + geom_raster()
    + scale_fill_identity()
    + coord_fixed()
    + labs(
        title=title,
        subtitle=f"Encoded: {content}  |  Error Correction: {error_correction} ({ECC_SHARE[error_correction]})",
        caption=f"Version {version}  ·  {side}×{side} modules  ·  ECC Level {error_correction}",
    )
    + theme_void()
    + theme(
        plot_title=element_text(size=16, hjust=0.5, face="bold", color=INK),
        plot_subtitle=element_text(size=12, hjust=0.5, color=INK_SOFT),
        plot_caption=element_text(size=11, hjust=0.5, color=INK_MUTED),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    )
)

# coord_fixed narrows the plot inside the square canvas; the grid paints the side margins
plot = gggrid([plot]) + ggsize(600, 600) + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))

# Save: square 2400 × 2400 px (PNG + interactive HTML)
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
