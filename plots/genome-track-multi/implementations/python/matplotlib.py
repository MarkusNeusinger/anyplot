""" pyplots.ai
genome-track-multi: Genome Track Viewer
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-06
"""

import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection


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
coverage_edge_color = "#3A7BBF"
snp_color = "#E07B54"
indel_color = "#8B5E3C"
promoter_color = "#4CAF50"
enhancer_color = "#FFB74D"
insulator_color = "#9575CD"
track_bg_1 = "#F7F9FC"
track_bg_2 = "#FFFFFF"

# Plot
fig, axes = plt.subplots(
    4, 1, figsize=(16, 9), sharex=True, gridspec_kw={"height_ratios": [2, 2.5, 1.5, 1.5], "hspace": 0.06}
)

# Track 1: Gene annotations
ax_genes = axes[0]
for gene in genes:
    y_center = 0.5
    # Intron line with directional chevrons
    ax_genes.plot(
        [gene["start"], gene["end"]],
        [y_center, y_center],
        color=gene_color,
        linewidth=1.8,
        solid_capstyle="butt",
        alpha=0.6,
    )
    # Add strand-direction chevrons along intron
    n_chevrons = max(2, int((gene["end"] - gene["start"]) / 3000))
    chevron_positions = np.linspace(gene["start"] + 1500, gene["end"] - 1500, n_chevrons)
    for cx in chevron_positions:
        dx = 600 if gene["strand"] == "+" else -600
        ax_genes.plot(
            [cx - dx, cx, cx - dx],
            [y_center - 0.12, y_center, y_center + 0.12],
            color=gene_color,
            linewidth=1.2,
            alpha=0.5,
        )
    # Exon rectangles
    for exon_start, exon_end in gene["exons"]:
        rect = mpatches.FancyBboxPatch(
            (exon_start, y_center - 0.28),
            exon_end - exon_start,
            0.56,
            boxstyle="round,pad=0,rounding_size=200",
            facecolor=exon_color,
            edgecolor="white",
            linewidth=1.0,
        )
        ax_genes.add_patch(rect)
    # Gene label with text outline for clarity
    arrow_char = "\u25b6" if gene["strand"] == "+" else "\u25c0"
    mid_x = (gene["start"] + gene["end"]) / 2
    txt = ax_genes.text(
        mid_x,
        y_center + 0.48,
        f"{gene['name']} {arrow_char}",
        fontsize=14,
        va="bottom",
        ha="center",
        color="#222222",
        fontweight="semibold",
    )
    txt.set_path_effects([pe.withStroke(linewidth=3, foreground="white")])

ax_genes.set_ylim(-0.2, 1.3)
ax_genes.set_ylabel("Genes", fontsize=20, fontweight="medium", labelpad=15)
ax_genes.set_yticks([])
for spine in ax_genes.spines.values():
    spine.set_visible(False)
ax_genes.set_facecolor(track_bg_1)

# Track 2: Coverage
ax_cov = axes[1]
ax_cov.fill_between(coverage_positions, coverage_depth, alpha=0.35, color=coverage_color, linewidth=0)
ax_cov.fill_between(
    coverage_positions, coverage_depth, alpha=0.15, color=coverage_color, linewidth=0, where=coverage_depth > 0
)
ax_cov.plot(coverage_positions, coverage_depth, color=coverage_edge_color, linewidth=1.8, alpha=0.85)
ax_cov.set_ylabel("Coverage\n(read depth)", fontsize=20, fontweight="medium", labelpad=15)
ax_cov.set_ylim(0, coverage_depth.max() * 1.15)
ax_cov.tick_params(axis="y", labelsize=16)
ax_cov.spines["top"].set_visible(False)
ax_cov.spines["right"].set_visible(False)
ax_cov.yaxis.grid(True, alpha=0.15, linewidth=0.8)
ax_cov.set_facecolor(track_bg_2)

