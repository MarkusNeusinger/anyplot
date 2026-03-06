"""pyplots.ai
genome-track-multi: Genome Track Viewer
Library: matplotlib | Python 3.13
Quality: pending | Created: 2026-03-06
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np


np.random.seed(42)

# Genomic region: chr7:27,200,000-27,280,000 (HOXA cluster region)
chrom = "chr7"
region_start = 27_200_000
region_end = 27_280_000

# Gene track data
genes = [
    {
        "name": "HOXA1",
        "start": 27_204_000,
        "end": 27_214_000,
        "strand": "+",
        "exons": [(27_204_000, 27_205_500), (27_207_000, 27_208_200), (27_211_000, 27_214_000)],
    },
    {
        "name": "HOXA2",
        "start": 27_220_000,
        "end": 27_232_000,
        "strand": "+",
        "exons": [(27_220_000, 27_221_800), (27_225_000, 27_226_500), (27_229_500, 27_232_000)],
    },
    {
        "name": "HOXA3",
        "start": 27_240_000,
        "end": 27_258_000,
        "strand": "-",
        "exons": [(27_240_000, 27_242_500), (27_247_000, 27_249_000), (27_254_000, 27_258_000)],
    },
    {
        "name": "HOXA4",
        "start": 27_262_000,
        "end": 27_275_000,
        "strand": "+",
        "exons": [(27_262_000, 27_264_000), (27_268_000, 27_270_500), (27_273_000, 27_275_000)],
    },
]

# Coverage track data (simulated RNA-seq)
coverage_positions = np.linspace(region_start, region_end, 800)
coverage_base = np.random.exponential(5, 800)
for gene in genes:
    for exon_start, exon_end in gene["exons"]:
        mask = (coverage_positions >= exon_start) & (coverage_positions <= exon_end)
        coverage_base[mask] += np.random.exponential(40, mask.sum())
coverage_depth = np.convolve(coverage_base, np.ones(5) / 5, mode="same")

# Variant track data (SNPs and indels)
variant_positions = np.array(
    [
        27_205_200,
        27_208_100,
        27_215_000,
        27_221_500,
        27_226_200,
        27_233_000,
        27_241_800,
        27_248_500,
        27_255_500,
        27_263_500,
        27_269_000,
        27_274_200,
        27_237_000,
        27_260_000,
        27_270_800,
    ]
)
variant_types = ["SNP"] * 10 + ["indel"] * 5
variant_quality = np.random.uniform(20, 100, len(variant_positions))

# Regulatory elements
regulatory_elements = [
    {"type": "Promoter", "start": 27_202_000, "end": 27_204_000},
    {"type": "Enhancer", "start": 27_216_000, "end": 27_219_000},
    {"type": "Promoter", "start": 27_218_500, "end": 27_220_000},
    {"type": "Enhancer", "start": 27_234_000, "end": 27_238_000},
    {"type": "Promoter", "start": 27_238_500, "end": 27_240_000},
    {"type": "Insulator", "start": 27_258_500, "end": 27_261_000},
    {"type": "Promoter", "start": 27_260_500, "end": 27_262_000},
    {"type": "Enhancer", "start": 27_276_000, "end": 27_279_000},
]

# Colors
gene_color = "#306998"
exon_color = "#306998"
coverage_color = "#5B9BD5"
snp_color = "#E07B54"
indel_color = "#8B5E3C"
promoter_color = "#4CAF50"
enhancer_color = "#FFB74D"
insulator_color = "#9575CD"

# Plot
fig, axes = plt.subplots(
    4, 1, figsize=(16, 9), sharex=True, gridspec_kw={"height_ratios": [2, 2.5, 1.5, 1.5], "hspace": 0.08}
)

# Track 1: Gene annotations
ax_genes = axes[0]
for gene in genes:
    y_center = 0.5
    intron_y = y_center
    ax_genes.plot(
        [gene["start"], gene["end"]], [intron_y, intron_y], color=gene_color, linewidth=1.5, solid_capstyle="butt"
    )
    for exon_start, exon_end in gene["exons"]:
        rect = mpatches.FancyBboxPatch(
            (exon_start, intron_y - 0.25),
            exon_end - exon_start,
            0.5,
            boxstyle="round,pad=0",
            facecolor=exon_color,
            edgecolor="white",
            linewidth=0.8,
        )
        ax_genes.add_patch(rect)
    arrow_char = "\u25b6" if gene["strand"] == "+" else "\u25c0"
    mid_x = (gene["start"] + gene["end"]) / 2
    ax_genes.text(
        mid_x,
        intron_y + 0.45,
        f"{gene['name']} {arrow_char}",
        fontsize=13,
        va="bottom",
        ha="center",
        color="#333333",
        fontweight="medium",
    )

ax_genes.set_ylim(-0.2, 1.2)
ax_genes.set_ylabel("Genes", fontsize=16, fontweight="medium", labelpad=15)
ax_genes.set_yticks([])
ax_genes.spines["top"].set_visible(False)
ax_genes.spines["right"].set_visible(False)
ax_genes.spines["left"].set_visible(False)
ax_genes.spines["bottom"].set_visible(False)
ax_genes.set_facecolor("#FAFAFA")

# Track 2: Coverage
ax_cov = axes[1]
ax_cov.fill_between(coverage_positions, coverage_depth, alpha=0.6, color=coverage_color, linewidth=0)
ax_cov.plot(coverage_positions, coverage_depth, color=coverage_color, linewidth=1.2, alpha=0.9)
ax_cov.set_ylabel("Coverage", fontsize=16, fontweight="medium", labelpad=15)
ax_cov.set_ylim(0, coverage_depth.max() * 1.15)
ax_cov.tick_params(axis="y", labelsize=13)
ax_cov.spines["top"].set_visible(False)
ax_cov.spines["right"].set_visible(False)
ax_cov.yaxis.grid(True, alpha=0.15, linewidth=0.8)

# Track 3: Variants (lollipop plot)
ax_var = axes[2]
for pos, vtype, qual in zip(variant_positions, variant_types, variant_quality, strict=False):
    color = snp_color if vtype == "SNP" else indel_color
    marker = "o" if vtype == "SNP" else "D"
    stem_height = qual / 100
    ax_var.plot([pos, pos], [0, stem_height], color=color, linewidth=1.5, alpha=0.7)
    ax_var.scatter(pos, stem_height, color=color, marker=marker, s=80, edgecolors="white", linewidth=0.5, zorder=3)

snp_patch = mpatches.Patch(color=snp_color, label="SNP")
indel_patch = mpatches.Patch(color=indel_color, label="Indel")
ax_var.legend(handles=[snp_patch, indel_patch], fontsize=12, loc="upper right", framealpha=0.8, edgecolor="none")
ax_var.set_ylabel("Variants", fontsize=16, fontweight="medium", labelpad=15)
ax_var.set_ylim(0, 1.25)
ax_var.set_yticks([0, 0.5, 1.0])
ax_var.set_yticklabels(["0", "50", "100"], fontsize=13)
ax_var.tick_params(axis="y", labelsize=13)
ax_var.spines["top"].set_visible(False)
ax_var.spines["right"].set_visible(False)
ax_var.set_facecolor("#FAFAFA")

# Track 4: Regulatory elements
ax_reg = axes[3]
reg_colors = {"Promoter": promoter_color, "Enhancer": enhancer_color, "Insulator": insulator_color}
for elem in regulatory_elements:
    color = reg_colors[elem["type"]]
    rect = mpatches.FancyBboxPatch(
        (elem["start"], 0.2),
        elem["end"] - elem["start"],
        0.6,
        boxstyle="round,pad=0",
        facecolor=color,
        edgecolor="white",
        linewidth=0.8,
        alpha=0.85,
    )
    ax_reg.add_patch(rect)

reg_patches = [mpatches.Patch(color=c, label=t) for t, c in reg_colors.items()]
ax_reg.legend(handles=reg_patches, fontsize=12, loc="upper right", framealpha=0.8, edgecolor="none", ncol=3)
ax_reg.set_ylim(0, 1.2)
ax_reg.set_ylabel("Regulatory", fontsize=16, fontweight="medium", labelpad=15)
ax_reg.set_yticks([])
ax_reg.spines["top"].set_visible(False)
ax_reg.spines["right"].set_visible(False)
ax_reg.spines["left"].set_visible(False)

# Shared x-axis
ax_reg.set_xlim(region_start, region_end)
ax_reg.set_xlabel(f"Genomic Position — {chrom} (bp)", fontsize=18)
ax_reg.tick_params(axis="x", labelsize=14)
ax_reg.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x / 1e6:.2f} Mb"))

# Title
fig.suptitle("genome-track-multi \u00b7 matplotlib \u00b7 pyplots.ai", fontsize=22, fontweight="medium", y=0.98)

plt.savefig("plot.png", dpi=300, bbox_inches="tight")
