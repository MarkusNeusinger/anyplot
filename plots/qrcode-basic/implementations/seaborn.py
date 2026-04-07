""" pyplots.ai
qrcode-basic: Basic QR Code Generator
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 87/100 | Updated: 2026-04-07
"""

import matplotlib.pyplot as plt
import numpy as np
import qrcode
import seaborn as sns
from matplotlib.colors import ListedColormap


# Configure seaborn theme and context for polished output
sns.set_context("poster", font_scale=1.0)
sns.set_style("white")

# Generate QR code with proper encoding
encoded_url = "https://pyplots.ai"
qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=1, border=4)
qr.add_data(encoded_url)
qr.make(fit=True)

# Convert QR matrix to numpy array
qr_matrix = np.array(qr.get_matrix(), dtype=np.uint8)

# Build a seaborn-native colormap from palette
dark, light = sns.color_palette("dark:#000000", 1)[0], sns.color_palette("light:#FFFFFF", 1)[0]
qr_cmap = ListedColormap([light, dark])

# Plot
fig, ax = plt.subplots(figsize=(12, 12))

sns.heatmap(
    qr_matrix,
    ax=ax,
    cmap=qr_cmap,
    vmin=0,
    vmax=1,
    square=True,
    cbar=False,
    xticklabels=False,
    yticklabels=False,
    linewidths=0,
    linecolor="white",
)

# Remove all chrome
sns.despine(ax=ax, left=True, bottom=True)
ax.set_xlabel("")
ax.set_ylabel("")
ax.tick_params(left=False, bottom=False)

# Title with hierarchy
ax.set_title("qrcode-basic · seaborn · pyplots.ai", fontsize=28, fontweight="bold", pad=28, color="#1a1a2e")

# Subtitle showing encoded content for data storytelling
ax.text(
    0.5,
    -0.03,
    f"Encodes: {encoded_url}  ·  Error Correction: M (15%)  ·  Version {qr.version}",
    transform=ax.transAxes,
    ha="center",
    va="top",
    fontsize=16,
    color="#555555",
    fontstyle="italic",
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
