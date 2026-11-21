"""anyplot.ai
manhattan-gwas: Manhattan Plot for GWAS
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-15
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

# Imprint palette: position 1 is the brand green, positions 1 and 2 alternate across chromosomes
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]

# Constants
GENOME_WIDE_P = 5e-8  # conventional genome-wide significance threshold
SUGGESTIVE_P = 1e-5  # conventional suggestive threshold
CHROMOSOME_GAP = 10_000_000  # base pairs of empty space between neighbouring chromosomes

# Columns: set these to your table's column names
CHROMOSOME = "Chromosome"  # role: chromosome
POSITION = "Position (bp)"  # role: position
P_VALUE = "p-value"  # role: p_value

# Data: replace this block with your own table, for example df = pd.read_csv("gwas.csv")
np.random.seed(42)
chrom_sizes_mb = [249, 243, 198, 191, 182, 171, 159, 146, 141, 136, 135, 134, 115, 107, 103, 90, 81, 78, 59, 63, 48, 51]
chromosomes = []
positions = []
p_values = []
for chrom, size in enumerate(chrom_sizes_mb, start=1):
    n_snps = int(size * 40)
    chrom_positions = np.sort(np.random.randint(1, size * 1_000_000, n_snps))
    chrom_pvals = np.random.uniform(0, 1, n_snps)

    # Strong association peaks on a few chromosomes
    if chrom in [2, 6, 11, 16]:
        peak_idx = np.random.choice(n_snps, size=np.random.randint(3, 8), replace=False)
        chrom_pvals[peak_idx] = 10 ** (-np.random.uniform(8, 15, len(peak_idx)))

    # Suggestive hits on others
    if chrom in [1, 3, 8, 12, 19]:
        suggestive_idx = np.random.choice(n_snps, size=np.random.randint(2, 5), replace=False)
        chrom_pvals[suggestive_idx] = 10 ** (-np.random.uniform(5, 7.5, len(suggestive_idx)))

    chromosomes.extend([chrom] * n_snps)
    positions.extend(chrom_positions)
    p_values.extend(chrom_pvals)
df = pd.DataFrame({CHROMOSOME: chromosomes, POSITION: positions, P_VALUE: p_values})

# Plot: reads only df and the constants above
neg_log_p = -np.log10(df[P_VALUE])
genome_wide_threshold = -np.log10(GENOME_WIDE_P)
suggestive_threshold = -np.log10(SUGGESTIVE_P)

# Lay chromosomes end to end: each one starts after the previous one's last position plus a gap
chrom_end = df.groupby(CHROMOSOME, sort=False)[POSITION].max()
chrom_start = (chrom_end + CHROMOSOME_GAP).cumsum().shift(fill_value=0)
cumulative_pos = df[POSITION] + df[CHROMOSOME].map(chrom_start)
chrom_centers = chrom_start + df.groupby(CHROMOSOME, sort=False)[POSITION].median()
significant = neg_log_p >= genome_wide_threshold

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Alternating colors by chromosome order; points above the genome-wide line are emphasised
for i, chrom in enumerate(chrom_centers.index):
    rows = (df[CHROMOSOME] == chrom) & ~significant
    ax.scatter(cumulative_pos[rows], neg_log_p[rows], color=IMPRINT_PALETTE[i % 2], s=4, alpha=0.6, edgecolors="none")
ax.scatter(
    cumulative_pos[significant],
    neg_log_p[significant],
    color=BRAND,
    s=14,
    alpha=0.9,
    edgecolors=INK_SOFT,
    linewidths=0.3,
    zorder=5,
)

# Threshold lines
ax.axhline(
    genome_wide_threshold,
    color=INK_SOFT,
    linestyle="--",
    linewidth=1.2,
    alpha=0.6,
    label=f"Genome-wide significance (p < {GENOME_WIDE_P:.0e})",
)
ax.axhline(
    suggestive_threshold,
    color=INK_SOFT,
    linestyle=":",
    linewidth=1.2,
    alpha=0.5,
    label=f"Suggestive threshold (p < {SUGGESTIVE_P:.0e})",
)

# Style
title = "manhattan-gwas · python · matplotlib · anyplot.ai"
ax.set_title(title, fontsize=12, fontweight="medium", color=INK)
# Neighbouring labels closer than 3% of the axis span alternate onto a second row
tick_labels = []
lowered = False
for gap, chrom in zip(np.diff(chrom_centers.to_numpy(), prepend=-np.inf), chrom_centers.index, strict=True):
    lowered = gap < 0.03 * cumulative_pos.max() and not lowered
    tick_labels.append(("\n" if lowered else "") + str(chrom))
ax.set_xticks(chrom_centers.to_numpy(), tick_labels)
ax.set_xlim(0, cumulative_pos.max() * 1.01)
ax.set_ylim(0, neg_log_p.max() * 1.1)
ax.set_xlabel(CHROMOSOME, fontsize=10, color=INK)
ax.set_ylabel(f"-log₁₀({P_VALUE})", fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)

leg = ax.legend(fontsize=8, loc="upper right", frameon=True)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
