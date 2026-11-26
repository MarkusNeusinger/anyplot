"""anyplot.ai
barcode-code128: Code 128 Barcode
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 83/100 | Updated: 2026-11-26
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

sns.set_theme(
    style="white",
    rc={"figure.facecolor": PAGE_BG, "axes.facecolor": PAGE_BG, "axes.edgecolor": INK_SOFT, "text.color": INK},
)

TILE = "#FAF8F1"  # light tile behind the symbol in both themes
BAR = "#1A1A17"
# Imprint palette in canonical order for Start, Data, Check, Stop
PART_COLORS = {"Start": "#009E73", "Data": "#C475FD", "Check": "#4467A3", "Stop": "#BD8233"}


def label_color(fill):
    """Pick white or near-black text, whichever contrasts more with the fill."""
    lin = [(c / 255) ** 2.2 for c in (int(fill[i : i + 2], 16) for i in (1, 3, 5))]
    lum = 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]
    return "white" if 1.05 / (lum + 0.05) >= (lum + 0.05) / 0.06 else BAR


# Code 128 encoding tables (subset B — full printable ASCII)
CODE128_B_PATTERNS = {
    " ": "11011001100",
    "!": "11001101100",
    '"': "11001100110",
    "#": "10010011000",
    "$": "10010001100",
    "%": "10001001100",
    "&": "10011001000",
    "'": "10011000100",
    "(": "10001100100",
    ")": "11001001000",
    "*": "11001000100",
    "+": "11000100100",
    ",": "10110011100",
    "-": "10011011100",
    ".": "10011001110",
    "/": "10111001100",
    "0": "10011101100",
    "1": "10011100110",
    "2": "11001110010",
    "3": "11001011100",
    "4": "11001001110",
    "5": "11011100100",
    "6": "11001110100",
    "7": "11101101110",
    "8": "11101001100",
    "9": "11100101100",
    ":": "11100100110",
    ";": "11101100100",
    "<": "11100110100",
    "=": "11100110010",
    ">": "11011011000",
    "?": "11011000110",
    "@": "11000110110",
    "A": "10100011000",
    "B": "10001011000",
    "C": "10001000110",
    "D": "10110001000",
    "E": "10001101000",
    "F": "10001100010",
    "G": "11010001000",
    "H": "11000101000",
    "I": "11000100010",
    "J": "10110111000",
    "K": "10110001110",
    "L": "10001101110",
    "M": "10111011000",
    "N": "10111000110",
    "O": "10001110110",
    "P": "11101110110",
    "Q": "11010001110",
    "R": "11000101110",
    "S": "11011101000",
    "T": "11011100010",
    "U": "11011101110",
    "V": "11101011000",
    "W": "11101000110",
    "X": "11100010110",
    "Y": "11101101000",
    "Z": "11101100010",
    "[": "11100011010",
    "\\": "11101111010",
    "]": "11001000010",
    "^": "11110001010",
    "_": "10100110000",
    "`": "10100001100",
    "a": "10010110000",
    "b": "10010000110",
    "c": "10000101100",
    "d": "10000100110",
    "e": "10110010000",
    "f": "10110000100",
    "g": "10011010000",
    "h": "10011000010",
    "i": "10000110100",
    "j": "10000110010",
    "k": "11000010010",
    "l": "11001010000",
    "m": "11110111010",
    "n": "11000010100",
    "o": "10001111010",
    "p": "10100111100",
    "q": "10010111100",
    "r": "10010011110",
    "s": "10111100100",
    "t": "10011110100",
    "u": "10011110010",
    "v": "11110100100",
    "w": "11110010100",
    "x": "11110010010",
    "y": "11011011110",
    "z": "11011110110",
    "{": "11110110110",
    "|": "10101111000",
    "}": "10100011110",
    "~": "10001011110",
}

# Patterns for check digit values 95–105 (no ASCII mapping)
CHECK_PATTERNS = [
    "11110101000",
    "11110100010",
    "10111011110",
    "10111101110",
    "10111110110",
    "11101011110",
    "11110101110",
    "11010000100",
    "11010010000",
    "11010011100",
    "11000111010",
]

START_B = "11010010000"
STOP = "1100011101011"
QUIET = "0" * 10

# Column names
PART = "part"  # role: extra
PATTERN = "pattern"  # role: content
VALUE = "value"  # role: extra

# Data
content = "LAB-7731-B204"  # hospital specimen tube ID

# Code 128 subset B: the value of a character is ord(char) - 32; values 95-105 have no ASCII character
pattern_by_value = [CODE128_B_PATTERNS[chr(32 + v)] for v in range(95)] + CHECK_PATTERNS
data_values = [ord(char) - 32 for char in content]
check_value = (104 + sum(v * (i + 1) for i, v in enumerate(data_values))) % 103  # modulo-103 check character

rows = [("Start", 104, START_B)]
rows += [("Data", v, pattern_by_value[v]) for v in data_values]
rows += [("Check", check_value, pattern_by_value[check_value]), ("Stop", 106, STOP)]
df = pd.DataFrame(rows, columns=[PART, VALUE, PATTERN])

# Plot: zone boundaries, barcode matrix and annotation strip all derive from df
barcode_with_quiet = QUIET + "".join(df[PATTERN]) + QUIET
n_cols = len(barcode_with_quiet)
q = len(QUIET)
widths = df.groupby(PART, sort=False)[PATTERN].apply(lambda p: p.str.len().sum())
edges = q + np.concatenate([[0], widths.cumsum().to_numpy()])
labels = {"Data": f"Data · {len(content)} chars"}

zone_defs = [(0, q, INK_SOFT, 0.20, "")]
for (part, color), x0, x1 in zip(PART_COLORS.items(), edges[:-1], edges[1:], strict=True):
    zone_defs.append((x0, x1, color, 1.0, labels.get(part, part)))
zone_defs.append((n_cols - q, n_cols, INK_SOFT, 0.20, ""))

# Build 2D barcode matrix
barcode_array = np.array([[int(bit) for bit in barcode_with_quiet]])
barcode_data = np.repeat(barcode_array, 40, axis=0)

# Black bars on a light tile in both themes (the standard symbol), built as a seaborn blend palette
cmap = sns.blend_palette([TILE, BAR], n_colors=256, as_cmap=True)
# Layout: barcode panel + zone annotation strip
fig, (ax, ax_ann) = plt.subplots(
    2, 1, figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG, gridspec_kw={"height_ratios": [6, 1], "hspace": 0.03}
)

# Barcode panel
sns.heatmap(barcode_data, cmap=cmap, cbar=False, xticklabels=False, yticklabels=False, linewidths=0, ax=ax)
sns.despine(ax=ax, left=True, bottom=True, top=True, right=True)
ax.set_title("barcode-code128 · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=10)

# Zone annotation strip — structural callouts for each barcode section
ax_ann.set_facecolor(ELEVATED_BG)
ax_ann.set_xlim(0, n_cols)
ax_ann.set_ylim(0, 1)

for x0, x1, color, alpha, label in zone_defs:
    width = x1 - x0
    ax_ann.add_patch(plt.Rectangle((x0, 0), width, 1, color=color, alpha=alpha))
    if label:
        ax_ann.text(
            (x0 + x1) / 2,
            0.5,
            label,
            ha="center",
            va="center",
            fontsize=7,
            color=label_color(color) if alpha == 1.0 else "white",
            fontweight="bold",
            linespacing=1.3,
        )

sns.despine(ax=ax_ann, left=True, bottom=True, top=True, right=True)
ax_ann.set_xticks([])
ax_ann.set_yticks([])

fig.subplots_adjust(top=0.88, bottom=0.11, left=0.02, right=0.98)
fig.text(
    0.5, 0.04, content, ha="center", va="center", fontsize=10, fontfamily="monospace", fontweight="bold", color=INK
)

# Save
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
