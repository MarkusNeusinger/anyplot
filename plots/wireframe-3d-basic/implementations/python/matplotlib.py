"""anyplot.ai
wireframe-3d-basic: Basic 3D Wireframe Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-06
"""

import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.ticker import MaxNLocator


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Imprint palette position 1

# Data - ripple function z = sin(sqrt(x^2 + y^2))
np.random.seed(42)
x = np.linspace(-6, 6, 40)
y = np.linspace(-6, 6, 40)
X, Y = np.meshgrid(x, y)
R = np.sqrt(X**2 + Y**2)
Z = np.sin(R)

# Imprint sequential colormap, used only for the floor contour echo below
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", ["#009E73", "#4467A3"])

# Create 3D plot (3200x1800 px)
fig = plt.figure(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax = fig.add_subplot(111, projection="3d")
ax.set_facecolor(PAGE_BG)

# Ripple wireframe in brand green — the single consistent-color primary series.
# rcount/ccount subsample the 40x40 data grid down to 25x25 drawn lines so the
# mesh stays crisp instead of moire-ing into a dense hairball at this viewing angle.
ax.plot_wireframe(X, Y, Z, color=BRAND, linewidth=1.6, alpha=0.85, rcount=25, ccount=25)

# Contour projection on the floor plane echoes the ripple's height structure
# as a topographic footprint, giving a second, easier-to-read view of the
# same Z data without competing with the wireframe's brand-green identity
z_floor = Z.min() - 0.6
ax.contour(X, Y, Z, zdir="z", offset=z_floor, levels=10, cmap=imprint_seq, linewidths=1.0, alpha=0.55)
ax.set_zlim(z_floor, Z.max() + 0.15)

# Set viewing angle (elevation 30, azimuth 45 as per spec)
ax.view_init(elev=30, azim=45)

# Labels and styling
ax.set_xlabel("Distance from Center (X)", fontsize=12, labelpad=10, color=INK)
ax.set_ylabel("Distance from Center (Y)", fontsize=12, labelpad=10, color=INK)
ax.set_zlabel("Amplitude (Z)", fontsize=12, labelpad=8, color=INK)
ax.set_title("wireframe-3d-basic · matplotlib · anyplot.ai", fontsize=15, fontweight="medium", pad=14, color=INK)

# Tick parameters — fewer, cleaner ticks with a compact numeric format
ax.xaxis.set_major_locator(MaxNLocator(5))
ax.yaxis.set_major_locator(MaxNLocator(5))
ax.zaxis.set_major_locator(MaxNLocator(5))
ax.zaxis.set_major_formatter("{x:.1f}")
ax.tick_params(axis="both", labelsize=10, colors=INK_SOFT)
ax.tick_params(axis="z", labelsize=10, colors=INK_SOFT)

# Theme-adaptive panes and grid
ax.xaxis.pane.set_facecolor(PAGE_BG)
ax.yaxis.pane.set_facecolor(PAGE_BG)
ax.zaxis.pane.set_facecolor(PAGE_BG)
ax.xaxis.pane.set_edgecolor(INK_SOFT)
ax.yaxis.pane.set_edgecolor(INK_SOFT)
ax.zaxis.pane.set_edgecolor(INK_SOFT)
ax.grid(True, alpha=0.15, linestyle="-", color=INK_SOFT, linewidth=0.6)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)  # bbox_inches MUST stay default (None)
