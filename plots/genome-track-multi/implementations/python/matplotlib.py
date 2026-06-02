"""anyplot.ai
genome-track-multi: Genome Track Viewer
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-06
"""

import os

import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint categorical palette — positions 1→7 assigned across all tracks
GENE_COLOR = "#009E73"  # position 1 — gene exons (★ first categorical series)
SNP_COLOR = "#C475FD"  # position 2 — SNP variants
COVERAGE_COLOR = "#4467A3"  # position 3 — read depth (blue: semantic fit for sequencing flow)
INDEL_COLOR = "#BD8233"  # position 4 — indel variants
PROMOTER_COLOR = "#AE3030"  # position 5 — promoter elements (active regulation)
ENHANCER_COLOR = "#2ABCCD"  # position 6 — enhancer elements
INSULATOR_COLOR = "#954477"  # position 7 — insulator elements

# Data: chr7 HOXA gene cluster region
np.random.seed(42)
chrom = "chr7"
region_start = 27_200_000
region_end = 27_280_000

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

# Coverage: simulated RNA-seq read depth
coverage_positions = np.linspace(region_start, region_end, 800)
coverage_base = np.random.exponential(5, 800)
for gene in genes:
    for exon_start, exon_end in gene["exons"]:
        mask = (coverage_positions >= exon_start) & (coverage_positions <= exon_end)
        coverage_base[mask] += np.random.exponential(40, mask.sum())
coverage_depth = np.convolve(coverage_base, np.ones(5) / 5, mode="same")

# Variants: SNPs and indels with quality scores
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
reg_colors = {"Promoter": PROMOTER_COLOR, "Enhancer": ENHANCER_COLOR, "Insulator": INSULATOR_COLOR}

# Exon positions collected for cross-track guide bands
all_exons = [exon for gene in genes for exon in gene["exons"]]

# Title (53 chars — within 67-char baseline, no scaling needed)
title = "genome-track-multi · python · matplotlib · anyplot.ai"

# Figure — 3200×1800 landscape canvas
fig, axes = plt.subplots(
    4, 1, figsize=(8, 4.5), dpi=400, sharex=True, facecolor=PAGE_BG, gridspec_kw={"height_ratios": [2, 2.5, 1.5, 1.5]}
)
fig.subplots_adjust(left=0.115, right=0.97, top=0.90, bottom=0.14, hspace=0.08)

# Subtle exon guide bands across all four tracks — connects peaks/variants/elements to gene exons
for ax in axes:
    ax.set_facecolor(PAGE_BG)
    for exon_s, exon_e in all_exons:
        ax.axvspan(exon_s, exon_e, alpha=0.05, color=GENE_COLOR, zorder=0)

# Track 1: Gene annotations
ax_genes = axes[0]
for gene in genes:
    yc = 0.5
    ax_genes.plot(
        [gene["start"], gene["end"]], [yc, yc], color=GENE_COLOR, linewidth=1.5, solid_capstyle="butt", alpha=0.45
    )
    n_chevrons = max(2, int((gene["end"] - gene["start"]) / 3000))
    for cx in np.linspace(gene["start"] + 1500, gene["end"] - 1500, n_chevrons):
        dx = 600 if gene["strand"] == "+" else -600
        ax_genes.plot([cx - dx, cx, cx - dx], [yc - 0.12, yc, yc + 0.12], color=GENE_COLOR, linewidth=1.0, alpha=0.55)
    for exon_start, exon_end in gene["exons"]:
        rect = mpatches.FancyBboxPatch(
            (exon_start, yc - 0.28),
            exon_end - exon_start,
            0.56,
            boxstyle="round,pad=0,rounding_size=200",
            facecolor=GENE_COLOR,
            edgecolor=PAGE_BG,
            linewidth=0.8,
        )
        ax_genes.add_patch(rect)
    arrow_char = "▶" if gene["strand"] == "+" else "◀"
    txt = ax_genes.text(
        (gene["start"] + gene["end"]) / 2,
        yc + 0.48,
        f"{gene['name']} {arrow_char}",
        fontsize=8,
        va="bottom",
        ha="center",
        color=INK,
        fontweight="semibold",
    )
    txt.set_path_effects([pe.withStroke(linewidth=2, foreground=PAGE_BG)])

ax_genes.set_ylim(-0.15, 1.35)
ax_genes.set_ylabel("Genes", fontsize=10, fontweight="medium", labelpad=6, color=INK)
ax_genes.set_yticks([])
for spine in ax_genes.spines.values():
    spine.set_visible(False)
ax_genes.tick_params(axis="x", which="both", bottom=False)

