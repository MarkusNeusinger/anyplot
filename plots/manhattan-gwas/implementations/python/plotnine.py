""" pyplots.ai
manhattan-gwas: Manhattan Plot for GWAS
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_text,
    geom_hline,
    geom_point,
    ggplot,
    labs,
    scale_color_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data - Simulated GWAS results with significant peaks
np.random.seed(42)

# Chromosome sizes (approximate in Mb, scaled for visualization)
chr_sizes = {
    "1": 249,
    "2": 243,
    "3": 198,
    "4": 191,
    "5": 182,
    "6": 171,
    "7": 159,
    "8": 145,
    "9": 138,
    "10": 134,
    "11": 135,
    "12": 133,
    "13": 115,
    "14": 107,
    "15": 102,
    "16": 90,
    "17": 83,
    "18": 80,
    "19": 59,
    "20": 64,
    "21": 47,
    "22": 51,
}

# Generate SNPs per chromosome (proportional to size)
chromosomes = list(chr_sizes.keys())
snp_data = []

# Cumulative positions for x-axis
cumulative_offset = 0
chr_offsets = {}
chr_midpoints = {}

for chrom in chromosomes:
    chr_offsets[chrom] = cumulative_offset
    size = chr_sizes[chrom]
    n_snps = int(size * 40)  # ~40 SNPs per Mb = ~8000 total

    # Generate positions
    positions = np.sort(np.random.uniform(0, size * 1e6, n_snps))

    # Generate p-values (mostly non-significant, with some peaks)
    p_values = np.random.uniform(0.001, 1, n_snps)

    # Add significant peaks on some chromosomes
    if chrom in ["2", "6", "11", "17"]:
        # Add 20-40 highly significant SNPs
        n_sig = np.random.randint(20, 40)
        peak_idx = np.random.choice(n_snps, n_sig, replace=False)
        p_values[peak_idx] = 10 ** np.random.uniform(-10, -7.3, n_sig)

    # Add some suggestive signals on other chromosomes
    if chrom in ["4", "9", "15", "20"]:
        n_sug = np.random.randint(10, 20)
        sug_idx = np.random.choice(n_snps, n_sug, replace=False)
        p_values[sug_idx] = 10 ** np.random.uniform(-7, -5, n_sug)

    # Calculate cumulative position
    cumulative_positions = positions + cumulative_offset

    chr_midpoints[chrom] = cumulative_offset + (size * 1e6) / 2

    for i in range(n_snps):
        snp_data.append(
            {
                "chromosome": chrom,
                "position": positions[i],
                "cumulative_pos": cumulative_positions[i],
                "p_value": p_values[i],
            }
        )

    cumulative_offset += size * 1e6

# Create DataFrame
df = pd.DataFrame(snp_data)

# Calculate -log10(p-value)
df["neg_log_p"] = -np.log10(df["p_value"])

# Assign alternating colors based on chromosome
chr_order = {c: i for i, c in enumerate(chromosomes)}
df["chr_num"] = df["chromosome"].map(chr_order)
df["color_group"] = df["chr_num"].apply(lambda x: "odd" if x % 2 == 0 else "even")

# Threshold lines
genome_wide_threshold = -np.log10(5e-8)  # ~7.3
suggestive_threshold = -np.log10(1e-5)  # 5

# Identify top SNPs for potential labeling (above genome-wide significance)
df["significant"] = df["neg_log_p"] > genome_wide_threshold

# Create chromosome tick positions and labels
chr_ticks = [chr_midpoints[c] / 1e6 for c in chromosomes]  # Convert to Mb for display
chr_labels = chromosomes

# Scale positions to Mb for cleaner axis
df["cumulative_pos_mb"] = df["cumulative_pos"] / 1e6

# Plot
plot = (
    ggplot(df, aes(x="cumulative_pos_mb", y="neg_log_p", color="color_group"))
    + geom_point(size=1.2, alpha=0.7, show_legend=False)
    + geom_hline(yintercept=genome_wide_threshold, linetype="dashed", color="#E31A1C", size=1)
    + geom_hline(yintercept=suggestive_threshold, linetype="dotted", color="#FF7F00", size=0.8)
    + scale_color_manual(values={"odd": "#306998", "even": "#636363"})
    + scale_x_continuous(breaks=chr_ticks, labels=chr_labels)
    + scale_y_continuous(limits=(0, max(df["neg_log_p"]) * 1.05))
    + labs(x="Chromosome", y="-log₁₀(p-value)", title="manhattan-gwas · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, ha="center"),
        axis_title_x=element_text(size=20),
        axis_title_y=element_text(size=20),
        axis_text_x=element_text(size=12),
        axis_text_y=element_text(size=16),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
    )
)

# Save
plot.save("plot.png", dpi=300, width=16, height=9)
