""" pyplots.ai
manhattan-gwas: Manhattan Plot for GWAS
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-31
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


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
df["color_group"] = df["chromosome"].apply(lambda x: int(x) % 2)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Create custom palette - Python Blue and a muted gray
palette = {0: "#306998", 1: "#8B9DC3"}

# Plot points using seaborn scatterplot with hue for alternating colors
sns.scatterplot(
    data=df,
    x="cumulative_position",
    y="neg_log_p",
    hue="color_group",
    palette=palette,
    s=15,
    alpha=0.7,
    edgecolor="none",
    legend=False,
    ax=ax,
)

# Highlight significant SNPs (above genome-wide threshold)
significant = df[df["neg_log_p"] > 7.3]
if len(significant) > 0:
    ax.scatter(
        significant["cumulative_position"],
        significant["neg_log_p"],
        c="#FFD43B",  # Python Yellow for significant hits
        s=40,
        edgecolor="black",
        linewidth=0.5,
        zorder=5,
    )

# Genome-wide significance threshold
ax.axhline(y=7.3, color="#D62728", linestyle="--", linewidth=2, label="Genome-wide significance (p < 5×10⁻⁸)")

# Suggestive threshold
ax.axhline(y=5, color="#7F7F7F", linestyle=":", linewidth=1.5, label="Suggestive (p < 1×10⁻⁵)")

# Set x-axis ticks at chromosome centers
ax.set_xticks([chrom_centers[c] for c in chromosomes])
ax.set_xticklabels(chromosomes)

# Styling
ax.set_xlabel("Chromosome", fontsize=20)
ax.set_ylabel("-log₁₀(p-value)", fontsize=20)
ax.set_title("manhattan-gwas · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=14)
ax.tick_params(axis="x", labelsize=12)

# Set axis limits
ax.set_xlim(0, cumulative_pos)
ax.set_ylim(0, max(df["neg_log_p"]) * 1.05)

# Remove top and right spines for cleaner look
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Add legend
ax.legend(loc="upper right", fontsize=14, framealpha=0.9)

# Subtle grid on y-axis only
ax.yaxis.grid(True, alpha=0.3, linestyle="-")
ax.xaxis.grid(False)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
