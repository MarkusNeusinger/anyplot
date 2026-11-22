""" anyplot.ai
boxen-basic: Basic Boxen Plot (Letter-Value Plot)
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 75/100 | Updated: 2026-11-22
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

# Imprint palette: all eight positions in canonical order (first series always #009E73)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Library setup
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

# Columns: set these to your table's column names
GENE = "Gene"  # role: category
EXPRESSION = "Expression Level (log2)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("expression.csv")
np.random.seed(42)
n_per_group = 4000
rows = []
for gene_name in ["TP53", "BRCA1", "MYC", "EGFR"]:
    if gene_name == "TP53":
        # Tumor suppressor - bimodal (wild-type vs mutant expression)
        draws = np.concatenate(
            [
                np.random.normal(loc=6.5, scale=0.8, size=int(n_per_group * 0.6)),
                np.random.normal(loc=2.0, scale=0.5, size=int(n_per_group * 0.4)),
            ]
        )
    elif gene_name == "BRCA1":
        # Breast cancer susceptibility - right-skewed, occasional high expression
        draws = np.concatenate(
            [
                np.random.exponential(scale=3.5, size=int(n_per_group * 0.85)),
                np.random.uniform(15, 25, size=int(n_per_group * 0.15)),
            ]
        )
    elif gene_name == "MYC":
        # Oncogene - highly variable, long tail
        draws = np.random.lognormal(mean=2.0, sigma=1.2, size=n_per_group)
    else:
        # Growth receptor - relatively symmetric with moderate spread
        draws = np.random.normal(loc=8.0, scale=2.0, size=n_per_group)
    # Ensure positive expression values
    draws = np.clip(draws, 0.1, None)
    rows.append(pd.DataFrame({GENE: gene_name, EXPRESSION: draws}))
df = pd.concat(rows, ignore_index=True)

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)

n_genes = df[GENE].nunique()
sns.boxenplot(
    data=df,
    x=GENE,
    y=EXPRESSION,
    hue=GENE,
    palette=IMPRINT_PALETTE[:n_genes],
    legend=False,
    width=0.6,
    linewidth=0.8,
    linecolor=INK_SOFT,
    flier_kws={"s": 6},
    ax=ax,
)

# Styling
ax.set_title("boxen-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=10)
ax.set_xlabel(GENE, fontsize=10, color=INK)
ax.set_ylabel(EXPRESSION, fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.yaxis.grid(True, alpha=0.10, linewidth=0.6, color=INK_SOFT)

# Remove top and right spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for spine in ["left", "bottom"]:
    ax.spines[spine].set_color(INK_SOFT)
    ax.spines[spine].set_linewidth(0.6)

# Legend explaining quantile levels
ax.text(
    0.5,
    -0.14,
    "Nested boxes represent letter values: the widest spans the quartiles, narrower ones the eighths, sixteenths, etc.",
    transform=ax.transAxes,
    ha="center",
    va="top",
    fontsize=7,
    color=INK_SOFT,
    style="italic",
)

fig.subplots_adjust(left=0.08, right=0.97, top=0.9, bottom=0.2)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
