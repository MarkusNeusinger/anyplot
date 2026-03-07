""" pyplots.ai
genome-track-multi: Genome Track Viewer
Library: pygal 3.1.0 | Python 3.14.3
Quality: 89/100 | Created: 2026-03-06
"""

import importlib
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

# === Genomic data: EGFR gene region on chromosome 7 ===
chrom = "chr7"
region_start = 55_086_000
region_end = 55_280_000
region_length = region_end - region_start

exons = [
    (55_086_714, 55_087_058),
    (55_088_200, 55_088_590),
    (55_141_300, 55_141_640),
    (55_143_280, 55_143_580),
    (55_146_570, 55_146_830),
    (55_151_290, 55_151_612),
    (55_154_000, 55_154_209),
    (55_155_830, 55_156_100),
    (55_160_100, 55_160_300),
    (55_165_300, 55_165_520),
    (55_168_500, 55_168_680),
    (55_171_000, 55_171_280),
    (55_174_700, 55_174_890),
    (55_177_300, 55_177_500),
    (55_181_300, 55_181_500),
    (55_191_700, 55_191_900),
    (55_198_700, 55_198_950),
    (55_200_500, 55_200_760),
    (55_205_300, 55_205_550),
    (55_209_800, 55_210_050),
    (55_214_200, 55_214_500),
    (55_218_900, 55_219_200),
    (55_220_200, 55_220_490),
    (55_223_500, 55_223_750),
    (55_226_500, 55_226_800),
    (55_228_000, 55_228_400),
    (55_232_900, 55_233_150),
    (55_238_800, 55_240_817),
]

n_cov = 500
cov_pos = np.linspace(region_start, region_end, n_cov)
cov_base = np.random.poisson(30, n_cov).astype(float)
for es, ee in exons:
    mask = (cov_pos >= es) & (cov_pos <= ee)
    cov_base[mask] += np.random.poisson(60, mask.sum())
cov_vals = np.convolve(cov_base, np.ones(5) / 5, mode="same")

variants = [
    {"pos": 55_089_100, "type": "SNP", "quality": 95},
    {"pos": 55_092_500, "type": "SNP", "quality": 88},
    {"pos": 55_141_500, "type": "SNP", "quality": 72},
    {"pos": 55_143_400, "type": "indel", "quality": 65},
    {"pos": 55_152_300, "type": "SNP", "quality": 91},
    {"pos": 55_160_200, "type": "SNP", "quality": 80},
    {"pos": 55_174_800, "type": "SNP", "quality": 97},
    {"pos": 55_191_800, "type": "indel", "quality": 55},
    {"pos": 55_205_400, "type": "SNP", "quality": 85},
    {"pos": 55_220_350, "type": "SNP", "quality": 78},
    {"pos": 55_233_000, "type": "SNP", "quality": 92},
    {"pos": 55_239_500, "type": "SNP", "quality": 88},
]

regulatory = [
    {"start": 55_086_000, "end": 55_088_000, "type": "Promoter"},
    {"start": 55_100_000, "end": 55_105_000, "type": "Enhancer"},
    {"start": 55_130_000, "end": 55_135_000, "type": "Enhancer"},
    {"start": 55_170_000, "end": 55_173_000, "type": "Enhancer"},
    {"start": 55_210_000, "end": 55_213_000, "type": "Enhancer"},
    {"start": 55_245_000, "end": 55_248_000, "type": "CTCF"},
]

# === Colorblind-safe palette (Tol bright) ===
GENE_CLR = "#4477AA"
COV_CLR = "#66CCEE"
COV_STROKE = "#2277BB"
SNP_CLR = "#EE6677"
INDEL_CLR = "#AA3377"
PROM_CLR = "#CCBB44"
ENH_CLR = "#228833"
CTCF_CLR = "#EE8866"
TRACK_ACCENTS = [GENE_CLR, COV_STROKE, SNP_CLR, ENH_CLR]

# === Layout ===
WIDTH = 4800
HEIGHT = 2700
MARGIN_LEFT = 300
MARGIN_RIGHT = 100
MARGIN_TOP = 170
MARGIN_BOTTOM = 150
PLOT_W = WIDTH - MARGIN_LEFT - MARGIN_RIGHT
PLOT_H = HEIGHT - MARGIN_TOP - MARGIN_BOTTOM
N_TRACKS = 4
TRACK_GAP = 24
TRACK_H = (PLOT_H - (N_TRACKS - 1) * TRACK_GAP) / N_TRACKS

# Pygal internal data padding fraction (1/52 per side)
PYGAL_PAD = 1 / 52

# Normalize genomic positions to [0, 1]
norm_pos = (cov_pos - region_start) / region_length
norm_variants = [(v["pos"] - region_start) / region_length for v in variants]

