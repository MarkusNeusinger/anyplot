""" pyplots.ai
qrcode-basic: Basic QR Code Generator
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 90/100 | Updated: 2026-04-07
"""

import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import qrcode
from matplotlib.colors import ListedColormap


# Data - Generate a real, scannable QR code encoding "https://pyplots.ai"
content = "https://pyplots.ai"

qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=1, border=4)
qr.add_data(content)
qr.make(fit=True)

# Convert QR code to numpy matrix
qr_matrix = np.array(qr.get_matrix(), dtype=int)
rows, cols = qr_matrix.shape

# Plot
fig, ax = plt.subplots(figsize=(12, 12), facecolor="white")

# Custom two-color colormap for crisp rendering
qr_cmap = ListedColormap(["#FFFFFF", "#1A1A2E"])
ax.imshow(qr_matrix, cmap=qr_cmap, interpolation="nearest", vmin=0, vmax=1, aspect="equal")

# Completely remove axes and all frame artifacts
ax.set_axis_off()
for spine in ax.spines.values():
    spine.set_visible(False)
ax.set_frame_on(False)

# Decorative rounded-corner frame around the QR code using FancyBboxPatch
padding = 0.8
frame = mpatches.FancyBboxPatch(
    (-padding, -padding),
    cols - 1 + 2 * padding,
    rows - 1 + 2 * padding,
    boxstyle=mpatches.BoxStyle.Round(pad=0.6, rounding_size=1.5),
    facecolor="none",
    edgecolor="#306998",
    linewidth=2.5,
    zorder=5,
)
ax.add_patch(frame)

# Subtle shadow frame behind the main frame for depth
shadow = mpatches.FancyBboxPatch(
    (-padding + 0.15, -padding + 0.15),
    cols - 1 + 2 * padding,
    rows - 1 + 2 * padding,
    boxstyle=mpatches.BoxStyle.Round(pad=0.6, rounding_size=1.5),
    facecolor="none",
    edgecolor="#306998",
    linewidth=2.5,
    alpha=0.15,
    zorder=4,
)
ax.add_patch(shadow)

# Extend view to accommodate frame and annotations
ax.set_xlim(-2.5, cols + 1.5)
ax.set_ylim(rows + 1.5, -2.5)

fig.subplots_adjust(left=0.06, right=0.94, top=0.87, bottom=0.14)

# Title with patheffects for subtle glow
title = ax.set_title(
    "qrcode-basic \u00b7 matplotlib \u00b7 pyplots.ai", fontsize=28, fontweight="bold", pad=30, color="#306998"
)
title.set_path_effects([pe.withStroke(linewidth=3, foreground="white"), pe.Normal()])

# Accent rule line using axhline in figure coordinates via fig.add_axes
accent_ax = fig.add_axes([0.25, 0.105, 0.50, 0.002])
accent_ax.set_xlim(0, 1)
accent_ax.set_ylim(0, 1)
gradient = np.linspace(0, 1, 256).reshape(1, -1)
accent_ax.imshow(gradient, aspect="auto", cmap=ListedColormap(["#306998", "#FFD43B"]), extent=[0, 1, 0, 1])
accent_ax.set_axis_off()

# Metadata text with patheffects
encoded_text = fig.text(
    0.5,
    0.085,
    f"Encoded: {content}",
    ha="center",
    fontsize=20,
    color="#444444",
    family="monospace",
    fontweight="medium",
)
encoded_text.set_path_effects([pe.withStroke(linewidth=2, foreground="white"), pe.Normal()])

version_info = (
    f"QR Code Version {qr.version} ({qr_matrix.shape[0]}\u00d7{qr_matrix.shape[1]}) \u00b7 Error Correction Level M"
)
meta_text = fig.text(0.5, 0.04, version_info, ha="center", fontsize=16, color="#777777", style="italic")
meta_text.set_path_effects([pe.withStroke(linewidth=1.5, foreground="white"), pe.Normal()])

plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
