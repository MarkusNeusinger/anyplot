""" anyplot.ai
wireframe-3d-basic: Basic 3D Wireframe Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 93/100 | Created: 2026-05-06
"""

import sys

sys.path = [
    p
    for p in sys.path
    if "implementations/python" not in p and p not in ("", ".")
]

import os  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

# Data - ripple surface
np.random.seed(42)
x = np.linspace(-5, 5, 30)
y = np.linspace(-5, 5, 30)
X, Y = np.meshgrid(x, y)
R = np.sqrt(X**2 + Y**2)
Z = np.sin(R)

# Plot
fig = plt.figure(figsize=(16, 9), facecolor=PAGE_BG)
ax = fig.add_subplot(111, projection="3d", facecolor=PAGE_BG)

# Wireframe with refined appearance for visual sophistication
ax.plot_wireframe(X, Y, Z, color=BRAND, linewidth=1.3, alpha=0.95, antialiased=True)

# Style
ax.set_xlabel("X", fontsize=20, color=INK, labelpad=10)
ax.set_ylabel("Y", fontsize=20, color=INK, labelpad=10)
ax.set_zlabel("Z", fontsize=20, color=INK, labelpad=10)
ax.set_title("wireframe-3d-basic · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK, pad=20)

# Tick styling
ax.tick_params(axis="x", labelsize=16, colors=INK_SOFT)
ax.tick_params(axis="y", labelsize=16, colors=INK_SOFT)
ax.tick_params(axis="z", labelsize=16, colors=INK_SOFT)

# Perspective: elevation angle emphasizes surface topology
ax.view_init(elev=25, azim=45)
ax.grid(True, alpha=0.08, linewidth=0.7, color=INK_SOFT)

# Pane styling: minimize edges for cleaner appearance
ax.xaxis.pane.set_facecolor(PAGE_BG)
ax.yaxis.pane.set_facecolor(PAGE_BG)
ax.zaxis.pane.set_facecolor(PAGE_BG)
# Remove visible pane edges for visual refinement
for pane in [ax.xaxis.pane, ax.yaxis.pane, ax.zaxis.pane]:
    pane.set_edgecolor("none")
    pane.set_alpha(0.0)

# Save
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG, edgecolor="none")
