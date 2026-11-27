"""anyplot.ai
band-basic: Basic Band Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-05-29
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens — Imprint palette, theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: position 1 (#009E73) fills the band, position 3 (#4467A3) draws the central line
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
SUBSTRATE = "Substrate concentration (mM)"  # role: x
LOWER = "Lower bound (µmol/min)"  # role: y_lower
UPPER = "Upper bound (µmol/min)"  # role: y_upper
RATE = "Reaction rate (µmol/min)"  # role: y_center

# Data: replace this block with your own table, for example df = pd.read_csv("assay.csv")
# Enzyme kinetics: Michaelis-Menten saturation curve, mean and 95 % interval of 150 replicate assays
rng = np.random.default_rng(42)
n_replicates = 150
substrate = np.linspace(0.2, 10, 60)
v_max, k_m = 95.0, 2.2
true_rate = v_max * substrate / (k_m + substrate)
runs = true_rate * rng.lognormal(mean=0, sigma=0.12, size=(n_replicates, len(substrate)))
df = pd.DataFrame(
    {
        SUBSTRATE: substrate,
        LOWER: np.percentile(runs, 2.5, axis=0),
        UPPER: np.percentile(runs, 97.5, axis=0),
        RATE: runs.mean(axis=0),
    }
)

# Plot: reads only df and the constants above
sns.set_context("notebook", font_scale=1.0)
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
        "grid.alpha": 0.15,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)

ax.fill_between(
    df[SUBSTRATE],
    df[LOWER],
    df[UPPER],
    color=IMPRINT_PALETTE[0],
    alpha=0.25,
    linewidth=0,
    label="95% interval across replicates",
)
sns.lineplot(data=df, x=SUBSTRATE, y=RATE, color=IMPRINT_PALETTE[2], linewidth=2.5, zorder=10, label="Mean rate", ax=ax)

ax.set_title("band-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel(SUBSTRATE, fontsize=10, color=INK)
ax.set_ylabel(RATE, fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8)

sns.despine(ax=ax)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.6, color=INK)
ax.legend(fontsize=8, loc="lower right", framealpha=0.9, facecolor=ELEVATED_BG, edgecolor=INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
