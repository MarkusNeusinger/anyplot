"""anyplot.ai
scatter-categorical: Categorical Scatter Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-12
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
MARKERS = ["o", "s", "^", "D", "v", "P", "X", "h"]  # one marker shape per group, same order as the palette

# Columns: set these to your table's column names
PETAL_LENGTH = "Petal length (cm)"  # role: x
PETAL_WIDTH = "Petal width (cm)"  # role: y
SPECIES = "Species"  # role: category

# Data: replace this block with your own table, for example df = pd.read_csv("petals.csv")
rng = np.random.default_rng(42)
n_per_group = 40
# (mean length, sd length, mean width, sd width) per species
profiles = {"Species A": (1.5, 0.3, 0.3, 0.1), "Species B": (4.0, 0.5, 1.3, 0.2), "Species C": (5.5, 0.6, 2.0, 0.3)}
df = pd.concat(
    [
        pd.DataFrame(
            {PETAL_LENGTH: rng.normal(mx, sx, n_per_group), PETAL_WIDTH: rng.normal(my, sy, n_per_group), SPECIES: name}
        )
        for name, (mx, sx, my, sy) in profiles.items()
    ],
    ignore_index=True,
)

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

for i, (species, rows) in enumerate(df.groupby(SPECIES, sort=False)):
    ax.scatter(
        rows[PETAL_LENGTH],
        rows[PETAL_WIDTH],
        s=70,
        color=IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)],
        alpha=0.8,
        marker=MARKERS[i % len(MARKERS)],
        edgecolors=PAGE_BG,
        linewidth=0.5,
        label=species,
    )

# Style
ax.set_xlabel(PETAL_LENGTH, fontsize=10, color=INK)
ax.set_ylabel(PETAL_WIDTH, fontsize=10, color=INK)
ax.set_title("scatter-categorical · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)

for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)

leg = ax.legend(title=SPECIES, fontsize=8, title_fontsize=9, loc="upper left")
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)
leg.get_title().set_color(INK)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
