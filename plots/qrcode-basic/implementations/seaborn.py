""" pyplots.ai
qrcode-basic: Basic QR Code Generator
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 82/100 | Updated: 2026-04-07
"""

import matplotlib.pyplot as plt
import numpy as np
import qrcode
import seaborn as sns


# Generate QR code with proper encoding
qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=1, border=4)
qr.add_data("https://pyplots.ai")
qr.make(fit=True)

# Convert QR matrix to numpy array
qr_matrix = np.array(qr.get_matrix(), dtype=np.uint8)

# Plot
fig, ax = plt.subplots(figsize=(12, 12))

sns.heatmap(
    qr_matrix,
    ax=ax,
    cmap=["#FFFFFF", "#000000"],
    vmin=0,
    vmax=1,
    square=True,
    cbar=False,
    xticklabels=False,
    yticklabels=False,
    linewidths=0,
)

# Style
ax.set_xlabel("")
ax.set_ylabel("")
ax.set_title("qrcode-basic · seaborn · pyplots.ai", fontsize=28, fontweight="medium", pad=24)
ax.tick_params(left=False, bottom=False)

for spine in ax.spines.values():
    spine.set_visible(False)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
