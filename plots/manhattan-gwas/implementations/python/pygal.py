"""anyplot.ai
manhattan-gwas: Manhattan Plot for GWAS
Library: pygal 3.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-15
"""

import os

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
GENOME_WIDE_P = 5e-8  # conventional genome-wide significance threshold
SUGGESTIVE_P = 1e-5  # conventional suggestive threshold

# Columns: set these to your table's column names
CHROMOSOME = "Chromosome"  # role: chromosome
POSITION = "Position (Mb)"  # role: position
P_VALUE = "p-value"  # role: p_value

# Data: replace this block with your own table, for example df = pd.read_csv("gwas.csv")
rng = np.random.default_rng(42)
chrom_lengths = {
    "1": 249,
    "2": 243,
    "3": 198,
    "4": 191,
    "5": 182,
    "6": 171,
    "7": 159,
    "8": 146,
    "9": 141,
    "10": 136,
    "11": 135,
    "12": 134,
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
n_snps = 500
frames = []
for chrom, length in chrom_lengths.items():
    pvalues = rng.uniform(0, 1, n_snps)
    # Association peaks on three chromosomes
    if chrom in ("6", "11", "16"):
        hits = rng.choice(n_snps, rng.integers(3, 8), replace=False)
        pvalues[hits] = 10 ** (-rng.uniform(8, 15, len(hits)))
    # Suggestive signals everywhere
    suggestive = rng.choice(n_snps, rng.integers(5, 15), replace=False)
    pvalues[suggestive] = 10 ** (-rng.uniform(5, 8, len(suggestive)))
    frames.append(
        pd.DataFrame({CHROMOSOME: chrom, POSITION: np.sort(rng.uniform(0, length, n_snps)), P_VALUE: pvalues})
    )
df = pd.concat(frames, ignore_index=True)

# Plot: cumulative genome position, chromosomes laid end to end in data order
chroms = list(dict.fromkeys(df[CHROMOSOME]))
lengths = df.groupby(CHROMOSOME, sort=False)[POSITION].max().reindex(chroms)
offsets = lengths.cumsum().shift(fill_value=0)
genome_end = float(lengths.sum())
midpoints = (offsets + lengths / 2).tolist()

df["x"] = df[POSITION] + df[CHROMOSOME].map(offsets)
df["y"] = -np.log10(df[P_VALUE])
df["odd"] = df[CHROMOSOME].map({c: i % 2 == 0 for i, c in enumerate(chroms)})
gw_line = -np.log10(GENOME_WIDE_P)
sugg_line = -np.log10(SUGGESTIVE_P)
significant = df["y"] >= gw_line

# Style
title = "manhattan-gwas · python · pygal · anyplot.ai"
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT_PALETTE,
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=34,
    legend_font_size=36,
    value_font_size=36,
    stroke_width=4,
)


def chromosome_label(x_value):
    """Label of the chromosome whose midpoint is closest to x_value."""
    return chroms[int(np.argmin([abs(x_value - m) for m in midpoints]))]


chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title=title,
    x_title=CHROMOSOME,
    y_title="-log₁₀(p-value)",
    legend_at_bottom=True,
    legend_at_bottom_columns=5,
    legend_box_size=30,
    stroke=False,
    dots_size=3.5,
    show_x_guides=False,
    show_y_guides=True,
    truncate_label=-1,
    print_values=False,
    x_label_rotation=0,
    range=(min(0.0, float(np.floor(df["y"].min()))), float(np.ceil(max(df["y"].max(), gw_line) + 1))),
    xrange=(0, genome_end),
    explicit_size=True,
    margin_bottom=40,
)
chart.x_labels = midpoints
chart.x_value_formatter = chromosome_label

# Each point sits at its base-pair position; adjacent chromosomes alternate color
chart.add(
    "Odd chromosomes",
    list(zip(df.loc[~significant & df["odd"], "x"], df.loc[~significant & df["odd"], "y"], strict=True)),
    stroke=False,
)
chart.add(
    "Even chromosomes",
    list(zip(df.loc[~significant & ~df["odd"], "x"], df.loc[~significant & ~df["odd"], "y"], strict=True)),
    stroke=False,
)
hits = df[significant]
chart.add(
    "Genome-wide significant",
    [
        {"value": (row.x, row.y), "label": f"Chr {row[CHROMOSOME]}: {row[POSITION]:.1f} Mb, -log₁₀(p) = {row.y:.1f}"}
        for _, row in hits.iterrows()
    ],
    stroke=False,
    dots_size=6,
)

# Dashed threshold lines across the whole genome
dashed = {"width": 4, "dasharray": "24,14", "linecap": "butt"}
chart.add(
    f"Suggestive (p = {SUGGESTIVE_P:g})",
    [(0, sugg_line), (genome_end, sugg_line)],
    stroke=True,
    show_dots=False,
    stroke_style=dashed,
)
chart.add(
    f"Genome-wide (p = {GENOME_WIDE_P:g})",
    [(0, gw_line), (genome_end, gw_line)],
    stroke=True,
    show_dots=False,
    stroke_style=dashed,
)

# Save
chart.render_to_file(f"plot-{THEME}.html")
chart.render_to_png(f"plot-{THEME}.png")
