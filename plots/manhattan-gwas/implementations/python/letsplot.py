"""anyplot.ai
manhattan-gwas: Manhattan Plot for GWAS
Library: letsplot 4.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-15
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
RULE = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
GENOME_WIDE_P = 5e-8  # conventional genome-wide significance
SUGGESTIVE_P = 1e-5  # conventional suggestive threshold

# Columns: set these to your table's column names
CHROMOSOME = "Chromosome"  # role: chromosome
POSITION = "Position (bp)"  # role: position
P_VALUE = "p-value"  # role: p_value

# Data: replace this block with your own table, for example df = pd.read_csv("gwas.csv")
np.random.seed(42)
n_snps_per_chrom = 2000
frames = []
for i in range(22):
    chrom = str(i + 1)
    chrom_size = 250_000_000 - i * 5_000_000
    positions = np.sort(np.random.randint(1, chrom_size, n_snps_per_chrom))
    p_values = np.random.uniform(0, 1, n_snps_per_chrom)
    if chrom in ["2", "6", "11", "17"]:
        peak_idx = np.random.choice(n_snps_per_chrom, size=15, replace=False)
        p_values[peak_idx] = 10 ** (-np.random.uniform(6, 12, 15))
    if chrom in ["1", "5", "8", "14", "19"]:
        suggestive_idx = np.random.choice(n_snps_per_chrom, size=10, replace=False)
        p_values[suggestive_idx] = 10 ** (-np.random.uniform(4.5, 7, 10))
    frames.append(pd.DataFrame({CHROMOSOME: chrom, POSITION: positions, P_VALUE: p_values}))
df = pd.concat(frames, ignore_index=True)

# Plot: reads only df and the constants above
NEG_LOG_P = f"-log₁₀({P_VALUE})"
df[NEG_LOG_P] = -np.log10(df[P_VALUE])

# Lay chromosomes end to end, in the order they appear in the data
chromosomes = list(dict.fromkeys(df[CHROMOSOME]))
extent = df.groupby(CHROMOSOME, sort=False)[POSITION].max()
offset = extent.cumsum() - extent
df["cumulative"] = df[POSITION] + df[CHROMOSOME].map(offset)
tick_positions = (offset + extent / 2).tolist()

# Alternate colors between adjacent chromosomes
chrom_rank = df[CHROMOSOME].map({c: i for i, c in enumerate(chromosomes)})
df["band"] = np.where(chrom_rank % 2 == 0, IMPRINT_PALETTE[0], IMPRINT_PALETTE[1])

genome_wide_threshold = -np.log10(GENOME_WIDE_P)
suggestive_threshold = -np.log10(SUGGESTIVE_P)
significant = df[df[NEG_LOG_P] >= genome_wide_threshold]

plot = (
    ggplot(df, aes(x="cumulative", y=NEG_LOG_P, color="band"))
    + geom_point(size=1.0, alpha=0.7)
    + scale_color_identity()
    + geom_point(
        data=significant, mapping=aes(x="cumulative", y=NEG_LOG_P), color=IMPRINT_PALETTE[4], size=1.8, alpha=0.9
    )
    + geom_hline(yintercept=genome_wide_threshold, linetype="dashed", color=IMPRINT_PALETTE[4], size=0.6)
    + geom_hline(yintercept=suggestive_threshold, linetype="dotted", color=INK_MUTED, size=0.5)
    + labs(title="manhattan-gwas · python · letsplot · anyplot.ai", x=CHROMOSOME, y=NEG_LOG_P)
    + scale_x_continuous(breaks=tick_positions, labels=chromosomes)
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major_y=element_line(color=RULE, size=0.3),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        plot_title=element_text(size=16, face="bold", color=INK),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.4),
    )
    + ggsize(800, 450)
)

ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
