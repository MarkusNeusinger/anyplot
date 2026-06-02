""" anyplot.ai
genome-track-multi: Genome Track Viewer
Library: pygal 3.1.0 | Python 3.13.13
Quality: 88/100 | Updated: 2026-06-02
"""

import importlib
import os
import re
import sys

import numpy as np


# Script filename matches library name; use importlib to avoid circular import
_script_dir = sys.path[0]
sys.path.remove(_script_dir)
pygal = importlib.import_module("pygal")
Style = importlib.import_module("pygal.style").Style
cairosvg = importlib.import_module("cairosvg")
sys.path.insert(0, _script_dir)

np.random.seed(42)

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — data series
GENE_CLR = "#4467A3"  # blue — gene exons (manual SVG, semantic: reference)
COV_CLR = "#009E73"  # brand green — coverage (first Imprint series)
COV_STROKE = "#007A59"  # darker green for fill edge
SNP_CLR = "#AE3030"  # matte red — SNPs (semantic: mutation)
INDEL_CLR = "#C475FD"  # lavender — indels
PROM_CLR = "#BD8233"  # ochre — promoters
ENH_CLR = "#2ABCCD"  # cyan — enhancers
CTCF_CLR = "#954477"  # rose — CTCF binding sites
TRACK_ACCENTS = [GENE_CLR, COV_CLR, SNP_CLR, ENH_CLR]

# === Genomic data: BRCA1 gene region on chromosome 17 ===
chrom = "chr17"
region_start = 41_150_000
region_end = 41_310_000
region_length = region_end - region_start

# BRCA1 exons — 23 exons, minus strand (~hg38 coordinates)
exons = [
    (41_196_312, 41_197_819),
    (41_199_659, 41_199_720),
    (41_203_079, 41_203_134),
    (41_209_068, 41_209_152),
    (41_215_349, 41_215_390),
    (41_219_624, 41_219_712),
    (41_222_944, 41_223_255),
    (41_226_347, 41_226_538),
    (41_228_504, 41_228_592),
    (41_234_415, 41_234_592),
    (41_238_000, 41_238_200),
    (41_242_961, 41_243_049),
    (41_246_877, 41_246_956),
    (41_249_260, 41_249_338),
    (41_251_791, 41_251_897),
    (41_256_139, 41_256_278),
    (41_258_473, 41_258_535),
    (41_267_742, 41_267_796),
    (41_270_711, 41_270_795),
    (41_273_218, 41_273_341),
    (41_276_033, 41_276_132),
    (41_277_186, 41_277_468),
    (41_277_500, 41_279_374),
]

n_cov = 500
cov_pos = np.linspace(region_start, region_end, n_cov)
cov_base = np.random.poisson(25, n_cov).astype(float)
for es, ee in exons:
    mask = (cov_pos >= es) & (cov_pos <= ee)
    cov_base[mask] += np.random.poisson(55, mask.sum())
cov_vals = np.convolve(cov_base, np.ones(5) / 5, mode="same")

variants = [
    {"pos": 41_197_000, "type": "SNP", "quality": 92},
    {"pos": 41_199_700, "type": "SNP", "quality": 85},
    {"pos": 41_203_100, "type": "indel", "quality": 62},
    {"pos": 41_209_100, "type": "SNP", "quality": 78},
    {"pos": 41_215_370, "type": "SNP", "quality": 95},
    {"pos": 41_219_660, "type": "SNP", "quality": 88},
    {"pos": 41_223_100, "type": "indel", "quality": 55},
    {"pos": 41_234_480, "type": "SNP", "quality": 91},
    {"pos": 41_243_000, "type": "SNP", "quality": 75},
    {"pos": 41_249_300, "type": "SNP", "quality": 82},
    {"pos": 41_256_200, "type": "SNP", "quality": 97},
    {"pos": 41_267_770, "type": "indel", "quality": 68},
    {"pos": 41_277_200, "type": "SNP", "quality": 89},
]

regulatory = [
    {"start": 41_150_000, "end": 41_153_000, "type": "Promoter"},
    {"start": 41_170_000, "end": 41_175_000, "type": "Enhancer"},
    {"start": 41_190_000, "end": 41_196_000, "type": "Promoter"},
    {"start": 41_225_000, "end": 41_229_000, "type": "Enhancer"},
    {"start": 41_260_000, "end": 41_264_000, "type": "Enhancer"},
    {"start": 41_300_000, "end": 41_304_000, "type": "CTCF"},
]

