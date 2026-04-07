"""pyplots.ai
qrcode-basic: Basic QR Code Generator
Library: seaborn 0.13.2 | Python 3.14.3
"""

import matplotlib.pyplot as plt
import numpy as np
import qrcode
import seaborn as sns
from matplotlib.colors import ListedColormap
from matplotlib.patches import FancyBboxPatch


# Configure seaborn with consolidated set_theme
sns.set_theme(context="poster", style="white", font_scale=1.0)

# Generate QR code with proper encoding
encoded_url = "https://pyplots.ai"
qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=1, border=4)
qr.add_data(encoded_url)
qr.make(fit=True)

# Convert QR matrix to numpy array
qr_matrix = np.array(qr.get_matrix(), dtype=np.uint8)
n_modules = qr_matrix.shape[0] - 8  # exclude quiet zone (border=4 each side)

# Branded color scheme using seaborn palette
brand_dark = sns.color_palette("dark:#1a1a2e", 1)[0]
brand_accent = sns.color_palette("muted")[0]  # seaborn muted blue for accents
qr_cmap = ListedColormap(["#ffffff", brand_dark])

# Plot on square canvas
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
sns.despine(ax=ax, left=True, bottom=True, top=True, right=True)
ax.set_xlabel("")
ax.set_ylabel("")
ax.tick_params(left=False, bottom=False)

# Annotate finder patterns with subtle highlight boxes
finder_size = 7
border = 4
finder_positions = [
    (border, border, "top-left"),
    (border, qr_matrix.shape[1] - border - finder_size, "top-right"),
    (qr_matrix.shape[0] - border - finder_size, border, "bottom-left"),
]
for row, col, _label in finder_positions:
    rect = FancyBboxPatch(
        (col - 0.3, row - 0.3),
        finder_size + 0.6,
        finder_size + 0.6,
        boxstyle="round,pad=0.2",
        linewidth=1.5,
        edgecolor=brand_accent,
        facecolor="none",
        alpha=0.5,
    )
    ax.add_patch(rect)

# Finder pattern annotation arrow pointing to top-right finder
fp_x = qr_matrix.shape[1] - border - finder_size / 2
fp_y = border + finder_size / 2
ax.annotate(
    "Finder Pattern",
    xy=(fp_x, fp_y),
    xytext=(fp_x + 2.5, fp_y - 5),
    fontsize=13,
    fontweight="medium",
    color=brand_accent,
    ha="center",
    arrowprops={"arrowstyle": "->", "color": brand_accent, "lw": 1.5},
)

# Quiet zone label on left side
ax.text(
    1.2,
    qr_matrix.shape[0] / 2,
    "Quiet Zone",
    fontsize=12,
    color="#888888",
    rotation=90,
    ha="center",
    va="center",
    fontstyle="italic",
)

# Title with strong typographic hierarchy
ax.set_title("qrcode-basic · seaborn · pyplots.ai", fontsize=28, fontweight="bold", pad=24, color="#1a1a2e")

# Subtitle with encoded content and technical details — tighter spacing below QR
fig.text(
    0.5,
    0.03,
    f"Encodes: {encoded_url}  ·  Error Correction: M (15%)  ·  Version {qr.version}  ·  {n_modules}×{n_modules} modules",
    ha="center",
    va="bottom",
    fontsize=15,
    color="#666666",
    fontstyle="italic",
)

plt.subplots_adjust(bottom=0.07, top=0.93)
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
