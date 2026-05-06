""" anyplot.ai
ternary-basic: Basic Ternary Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 96/100 | Updated: 2026-05-06
"""

import os
import sys


# Remove script directory from sys.path to avoid local matplotlib.py shadow
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != script_dir]

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402


# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Okabe-Ito position 1

# Set seaborn/matplotlib theme
sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK,
        "grid.alpha": 0.10,
    },
)

# Data - Cement composition samples (Limestone, Clay, Gypsum)
# Realistic cement clinker composition percentages
np.random.seed(42)
n_points = 50

# Generate random compositions that sum to 100
raw = np.random.dirichlet(alpha=[2, 2, 2], size=n_points) * 100
df = pd.DataFrame({"Limestone": raw[:, 0], "Clay": raw[:, 1], "Gypsum": raw[:, 2]})

# Ternary coordinates transformation (vectorized)
# Convert (a, b, c) to Cartesian (x, y) where a + b + c = 100
# Triangle vertices: Bottom-left (0,0)=Limestone, Bottom-right (1,0)=Clay, Top (0.5, sqrt(3)/2)=Gypsum
sqrt3_2 = np.sqrt(3) / 2
limestone_norm = df["Limestone"].values / 100
clay_norm = df["Clay"].values / 100
gypsum_norm = df["Gypsum"].values / 100
x = 0.5 * (2 * clay_norm + gypsum_norm)
y = sqrt3_2 * gypsum_norm

# Create plot
fig, ax = plt.subplots(figsize=(12, 12), facecolor=PAGE_BG)

# Draw triangle outline
triangle = np.array([[0, 0], [1, 0], [0.5, sqrt3_2], [0, 0]])
ax.plot(triangle[:, 0], triangle[:, 1], color=INK_SOFT, linewidth=2, zorder=5)

# Draw grid lines at 10% intervals
grid_lw = 1

for level in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]:
    # Lines parallel to bottom (constant Gypsum)
    x1, y1 = 0.5 * level, sqrt3_2 * level
    x2, y2 = 1 - 0.5 * level, sqrt3_2 * level
    ax.plot([x1, x2], [y1, y2], color=INK, alpha=0.10, linewidth=grid_lw, zorder=1)

    # Lines parallel to left edge (constant Clay)
    x1, y1 = level, 0
    x2, y2 = 0.5 + 0.5 * level, sqrt3_2 * (1 - level)
    ax.plot([x1, x2], [y1, y2], color=INK, alpha=0.10, linewidth=grid_lw, zorder=1)

    # Lines parallel to right edge (constant Limestone)
    x1, y1 = 0.5 * (1 - level), sqrt3_2 * (1 - level)
    x2, y2 = 1 - level, 0
    ax.plot([x1, x2], [y1, y2], color=INK, alpha=0.10, linewidth=grid_lw, zorder=1)

# Add tick marks along edges (at 20% intervals)
tick_length = 0.02

for level in [0.2, 0.4, 0.6, 0.8]:
    # Bottom edge ticks (Clay percentage increasing left to right)
    ax.plot([level, level], [-tick_length, 0], color=INK_SOFT, linewidth=1.5, zorder=5)
    ax.text(level, -0.05, f"{int(level * 100)}%", ha="center", va="top", fontsize=14, color=INK_SOFT)

    # Left edge ticks (Gypsum percentage)
    x_tick = 0.5 * level
    y_tick = sqrt3_2 * level
    dx, dy = -tick_length * np.cos(np.pi / 6), -tick_length * np.sin(np.pi / 6)
    ax.plot([x_tick, x_tick + dx], [y_tick, y_tick + dy], color=INK_SOFT, linewidth=1.5, zorder=5)
    ax.text(
        x_tick + dx - 0.03,
        y_tick + dy + 0.01,
        f"{int(level * 100)}%",
        ha="right",
        va="center",
        fontsize=14,
        color=INK_SOFT,
    )

    # Right edge ticks (Gypsum percentage from right side)
    x_tick = 1 - 0.5 * level
    y_tick = sqrt3_2 * level
    dx, dy = tick_length * np.cos(np.pi / 6), -tick_length * np.sin(np.pi / 6)
    ax.plot([x_tick, x_tick + dx], [y_tick, y_tick + dy], color=INK_SOFT, linewidth=1.5, zorder=5)
    ax.text(
        x_tick + dx + 0.03,
        y_tick + dy + 0.01,
        f"{int(level * 100)}%",
        ha="left",
        va="center",
        fontsize=14,
        color=INK_SOFT,
    )

# Plot data points
scatter_df = pd.DataFrame({"x": x, "y": y})
ax.scatter(scatter_df["x"], scatter_df["y"], color=BRAND, s=200, alpha=0.7, edgecolor=PAGE_BG, linewidth=1.5, zorder=10)

# Vertex labels
label_offset = 0.08
ax.text(0, -label_offset, "Limestone (100%)", ha="center", va="top", fontsize=20, fontweight="bold", color=INK)
ax.text(1, -label_offset, "Clay (100%)", ha="center", va="top", fontsize=20, fontweight="bold", color=INK)
ax.text(
    0.5, sqrt3_2 + label_offset, "Gypsum (100%)", ha="center", va="bottom", fontsize=20, fontweight="bold", color=INK
)

# Title
ax.set_title(
    "Cement Composition · ternary-basic · seaborn · pyplots.ai", fontsize=24, pad=20, color=INK, fontweight="medium"
)

# Clean up axes
ax.set_xlim(-0.15, 1.15)
ax.set_ylim(-0.18, 1.05)
ax.set_aspect("equal")
ax.axis("off")

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