# === Layout: 3200 × 1800 composite SVG ===
WIDTH = 3200
HEIGHT = 1800
MARGIN_LEFT = 240
MARGIN_RIGHT = 80
MARGIN_TOP = 140
MARGIN_BOTTOM = 120
PLOT_W = WIDTH - MARGIN_LEFT - MARGIN_RIGHT  # 2880
PLOT_H = HEIGHT - MARGIN_TOP - MARGIN_BOTTOM  # 1540
N_TRACKS = 4
TRACK_GAP = 20
TRACK_H = (PLOT_H - (N_TRACKS - 1) * TRACK_GAP) / N_TRACKS  # 370.0

PYGAL_PAD = 1 / 52  # pygal internal margin fraction per side

norm_pos = (cov_pos - region_start) / region_length
norm_variants = [(v["pos"] - region_start) / region_length for v in variants]

# === Coverage chart: pygal.XY fill + hermite interpolation ===
cov_style = Style(
    background="transparent",
    plot_background="transparent",
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle="transparent",
    colors=(COV_CLR,),
    font_family="sans-serif",
    tooltip_font_size=18,
)
cov_chart = pygal.XY(
    width=int(PLOT_W),
    height=int(TRACK_H),
    style=cov_style,
    fill=True,
    show_legend=False,
    show_x_labels=False,
    show_y_labels=False,
    show_x_guides=False,
    show_y_guides=False,
    margin=0,
    interpolate="hermite",
    dots_size=0,
    stroke_style={"width": 2, "color": COV_STROKE},
    range=(0, float(cov_vals.max() * 1.05)),
)
cov_xy = [
    {"value": (float(nx), float(v)), "label": f"Depth: {v:.0f}x at {p / 1e6:.3f} Mb"}
    for nx, p, v in zip(norm_pos, cov_pos, cov_vals, strict=True)
]
cov_chart.add("Read Depth", cov_xy)
cov_svg_raw = cov_chart.render(is_unicode=True)

# === Variant chart: pygal.XY scatter ===
var_style = Style(
    background="transparent",
    plot_background="transparent",
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle="transparent",
    colors=(SNP_CLR, INDEL_CLR),
    font_family="sans-serif",
    tooltip_font_size=18,
)
var_chart = pygal.XY(
    width=int(PLOT_W),
    height=int(TRACK_H),
    style=var_style,
    show_legend=False,
    show_x_labels=False,
    show_y_labels=False,
    show_x_guides=False,
    show_y_guides=False,
    margin=0,
    dots_size=10,
    stroke=False,
    range=(0, 105),
)
snp_series = [
    {"value": (float(nv), float(v["quality"])), "label": f"SNP at {v['pos']:,} (Q={v['quality']})"}
    for v, nv in zip(variants, norm_variants, strict=True)
    if v["type"] == "SNP"
]
indel_series = [
    {"value": (float(nv), float(v["quality"])), "label": f"Indel at {v['pos']:,} (Q={v['quality']})"}
    for v, nv in zip(variants, norm_variants, strict=True)
    if v["type"] == "indel"
]
var_chart.add("SNP", snp_series)
var_chart.add("Indel", indel_series)
var_svg_raw = var_chart.render(is_unicode=True)

# === Regulatory chart: pygal.Histogram for interval bars ===
reg_style = Style(
    background="transparent",
    plot_background="transparent",
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle="transparent",
    colors=(PROM_CLR, ENH_CLR, CTCF_CLR),
    font_family="sans-serif",
    tooltip_font_size=18,
)
reg_chart = pygal.Histogram(
    width=int(PLOT_W),
    height=int(TRACK_H),
    style=reg_style,
    show_legend=False,
    show_x_labels=False,
    show_y_labels=False,
    show_x_guides=False,
    show_y_guides=False,
    margin=0,
    range=(0, 1.5),
)
promoters = [
    (1.0, (r["start"] - region_start) / region_length, (r["end"] - region_start) / region_length)
    for r in regulatory
    if r["type"] == "Promoter"
]
enhancers = [
    (1.0, (r["start"] - region_start) / region_length, (r["end"] - region_start) / region_length)
    for r in regulatory
    if r["type"] == "Enhancer"
]
ctcf_els = [
    (1.0, (r["start"] - region_start) / region_length, (r["end"] - region_start) / region_length)
    for r in regulatory
    if r["type"] == "CTCF"
]
# Anchor bars at x=0 and x=1 to lock the histogram x-range
promoters.extend([(0, 0.0, 0.001), (0, 0.999, 1.0)])
reg_chart.add("Promoter", promoters)
reg_chart.add("Enhancer", enhancers)
reg_chart.add("CTCF", ctcf_els)
reg_svg_raw = reg_chart.render(is_unicode=True)

