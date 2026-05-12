""" anyplot.ai
box-horizontal: Horizontal Box Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-12
"""

import os
import sys


# noqa: E402 - sys.path manipulation required before imports to avoid module shadowing
sys.path = [p for p in sys.path if p not in ("", ".")]

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

# Data - Response times (ms) by service type
np.random.seed(42)

services = [
    "Authentication Service",
    "Database Query",
    "File Upload",
    "Payment Processing",
    "Email Notification",
    "Image Processing",
]

# Generate data with different distributions to show variety
data = [
    np.random.normal(150, 30, 80),  # Auth - tight distribution
    np.concatenate([np.random.normal(200, 40, 70), [450, 480, 520]]),  # DB - with outliers
    np.random.normal(500, 100, 90),  # File upload - wider spread
    np.random.exponential(180, 85) + 100,  # Payment - skewed right
    np.random.normal(80, 15, 75),  # Email - fast and tight
    np.random.uniform(300, 800, 60),  # Image - wide uniform spread
]

# Create figure
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Create horizontal box plot
bp = ax.boxplot(
    data,
    vert=False,
    tick_labels=services,
    patch_artist=True,
    widths=0.6,
    flierprops={"marker": "o", "markersize": 8, "markerfacecolor": BRAND, "markeredgecolor": BRAND},
    medianprops={"color": INK, "linewidth": 2.5},
    whiskerprops={"color": INK_SOFT, "linewidth": 2},
    capprops={"color": INK_SOFT, "linewidth": 2},
    boxprops={"facecolor": BRAND, "edgecolor": BRAND, "linewidth": 2, "alpha": 0.7},
)

# Labels and styling
ax.set_xlabel("Response Time (ms)", fontsize=20, color=INK)
ax.set_ylabel("Service Type", fontsize=20, color=INK)
ax.set_title("box-horizontal · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)
ax.xaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
