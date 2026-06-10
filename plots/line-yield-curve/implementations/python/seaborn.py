"""anyplot.ai
line-yield-curve: Yield Curve (Interest Rate Term Structure)
Library: seaborn | Python 3.13
Quality: pending | Created: 2026-06-10
"""

import os
import sys


# Prevent local files (matplotlib.py, etc.) from shadowing installed packages
_script_dir = os.path.dirname(os.path.abspath(__file__))
if _script_dir in sys.path:
    sys.path.remove(_script_dir)
if "" in sys.path:
    sys.path.remove("")
if "." in sys.path:
    sys.path.remove(".")

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens — Imprint palette (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint categorical palette — hybrid-v3 sort, first series always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
SEMANTIC_RED = "#AE3030"  # Imprint anchor — bad / loss / error

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

# Data — U.S. Treasury yield curves on three dates
maturities = ["1M", "3M", "6M", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"]
maturity_years = [1 / 12, 0.25, 0.5, 1, 2, 3, 5, 7, 10, 20, 30]

curves = {
    "2021-07-15 (Normal)": [0.05, 0.05, 0.06, 0.09, 0.25, 0.46, 0.83, 1.13, 1.34, 1.86, 1.99],
    "2023-07-15 (Inverted)": [5.28, 5.40, 5.47, 5.40, 4.87, 4.55, 4.18, 4.07, 3.98, 4.22, 4.05],
    "2024-09-15 (Flat)": [4.96, 4.92, 4.72, 4.25, 3.60, 3.48, 3.44, 3.52, 3.65, 4.03, 4.01],
}

rows = []
for date_label, yields in curves.items():
    for m_label, m_years, y_pct in zip(maturities, maturity_years, yields, strict=True):
        rows.append({"Date": date_label, "maturity": m_label, "maturity_years": m_years, "yield_pct": y_pct})
df = pd.DataFrame(rows)

# Canvas — 3200×1800 px landscape (figsize=(8, 4.5) × dpi=400)
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Plot
sns.lineplot(
    data=df,
    x="maturity_years",
    y="yield_pct",
    hue="Date",
    style="Date",
    markers=True,
    dashes=False,
    palette=IMPRINT_PALETTE[:3],
    linewidth=2.5,
    markersize=8,
    ax=ax,
)

# Shade 2Y–10Y inversion zone (Imprint semantic-red: loss / danger)
inv_yields = np.array(curves["2023-07-15 (Inverted)"])
idx_2y = maturity_years.index(2)
idx_10y = maturity_years.index(10)
yield_2y = inv_yields[idx_2y]
yield_10y = inv_yields[idx_10y]
if yield_2y > yield_10y:
    ax.fill_between([2, 10], yield_10y, yield_2y, alpha=0.10, color=SEMANTIC_RED, zorder=0)
    ax.text(6, (yield_2y + yield_10y) / 2, "2Y–10Y Inversion", fontsize=9, color=SEMANTIC_RED, ha="center", va="center")

# Style
title = "U.S. Treasury Yield Curves · line-yield-curve · python · seaborn · anyplot.ai"
n = len(title)
title_fontsize = max(8, round(12 * 67 / n)) if n > 67 else 12
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK)
ax.set_xlabel("Maturity", fontsize=10, color=INK)
ax.set_ylabel("Yield (%)", fontsize=10, color=INK)

ax.set_xscale("log")
ax.set_xticks(maturity_years)
ax.set_xticklabels(maturities, fontsize=8)
ax.xaxis.set_minor_locator(mticker.NullLocator())
ax.xaxis.set_minor_formatter(mticker.NullFormatter())
ax.tick_params(axis="y", labelsize=8)

ax.yaxis.grid(True, alpha=0.15, linewidth=0.8)

# Seaborn-idiomatic refinements
sns.despine(ax=ax)
handles, labels = ax.get_legend_handles_labels()
ax.legend(handles, labels, loc="center left", title="Date", fontsize=8, title_fontsize=9, frameon=False)

# Save — no bbox_inches='tight' (avoids canvas trimming from 3200×1800)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