# Track 2: Coverage (RNA-seq depth)
ax_cov = axes[1]
ax_cov.set_axisbelow(True)
ax_cov.yaxis.grid(True, alpha=0.12, linewidth=0.6, color=INK)
ax_cov.fill_between(coverage_positions, coverage_depth, alpha=0.28, color=COVERAGE_COLOR, linewidth=0)
ax_cov.plot(coverage_positions, coverage_depth, color=COVERAGE_COLOR, linewidth=1.2, alpha=0.85)
ax_cov.set_ylabel("Coverage\n(depth)", fontsize=10, fontweight="medium", labelpad=6, color=INK)
ax_cov.set_ylim(0, coverage_depth.max() * 1.15)
ax_cov.tick_params(axis="y", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
ax_cov.tick_params(axis="x", which="both", bottom=False)
ax_cov.spines["top"].set_visible(False)
ax_cov.spines["right"].set_visible(False)
ax_cov.spines["bottom"].set_visible(False)
ax_cov.spines["left"].set_color(INK_SOFT)

# Track 3: Variants (lollipop chart)
ax_var = axes[2]
ax_var.set_axisbelow(True)
ax_var.yaxis.grid(True, alpha=0.12, linewidth=0.6, color=INK)
stem_lines, stem_colors_list = [], []
snp_x, snp_y, indel_x, indel_y = [], [], [], []
for pos, vtype, qual in zip(variant_positions, variant_types, variant_quality, strict=False):
    h = qual / 100
    stem_lines.append([(pos, 0), (pos, h)])
    stem_colors_list.append(SNP_COLOR if vtype == "SNP" else INDEL_COLOR)
    if vtype == "SNP":
        snp_x.append(pos)
        snp_y.append(h)
    else:
        indel_x.append(pos)
        indel_y.append(h)

ax_var.add_collection(LineCollection(stem_lines, colors=stem_colors_list, linewidths=1.5, alpha=0.55))
ax_var.scatter(
    snp_x, snp_y, color=SNP_COLOR, marker="o", s=55, edgecolors=PAGE_BG, linewidth=0.6, zorder=3, label="SNP"
)
ax_var.scatter(
    indel_x, indel_y, color=INDEL_COLOR, marker="D", s=45, edgecolors=PAGE_BG, linewidth=0.6, zorder=3, label="Indel"
)
leg_var = ax_var.legend(
    fontsize=8, loc="upper right", framealpha=0.9, edgecolor=INK_SOFT, handletextpad=0.4, borderpad=0.4
)
if leg_var:
    leg_var.get_frame().set_facecolor(ELEVATED_BG)
    plt.setp(leg_var.get_texts(), color=INK_SOFT)
ax_var.set_ylabel("Variants\n(quality)", fontsize=10, fontweight="medium", labelpad=6, color=INK)
ax_var.set_ylim(0, 1.3)
ax_var.set_yticks([0, 0.5, 1.0])
ax_var.set_yticklabels(["0", "50", "100"])
ax_var.tick_params(axis="y", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
ax_var.tick_params(axis="x", which="both", bottom=False)
ax_var.spines["top"].set_visible(False)
ax_var.spines["right"].set_visible(False)
ax_var.spines["bottom"].set_visible(False)
ax_var.spines["left"].set_color(INK_SOFT)

# Track 4: Regulatory elements
ax_reg = axes[3]
for elem in regulatory_elements:
    c = reg_colors[elem["type"]]
    rect = mpatches.FancyBboxPatch(
        (elem["start"], 0.15),
        elem["end"] - elem["start"],
        0.7,
        boxstyle="round,pad=0,rounding_size=300",
        facecolor=c,
        edgecolor=PAGE_BG,
        linewidth=0.8,
        alpha=0.88,
    )
    ax_reg.add_patch(rect)
    if elem["end"] - elem["start"] > 2000:
        txt = ax_reg.text(
            (elem["start"] + elem["end"]) / 2,
            0.5,
            elem["type"][0],
            fontsize=8,
            ha="center",
            va="center",
            color="white",
            fontweight="bold",
        )
        txt.set_path_effects([pe.withStroke(linewidth=2, foreground=c)])

reg_patches = [mpatches.Patch(color=c, label=t) for t, c in reg_colors.items()]
leg_reg = ax_reg.legend(handles=reg_patches, fontsize=8, loc="upper right", framealpha=0.9, edgecolor=INK_SOFT, ncol=3)
if leg_reg:
    leg_reg.get_frame().set_facecolor(ELEVATED_BG)
    plt.setp(leg_reg.get_texts(), color=INK_SOFT)
ax_reg.set_ylim(0, 1.2)
ax_reg.set_ylabel("Regulatory", fontsize=10, fontweight="medium", labelpad=6, color=INK)
ax_reg.set_yticks([])
ax_reg.spines["top"].set_visible(False)
ax_reg.spines["right"].set_visible(False)
ax_reg.spines["left"].set_visible(False)
ax_reg.spines["bottom"].set_color(INK_SOFT)

# Shared x-axis (displayed on bottom track only)
ax_reg.set_xlim(region_start, region_end)
ax_reg.set_xlabel(f"Genomic Position — {chrom} (Mb)", fontsize=10, color=INK)
ax_reg.tick_params(axis="x", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
ax_reg.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x / 1e6:.2f}"))

# Title
fig.suptitle(title, fontsize=12, fontweight="medium", color=INK, y=0.97)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
