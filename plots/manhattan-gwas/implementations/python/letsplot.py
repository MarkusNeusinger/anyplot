""" pyplots.ai
manhattan-gwas: Manhattan Plot for GWAS
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-31
"""

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Set seed for reproducibility
np.random.seed(42)

# Generate simulated GWAS data
n_snps_per_chrom = 2000
chromosomes = [str(i) for i in range(1, 23)]

data = []
cumulative_pos = 0
chrom_centers = {}

for i, chrom in enumerate(chromosomes):
    # Random positions within chromosome (scaled by chromosome "size")
    chrom_size = 250_000_000 - i * 5_000_000  # Varying chromosome sizes
    positions = np.sort(np.random.randint(1, chrom_size, n_snps_per_chrom))

    # Generate p-values - mostly non-significant with some peaks
    p_values = np.random.uniform(0, 1, n_snps_per_chrom)

    # Add some significant peaks (simulate real GWAS signals)
    if chrom in ["2", "6", "11", "17"]:
        peak_idx = np.random.choice(n_snps_per_chrom, size=15, replace=False)
        p_values[peak_idx] = 10 ** (-np.random.uniform(6, 12, 15))

    # Add suggestive signals to more chromosomes
    if chrom in ["1", "5", "8", "14", "19"]:
        suggestive_idx = np.random.choice(n_snps_per_chrom, size=10, replace=False)
        p_values[suggestive_idx] = 10 ** (-np.random.uniform(4.5, 7, 10))

    # Calculate cumulative position for x-axis
    cumulative_positions = positions + cumulative_pos

    # Store chromosome center for labeling
    chrom_centers[chrom] = cumulative_pos + chrom_size / 2

    for pos, cum_pos, pval in zip(positions, cumulative_positions, p_values):
        data.append(
            {
                "chromosome": chrom,
                "position": pos,
                "cumulative_pos": cum_pos,
                "p_value": pval,
                "neg_log10_p": -np.log10(pval),
            }
        )

    cumulative_pos += chrom_size

df = pd.DataFrame(data)

# Create chromosome index for coloring (alternating pattern)
df["chrom_idx"] = df["chromosome"].astype(int) % 2

# Assign colors based on alternating pattern
df["color_group"] = df["chrom_idx"].map({0: "even", 1: "odd"})

# Significance thresholds
genome_wide_threshold = -np.log10(5e-8)  # ~7.3
suggestive_threshold = -np.log10(1e-5)  # 5

# Mark significant SNPs
df["significant"] = df["neg_log10_p"] >= genome_wide_threshold

# Create x-axis tick positions and labels
tick_positions = [chrom_centers[c] for c in chromosomes]

# Create the Manhattan plot
plot = (
    ggplot(df, aes(x="cumulative_pos", y="neg_log10_p", color="color_group"))
    + geom_point(size=1.5, alpha=0.7)
    + scale_color_manual(values=["#306998", "#7A9BBD"], guide="none")
    # Highlight significant points
    + geom_point(
        data=df[df["significant"]], mapping=aes(x="cumulative_pos", y="neg_log10_p"), color="#DC2626", size=3, alpha=0.9
    )
    # Genome-wide significance threshold line
    + geom_hline(yintercept=genome_wide_threshold, linetype="dashed", color="#DC2626", size=0.8)
    # Suggestive threshold line
    + geom_hline(yintercept=suggestive_threshold, linetype="dotted", color="#666666", size=0.6)
    + labs(title="manhattan-gwas · letsplot · pyplots.ai", x="Chromosome", y="-log₁₀(p-value)")
    + scale_x_continuous(breaks=tick_positions, labels=chromosomes)
    + theme_minimal()
    + theme(
        plot_title=element_text(size=28, face="bold"),
        axis_title_x=element_text(size=22),
        axis_title_y=element_text(size=22),
        axis_text_x=element_text(size=14),
        axis_text_y=element_text(size=16),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x for 4800x2700)
ggsave(plot, "plot.png", path=".", scale=3)

# Save interactive HTML version
ggsave(plot, "plot.html", path=".")
