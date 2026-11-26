"""anyplot.ai
histogram-basic: Basic Histogram
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-05-28
"""

import os as _os
import sys


# Prevent the local matplotlib.py in this directory from shadowing the package
_script_dir = _os.path.realpath(_os.path.dirname(_os.path.abspath(__file__)))
sys.path[:] = [p for p in sys.path if _os.path.realpath(p if p else ".") != _script_dir]
del _script_dir, _os

import os

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
import seaborn as sns


THEME = os.getenv("ANYPLOT_THEME", "light")

PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]

# Columns: set these to your table's column names
ORDER_AMOUNT = "Order Amount (USD)"  # role: values
COUNT_LABEL = "Number of Orders"  # label of the frequency axis

# Data: replace this block with your own table, for example df = pd.read_csv("orders.csv")
# E-commerce order amounts: two spending segments give a skewed, two-peaked outline.
rng = np.random.default_rng(42)
amounts = np.concatenate([rng.lognormal(np.log(45), 0.3, 400), rng.lognormal(np.log(350), 0.35, 350)])
df = pd.DataFrame({ORDER_AMOUNT: amounts[(amounts > 5) & (amounts <= 1200)]})

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
        "grid.alpha": 0.15,
    },
)

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)

n_bins = int(np.clip(1.5 * np.sqrt(len(df)), 10, 60))
sns.histplot(
    data=df, x=ORDER_AMOUNT, bins=n_bins, color=BRAND, edgecolor=PAGE_BG, linewidth=0.5, alpha=1.0, stat="count", ax=ax
)

# Style
ax.set_title("histogram-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=8)
ax.set_xlabel(ORDER_AMOUNT, fontsize=10, color=INK, labelpad=6)
ax.set_ylabel(COUNT_LABEL, fontsize=10, color=INK, labelpad=6)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"${int(x):,}"))
ax.set_xlim(0, df[ORDER_AMOUNT].max() * 1.03)
ax.set_ylim(bottom=0)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.6, color=INK)
ax.xaxis.grid(False)

fig.subplots_adjust(left=0.09, right=0.97, top=0.90, bottom=0.13)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
plt.close()
