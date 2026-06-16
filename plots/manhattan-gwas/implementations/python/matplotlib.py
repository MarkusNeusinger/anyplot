""" anyplot.ai
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
BRAND = "#009E73"

# Okabe-Ito palette for chromosome alternation
CHROM_COLORS = ["#009E73", "#C475FD"]  # Brand green and vermillion, alternating

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
    n_snps = int(size * 40)
    chrom_positions = np.sort(np.random.randint(1, size * 1_000_000, n_snps))

    chrom_pvals = np.random.uniform(0, 1, n_snps)

    # Add some significant SNPs in certain chromosomes
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
df = df.sort_values(["chrom_num", "position"]).reset_index(drop=True)

# Add cumulative position offset
chrom_centers = {}
cumulative_offset = 0
for chrom in sorted(df["chrom_num"].unique()):
    chrom_mask = df["chrom_num"] == chrom
    chrom_data = df.loc[chrom_mask].copy()
    chrom_positions = chrom_data["position"].values + cumulative_offset
    df.loc[chrom_mask, "cumulative_pos"] = chrom_positions
    chrom_centers[chrom] = cumulative_offset + chrom_data["position"].median()
    cumulative_offset += chrom_data["position"].max() + 10_000_000

# Define thresholds
genome_wide_threshold = -np.log10(5e-8)
suggestive_threshold = -np.log10(1e-5)

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Plot points by chromosome with alternating Okabe-Ito colors
for i, chrom in enumerate(sorted(df["chrom_num"].unique())):
    chrom_data = df[df["chrom_num"] == chrom]
    color = CHROM_COLORS[i % 2]

    # Smaller markers for dense data
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

    # Plot significant points with emphasis (using brand color)
    if len(significant_data) > 0:
        ax.scatter(
            significant_data["cumulative_pos"],
            significant_data["-log10p"],
            c=BRAND,
            s=50,
            alpha=0.9,
            edgecolors=INK_SOFT,
            linewidths=0.5,
            zorder=5,
            rasterized=True,
        )

# Add threshold lines
ax.axhline(
    y=genome_wide_threshold,
    color=INK_SOFT,
    linestyle="--",
    linewidth=2,
    label="Genome-wide significance (p < 5×10⁻⁸)",
    alpha=0.6,
)
ax.axhline(
    y=suggestive_threshold,
    color=INK_SOFT,
    linestyle=":",
    linewidth=2,
    label="Suggestive threshold (p < 1×10⁻⁵)",
    alpha=0.4,
)

# Set x-axis with chromosome labels
ax.set_xticks([chrom_centers[c] for c in sorted(chrom_centers.keys())])
ax.set_xticklabels([str(c) for c in sorted(chrom_centers.keys())], fontsize=16)
ax.set_xlim(0, df["cumulative_pos"].max() * 1.01)

# Set y-axis
ax.set_ylim(0, df["-log10p"].max() * 1.1)

# Style
ax.set_xlabel("Chromosome", fontsize=20, color=INK)
ax.set_ylabel("-log₁₀(p-value)", fontsize=20, color=INK)
ax.set_title("manhattan-gwas · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="y", labelsize=16, colors=INK_SOFT, labelcolor=INK_SOFT)
ax.tick_params(axis="x", labelsize=16, colors=INK_SOFT, labelcolor=INK_SOFT)

# Spine styling
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Legend
leg = ax.legend(fontsize=16, loc="upper right", frameon=True)
if leg:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    for text in leg.get_texts():
        text.set_color(INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
