"""anyplot.ai
frequency-polygon-basic: Frequency Polygon for Distribution Comparison
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-05-17
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

# Imprint palette, canonical order, first series always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

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

# Constants
N_BINS = 20  # number of shared bins across all groups
MARKERS = ["o", "s", "^", "D", "v", "P", "X", "*"]  # one marker per group, in palette order

# Columns: set these to your table's column names
COMMUTE = "Commute time (min)"  # role: values
MODE = "Transport mode"  # role: group

# Data: replace this block with your own table, for example df = pd.read_csv("commutes.csv")
rng = np.random.default_rng(42)
n_trips = 300
cycling = rng.normal(loc=22, scale=6, size=n_trips)
bus = rng.lognormal(mean=np.log(36), sigma=0.35, size=n_trips)
train = np.concatenate(
    [
        rng.normal(loc=28, scale=5, size=int(n_trips * 0.65)),
        rng.normal(loc=58, scale=8, size=n_trips - int(n_trips * 0.65)),
    ]
)
df = pd.DataFrame(
    {
        COMMUTE: np.clip(np.concatenate([cycling, bus, train]), 2, None),
        MODE: ["Cycling"] * n_trips + ["Bus"] * n_trips + ["Train"] * n_trips,
    }
)

# Plot: reads only df and the constants above
# Shared bin edges so every polygon has its vertices at the same x positions
values = df[COMMUTE].dropna()
edges = np.histogram_bin_edges(values, bins=N_BINS)
centers = (edges[:-1] + edges[1:]) / 2
modes = list(df[MODE].unique())

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

for i, mode in enumerate(modes):
    counts, _ = np.histogram(df.loc[df[MODE] == mode, COMMUTE].dropna(), bins=edges)
    # Extend to zero at both ends so the polygon closes on the baseline
    poly = pd.DataFrame({COMMUTE: np.r_[edges[0], centers, edges[-1]], "Frequency": np.r_[0, counts, 0]})
    sns.lineplot(
        data=poly,
        x=COMMUTE,
        y="Frequency",
        ax=ax,
        color=IMPRINT_PALETTE[i],
        linewidth=2,
        marker=MARKERS[i],
        markersize=5,
        markevery=slice(1, -1),
        label=mode,
    )
    ax.fill_between(poly[COMMUTE], poly["Frequency"], alpha=0.15, color=IMPRINT_PALETTE[i])

# Style
ax.set_title("frequency-polygon-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel(COMMUTE, fontsize=10)
ax.set_ylabel("Frequency", fontsize=10)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.set_ylim(bottom=0)
sns.despine(ax=ax)
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)
ax.legend(title=MODE, fontsize=8, title_fontsize=9, loc="upper right", framealpha=0.95)

fig.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
