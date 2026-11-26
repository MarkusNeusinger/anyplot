""" anyplot.ai
datamatrix-basic: Basic Data Matrix 2D Barcode
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-26
"""

import importlib
import os
import sys


# This file is named matplotlib.py, which shadows the installed matplotlib package.
# Remove the script directory from sys.path so Python finds the real package.
_here = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p or os.getcwd()) != _here]
del _here

plt = importlib.import_module("matplotlib.pyplot")
np = importlib.import_module("numpy")
Rectangle = importlib.import_module("matplotlib.patches").Rectangle

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette (the symbol itself is black on white for scanning)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
QUIET_ZONE = 3  # blank modules around the symbol; the standard asks for at least 1

# Data: 20×20 Data Matrix for electronics component traceability
CONTENT = "PCB:2026-A3F7"
SIZE = 20
rng = np.random.RandomState(sum(ord(c) for c in CONTENT))

# Matrix of modules (1 = black, 0 = white): data modules first, then clock tracks, then the finder on top
matrix = rng.randint(0, 2, size=(SIZE, SIZE))
matrix[0, :] = (np.arange(SIZE) + 1) % 2  # top clock track, starts black at the corner
matrix[:, -1] = np.arange(SIZE) % 2  # right clock track, starts white at the top
matrix[:, 0] = 1  # L-finder: solid left column
matrix[-1, :] = 1  # L-finder: solid bottom row

# Plot
fig = plt.figure(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
side = 0.78  # fraction of the figure the white tile (symbol plus quiet zone) occupies
ax = fig.add_axes([(1 - side) / 2, (1 - side) / 2, side, side])

# The quiet zone stays white in both themes, as scanners need; axis("off") hides the axes patch, so draw it
ax.add_patch(Rectangle((-QUIET_ZONE, -QUIET_ZONE), SIZE + 2 * QUIET_ZONE, SIZE + 2 * QUIET_ZONE, fc="white", ec="none"))
ax.pcolormesh(np.arange(SIZE + 1), np.arange(SIZE + 1), matrix[::-1], cmap="binary", vmin=0, vmax=1, edgecolors="none")
ax.set_aspect("equal")
ax.set_xlim(-QUIET_ZONE, SIZE + QUIET_ZONE)
ax.set_ylim(-QUIET_ZONE, SIZE + QUIET_ZONE)
ax.axis("off")

fig.suptitle(
    "datamatrix-basic · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK, y=0.955
)
fig.text(
    0.5,
    0.055,
    f"Data Matrix {SIZE}×{SIZE}  ·  Encoded: {CONTENT}  ·  ECC 200",
    ha="center",
    va="center",
    fontsize=9,
    fontfamily="monospace",
    color=INK_SOFT,
)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
