"""pyplots.ai
genome-track-multi: Genome Track Viewer
Library: letsplot | Python 3.13
Quality: pending | Created: 2026-03-06
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403


LetsPlot.setup_html()  # noqa: F405

np.random.seed(42)

# Genomic region: chr7:27,200,000-27,280,000 (HOXA gene cluster)
chrom = "chr7"
region_start = 27200000
region_end = 27280000

# Track 1: Gene annotations
genes = pd.DataFrame(
    {
        "name": ["HOXA1", "HOXA2", "HOXA3", "HOXA4", "HOXA5"],
        "start": [27204000, 27220000, 27238000, 27252000, 27264000],
        "end": [27212000, 27229000, 27248000, 27260000, 27274000],
        "strand": ["+", "+", "+", "-", "+"],
    }
)

# Exons within each gene (2-4 exons per gene)
exons = pd.DataFrame(
    {
        "gene": [
            "HOXA1",
            "HOXA1",
            "HOXA1",
            "HOXA2",
            "HOXA2",
            "HOXA3",
            "HOXA3",
            "HOXA3",
            "HOXA3",
            "HOXA4",
            "HOXA4",
            "HOXA4",
            "HOXA5",
            "HOXA5",
            "HOXA5",
        ],
        "start": [
            27204000,
            27206500,
            27210000,
            27220000,
            27225000,
            27238000,
            27241000,
            27244000,
            27246500,
            27252000,
            27255000,
            27258000,
            27264000,
            27268000,
            27271500,
        ],
        "end": [
            27205200,
            27207800,
            27212000,
            27221500,
            27229000,
            27239500,
            27242500,
            27245200,
            27248000,
            27253500,
            27256500,
            27260000,
            27265500,
            27269500,
            27274000,
        ],
    }
)

# Track 2: Coverage - simulated RNA-seq read depth
coverage_positions = np.arange(region_start, region_end, 200)
base_coverage = np.random.exponential(5, len(coverage_positions))

# Boost coverage over exonic regions
for _, exon in exons.iterrows():
    mask = (coverage_positions >= exon["start"]) & (coverage_positions <= exon["end"])
    base_coverage[mask] += np.random.exponential(40, mask.sum())

coverage_df = pd.DataFrame({"position": coverage_positions, "depth": np.clip(base_coverage, 0, 120)})

# Track 3: Variants (SNPs and indels)
variant_positions = np.sort(np.random.choice(range(region_start + 1000, region_end - 1000), size=18, replace=False))
variant_types = np.random.choice(["SNP", "SNP", "SNP", "Indel"], size=18)
variant_quality = np.random.uniform(20, 99, size=18)
variants_df = pd.DataFrame({"position": variant_positions, "type": variant_types, "quality": variant_quality})

# Track 4: Regulatory elements
regulatory = pd.DataFrame(
    {
        "start": [27201000, 27215000, 27233000, 27249000, 27262000, 27275000],
        "end": [27203000, 27218000, 27236000, 27251000, 27263500, 27278000],
        "element": ["Promoter", "Enhancer", "Promoter", "Enhancer", "Promoter", "Enhancer"],
    }
)

# Track layout: y-offset for each track
track_gene_y = 3.0
track_cov_y = 2.0
track_var_y = 1.0
track_reg_y = 0.0
track_height = 0.35

# Scale positions to kb for readability
scale = 1000.0

# --- Gene track data ---
gene_intron_df = pd.DataFrame(
    {"x": genes["start"] / scale, "xend": genes["end"] / scale, "y": track_gene_y, "yend": track_gene_y}
)

exon_df = pd.DataFrame(
    {
        "xmin": exons["start"] / scale,
        "xmax": exons["end"] / scale,
        "ymin": track_gene_y - track_height,
        "ymax": track_gene_y + track_height,
    }
)

gene_label_df = pd.DataFrame(
    {"x": (genes["start"] + genes["end"]) / 2 / scale, "y": track_gene_y + track_height + 0.15, "label": genes["name"]}
)

# Strand arrows
strand_arrows = []
for _, g in genes.iterrows():
    mid = (g["start"] + g["end"]) / 2 / scale
    arrow_char = "\u25b6" if g["strand"] == "+" else "\u25c0"
    strand_arrows.append({"x": mid, "y": track_gene_y - track_height - 0.15, "label": arrow_char})
strand_df = pd.DataFrame(strand_arrows)

# --- Coverage track data ---
cov_plot_df = coverage_df.copy()
cov_plot_df["x"] = cov_plot_df["position"] / scale
# Normalize coverage to fit within track band
max_depth = cov_plot_df["depth"].max()
cov_plot_df["y"] = track_cov_y - track_height + (cov_plot_df["depth"] / max_depth) * (2 * track_height)
cov_plot_df["ybase"] = track_cov_y - track_height

# --- Variant track data ---
var_plot_df = variants_df.copy()
var_plot_df["x"] = var_plot_df["position"] / scale
var_plot_df["y_base"] = track_var_y
# Lollipop height based on quality
var_plot_df["y_top"] = track_var_y + (var_plot_df["quality"] / 100) * (2 * track_height)

# --- Regulatory track data ---
reg_plot_df = pd.DataFrame(
    {
        "xmin": regulatory["start"] / scale,
        "xmax": regulatory["end"] / scale,
        "ymin": track_reg_y - track_height,
        "ymax": track_reg_y + track_height,
        "element": regulatory["element"],
    }
)

# Track background shading
track_bg = pd.DataFrame(
    {
        "xmin": [region_start / scale] * 4,
        "xmax": [region_end / scale] * 4,
        "ymin": [
            track_reg_y - track_height - 0.25,
            track_var_y - track_height - 0.25,
            track_cov_y - track_height - 0.25,
            track_gene_y - track_height - 0.25,
        ],
        "ymax": [
            track_reg_y + track_height + 0.3,
            track_var_y + track_height + 0.3,
            track_cov_y + track_height + 0.3,
            track_gene_y + track_height + 0.45,
        ],
        "track": ["Regulatory", "Variants", "Coverage", "Genes"],
    }
)

# Track labels
track_labels_df = pd.DataFrame(
    {
        "x": [region_start / scale - 0.2] * 4,
        "y": [track_reg_y, track_var_y, track_cov_y, track_gene_y],
        "label": ["Regulatory", "Variants", "Coverage", "Genes"],
    }
)

# Colors
gene_color = "#306998"
exon_color = "#306998"
cov_fill = "#4A90D9"
snp_color = "#E8833A"
indel_color = "#D55E00"
promoter_color = "#2CA02C"
enhancer_color = "#9467BD"

# Plot
plot = (
    ggplot()
    # Track background shading
    + geom_rect(
        aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"),
        data=track_bg,
        fill="#F7F7F7",
        color="#EEEEEE",
        size=0.3,
        alpha=0.6,
    )
    # Gene track: intron lines
    + geom_segment(aes(x="x", xend="xend", y="y", yend="yend"), data=gene_intron_df, color=gene_color, size=1.0)
    # Gene track: exon rectangles
    + geom_rect(
        aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"),
        data=exon_df,
        fill=exon_color,
        color="#1E4F7A",
        size=0.5,
        alpha=0.85,
    )
    # Gene labels
    + geom_text(aes(x="x", y="y", label="label"), data=gene_label_df, size=11, color="#333333", fontface="italic")
    # Strand direction arrows
    + geom_text(aes(x="x", y="y", label="label"), data=strand_df, size=9, color="#666666")
    # Coverage track: filled area using ribbon to constrain to track band
    + geom_ribbon(
        aes(x="x", ymin="ybase", ymax="y"), data=cov_plot_df, fill=cov_fill, color=cov_fill, alpha=0.5, size=0.3
    )
    # Variant track: lollipop stems
    + geom_segment(aes(x="x", xend="x", y="y_base", yend="y_top", color="type"), data=var_plot_df, size=0.8)
    # Variant track: lollipop heads
    + geom_point(aes(x="x", y="y_top", color="type"), data=var_plot_df, size=4)
    # Regulatory track
    + geom_rect(
        aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="element"),
        data=reg_plot_df,
        alpha=0.75,
        size=0.3,
        color="#FFFFFF",
    )
    # Track labels on the left
    + geom_text(
        aes(x="x", y="y", label="label"), data=track_labels_df, size=12, color="#444444", fontface="bold", hjust=1
    )
    # Scales
    + scale_color_manual(values={"SNP": snp_color, "Indel": indel_color}, name="Variant Type")
    + scale_fill_manual(values={"Promoter": promoter_color, "Enhancer": enhancer_color}, name="Regulatory")
    + scale_x_continuous(name=f"Genomic Position ({chrom}, kb)", expand=[0.06, 0])
    + scale_y_continuous(expand=[0.05, 0.05])
    + labs(
        title="genome-track-multi \u00b7 letsplot \u00b7 pyplots.ai",
        subtitle="HOXA Gene Cluster \u2014 chr7:27,200\u201327,280 kb",
    )
    + coord_cartesian(xlim=[region_start / scale - 9, region_end / scale + 1])
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold", color="#1a1a1a"),
        plot_subtitle=element_text(size=17, color="#666666"),
        axis_title_x=element_text(size=20, color="#333333"),
        axis_title_y=element_blank(),
        axis_text_x=element_text(size=16, color="#555555"),
        axis_text_y=element_blank(),
        axis_ticks_y=element_blank(),
        panel_grid_major_x=element_line(color="#EAEAEA", size=0.3),
        panel_grid_major_y=element_blank(),
        panel_grid_minor=element_blank(),
        legend_title=element_text(size=16),
        legend_text=element_text(size=14),
        legend_position="bottom",
        plot_background=element_rect(fill="white", color="white"),
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
