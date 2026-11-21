""" anyplot.ai
manhattan-gwas: Manhattan Plot for GWAS
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 85/100 | Updated: 2026-11-21
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

# Imprint palette: adjacent chromosomes alternate between the first two positions
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
GENOME_WIDE = 7.3  # -log10(5e-8), the conventional genome-wide significance line
SUGGESTIVE = 5.0  # -log10(1e-5)

# Columns: set these to your table's column names
CHROMOSOME = "Chromosome"  # role: chromosome
POSITION = "Position (bp)"  # role: position
P_VALUE = "p-value"  # role: p_value

# Data: replace this block with your own table, for example df = pd.read_csv("gwas.csv")
np.random.seed(42)
chromosomes = [str(i) for i in range(1, 23)]
chrom_sizes = [250, 243, 198, 190, 182, 171, 159, 145, 138, 133, 135, 133, 114, 107, 102, 90, 83, 80, 59, 64, 47, 51]

frames = []
for chrom, size in zip(chromosomes, chrom_sizes, strict=True):
    n_snps = int(size * 40)  # ~40 SNPs per Mb
    positions = np.sort(np.random.randint(0, size * 1_000_000, n_snps))
    p_values = np.random.beta(1, 1, n_snps)

    # Association peaks on three chromosomes
    if chrom == "6":
        peak = (positions > 25_000_000) & (positions < 35_000_000)
        p_values[peak] = 10 ** (-np.random.uniform(7, 12, peak.sum()))
    elif chrom == "11":
        peak = (positions > 60_000_000) & (positions < 70_000_000)
        p_values[peak] = 10 ** (-np.random.uniform(6, 9, peak.sum()))
    elif chrom == "2":
        peak = (positions > 100_000_000) & (positions < 110_000_000)
        p_values[peak] = 10 ** (-np.random.uniform(5.5, 8, peak.sum()))

    frames.append(pd.DataFrame({CHROMOSOME: chrom, POSITION: positions, P_VALUE: p_values}))
df = pd.concat(frames, ignore_index=True)

# Plot: reads only df and the constants above
order = list(dict.fromkeys(df[CHROMOSOME]))
extent = df.groupby(CHROMOSOME, sort=False)[POSITION].max().reindex(order).astype(float)
offset = extent.cumsum().shift(fill_value=0)
centers = offset + extent / 2

plot_df = df.assign(
    cumulative=df[POSITION] + df[CHROMOSOME].map(offset),
    neg_log_p=-np.log10(df[P_VALUE]),
    parity=df[CHROMOSOME].map({c: i % 2 for i, c in enumerate(order)}),
)
significant = plot_df[plot_df["neg_log_p"] > GENOME_WIDE]

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
sns.scatterplot(
    data=plot_df,
    x="cumulative",
    y="neg_log_p",
    hue="parity",
    palette=IMPRINT_PALETTE[: plot_df["parity"].nunique()],
    s=4,
    alpha=0.7,
    linewidth=0,
    legend=False,
    rasterized=True,
    ax=ax,
)

# Variants above the genome-wide line, marked with a larger ink-edged point
ax.scatter(
    significant["cumulative"],
    significant["neg_log_p"],
    color=IMPRINT_PALETTE[0],
    s=16,
    alpha=0.9,
    edgecolor=INK,
    linewidth=0.4,
    zorder=5,
    label=f"Significant variants (n = {len(significant)})",
)

ax.axhline(GENOME_WIDE, color=INK_SOFT, linestyle="--", linewidth=1.2, label="Genome-wide significance (p < 5×10⁻⁸)")
ax.axhline(SUGGESTIVE, color=INK_SOFT, linestyle=":", linewidth=1.0, alpha=0.8, label="Suggestive (p < 1×10⁻⁵)")

# Labels of crowded small chromosomes alternate onto a second line so they stay readable
crowded = (centers.diff() < extent.sum() * 0.03).to_numpy()
labels = ["\n" + c if tight and i % 2 else c for i, (c, tight) in enumerate(zip(order, crowded, strict=True))]
ax.set_xticks(centers.to_numpy(), labels)
ax.set_xlim(0, extent.sum())
ax.set_ylim(0, plot_df["neg_log_p"].max() * 1.05)
ax.set_xlabel(CHROMOSOME, fontsize=10)
ax.set_ylabel("-log₁₀(p-value)", fontsize=10)
ax.set_title("manhattan-gwas · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="x", labelsize=7)
ax.tick_params(axis="y", labelsize=8)
ax.yaxis.grid(True, linewidth=0.5)
ax.xaxis.grid(False)
sns.despine(ax=ax)
ax.legend(loc="upper right", fontsize=8, framealpha=0.95)

fig.subplots_adjust(left=0.08, right=0.97, top=0.9, bottom=0.17)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
