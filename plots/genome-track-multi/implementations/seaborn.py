""" pyplots.ai
genome-track-multi: Genome Track Viewer
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 68/100 | Created: 2026-03-06
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np


np.random.seed(42)

# Genomic region: chr7, a ~50kb window around a gene cluster
chrom = "chr7"
region_start = 55_000
region_end = 105_000

# Gene track data - two genes with exon/intron structure
genes = [
    {
        "name": "GENEA",
        "strand": "+",
        "start": 58_000,
        "end": 82_000,
        "exons": [(58_000, 60_500), (64_000, 66_000), (70_000, 72_500), (78_000, 82_000)],
    },
    {
        "name": "GENEB",
        "strand": "-",
        "start": 86_000,
        "end": 101_000,
        "exons": [(86_000, 88_500), (92_000, 94_000), (98_000, 101_000)],
    },
]

# Coverage track - simulated read depth
positions = np.arange(region_start, region_end, 100)
base_coverage = np.random.poisson(25, len(positions)).astype(float)
for gene in genes:
    for exon_start, exon_end in gene["exons"]:
        mask = (positions >= exon_start) & (positions <= exon_end)
        base_coverage[mask] += np.random.poisson(40, mask.sum())
coverage = np.convolve(base_coverage, np.ones(5) / 5, mode="same")

# Variant track - SNPs and indels
variant_positions = [59_200, 65_300, 71_800, 79_500, 87_600, 93_200, 99_400, 61_000, 75_000, 95_500]
variant_types = ["SNP", "SNP", "SNP", "SNP", "SNP", "SNP", "SNP", "indel", "indel", "indel"]
variant_quality = [95, 78, 88, 42, 91, 65, 85, 72, 55, 80]

# Regulatory track - enhancers and promoters
regulatory = [
    {"type": "promoter", "start": 56_000, "end": 58_000},
    {"type": "enhancer", "start": 67_000, "end": 69_500},
    {"type": "promoter", "start": 84_000, "end": 86_000},
    {"type": "enhancer", "start": 94_500, "end": 97_500},
]

# Plot
fig, axes = plt.subplots(4, 1, figsize=(16, 9), height_ratios=[2.5, 3, 2, 1.8])
fig.subplots_adjust(hspace=0.08)

track_colors = {
    "gene": "#306998",
    "coverage": "#306998",
    "snp": "#E07A3A",
    "indel": "#8B5CF6",
    "promoter": "#D94F4F",
    "enhancer": "#3AA66E",
}

# Track 1: Gene annotations
ax_gene = axes[0]
ax_gene.set_ylim(-1.5, 2.5)

for i, gene in enumerate(genes):
    y_center = 1.2 * i
    gene_color = track_colors["gene"]

    # Intron line
    ax_gene.plot(
        [gene["start"], gene["end"]], [y_center, y_center], color=gene_color, linewidth=1.5, solid_capstyle="butt"
    )

    # Exon rectangles
    for exon_start, exon_end in gene["exons"]:
        rect = mpatches.Rectangle(
            (exon_start, y_center - 0.35),
            exon_end - exon_start,
            0.7,
            facecolor=gene_color,
            edgecolor="white",
            linewidth=0.8,
        )
        ax_gene.add_patch(rect)

    # Strand arrow
    arrow_x = gene["end"] + 800 if gene["strand"] == "+" else gene["start"] - 800
    arrow_dx = 1200 if gene["strand"] == "+" else -1200
    ax_gene.annotate(
        "",
        xy=(arrow_x + arrow_dx, y_center),
        xytext=(arrow_x, y_center),
        arrowprops={"arrowstyle": "->", "color": gene_color, "lw": 2},
    )

    # Gene label
    label_x = gene["end"] + 2500 if gene["strand"] == "+" else gene["start"] - 2500
    ha = "left" if gene["strand"] == "+" else "right"
    ax_gene.text(
        label_x,
        y_center,
        f"{gene['name']} ({gene['strand']})",
        fontsize=14,
        fontweight="bold",
        color=gene_color,
        va="center",
        ha=ha,
    )

ax_gene.set_xlim(region_start - 1000, region_end + 1000)
ax_gene.set_ylabel("Genes", fontsize=16, fontweight="medium")
ax_gene.set_yticks([])
ax_gene.set_xticks([])
for spine in ax_gene.spines.values():
    spine.set_visible(False)

# Track 2: Coverage
ax_cov = axes[1]
ax_cov.fill_between(positions, coverage, alpha=0.5, color=track_colors["coverage"])
ax_cov.plot(positions, coverage, color=track_colors["coverage"], linewidth=1.2)
ax_cov.set_xlim(region_start - 1000, region_end + 1000)
ax_cov.set_ylabel("Coverage", fontsize=16, fontweight="medium")
ax_cov.set_ylim(0, coverage.max() * 1.15)
ax_cov.set_xticks([])
ax_cov.spines["top"].set_visible(False)
ax_cov.spines["right"].set_visible(False)
ax_cov.spines["bottom"].set_visible(False)
ax_cov.tick_params(axis="y", labelsize=13)
ax_cov.yaxis.grid(True, alpha=0.15, linewidth=0.8)

# Track 3: Variants (lollipop plot)
ax_var = axes[2]
for pos, vtype, qual in zip(variant_positions, variant_types, variant_quality, strict=True):
    color = track_colors["snp"] if vtype == "SNP" else track_colors["indel"]
    marker = "o" if vtype == "SNP" else "D"
    ax_var.plot([pos, pos], [0, qual], color=color, linewidth=1.5, alpha=0.7)
    ax_var.scatter(pos, qual, color=color, s=120, marker=marker, edgecolors="white", linewidth=0.8, zorder=3)

ax_var.set_xlim(region_start - 1000, region_end + 1000)
ax_var.set_ylabel("Variants", fontsize=16, fontweight="medium")
ax_var.set_ylim(0, 110)
ax_var.set_xticks([])
ax_var.spines["top"].set_visible(False)
ax_var.spines["right"].set_visible(False)
ax_var.spines["bottom"].set_visible(False)
ax_var.tick_params(axis="y", labelsize=13)
ax_var.yaxis.grid(True, alpha=0.15, linewidth=0.8)

# Variant legend
snp_handle = plt.scatter(
    [], [], color=track_colors["snp"], s=80, marker="o", edgecolors="white", linewidth=0.8, label="SNP"
)
indel_handle = plt.scatter(
    [], [], color=track_colors["indel"], s=80, marker="D", edgecolors="white", linewidth=0.8, label="Indel"
)
ax_var.legend(handles=[snp_handle, indel_handle], fontsize=12, loc="upper right", framealpha=0.7, edgecolor="none")

# Track 4: Regulatory elements
ax_reg = axes[3]
ax_reg.set_ylim(-0.5, 1.5)

for reg in regulatory:
    color = track_colors[reg["type"]]
    rect = mpatches.Rectangle(
        (reg["start"], 0.15),
        reg["end"] - reg["start"],
        0.7,
        facecolor=color,
        edgecolor="white",
        linewidth=0.8,
        alpha=0.85,
    )
    ax_reg.add_patch(rect)

ax_reg.set_xlim(region_start - 1000, region_end + 1000)
ax_reg.set_ylabel("Regulatory", fontsize=16, fontweight="medium")
ax_reg.set_yticks([])
ax_reg.spines["top"].set_visible(False)
ax_reg.spines["right"].set_visible(False)
ax_reg.spines["left"].set_visible(False)

# Regulatory legend
prom_handle = mpatches.Patch(color=track_colors["promoter"], label="Promoter")
enh_handle = mpatches.Patch(color=track_colors["enhancer"], label="Enhancer")
ax_reg.legend(handles=[prom_handle, enh_handle], fontsize=12, loc="upper right", framealpha=0.7, edgecolor="none")

# Shared x-axis formatting
ax_reg.set_xlabel(f"Genomic Position ({chrom})", fontsize=18)
ax_reg.tick_params(axis="x", labelsize=14)
ax_reg.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x / 1000:.0f}kb"))

# Subtle background shading for alternating tracks
for i, ax in enumerate(axes):
    if i % 2 == 1:
        ax.set_facecolor("#F8F9FA")

# Title
fig.suptitle("genome-track-multi \u00b7 seaborn \u00b7 pyplots.ai", fontsize=22, fontweight="medium", y=0.97)

plt.savefig("plot.png", dpi=300, bbox_inches="tight")
