""" pyplots.ai
genome-track-multi: Genome Track Viewer
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 89/100 | Created: 2026-03-06
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_hline,
    geom_point,
    geom_rect,
    geom_ribbon,
    geom_segment,
    geom_text,
    ggplot,
    guide_legend,
    guides,
    labs,
    scale_color_manual,
    scale_fill_brewer,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


np.random.seed(42)

# Genomic region: chr7, EGFR locus (~55kb region)
chrom = "chr7"
region_start = 55_086_000
region_end = 55_141_000

# Track vertical layout (bottom to top): each track gets a band
# Regulatory: 0 - 1
# Variants:   1.5 - 3.5
# Coverage:   4.0 - 6.0
# Genes:      6.5 - 7.5

# Background shading for track separation (alternating grey/white)
track_bg_grey = pd.DataFrame(
    {"xmin": [region_start, region_start], "xmax": [region_end, region_end], "ymin": [0.0, 4.0], "ymax": [1.0, 6.0]}
)
track_bg_white = pd.DataFrame(
    {"xmin": [region_start, region_start], "xmax": [region_end, region_end], "ymin": [1.5, 6.5], "ymax": [3.5, 7.5]}
)

# Track labels (larger size)
track_labels = pd.DataFrame(
    {
        "x": [region_start + 800] * 4,
        "y": [0.88, 3.35, 5.88, 7.38],
        "label": ["Regulatory", "Variants", "Coverage", "Genes"],
    }
)

# --- Gene Track (y: 6.5 - 7.5, center at 7.0) ---
gene_center = 7.0
exon_half = 0.25

exons = pd.DataFrame(
    {
        "start": [
            55_086_725,
            55_087_058,
            55_088_850,
            55_092_340,
            55_095_262,
            55_097_600,
            55_099_310,
            55_110_700,
            55_117_550,
            55_124_950,
            55_131_800,
            55_136_500,
            55_139_800,
        ],
        "end": [
            55_087_020,
            55_087_350,
            55_089_150,
            55_092_580,
            55_095_530,
            55_097_870,
            55_099_550,
            55_110_960,
            55_117_810,
            55_125_200,
            55_132_050,
            55_136_750,
            55_140_100,
        ],
    }
)
exons["ymin"] = gene_center - exon_half
exons["ymax"] = gene_center + exon_half

# Intron connector lines
intron_lines = pd.DataFrame(
    {
        "x": exons["end"].iloc[:-1].values,
        "xend": exons["start"].iloc[1:].values,
        "y": [gene_center] * (len(exons) - 1),
        "yend": [gene_center] * (len(exons) - 1),
    }
)

# Strand direction chevrons (+ strand, pointing right) - increased visibility
chevron_x = np.linspace(region_start + 3000, region_end - 3000, 25)
chevron_size = 400
chevrons_up = pd.DataFrame(
    {
        "x": chevron_x,
        "xend": chevron_x + chevron_size,
        "y": [gene_center] * len(chevron_x),
        "yend": [gene_center + 0.14] * len(chevron_x),
    }
)
chevrons_down = pd.DataFrame(
    {
        "x": chevron_x,
        "xend": chevron_x + chevron_size,
        "y": [gene_center] * len(chevron_x),
        "yend": [gene_center - 0.14] * len(chevron_x),
    }
)

# Gene label
gene_label = pd.DataFrame({"x": [(region_start + region_end) / 2], "y": [gene_center + 0.42], "label": ["EGFR  (+)"]})

# --- Coverage Track (y: 4.0 - 6.0) ---
cov_base = 4.0
cov_height = 2.0
positions = np.arange(region_start, region_end, 150)
raw_coverage = 25 + 12 * np.sin(np.linspace(0, 3.5 * np.pi, len(positions)))

for _, exon in exons.iterrows():
    mask = (positions >= exon["start"] - 800) & (positions <= exon["end"] + 800)
    raw_coverage[mask] += np.random.uniform(15, 45)

raw_coverage += np.random.normal(0, 4, len(positions))
raw_coverage = np.maximum(raw_coverage, 0)
max_cov = raw_coverage.max()
normalized_cov = raw_coverage / max_cov * cov_height

coverage_df = pd.DataFrame({"x": positions, "ymin": [cov_base] * len(positions), "ymax": cov_base + normalized_cov})

# --- Variant Track (y: 1.5 - 3.5) ---
var_base = 1.5
var_height = 2.0
n_variants = 18
variant_positions = np.sort(np.random.randint(region_start + 500, region_end - 500, n_variants))
variant_quality = np.random.uniform(10, 100, n_variants)
variant_types = np.random.choice(["SNP", "Indel"], n_variants, p=[0.75, 0.25])
normalized_quality = variant_quality / 100.0 * var_height

# Colorblind-safe Okabe-Ito palette for variants
snp_color = "#0072B2"
indel_color = "#E69F00"
variant_palette = {"SNP": snp_color, "Indel": indel_color}

variant_stems = pd.DataFrame(
    {
        "x": variant_positions,
        "xend": variant_positions,
        "y": [var_base] * n_variants,
        "yend": var_base + normalized_quality,
    }
)

# Use mapped color aesthetic for native legend
variant_heads = pd.DataFrame(
    {
        "x": variant_positions,
        "y": var_base + normalized_quality,
        "variant_type": pd.Categorical(variant_types, categories=["SNP", "Indel"], ordered=True),
    }
)

# --- Regulatory Track (y: 0.0 - 1.0, center at 0.5) ---
reg_center = 0.5
reg_half = 0.25

# Use mapped fill aesthetic for brewer scale + native legend
regulatory_elements = pd.DataFrame(
    {
        "start": [55_086_200, 55_088_400, 55_093_100, 55_098_900, 55_112_300, 55_120_000, 55_128_500, 55_135_200],
        "end": [55_086_700, 55_088_800, 55_093_500, 55_099_250, 55_112_700, 55_120_450, 55_128_900, 55_135_600],
        "feature_type": pd.Categorical(
            ["Promoter", "Enhancer", "Enhancer", "Promoter", "Enhancer", "Insulator", "Enhancer", "Promoter"],
            categories=["Promoter", "Enhancer", "Insulator"],
            ordered=True,
        ),
    }
)
regulatory_elements["ymin"] = reg_center - reg_half
regulatory_elements["ymax"] = reg_center + reg_half

# Colors
exon_color = "#306998"
coverage_fill = "#4B8BBE"
stem_color = "#999999"

# Separator lines between tracks
separators = pd.DataFrame({"yintercept": [1.25, 3.75, 6.25]})

# Build plot using grammar-of-graphics composition with mapped aesthetics
plot = (
    ggplot()
    # Track background shading (fixed fill, not aesthetic-mapped)
    + geom_rect(
        data=track_bg_grey, mapping=aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"), fill="#F0F0F0", alpha=0.6
    )
    + geom_rect(
        data=track_bg_white, mapping=aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"), fill="#FAFAFA", alpha=0.4
    )
    # Track separators
    + geom_hline(data=separators, mapping=aes(yintercept="yintercept"), color="#CCCCCC", size=0.5, linetype="dashed")
    # Gene track: intron lines
    + geom_segment(data=intron_lines, mapping=aes(x="x", xend="xend", y="y", yend="yend"), color=exon_color, size=0.7)
    # Gene track: strand chevrons (increased alpha for visibility)
    + geom_segment(
        data=chevrons_up, mapping=aes(x="x", xend="xend", y="y", yend="yend"), color=exon_color, size=0.4, alpha=0.55
    )
    + geom_segment(
        data=chevrons_down, mapping=aes(x="x", xend="xend", y="y", yend="yend"), color=exon_color, size=0.4, alpha=0.55
    )
    # Gene track: exon rectangles
    + geom_rect(
        data=exons,
        mapping=aes(xmin="start", xmax="end", ymin="ymin", ymax="ymax"),
        fill=exon_color,
        color="white",
        size=0.3,
    )
    # Gene track: label
    + geom_text(
        data=gene_label,
        mapping=aes(x="x", y="y", label="label"),
        size=11,
        color="#333333",
        fontstyle="italic",
        fontweight="bold",
    )
    # Coverage track: filled ribbon
    + geom_ribbon(
        data=coverage_df,
        mapping=aes(x="x", ymin="ymin", ymax="ymax"),
        fill=coverage_fill,
        alpha=0.55,
        color=coverage_fill,
        size=0.3,
    )
    # Variant track: stems
    + geom_segment(data=variant_stems, mapping=aes(x="x", xend="xend", y="y", yend="yend"), color=stem_color, size=0.6)
    # Variant track: heads with mapped color aesthetic (generates native legend)
    + geom_point(data=variant_heads, mapping=aes(x="x", y="y", color="variant_type"), size=4, alpha=0.9)
    + scale_color_manual(name="Variant Type", values=variant_palette, guide=guide_legend(order=1))
    # Regulatory track: rectangles with mapped fill + brewer scale (native legend)
    + geom_rect(
        data=regulatory_elements, mapping=aes(xmin="start", xmax="end", ymin="ymin", ymax="ymax", fill="feature_type")
    )
    + scale_fill_brewer(type="qual", palette="Dark2", name="Regulatory", guide=guide_legend(order=2))
    # Track labels
    + geom_text(
        data=track_labels,
        mapping=aes(x="x", y="y", label="label"),
        size=11,
        ha="left",
        fontweight="bold",
        color="#444444",
    )
    # Axes
    + scale_x_continuous(
        labels=lambda x: [f"{int(v):,}" for v in x], limits=(region_start, region_end), expand=(0.01, 0)
    )
    + scale_y_continuous(limits=(-0.2, 7.8), breaks=[], expand=(0, 0))
    + labs(title="genome-track-multi \u00b7 plotnine \u00b7 pyplots.ai", x=f"Genomic Position ({chrom})", y="")
    # Theme with plotnine-specific grammar-of-graphics styling
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold"),
        axis_title_x=element_text(size=20),
        axis_title_y=element_blank(),
        axis_text_x=element_text(size=14),
        axis_text_y=element_blank(),
        axis_ticks_major_y=element_blank(),
        legend_title=element_text(size=14, weight="bold"),
        legend_text=element_text(size=12),
        legend_position="right",
        legend_key_size=18,
        panel_grid_minor=element_blank(),
        panel_grid_major_x=element_line(color="#E0E0E0", size=0.3, alpha=0.4),
        panel_grid_major_y=element_blank(),
        panel_background=element_rect(fill="white", color=None),
        plot_background=element_rect(fill="white", color=None),
    )
    + guides(fill=guide_legend(override_aes={"alpha": 1}))
)

# Save
plot.save("plot.png", dpi=300, width=16, height=9)