# Track 3: Variants (lollipop plot) — using LineCollection for stems
ax_var = axes[2]
stem_lines = []
snp_x, snp_y, indel_x, indel_y = [], [], [], []
for pos, vtype, qual in zip(variant_positions, variant_types, variant_quality, strict=False):
    stem_height = qual / 100
    stem_lines.append([(pos, 0), (pos, stem_height)])
    if vtype == "SNP":
        snp_x.append(pos)
        snp_y.append(stem_height)
    else:
        indel_x.append(pos)
        indel_y.append(stem_height)

# Draw all stems at once with LineCollection
stem_colors = [snp_color if vt == "SNP" else indel_color for vt in variant_types]
lc = LineCollection(stem_lines, colors=stem_colors, linewidths=2, alpha=0.6)
ax_var.add_collection(lc)

# Scatter markers — larger for visibility
ax_var.scatter(snp_x, snp_y, color=snp_color, marker="o", s=150, edgecolors="white", linewidth=1, zorder=3, label="SNP")
ax_var.scatter(
    indel_x, indel_y, color=indel_color, marker="D", s=120, edgecolors="white", linewidth=1, zorder=3, label="Indel"
)

ax_var.legend(fontsize=16, loc="upper right", framealpha=0.85, edgecolor="none", handletextpad=0.5, borderpad=0.4)
ax_var.set_ylabel("Variants\n(quality)", fontsize=20, fontweight="medium", labelpad=15)
ax_var.set_ylim(0, 1.25)
ax_var.set_yticks([0, 0.5, 1.0])
ax_var.set_yticklabels(["0", "50", "100"])
ax_var.tick_params(axis="y", labelsize=16)
ax_var.spines["top"].set_visible(False)
ax_var.spines["right"].set_visible(False)
ax_var.set_facecolor(track_bg_1)

# Track 4: Regulatory elements
ax_reg = axes[3]
reg_colors = {"Promoter": promoter_color, "Enhancer": enhancer_color, "Insulator": insulator_color}
for elem in regulatory_elements:
    color = reg_colors[elem["type"]]
    rect = mpatches.FancyBboxPatch(
        (elem["start"], 0.15),
        elem["end"] - elem["start"],
        0.7,
        boxstyle="round,pad=0,rounding_size=300",
        facecolor=color,
        edgecolor="white",
        linewidth=1.0,
        alpha=0.85,
    )
    ax_reg.add_patch(rect)
    # Label inside larger elements
    width = elem["end"] - elem["start"]
    if width > 2000:
        mid = (elem["start"] + elem["end"]) / 2
        txt = ax_reg.text(
            mid, 0.5, elem["type"][0], fontsize=12, ha="center", va="center", color="white", fontweight="bold"
        )
        txt.set_path_effects([pe.withStroke(linewidth=2, foreground=color)])

reg_patches = [mpatches.Patch(color=c, label=t) for t, c in reg_colors.items()]
ax_reg.legend(handles=reg_patches, fontsize=16, loc="upper right", framealpha=0.85, edgecolor="none", ncol=3)
ax_reg.set_ylim(0, 1.2)
ax_reg.set_ylabel("Regulatory", fontsize=20, fontweight="medium", labelpad=15)
ax_reg.set_yticks([])
ax_reg.spines["top"].set_visible(False)
ax_reg.spines["right"].set_visible(False)
ax_reg.spines["left"].set_visible(False)
ax_reg.set_facecolor(track_bg_2)

# Shared x-axis
ax_reg.set_xlim(region_start, region_end)
ax_reg.set_xlabel(f"Genomic Position — {chrom} (Mb)", fontsize=20)
ax_reg.tick_params(axis="x", labelsize=16)
ax_reg.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x / 1e6:.2f}"))

# Title
fig.suptitle("genome-track-multi \u00b7 matplotlib \u00b7 pyplots.ai", fontsize=24, fontweight="medium", y=0.98)

plt.savefig("plot.png", dpi=300, bbox_inches="tight")
