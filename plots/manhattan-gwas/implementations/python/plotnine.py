"""anyplot.ai
manhattan-gwas: Manhattan Plot for GWAS
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 84/100 | Updated: 2026-05-15
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
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


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
GENOME_WIDE_P = 5e-8  # conventional genome-wide significance threshold
SUGGESTIVE_P = 1e-5  # optional suggestive threshold

# Columns: set these to your table's column names
CHROMOSOME = "Chromosome"  # role: chromosome
POSITION = "Position (bp)"  # role: position
P_VALUE = "p-value"  # role: p_value

# Data: replace this block with your own table, for example df = pd.read_csv("gwas.csv")
rng = np.random.default_rng(123)
chr_sizes_mb = [249, 243, 198, 191, 182, 171, 159, 145, 138, 134, 135, 133, 115, 107, 102, 90, 83, 80, 59, 64, 47, 51]
significant_chr = {1, 7, 9, 18}  # chromosomes carrying genome-wide significant peaks
suggestive_chr = {5, 12, 14, 19}  # chromosomes carrying suggestive signals
parts = []
for number, size_mb in enumerate(chr_sizes_mb, start=1):
    n_snps = size_mb * 40  # ~40 SNPs per Mb
    positions = np.sort(rng.uniform(0, size_mb * 1e6, n_snps))
    p_values = rng.uniform(0.001, 1, n_snps)
    if number in significant_chr:
        n_hit = rng.integers(20, 40)
        hit = rng.choice(n_snps, n_hit, replace=False)
        p_values[hit] = 10 ** rng.uniform(-10, -7.3, n_hit)
    if number in suggestive_chr:
        n_hit = rng.integers(10, 20)
        hit = rng.choice(n_snps, n_hit, replace=False)
        p_values[hit] = 10 ** rng.uniform(-7, -5, n_hit)
    parts.append(pd.DataFrame({CHROMOSOME: str(number), POSITION: positions, P_VALUE: p_values}))
df = pd.concat(parts, ignore_index=True)

# Plot: reads only df and the constants above
chromosomes = df[CHROMOSOME].unique().tolist()
extent = df.groupby(CHROMOSOME, sort=False)[POSITION].max()
offsets = extent.cumsum().shift(fill_value=0)  # start of each chromosome on the shared axis
midpoints = (offsets + extent / 2) / 1e6

df["cumulative_mb"] = (df[POSITION] + df[CHROMOSOME].map(offsets)) / 1e6
df["neg_log_p"] = -np.log10(df[P_VALUE])
df["band"] = df[CHROMOSOME].map({c: i % 2 for i, c in enumerate(chromosomes)}).astype(str)

genome_wide = -np.log10(GENOME_WIDE_P)
suggestive = -np.log10(SUGGESTIVE_P)

anyplot_theme = theme(
    figure_size=(8, 4.5),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
    panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
    panel_border=element_rect(color=INK_SOFT, fill=None),
    axis_title=element_text(color=INK, size=10),
    axis_text=element_text(color=INK_SOFT, size=8),
    axis_text_x=element_text(size=6),
    axis_line=element_line(color=INK_SOFT, size=0.5),
    plot_title=element_text(color=INK, size=12, hjust=0.5),
    legend_position="none",
)

plot = (
    ggplot(df, aes(x="cumulative_mb", y="neg_log_p", color="band"))
    + geom_point(size=1.2, alpha=0.7, stroke=0)
    + geom_hline(yintercept=genome_wide, linetype="dashed", color=IMPRINT_PALETTE[4], size=0.6)
    + geom_hline(yintercept=suggestive, linetype="dotted", color=INK_SOFT, size=0.6)
    + scale_color_manual(values=IMPRINT_PALETTE, limits=["0", "1"])
    + scale_x_continuous(breaks=midpoints.tolist(), labels=chromosomes, expand=(0.01, 0))
    + scale_y_continuous(limits=(0, df["neg_log_p"].max() * 1.05))
    + labs(x=CHROMOSOME, y="-log₁₀(p-value)", title="manhattan-gwas · python · plotnine · anyplot.ai")
    + theme_minimal()
    + anyplot_theme
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