# Precomputed viewBox padding for embedding pygal SVGs
pad_x = PLOT_W * PYGAL_PAD
pad_y = TRACK_H * PYGAL_PAD
vb_w = PLOT_W - 2 * pad_x
vb_h = TRACK_H - 2 * pad_y


def embed_pygal_svg(raw_svg, track_y):
    svg = re.sub(r"<\?xml[^?]*\?>\s*", "", raw_svg)
    svg = re.sub(r"<!DOCTYPE[^>]*>\s*", "", svg)
    svg_id = re.search(r'id="([^"]+)"', svg).group(1)
    return re.sub(
        r"<svg[^>]*>",
        f'<svg id="{svg_id}" class="pygal-chart" '
        f'x="{MARGIN_LEFT}" y="{track_y:.0f}" '
        f'width="{PLOT_W}" height="{TRACK_H:.0f}" '
        f'viewBox="{pad_x:.2f} {pad_y:.2f} {vb_w:.2f} {vb_h:.2f}">',
        svg,
        count=1,
    )


# === Build composite SVG ===
parts = []
parts.append(
    f'<svg xmlns="http://www.w3.org/2000/svg" '
    f'xmlns:xlink="http://www.w3.org/1999/xlink" '
    f'width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">'
)
parts.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{PAGE_BG}"/>')

# Clip path constrains track label text to the plot area
parts.append(
    f"<defs>"
    f'<clipPath id="plotArea">'
    f'<rect x="{MARGIN_LEFT}" y="{MARGIN_TOP}" width="{PLOT_W}" height="{PLOT_H}"/>'
    f"</clipPath>"
    f'<linearGradient id="hdr" x1="0" y1="0" x2="1" y2="0">'
    f'<stop offset="0%" stop-color="{GENE_CLR}" stop-opacity="0"/>'
    f'<stop offset="25%" stop-color="{GENE_CLR}" stop-opacity="0.8"/>'
    f'<stop offset="55%" stop-color="{COV_CLR}" stop-opacity="0.8"/>'
    f'<stop offset="80%" stop-color="{SNP_CLR}" stop-opacity="0.8"/>'
    f'<stop offset="100%" stop-color="{SNP_CLR}" stop-opacity="0"/>'
    f"</linearGradient>"
    f"</defs>"
)

# Title area
title = "BRCA1 Gene Region (chr17) · genome-track-multi · python · pygal · anyplot.ai"
title_fs = max(44, round(66 * 67 / len(title)))
parts.append(
    f'<text x="{WIDTH / 2}" y="68" font-family="sans-serif" font-size="{title_fs}" '
    f'fill="{INK}" text-anchor="middle" font-weight="bold">{title}</text>'
)
parts.append(
    f'<text x="{WIDTH / 2}" y="100" font-family="sans-serif" font-size="26" '
    f'fill="{INK_MUTED}" text-anchor="middle" font-style="italic">'
    f"Breast Cancer Susceptibility Gene 1 — 23 exons, ~83 kb</text>"
)
parts.append(f'<line x1="{WIDTH * 0.15}" y1="116" x2="{WIDTH * 0.85}" y2="116" stroke="url(#hdr)" stroke-width="3"/>')

# Track backgrounds, accent strips, labels
track_names = ["Genes", "Coverage", "Variants", "Regulatory"]
track_bgrounds = [PAGE_BG, ELEVATED_BG, PAGE_BG, ELEVATED_BG]
for i in range(N_TRACKS):
    ty = MARGIN_TOP + i * (TRACK_H + TRACK_GAP)
    parts.append(
        f'<rect x="{MARGIN_LEFT}" y="{ty:.0f}" width="{PLOT_W}" height="{TRACK_H:.0f}" fill="{track_bgrounds[i]}"/>'
    )
    parts.append(f'<rect x="{MARGIN_LEFT}" y="{ty:.0f}" width="5" height="{TRACK_H:.0f}" fill="{TRACK_ACCENTS[i]}"/>')
    parts.append(
        f'<text x="{MARGIN_LEFT - 14}" y="{ty + TRACK_H / 2 + 9:.0f}" '
        f'font-family="sans-serif" font-size="25" fill="{INK_SOFT}" '
        f'text-anchor="end" font-weight="bold">{track_names[i]}</text>'
    )