# === Coverage chart: pygal.XY with fill + hermite interpolation + tooltips ===
cov_style = Style(
    background="transparent",
    plot_background="transparent",
    foreground="#333",
    foreground_strong="#333",
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

# === Variant chart: pygal.XY scatter with tooltips ===
var_style = Style(
    background="transparent",
    plot_background="transparent",
    foreground="#333",
    foreground_strong="#333",
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

# === Regulatory chart: pygal.Histogram for interval visualization with tooltips ===
reg_style = Style(
    background="transparent",
    plot_background="transparent",
    foreground="#333",
    foreground_strong="#333",
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
# Anchor bars at x=0 and x=1 (zero height, invisible) to lock x-range to [0, 1]
promoters.extend([(0, 0.0, 0.001), (0, 0.999, 1.0)])
reg_chart.add("Promoter", promoters)
reg_chart.add("Enhancer", enhancers)
reg_chart.add("CTCF", ctcf_els)
reg_svg_raw = reg_chart.render(is_unicode=True)

# === Helper to clean and embed pygal SVG ===
pad_x = PLOT_W * PYGAL_PAD
pad_y = TRACK_H * PYGAL_PAD
vb_w = PLOT_W - 2 * pad_x
vb_h = TRACK_H - 2 * pad_y


def embed_pygal_svg(raw_svg, track_y):
    """Strip XML/DOCTYPE, rewrite <svg> tag for embedding with viewBox alignment."""
    svg = re.sub(r"<\?xml[^?]*\?>\s*", "", raw_svg)
    svg = re.sub(r"<!DOCTYPE[^>]*>\s*", "", svg)
    svg_id = re.search(r'id="([^"]+)"', svg).group(1)
    svg = re.sub(
        r"<svg[^>]*>",
        f'<svg id="{svg_id}" class="pygal-chart" '
        f'x="{MARGIN_LEFT}" y="{track_y:.0f}" '
        f'width="{PLOT_W}" height="{TRACK_H:.0f}" '
        f'viewBox="{pad_x:.2f} {pad_y:.2f} {vb_w:.2f} {vb_h:.2f}">',
        svg,
        count=1,
    )
    return svg


# === Build composite SVG ===
parts = []
parts.append(
    f'<svg xmlns="http://www.w3.org/2000/svg" '
    f'xmlns:xlink="http://www.w3.org/1999/xlink" '
    f'width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">'
)
parts.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="white"/>')

# Title with decorative accent
title = "EGFR Gene Region (chr7) \u00b7 genome-track-multi \u00b7 pygal \u00b7 pyplots.ai"
parts.append(
    f'<text x="{WIDTH / 2}" y="72" font-family="sans-serif" font-size="44" '
    f'fill="#1a1a1a" text-anchor="middle" font-weight="bold">{title}</text>'
)
# Subtitle for context
parts.append(
    f'<text x="{WIDTH / 2}" y="105" font-family="sans-serif" font-size="24" '
    f'fill="#777" text-anchor="middle" font-style="italic">'
    f"Epidermal Growth Factor Receptor \u2014 28 exons, ~194 kb</text>"
)
# Accent gradient line under title
parts.append(
    "<defs>"
    f'<linearGradient id="titleAccent" x1="0" y1="0" x2="1" y2="0">'
    f'<stop offset="0%" stop-color="{GENE_CLR}" stop-opacity="0"/>'
    f'<stop offset="20%" stop-color="{GENE_CLR}" stop-opacity="0.8"/>'
    f'<stop offset="50%" stop-color="{COV_STROKE}" stop-opacity="0.8"/>'
    f'<stop offset="80%" stop-color="{SNP_CLR}" stop-opacity="0.8"/>'
    f'<stop offset="100%" stop-color="{SNP_CLR}" stop-opacity="0"/>'
    "</linearGradient></defs>"
)
accent_x = WIDTH * 0.2
accent_w = WIDTH * 0.6
parts.append(
    f'<line x1="{accent_x}" y1="120" x2="{accent_x + accent_w}" y2="120" stroke="url(#titleAccent)" stroke-width="3"/>'
)

# Track backgrounds, accent strips, labels, separators
track_names = ["Genes", "Coverage", "Variants", "Regulatory"]
for i in range(N_TRACKS):
    ty = MARGIN_TOP + i * (TRACK_H + TRACK_GAP)
    bg = "#f5f5f5" if i % 2 == 0 else "#ffffff"
    parts.append(f'<rect x="{MARGIN_LEFT}" y="{ty:.0f}" width="{PLOT_W}" height="{TRACK_H:.0f}" fill="{bg}"/>')
    # Left accent color strip
    parts.append(f'<rect x="{MARGIN_LEFT}" y="{ty:.0f}" width="5" height="{TRACK_H:.0f}" fill="{TRACK_ACCENTS[i]}"/>')
    parts.append(
        f'<text x="{MARGIN_LEFT - 20}" y="{ty + TRACK_H / 2 + 8:.0f}" '
        f'font-family="sans-serif" font-size="28" fill="#333" '
        f'text-anchor="end" font-weight="bold">{track_names[i]}</text>'
    )

for i in range(1, N_TRACKS):
    sy = MARGIN_TOP + i * (TRACK_H + TRACK_GAP) - TRACK_GAP / 2
    parts.append(
        f'<line x1="{MARGIN_LEFT}" y1="{sy:.0f}" x2="{MARGIN_LEFT + PLOT_W}" '
        f'y2="{sy:.0f}" stroke="#ddd" stroke-width="1.5"/>'
    )

# --- Track 1: Gene annotations (manual SVG — no pygal chart type for this) ---
gene_ty = MARGIN_TOP
gene_cy = gene_ty + TRACK_H / 2

gene_x1 = MARGIN_LEFT + (exons[0][0] - region_start) / region_length * PLOT_W
gene_x2 = MARGIN_LEFT + (exons[-1][1] - region_start) / region_length * PLOT_W

parts.append(
    f'<line x1="{gene_x1:.1f}" y1="{gene_cy:.1f}" x2="{gene_x2:.1f}" '
    f'y2="{gene_cy:.1f}" stroke="{GENE_CLR}" stroke-width="3"/>'
)

exon_h = TRACK_H * 0.45
for es, ee in exons:
    x1 = MARGIN_LEFT + (es - region_start) / region_length * PLOT_W
    x2 = MARGIN_LEFT + (ee - region_start) / region_length * PLOT_W
    w = max(x2 - x1, 8)
    parts.append(
        f'<rect x="{x1:.1f}" y="{gene_cy - exon_h / 2:.1f}" width="{w:.1f}" '
        f'height="{exon_h:.1f}" fill="{GENE_CLR}" rx="2">'
        f"<title>Exon: {es:,}-{ee:,}</title></rect>"
    )

for j in range(1, 14):
    ax = gene_x1 + j * PLOT_W / 15
    if ax < gene_x2 - 20:
        gpos = region_start + (ax - MARGIN_LEFT) / PLOT_W * region_length
        if not any(es <= gpos <= ee for es, ee in exons):
            parts.append(
                f'<path d="M{ax - 8:.1f},{gene_cy + 6:.1f} '
                f"L{ax + 8:.1f},{gene_cy:.1f} "
                f'L{ax - 8:.1f},{gene_cy - 6:.1f}" fill="none" '
                f'stroke="{GENE_CLR}" stroke-width="2.5"/>'
            )

parts.append(
    f'<text x="{(gene_x1 + gene_x2) / 2:.1f}" '
    f'y="{gene_cy - exon_h / 2 - 14:.1f}" font-family="sans-serif" '
    f'font-size="26" fill="{GENE_CLR}" text-anchor="middle" '
    f'font-style="italic" font-weight="600">EGFR</text>'
)
# Strand indicator
parts.append(
    f'<text x="{gene_x2 + 30:.1f}" y="{gene_cy + 8:.1f}" font-family="sans-serif" '
    f'font-size="22" fill="{GENE_CLR}" font-weight="bold">(+)</text>'
)

# --- Track 2: Coverage (embedded pygal.XY with fill + hermite interpolation) ---
cov_ty = MARGIN_TOP + 1 * (TRACK_H + TRACK_GAP)
parts.append(embed_pygal_svg(cov_svg_raw, cov_ty))

# Coverage y-axis ticks (prominent)
max_cov = float(cov_vals.max())
cov_range_max = max_cov * 1.05
for tick_val in [0, int(max_cov)]:
    frac = tick_val / cov_range_max
    tick_y = cov_ty + TRACK_H * (1 - frac)
    parts.append(
        f'<text x="{MARGIN_LEFT - 10}" y="{tick_y + 6:.1f}" font-family="sans-serif" '
        f'font-size="22" fill="#444" text-anchor="end" font-weight="500">{tick_val}x</text>'
    )

# Annotation: coverage-exon correlation callout
peak_exon = exons[27]  # last large exon (55,238,800-55,240,817)
peak_x = MARGIN_LEFT + ((peak_exon[0] + peak_exon[1]) / 2 - region_start) / region_length * PLOT_W
peak_cov_idx = np.argmin(np.abs(cov_pos - (peak_exon[0] + peak_exon[1]) / 2))
peak_cov_val = cov_vals[peak_cov_idx]
peak_frac = peak_cov_val / cov_range_max
peak_y = cov_ty + TRACK_H * (1 - peak_frac)
ann_x = peak_x + 120
ann_y = peak_y - 40
parts.append(
    f'<line x1="{peak_x:.1f}" y1="{peak_y:.1f}" x2="{ann_x:.1f}" y2="{ann_y:.1f}" '
    f'stroke="#555" stroke-width="1.5" stroke-dasharray="4,3"/>'
)
parts.append(
    f'<text x="{ann_x + 8:.1f}" y="{ann_y + 5:.1f}" font-family="sans-serif" '
    f'font-size="18" fill="#555" font-style="italic">coverage peak at exon</text>'
)

# --- Track 3: Variants (embedded pygal.XY scatter with tooltips) ---
var_ty = MARGIN_TOP + 2 * (TRACK_H + TRACK_GAP)
parts.append(embed_pygal_svg(var_svg_raw, var_ty))

# Variant legend
vleg_x = MARGIN_LEFT + PLOT_W - 280
vleg_y = var_ty + 25
parts.append(f'<circle cx="{vleg_x}" cy="{vleg_y}" r="7" fill="{SNP_CLR}"/>')
parts.append(f'<text x="{vleg_x + 14}" y="{vleg_y + 6}" font-family="sans-serif" font-size="22" fill="#333">SNP</text>')
parts.append(f'<rect x="{vleg_x + 80}" y="{vleg_y - 8}" width="15" height="15" fill="{INDEL_CLR}" rx="2"/>')
parts.append(
    f'<text x="{vleg_x + 102}" y="{vleg_y + 6}" font-family="sans-serif" font-size="22" fill="#333">Indel</text>'
)

# --- Track 4: Regulatory (embedded pygal.Histogram with tooltips) ---
reg_ty = MARGIN_TOP + 3 * (TRACK_H + TRACK_GAP)
parts.append(embed_pygal_svg(reg_svg_raw, reg_ty))

# Regulatory type labels above bars
reg_cy = reg_ty + TRACK_H / 2
reg_h = TRACK_H * 0.45
for reg in regulatory:
    x1 = MARGIN_LEFT + (reg["start"] - region_start) / region_length * PLOT_W
    x2 = MARGIN_LEFT + (reg["end"] - region_start) / region_length * PLOT_W
    parts.append(
        f'<text x="{(x1 + x2) / 2:.1f}" y="{reg_ty + 30:.1f}" '
        f'font-family="sans-serif" font-size="18" fill="#555" '
        f'text-anchor="middle">{reg["type"]}</text>'
    )

# Regulatory legend
rlx = MARGIN_LEFT + PLOT_W - 460
rly = reg_ty + TRACK_H - 30
reg_clrs = {"Promoter": PROM_CLR, "Enhancer": ENH_CLR, "CTCF": CTCF_CLR}
for j, (rtype, rclr) in enumerate(reg_clrs.items()):
    lx = rlx + j * 155
    parts.append(f'<rect x="{lx}" y="{rly - 8}" width="16" height="16" fill="{rclr}" rx="2"/>')
    parts.append(
        f'<text x="{lx + 22}" y="{rly + 6}" font-family="sans-serif" font-size="20" fill="#333">{rtype}</text>'
    )

# X-axis with genomic coordinates
xay = MARGIN_TOP + PLOT_H + 10
tick_interval = 25_000
tick_start = ((region_start // tick_interval) + 1) * tick_interval

for tick_pos in range(tick_start, region_end, tick_interval):
    x = MARGIN_LEFT + (tick_pos - region_start) / region_length * PLOT_W
    parts.append(f'<line x1="{x:.1f}" y1="{xay}" x2="{x:.1f}" y2="{xay + 12}" stroke="#333" stroke-width="2"/>')
    parts.append(
        f'<line x1="{x:.1f}" y1="{MARGIN_TOP}" x2="{x:.1f}" '
        f'y2="{MARGIN_TOP + PLOT_H}" stroke="#e8e8e8" stroke-width="1" '
        f'stroke-dasharray="4,4"/>'
    )
    parts.append(
        f'<text x="{x:.1f}" y="{xay + 40}" font-family="sans-serif" '
        f'font-size="22" fill="#333" text-anchor="middle">'
        f"{tick_pos / 1_000_000:.2f} Mb</text>"
    )

parts.append(
    f'<text x="{MARGIN_LEFT + PLOT_W / 2}" y="{xay + 80}" '
    f'font-family="sans-serif" font-size="28" fill="#333" '
    f'text-anchor="middle" font-weight="500">Genomic Position ({chrom})</text>'
)

parts.append("</svg>")
svg_output = "\n".join(parts)

# Save PNG
cairosvg.svg2png(bytestring=svg_output.encode("utf-8"), write_to="plot.png")

# Save HTML with pygal interactive tooltips
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>genome-track-multi - pygal</title>
    <style>
        body {{ margin: 0; display: flex; justify-content: center; align-items: center;
               min-height: 100vh; background: #f5f5f5; }}
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

with open("plot.html", "w", encoding="utf-8") as fout:
    fout.write(html_content)
