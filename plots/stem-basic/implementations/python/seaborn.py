""" anyplot.ai
stem-basic: Basic Stem Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 88/100 | Updated: 2026-04-30
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

BRAND = "#009E73"

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

# Data - Discrete signal samples (damped sinusoidal impulse response)
np.random.seed(42)
n_samples = 30
x = np.arange(n_samples)
y = np.exp(-0.1 * x) * np.sin(0.5 * x) * 2.5

df = pd.DataFrame({"Sample Index": x, "Amplitude": y})

fig, ax = plt.subplots(figsize=(16, 9))

# Draw stems (thin vertical lines from baseline y=0 to data values)
ax.vlines(x=df["Sample Index"], ymin=0, ymax=df["Amplitude"], color=BRAND, linewidth=2.5, alpha=0.8)

# Draw markers at top of stems using seaborn
sns.scatterplot(
    data=df, x="Sample Index", y="Amplitude", s=300, color=BRAND, edgecolor=PAGE_BG, linewidth=2, ax=ax, zorder=3
)

# Draw baseline at y=0
ax.axhline(y=0, color=INK_SOFT, linewidth=1.5, alpha=0.5)

ax.set_xlabel("Sample Index (n)", fontsize=20)
ax.set_ylabel("Amplitude", fontsize=20)
ax.set_title("stem-basic · seaborn · anyplot.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)

ax.yaxis.grid(True, linestyle="-", linewidth=0.8, alpha=0.15)
ax.set_axisbelow(True)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