# Track separators
for i in range(1, N_TRACKS):
    sy = MARGIN_TOP + i * (TRACK_H + TRACK_GAP) - TRACK_GAP / 2
    parts.append(
        f'<line x1="{MARGIN_LEFT}" y1="{sy:.0f}" '
        f'x2="{MARGIN_LEFT + PLOT_W}" y2="{sy:.0f}" '
        f'stroke="{INK_MUTED}" stroke-width="1" stroke-opacity="0.35"/>'
    )

# Vertical position grid lines (shared across all tracks)
tick_interval = 20_000
tick_start = ((region_start // tick_interval) + 1) * tick_interval
for tick_pos in range(tick_start, region_end, tick_interval):
    tx = MARGIN_LEFT + (tick_pos - region_start) / region_length * PLOT_W
    parts.append(
        f'<line x1="{tx:.1f}" y1="{MARGIN_TOP}" x2="{tx:.1f}" '
        f'y2="{MARGIN_TOP + PLOT_H}" stroke="{INK_MUTED}" '
        f'stroke-width="0.8" stroke-dasharray="4,4" stroke-opacity="0.3"/>'
    )

# --- Track 1: Gene annotations (manual SVG — BRCA1, minus strand) ---
gene_ty = MARGIN_TOP
gene_cy = gene_ty + TRACK_H / 2
gene_x1 = MARGIN_LEFT + (exons[0][0] - region_start) / region_length * PLOT_W
gene_x2 = MARGIN_LEFT + (exons[-1][1] - region_start) / region_length * PLOT_W

parts.append(
    f'<line x1="{gene_x1:.1f}" y1="{gene_cy:.1f}" x2="{gene_x2:.1f}" '
    f'y2="{gene_cy:.1f}" stroke="{GENE_CLR}" stroke-width="2.5"/>'
)

exon_h = TRACK_H * 0.46
for es, ee in exons:
    ex1 = MARGIN_LEFT + (es - region_start) / region_length * PLOT_W
    ex2 = MARGIN_LEFT + (ee - region_start) / region_length * PLOT_W
    ew = max(ex2 - ex1, 7)
    parts.append(
        f'<rect x="{ex1:.1f}" y="{gene_cy - exon_h / 2:.1f}" width="{ew:.1f}" '
        f'height="{exon_h:.1f}" fill="{GENE_CLR}" rx="2">'
        f"<title>Exon: {es:,}–{ee:,}</title></rect>"
    )

# Minus-strand chevrons (left-pointing) at intron positions
for j in range(1, 13):
    ax = gene_x2 - j * PLOT_W / 14
    if ax > gene_x1 + 20:
        gpos = region_start + (ax - MARGIN_LEFT) / PLOT_W * region_length
        if not any(es <= gpos <= ee for es, ee in exons):
            parts.append(
                f'<path d="M{ax + 8:.1f},{gene_cy + 6:.1f} '
                f"L{ax - 8:.1f},{gene_cy:.1f} "
                f'L{ax + 8:.1f},{gene_cy - 6:.1f}" fill="none" '
                f'stroke="{GENE_CLR}" stroke-width="2"/>'
            )

parts.append(
    f'<text x="{(gene_x1 + gene_x2) / 2:.1f}" '
    f'y="{gene_cy - exon_h / 2 - 12:.1f}" '
    f'font-family="sans-serif" font-size="24" fill="{GENE_CLR}" '
    f'text-anchor="middle" font-style="italic" font-weight="600">BRCA1</text>'
)
parts.append(
    f'<text x="{gene_x2 + 22:.1f}" y="{gene_cy + 8:.1f}" '
    f'font-family="sans-serif" font-size="20" fill="{GENE_CLR}" '
    f'font-weight="bold">(−)</text>'
)

# --- Track 2: Coverage (embedded pygal.XY) ---
cov_ty = MARGIN_TOP + 1 * (TRACK_H + TRACK_GAP)
parts.append(embed_pygal_svg(cov_svg_raw, cov_ty))

max_cov = float(cov_vals.max())
cov_range_max = max_cov * 1.05
for tick_val in [0, int(max_cov)]:
    frac = tick_val / cov_range_max
    tick_y = cov_ty + TRACK_H * (1 - frac)
    parts.append(
        f'<text x="{MARGIN_LEFT - 8}" y="{tick_y + 6:.1f}" '
        f'font-family="sans-serif" font-size="19" fill="{INK_SOFT}" '
        f'text-anchor="end" font-weight="500">{tick_val}x</text>'
    )

# --- Track 3: Variants (embedded pygal.XY scatter) ---
var_ty = MARGIN_TOP + 2 * (TRACK_H + TRACK_GAP)
parts.append(embed_pygal_svg(var_svg_raw, var_ty))

vleg_x = MARGIN_LEFT + PLOT_W - 250
vleg_y = var_ty + 26
parts.append(f'<circle cx="{vleg_x}" cy="{vleg_y}" r="7" fill="{SNP_CLR}"/>')
parts.append(
    f'<text x="{vleg_x + 14}" y="{vleg_y + 6}" font-family="sans-serif" font-size="19" fill="{INK_SOFT}">SNP</text>'
)
parts.append(f'<rect x="{vleg_x + 72}" y="{vleg_y - 8}" width="14" height="14" fill="{INDEL_CLR}" rx="2"/>')
parts.append(
    f'<text x="{vleg_x + 92}" y="{vleg_y + 6}" font-family="sans-serif" font-size="19" fill="{INK_SOFT}">Indel</text>'
)

# --- Track 4: Regulatory (embedded pygal.Histogram) ---
reg_ty = MARGIN_TOP + 3 * (TRACK_H + TRACK_GAP)
parts.append(embed_pygal_svg(reg_svg_raw, reg_ty))

parts.append('<g clip-path="url(#plotArea)">')
for reg in regulatory:
    rx1 = MARGIN_LEFT + (reg["start"] - region_start) / region_length * PLOT_W
    rx2 = MARGIN_LEFT + (reg["end"] - region_start) / region_length * PLOT_W
    parts.append(
        f'<text x="{(rx1 + rx2) / 2:.1f}" y="{reg_ty + 30:.1f}" '
        f'font-family="sans-serif" font-size="17" fill="{INK_MUTED}" '
        f'text-anchor="middle">{reg["type"]}</text>'
    )
parts.append("</g>")

rlx = MARGIN_LEFT + PLOT_W - 410
rly = reg_ty + TRACK_H - 28
for j, (rtype, rclr) in enumerate({"Promoter": PROM_CLR, "Enhancer": ENH_CLR, "CTCF": CTCF_CLR}.items()):
    lx = rlx + j * 138
    parts.append(f'<rect x="{lx}" y="{rly - 8}" width="14" height="14" fill="{rclr}" rx="2"/>')
    parts.append(
        f'<text x="{lx + 20}" y="{rly + 6}" font-family="sans-serif" font-size="18" fill="{INK_SOFT}">{rtype}</text>'
    )

# X-axis ticks and labels
xay = MARGIN_TOP + PLOT_H + 8
for tick_pos in range(tick_start, region_end, tick_interval):
    tx = MARGIN_LEFT + (tick_pos - region_start) / region_length * PLOT_W
    parts.append(
        f'<line x1="{tx:.1f}" y1="{xay}" x2="{tx:.1f}" y2="{xay + 10}" stroke="{INK_SOFT}" stroke-width="1.5"/>'
    )
    parts.append(
        f'<text x="{tx:.1f}" y="{xay + 33}" font-family="sans-serif" '
        f'font-size="19" fill="{INK_SOFT}" text-anchor="middle">'
        f"{tick_pos / 1_000_000:.2f} Mb</text>"
    )

parts.append(
    f'<text x="{MARGIN_LEFT + PLOT_W / 2}" y="{xay + 73}" '
    f'font-family="sans-serif" font-size="24" fill="{INK}" '
    f'text-anchor="middle" font-weight="500">Genomic Position ({chrom})</text>'
)

parts.append("</svg>")
svg_output = "\n".join(parts)

# Save PNG — cairosvg renders at the declared 3200×1800 SVG dimensions
cairosvg.svg2png(
    bytestring=svg_output.encode("utf-8"), write_to=f"plot-{THEME}.png", output_width=WIDTH, output_height=HEIGHT
)

# Save HTML with pygal interactive tooltips
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>genome-track-multi - pygal</title>
    <style>
        body {{ margin: 0; display: flex; justify-content: center; align-items: center;
               min-height: 100vh; background: {PAGE_BG}; }}
        .chart {{ max-width: 100%; height: auto; }}
    </style>
</head>
<body>
    <figure class="chart">
        {svg_output}
    </figure>
</body>
</html>
"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as fout:
    fout.write(html_content)
