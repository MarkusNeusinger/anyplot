"""pyplots.ai
genome-track-multi: Genome Track Viewer
Library: letsplot 4.8.2 | Python 3.14.3
Quality: 87/100 | Created: 2026-03-06
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

# Track layout configuration
tracks = {
    "Genes": {"center": 4.2, "half_h": 0.42, "pad_bot": 0.25, "pad_top": 0.55},
    "Coverage": {"center": 2.7, "half_h": 0.65, "pad_bot": 0.25, "pad_top": 0.30},
    "Variants": {"center": 1.3, "half_h": 0.42, "pad_bot": 0.25, "pad_top": 0.30},
    "Regulatory": {"center": 0.0, "half_h": 0.42, "pad_bot": 0.25, "pad_top": 0.30},
}

# Scale positions to kb for readability
scale = 1000.0
x_start = region_start / scale
x_end = region_end / scale

# --- Gene track data ---
t = tracks["Genes"]
gene_intron_df = pd.DataFrame(
    {"x": genes["start"] / scale, "xend": genes["end"] / scale, "y": t["center"], "yend": t["center"]}
)

exon_df = pd.DataFrame(
    {
        "xmin": exons["start"] / scale,
        "xmax": exons["end"] / scale,
        "ymin": t["center"] - t["half_h"],
        "ymax": t["center"] + t["half_h"],
        "gene": exons["gene"],
    }
)
exon_df["exon_size"] = ((exons["end"] - exons["start"]) / 1000).round(1).astype(str) + " kb"

gene_label_df = pd.DataFrame(
    {"x": (genes["start"] + genes["end"]) / 2 / scale, "y": t["center"] + t["half_h"] + 0.22, "label": genes["name"]}
)

# Strand arrows
strand_arrows = []
for _, g in genes.iterrows():
    mid = (g["start"] + g["end"]) / 2 / scale
    arrow_char = "\u25b6" if g["strand"] == "+" else "\u25c0"
    strand_arrows.append({"x": mid, "y": t["center"] - t["half_h"] - 0.22, "label": arrow_char})
strand_df = pd.DataFrame(strand_arrows)

# --- Coverage track data ---
t = tracks["Coverage"]
cov_plot_df = coverage_df.copy()
cov_plot_df["x"] = cov_plot_df["position"] / scale
max_depth = cov_plot_df["depth"].max()
cov_plot_df["y"] = t["center"] - t["half_h"] + (cov_plot_df["depth"] / max_depth) * (2 * t["half_h"])
cov_plot_df["ybase"] = t["center"] - t["half_h"]
cov_plot_df["depth_label"] = cov_plot_df["depth"].round(1).astype(str) + "x"
cov_plot_df["pos_label"] = (cov_plot_df["position"] / 1000).round(1).astype(str) + " kb"

# --- Variant track data ---
t = tracks["Variants"]
var_plot_df = variants_df.copy()
var_plot_df["x"] = var_plot_df["position"] / scale
var_plot_df["y_base"] = t["center"]
# Ensure minimum stem height for low-quality variants (min 30% of max height)
min_stem = 0.3
max_stem = 2 * t["half_h"] + 0.15
var_plot_df["y_top"] = t["center"] + min_stem * max_stem + (var_plot_df["quality"] / 100) * (1 - min_stem) * max_stem
var_plot_df["qual_label"] = "QUAL: " + var_plot_df["quality"].round(1).astype(str)
var_plot_df["pos_label"] = (var_plot_df["position"] / 1000).round(1).astype(str) + " kb"

# --- Regulatory track data ---
t = tracks["Regulatory"]
reg_plot_df = pd.DataFrame(
    {
        "xmin": regulatory["start"] / scale,
        "xmax": regulatory["end"] / scale,
        "ymin": t["center"] - t["half_h"],
        "ymax": t["center"] + t["half_h"],
        "element": regulatory["element"],
        "size_label": ((regulatory["end"] - regulatory["start"]) / 1000).round(1).astype(str) + " kb",
    }
)

# Track background shading
bg_rows = []
for name, t in tracks.items():
    bg_rows.append(
        {
            "xmin": x_start,
            "xmax": x_end,
            "ymin": t["center"] - t["half_h"] - t["pad_bot"],
            "ymax": t["center"] + t["half_h"] + t["pad_top"],
            "track": name,
        }
    )
track_bg = pd.DataFrame(bg_rows)

# Divider lines between adjacent tracks
track_order = ["Regulatory", "Variants", "Coverage", "Genes"]
divider_positions = []
for i in range(len(track_order) - 1):
    lo = tracks[track_order[i]]
    hi = tracks[track_order[i + 1]]
    y_mid = (lo["center"] + lo["half_h"] + lo["pad_top"] + hi["center"] - hi["half_h"] - hi["pad_bot"]) / 2
    divider_positions.append(y_mid)

divider_df = pd.DataFrame({"x": [x_start] * 3, "xend": [x_end] * 3, "y": divider_positions, "yend": divider_positions})

# Track labels positioned inside each track's upper-left corner
track_labels_df = pd.DataFrame(
    {
        "x": [x_start + 1.0] * 4,
        "y": [tracks[n]["center"] + tracks[n]["half_h"] + tracks[n]["pad_top"] - 0.15 for n in track_order],
        "label": track_order,
    }
)

# Highlight region: variant-dense area near HOXA3 exon 2
highlight_df = pd.DataFrame(
    {
        "xmin": [27241.0],
        "xmax": [27243.0],
        "ymin": [tracks["Regulatory"]["center"] - tracks["Regulatory"]["half_h"] - tracks["Regulatory"]["pad_bot"]],
        "ymax": [tracks["Genes"]["center"] + tracks["Genes"]["half_h"] + tracks["Genes"]["pad_top"]],
    }
)

# Peak coverage annotation
peak_idx = cov_plot_df["depth"].idxmax()
peak_x = cov_plot_df.loc[peak_idx, "x"]
peak_depth = cov_plot_df.loc[peak_idx, "depth"]
t = tracks["Coverage"]
peak_annotation_df = pd.DataFrame(
    {"x": [peak_x + 2.0], "y": [t["center"] + t["half_h"] - 0.05], "label": [f"Peak: {peak_depth:.0f}x"]}
)

# Colors — refined palette
gene_color = "#306998"
exon_color = "#2B5F8A"
cov_fill = "#6AAED6"
cov_border = "#4A90D9"
snp_color = "#E8833A"
indel_color = "#C44E52"
promoter_color = "#2CA02C"
enhancer_color = "#8B6DAF"

# Custom x-axis tick labels with "kb" suffix - use wider spacing to avoid rotation
tick_positions = list(range(int(x_start), int(x_end) + 1, 20))
tick_labels = [f"{v} kb" for v in tick_positions]

# Plot
plot = (
    ggplot()
    # Highlight region for storytelling focal point
    + geom_rect(
        aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"),
        data=highlight_df,
        fill="#FFF8E1",
        color="#FFE082",
        size=0.5,
        alpha=0.4,
    )
    # Track background shading
    + geom_rect(
        aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"),
        data=track_bg,
        fill="#F8F9FA",
        color="#E8E8E8",
        size=0.3,
        alpha=0.5,
    )
    # Divider lines between tracks
    + geom_segment(
        aes(x="x", xend="xend", y="y", yend="yend"), data=divider_df, color="#D0D0D0", size=0.4, linetype="dashed"
    )
    # Gene track: intron lines
    + geom_segment(aes(x="x", xend="xend", y="y", yend="yend"), data=gene_intron_df, color=gene_color, size=1.2)
    # Gene track: exon rectangles with tooltips
    + geom_rect(
        aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"),
        data=exon_df,
        fill=exon_color,
        color="#1A3F5C",
        size=0.6,
        alpha=0.9,
        tooltips=layer_tooltips().line("Gene: @gene").line("Size: @exon_size"),
    )
    # Gene labels
    + geom_text(aes(x="x", y="y", label="label"), data=gene_label_df, size=16, color="#1a1a1a", fontface="italic")
    # Strand direction arrows
    + geom_text(aes(x="x", y="y", label="label"), data=strand_df, size=12, color="#555555")
    # Coverage track: filled area with tooltips
    + geom_ribbon(
        aes(x="x", ymin="ybase", ymax="y"),
        data=cov_plot_df,
        fill=cov_fill,
        color=cov_border,
        alpha=0.6,
        size=0.5,
        tooltips=layer_tooltips().line("Position: @pos_label").line("Depth: @depth_label"),
    )
    # Coverage peak annotation
    + geom_text(aes(x="x", y="y", label="label"), data=peak_annotation_df, size=12, color="#2B7BBE", fontface="bold")
    # Variant track: lollipop stems
    + geom_segment(aes(x="x", xend="x", y="y_base", yend="y_top", color="type"), data=var_plot_df, size=1.2)
    # Variant track: lollipop heads with tooltips
    + geom_point(
        aes(x="x", y="y_top", color="type"),
        data=var_plot_df,
        size=6,
        stroke=0.8,
        tooltips=layer_tooltips().line("@type").line("@qual_label").line("Position: @pos_label"),
    )
    # Regulatory track with tooltips
    + geom_rect(
        aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="element"),
        data=reg_plot_df,
        alpha=0.8,
        size=0.4,
        color="#FFFFFF",
        tooltips=layer_tooltips().line("@element").line("Size: @size_label"),
    )
    # Track labels inside the plot area
    + geom_text(
        aes(x="x", y="y", label="label"), data=track_labels_df, size=14, color="#444444", fontface="bold", hjust=0
    )
    # Scales
    + scale_color_manual(values={"SNP": snp_color, "Indel": indel_color}, name="Variant Type")
    + scale_fill_manual(values={"Promoter": promoter_color, "Enhancer": enhancer_color}, name="Regulatory")
    + scale_x_continuous(
        name=f"Genomic Position ({chrom})", breaks=tick_positions, labels=tick_labels, expand=[0.01, 0.01]
    )
    + scale_y_continuous(expand=[0.04, 0.04])
    + labs(
        title="genome-track-multi \u00b7 letsplot \u00b7 pyplots.ai",
        subtitle="HOXA Gene Cluster \u2014 chr7:27,200\u201327,280 kb  |  Highlight: variant-rich region in HOXA3",
    )
    + coord_cartesian(xlim=[x_start - 1, x_end + 1])
    + theme_minimal()
    + theme(
        plot_title=element_text(size=26, face="bold", color="#1a1a1a"),
        plot_subtitle=element_text(size=17, color="#555555"),
        axis_title_x=element_text(size=20, color="#333333"),
        axis_title_y=element_blank(),
        axis_text_x=element_text(size=16, color="#555555", angle=0),
        axis_text_y=element_blank(),
        axis_ticks_y=element_blank(),
        panel_grid_major_x=element_line(color="#EAEAEA", size=0.3),
        panel_grid_major_y=element_blank(),
        panel_grid_minor=element_blank(),
        legend_title=element_text(size=16, face="bold"),
        legend_text=element_text(size=14),
        legend_position="bottom",
        plot_background=element_rect(fill="white", color="white"),
        plot_margin=[40, 25, 20, 30],
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
