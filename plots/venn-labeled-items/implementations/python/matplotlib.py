"""anyplot.ai
venn-labeled-items: Chartgeist-Style Venn Diagram with Labeled Items
Library: matplotlib | Python 3.13
Quality: pending | Created: 2026-04-25
"""

import os

import matplotlib.pyplot as plt
from matplotlib.patches import Circle


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Okabe-Ito categorical (canonical positions 1, 2, 3)
COLOR_A = "#009E73"  # brand green — ALWAYS first series
COLOR_B = "#D55E00"  # vermillion
COLOR_C = "#0072B2"  # blue

# Data: three Chartgeist-style traits
RADIUS = 1.5
circles = [
    {"name": "Overhyped", "center": (-0.85, 0.50), "color": COLOR_A},
    {"name": "Actually Useful", "center": (0.85, 0.50), "color": COLOR_B},
    {"name": "Secretly Loved", "center": (0.00, -1.00), "color": COLOR_C},
]

# Items placed inside their assigned zone (label, x, y)
items = [
    # A only — Overhyped
    ("NFTs", -2.05, 1.05),
    ("Metaverse", -2.10, 0.55),
    ("Smart Fridges", -2.00, 0.05),
    # B only — Actually Useful
    ("Google Maps", 2.05, 1.05),
    ("Spreadsheets", 2.10, 0.55),
    ("Calendar Apps", 2.00, 0.05),
    # C only — Secretly Loved
    ("Roller Skating", -0.70, -2.10),
    ("Soap Operas", 0.70, -2.10),
    # A ∩ B
    ("ChatGPT", 0.00, 1.20),
    ("Smartwatches", 0.00, 0.85),
    # A ∩ C
    ("Crocs", -1.10, -0.20),
    ("Vinyl Records", -1.05, -0.60),
    # B ∩ C
    ("Dolly Parton", 1.10, -0.20),
    ("Spotify", 1.05, -0.60),
    # A ∩ B ∩ C
    ("Sourdough", 0.00, 0.12),
    ("TikTok", 0.00, -0.32),
]

# Plot
fig, ax = plt.subplots(figsize=(13, 13), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Three overlapping circles with semi-transparent fills
for circle in circles:
    ax.add_patch(
        Circle(
            circle["center"],
            RADIUS,
            facecolor=circle["color"],
            alpha=0.22,
            edgecolor=circle["color"],
            linewidth=2.5,
            zorder=1,
        )
    )

# Item labels
for label, x, y in items:
    ax.text(x, y, label, fontsize=16, color=INK, ha="center", va="center", family="serif", zorder=3)

# Category labels rendered outside each circle, on its outer side
category_positions = [
    ("Overhyped", -2.55, 1.85, "right", COLOR_A),
    ("Actually Useful", 2.55, 1.85, "left", COLOR_B),
    ("Secretly Loved", 0.00, -2.85, "center", COLOR_C),
]
for name, x, y, ha, color in category_positions:
    ax.text(x, y, name, fontsize=24, color=color, ha=ha, va="center", family="serif", fontweight="bold", zorder=4)

# Editorial title + canonical anyplot.ai title line
ax.text(
    0,
    3.05,
    "Chartgeist 2026",
    fontsize=32,
    color=INK,
    ha="center",
    va="center",
    family="serif",
    fontweight="bold",
    style="italic",
)
ax.text(
    0,
    2.55,
    "venn-labeled-items · matplotlib · anyplot.ai",
    fontsize=14,
    color=INK_MUTED,
    ha="center",
    va="center",
    family="serif",
)

# Frame
ax.set_xlim(-3.5, 3.5)
ax.set_ylim(-3.5, 3.5)
ax.set_aspect("equal")
ax.set_xticks([])
ax.set_yticks([])
for spine in ax.spines.values():
    spine.set_visible(False)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
