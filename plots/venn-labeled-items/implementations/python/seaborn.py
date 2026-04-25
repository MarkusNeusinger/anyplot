"""anyplot.ai
venn-labeled-items: Chartgeist-Style Venn Diagram with Labeled Items
Library: seaborn 0.13.2 | Python 3.14.4
"""

import os

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.patches import Circle


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

OKABE_GREEN = "#009E73"
OKABE_ORANGE = "#D55E00"
OKABE_BLUE = "#0072B2"

sns.set_theme(
    style="white",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": PAGE_BG,
        "axes.labelcolor": INK,
        "text.color": INK,
        "font.family": "serif",
    },
)

# Data
circles = [
    {"name": "Overhyped", "color": OKABE_GREEN, "center": (0.00, 0.55)},
    {"name": "Actually Useful", "color": OKABE_ORANGE, "center": (-0.476, -0.275)},
    {"name": "Secretly Loved", "color": OKABE_BLUE, "center": (0.476, -0.275)},
]

zone_items = {
    "A": ["NFTs", "Metaverse", "Web3"],
    "B": ["Spreadsheets", "Calculators"],
    "C": ["Karaoke", "Bob Ross"],
    "AB": ["Crypto", "ChatGPT"],
    "AC": ["TikTok", "Pumpkin Spice"],
    "BC": ["Google Maps", "Dolly Parton", "IKEA Meatballs"],
    "ABC": ["Sourdough"],
    "outside": ["Jury Duty"],
}

zone_centroids = {
    "A": (0.00, 1.05),
    "B": (-1.00, -0.62),
    "C": (1.00, -0.62),
    "AB": (-0.55, 0.32),
    "AC": (0.55, 0.32),
    "BC": (0.00, -0.65),
    "ABC": (0.00, 0.05),
    "outside": (-1.95, 1.30),
}

# Build a long-form items dataframe so we can use seaborn for the marker layer.
rows = []
spacing = 0.20
for zone, labels in zone_items.items():
    cx, cy = zone_centroids[zone]
    n = len(labels)
    start_y = cy + (n - 1) * spacing / 2
    for i, label in enumerate(labels):
        rows.append(
            {
                "zone": zone,
                "label": label,
                "x": cx,
                "y": start_y - i * spacing,
                "is_outside": zone == "outside",
                "is_triple": zone == "ABC",
            }
        )
items_df = pd.DataFrame(rows)

# Plot — square canvas suits the symmetric Venn layout
fig, ax = plt.subplots(figsize=(12, 12), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)
ax.set_aspect("equal")

r = 0.85
for c in circles:
    ax.add_patch(Circle(c["center"], radius=r, facecolor=c["color"], alpha=0.20, edgecolor=c["color"], linewidth=2.0))

# Subtle focal-point highlight on the triple-overlap zone for editorial emphasis
ax.add_patch(
    Circle(
        zone_centroids["ABC"],
        radius=0.13,
        facecolor=INK,
        alpha=0.05,
        edgecolor=INK_SOFT,
        linewidth=0.8,
        linestyle=(0, (2, 2)),
    )
)

# Seaborn scatter layer: small dot markers anchor every item.
# Different palette + size for the focal triple-overlap zone (DE-03 storytelling).
regular = items_df[~items_df["is_triple"]]
triple = items_df[items_df["is_triple"]]
sns.scatterplot(data=regular, x="x", y="y", color=INK_SOFT, s=18, alpha=0.55, edgecolor="none", legend=False, ax=ax)
sns.scatterplot(
    data=triple, x="x", y="y", color=INK, s=44, alpha=0.85, edgecolor=PAGE_BG, linewidth=1.2, legend=False, ax=ax
)

# Category labels (outside each circle, on the outer side)
ax.text(
    0,
    0.55 + r + 0.06,
    circles[0]["name"],
    ha="center",
    va="bottom",
    fontsize=24,
    fontweight="bold",
    color=circles[0]["color"],
    clip_on=False,
)
ax.text(
    -1.40,
    -0.275 - 0.80,
    circles[1]["name"],
    ha="right",
    va="top",
    fontsize=24,
    fontweight="bold",
    color=circles[1]["color"],
    clip_on=False,
)
ax.text(
    1.40,
    -0.275 - 0.80,
    circles[2]["name"],
    ha="left",
    va="top",
    fontsize=24,
    fontweight="bold",
    color=circles[2]["color"],
    clip_on=False,
)

# Item text labels — slightly above their dot markers
label_offset = 0.055
for _, row in items_df.iterrows():
    is_triple = row["is_triple"]
    is_outside = row["is_outside"]
    ax.text(
        row["x"],
        row["y"] + label_offset,
        row["label"],
        ha="center",
        va="bottom",
        fontsize=20 if is_triple else 17,
        fontweight="bold" if is_triple else "normal",
        color=INK_MUTED if is_outside else INK,
        style="italic" if is_outside else "normal",
        clip_on=False,
    )

# Hint label for the "outside" stack
ax.text(
    -1.95, 1.55, "(outside all)", ha="center", va="bottom", fontsize=14, color=INK_MUTED, style="italic", clip_on=False
)

# Title (mandatory format) + editorial subtitle
fig.suptitle("venn-labeled-items · seaborn · anyplot.ai", fontsize=26, fontweight="medium", color=INK, y=0.965)
fig.text(
    0.5,
    0.918,
    "Tech & Trends — a Chartgeist taxonomy of what we love, use, and overrate",
    ha="center",
    va="top",
    fontsize=18,
    color=INK_SOFT,
    style="italic",
)

ax.set_xlim(-2.35, 2.35)
ax.set_ylim(-2.05, 1.85)
ax.axis("off")

plt.savefig(f"plot-{THEME}.png", dpi=200, bbox_inches="tight", facecolor=PAGE_BG)
