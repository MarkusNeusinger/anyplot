""" anyplot.ai
manhattan-gwas: Manhattan Plot for GWAS
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-15
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

# Okabe-Ito palette for alternating chromosomes
OKABE_ITO_1 = "#009E73"  # bluish green (brand)
OKABE_ITO_2 = "#C475FD"  # vermillion

# Data - Simulate GWAS data with realistic structure
np.random.seed(42)

# Define chromosomes with approximate sizes (in Mb)
chromosomes = [str(i) for i in range(1, 23)]
chrom_sizes = [250, 243, 198, 190, 182, 171, 159, 145, 138, 133, 135, 133, 114, 107, 102, 90, 83, 80, 59, 64, 47, 51]

# Generate SNPs for each chromosome
data = []
cumulative_pos = 0
chrom_centers = {}
chrom_boundaries = [0]

for chrom, size in zip(chromosomes, chrom_sizes, strict=True):
    # Number of SNPs proportional to chromosome size
    n_snps = int(size * 40)  # ~40 SNPs per Mb, total ~10k SNPs

    # Random positions along chromosome
    positions = np.sort(np.random.randint(0, size * 1_000_000, n_snps))

    # Generate p-values - mostly non-significant with some peaks
    # Use beta distribution to get realistic p-value distribution
    p_values = np.random.beta(1, 1, n_snps)

    # Add significant peaks on specific chromosomes
    if chrom == "6":  # Major peak on chr6 (like MHC region)
        peak_region = (positions > 25_000_000) & (positions < 35_000_000)
        p_values[peak_region] = 10 ** (-np.random.uniform(7, 12, peak_region.sum()))
    elif chrom == "11":  # Moderate peak
        peak_region = (positions > 60_000_000) & (positions < 70_000_000)
        p_values[peak_region] = 10 ** (-np.random.uniform(6, 9, peak_region.sum()))
    elif chrom == "2":  # Smaller peak
        peak_region = (positions > 100_000_000) & (positions < 110_000_000)
        p_values[peak_region] = 10 ** (-np.random.uniform(5.5, 8, peak_region.sum()))

    # Calculate cumulative position
    cumulative_positions = positions + cumulative_pos

    # Store center for axis label
    chrom_centers[chrom] = cumulative_pos + (size * 1_000_000) / 2

    for pos, cum_pos, pval in zip(positions, cumulative_positions, p_values, strict=True):
        data.append(
            {
                "chromosome": chrom,
                "position": pos,
                "cumulative_position": cum_pos,
                "p_value": pval,
                "neg_log_p": -np.log10(pval),
            }
        )

    cumulative_pos += size * 1_000_000
    chrom_boundaries.append(cumulative_pos)

df = pd.DataFrame(data)

# Create alternating color groups for chromosomes
df["color_group"] = df["chromosome"].apply(lambda x: OKABE_ITO_1 if int(x) % 2 == 1 else OKABE_ITO_2)

# Configure theme-adaptive styling
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

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)

# Plot non-significant SNPs with alternating colors
for color in [OKABE_ITO_1, OKABE_ITO_2]:
    subset = df[df["color_group"] == color]
    ax.scatter(
        subset["cumulative_position"], subset["neg_log_p"], c=color, s=20, alpha=0.7, edgecolor="none", rasterized=True
    )

# Highlight significant SNPs (above genome-wide threshold)
significant = df[df["neg_log_p"] > 7.3]
if len(significant) > 0:
    ax.scatter(
        significant["cumulative_position"],
        significant["neg_log_p"],
        c=OKABE_ITO_1,
        s=60,
        alpha=0.9,
        edgecolor=INK,
        linewidth=0.8,
        zorder=5,
    )

# Genome-wide significance threshold
ax.axhline(y=7.3, color=INK_SOFT, linestyle="--", linewidth=2, alpha=0.6, label="Genome-wide significance (p < 5×10⁻⁸)")

# Suggestive threshold
ax.axhline(y=5, color=INK_SOFT, linestyle=":", linewidth=1.5, alpha=0.4, label="Suggestive (p < 1×10⁻⁵)")

# Set x-axis ticks at chromosome centers
ax.set_xticks([chrom_centers[c] for c in chromosomes])
ax.set_xticklabels(chromosomes, fontsize=16)

# Styling
ax.set_xlabel("Chromosome", fontsize=20, color=INK)
ax.set_ylabel("-log₁₀(p-value)", fontsize=20, color=INK)
ax.set_title("manhattan-gwas · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16)

# Set axis limits
ax.set_xlim(0, cumulative_pos)
ax.set_ylim(0, max(df["neg_log_p"]) * 1.05)

# Remove top and right spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

# Add legend
ax.legend(loc="upper right", fontsize=16, framealpha=0.95, edgecolor=INK_SOFT)

# Subtle grid on y-axis only
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8)
ax.xaxis.grid(False)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
