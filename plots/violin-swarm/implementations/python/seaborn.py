""" anyplot.ai
violin-swarm: Violin Plot with Overlaid Swarm Points
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-18
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette - first series always #009E73
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7"]

# Data - Gene expression levels (arbitrary units) across cell types
np.random.seed(42)

cell_types = ["Neuron", "Astrocyte", "Oligodendrocyte", "Microglia"]
n_per_type = 60

data = []
for cell_type in cell_types:
    # Different distributions per cell type
    if cell_type == "Neuron":
        values = np.random.normal(85, 12, n_per_type)
    elif cell_type == "Astrocyte":
        values = np.random.normal(72, 15, n_per_type)
    elif cell_type == "Oligodendrocyte":
        # Bimodal distribution
        values = np.concatenate([np.random.normal(55, 10, n_per_type // 2), np.random.normal(92, 8, n_per_type // 2)])
    else:  # Microglia
        values = np.random.normal(65, 14, n_per_type)

    for v in values:
        data.append({"Cell Type": cell_type, "Expression Level": v})

df = pd.DataFrame(data)

# Plot
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
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

fig, ax = plt.subplots(figsize=(16, 9))

# Violin plot with transparency
sns.violinplot(
    data=df,
    x="Cell Type",
    y="Expression Level",
    hue="Cell Type",
    palette=OKABE_ITO,
    alpha=0.4,
    inner=None,
    legend=False,
    ax=ax,
)

# Swarm plot overlay with darker shades
darker_palette = ["#006B50", "#A63F00", "#004D7A", "#8B5A7C"]
sns.swarmplot(
    data=df, x="Cell Type", y="Expression Level", hue="Cell Type", palette=darker_palette, size=6, legend=False, ax=ax
)

# Styling
ax.set_title("violin-swarm · Python · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.set_xlabel("Cell Type", fontsize=20, color=INK)
ax.set_ylabel("Expression Level", fontsize=20, color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax.grid(True, axis="y", alpha=0.15, linewidth=0.8)

# Spine styling
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for spine in ["left", "bottom"]:
    ax.spines[spine].set_color(INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
