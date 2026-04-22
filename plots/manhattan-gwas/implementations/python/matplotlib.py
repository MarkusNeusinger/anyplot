""" pyplots.ai
manhattan-gwas: Manhattan Plot for GWAS
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-31
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Data - Simulate GWAS results for 22 chromosomes
np.random.seed(42)

# Define chromosome sizes (approximate in Mb, scaled down for simulation)
chrom_sizes = {
    1: 249,
    2: 243,
    3: 198,
    4: 191,
    5: 182,
    6: 171,
    7: 159,
    8: 146,
    9: 141,
    10: 136,
    11: 135,
    12: 134,
    13: 115,
    14: 107,
    15: 103,
    16: 90,
    17: 81,
    18: 78,
    19: 59,
    20: 63,
    21: 48,
    22: 51,
}

# Generate SNPs for each chromosome
chromosomes = []
positions = []
p_values = []

for chrom, size in chrom_sizes.items():
    n_snps = int(size * 40)  # ~40 SNPs per Mb
    chrom_positions = np.sort(np.random.randint(1, size * 1_000_000, n_snps))

    # Generate p-values (mostly non-significant, with some significant peaks)
    chrom_pvals = np.random.uniform(0, 1, n_snps)

    # Add some significant SNPs in certain chromosomes (simulating real signals)
    if chrom in [2, 6, 11, 16]:
        peak_idx = np.random.choice(n_snps, size=np.random.randint(3, 8), replace=False)
        chrom_pvals[peak_idx] = 10 ** (-np.random.uniform(8, 15, len(peak_idx)))

    # Add suggestive hits in more chromosomes
    if chrom in [1, 3, 8, 12, 19]:
        suggestive_idx = np.random.choice(n_snps, size=np.random.randint(2, 5), replace=False)
        chrom_pvals[suggestive_idx] = 10 ** (-np.random.uniform(5, 7.5, len(suggestive_idx)))

    chromosomes.extend([chrom] * n_snps)
    positions.extend(chrom_positions)
    p_values.extend(chrom_pvals)

# Create DataFrame
df = pd.DataFrame({"chromosome": chromosomes, "position": positions, "p_value": p_values})

# Calculate -log10(p-value)
df["-log10p"] = -np.log10(df["p_value"])

# Calculate cumulative position for x-axis
df["chrom_num"] = df["chromosome"]
df = df.sort_values(["chrom_num", "position"])

# Add cumulative position offset
cumulative_offset = 0
chrom_centers = {}
for chrom in sorted(df["chrom_num"].unique()):
    chrom_mask = df["chrom_num"] == chrom
    df.loc[chrom_mask, "cumulative_pos"] = df.loc[chrom_mask, "position"] + cumulative_offset
    chrom_centers[chrom] = cumulative_offset + df.loc[chrom_mask, "position"].median()
    cumulative_offset += df.loc[chrom_mask, "position"].max() + 10_000_000  # Gap between chromosomes

# Define thresholds
genome_wide_threshold = -np.log10(5e-8)  # ~7.3
suggestive_threshold = -np.log10(1e-5)  # 5

# Define colors
colors = ["#306998", "#6699CC"]  # Python Blue and lighter blue for alternating

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Plot points by chromosome with alternating colors
for i, chrom in enumerate(sorted(df["chrom_num"].unique())):
    chrom_data = df[df["chrom_num"] == chrom]
    color = colors[i % 2]

    # Smaller markers for dense data, slightly larger for significant hits
    significant_mask = chrom_data["-log10p"] >= genome_wide_threshold
    regular_data = chrom_data[~significant_mask]
    significant_data = chrom_data[significant_mask]

    # Plot regular points
    ax.scatter(
        regular_data["cumulative_pos"],
        regular_data["-log10p"],
        c=color,
        s=15,
        alpha=0.6,
        edgecolors="none",
        rasterized=True,
    )

    # Plot significant points with emphasis
    if len(significant_data) > 0:
        ax.scatter(
            significant_data["cumulative_pos"],
            significant_data["-log10p"],
            c="#E74C3C",  # Red for significant hits
            s=50,
            alpha=0.9,
            edgecolors="white",
            linewidths=0.5,
            zorder=5,
            rasterized=True,
        )

# Add threshold lines
ax.axhline(
    y=genome_wide_threshold,
    color="#E74C3C",
    linestyle="--",
    linewidth=2,
    label="Genome-wide significance (p < 5×10⁻⁸)",
    alpha=0.8,
)
ax.axhline(
    y=suggestive_threshold,
    color="#FFD43B",
    linestyle="--",
    linewidth=2,
    label="Suggestive threshold (p < 1×10⁻⁵)",
    alpha=0.8,
)

# Set x-axis with chromosome labels
ax.set_xticks([chrom_centers[c] for c in sorted(chrom_centers.keys())])
ax.set_xticklabels([str(c) for c in sorted(chrom_centers.keys())], fontsize=14)
ax.set_xlim(0, df["cumulative_pos"].max() * 1.01)

# Set y-axis
ax.set_ylim(0, df["-log10p"].max() * 1.1)

# Labels and styling
ax.set_xlabel("Chromosome", fontsize=20)
ax.set_ylabel("-log₁₀(p-value)", fontsize=20)
ax.set_title("manhattan-gwas · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="y", labelsize=16)
ax.tick_params(axis="x", labelsize=14)

# Legend
ax.legend(fontsize=14, loc="upper right", framealpha=0.9)

# Remove top and right spines for cleaner look
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
