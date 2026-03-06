"""pyplots.ai
genome-track-multi: Genome Track Viewer
Library: pygal | Python 3.13
Quality: pending | Created: 2026-03-06
"""

import importlib
import sys

import numpy as np


_script_dir = sys.path[0]
sys.path.remove(_script_dir)
pygal = importlib.import_module("pygal")
Style = importlib.import_module("pygal.style").Style
cairosvg = importlib.import_module("cairosvg")
sys.path.insert(0, _script_dir)

# Data - Synthetic genomic data for EGFR gene region on chromosome 7
np.random.seed(42)

chrom = "chr7"
region_start = 55_086_000
region_end = 55_280_000
region_length = region_end - region_start

# Gene annotations (EGFR gene - simplified exon structure)
gene_name = "EGFR"
gene_strand = "+"
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

# Coverage data - simulated read depth across region
n_coverage_points = 500
coverage_positions = np.linspace(region_start, region_end, n_coverage_points)
base_coverage = np.random.poisson(30, n_coverage_points).astype(float)
for exon_start, exon_end in exons:
    mask = (coverage_positions >= exon_start) & (coverage_positions <= exon_end)
    base_coverage[mask] += np.random.poisson(60, mask.sum())
coverage_values = np.convolve(base_coverage, np.ones(5) / 5, mode="same")

# Variants (SNPs and indels)
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

# Regulatory elements
regulatory = [
    {"start": 55_086_000, "end": 55_088_000, "type": "Promoter"},
    {"start": 55_100_000, "end": 55_105_000, "type": "Enhancer"},
    {"start": 55_130_000, "end": 55_135_000, "type": "Enhancer"},
    {"start": 55_170_000, "end": 55_173_000, "type": "Enhancer"},
    {"start": 55_210_000, "end": 55_213_000, "type": "Enhancer"},
    {"start": 55_245_000, "end": 55_248_000, "type": "CTCF"},
]

# Colors
EXON_COLOR = "#2E8B57"
INTRON_COLOR = "#2E8B57"
COVERAGE_COLOR = "#306998"
SNP_COLOR = "#DC143C"
INDEL_COLOR = "#E8A317"
PROMOTER_COLOR = "#9370DB"
ENHANCER_COLOR = "#FFD43B"
CTCF_COLOR = "#FF8C00"

# Layout
WIDTH = 4800
HEIGHT = 2700
MARGIN_TOP = 160
MARGIN_BOTTOM = 160
MARGIN_LEFT = 300
MARGIN_RIGHT = 80
PLOT_WIDTH = WIDTH - MARGIN_LEFT - MARGIN_RIGHT
PLOT_HEIGHT = HEIGHT - MARGIN_TOP - MARGIN_BOTTOM

track_names = ["Genes", "Coverage", "Variants", "Regulatory"]
n_tracks = len(track_names)
track_gap = 30
track_height = (PLOT_HEIGHT - (n_tracks - 1) * track_gap) / n_tracks


# Coordinate helpers
def pos_to_x(genomic_pos):
    return MARGIN_LEFT + (genomic_pos - region_start) / region_length * PLOT_WIDTH


def track_top(track_idx):
    return MARGIN_TOP + track_idx * (track_height + track_gap)


# Style
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#222222",
    foreground_subtle="#cccccc",
    colors=(COVERAGE_COLOR,),
    title_font_size=48,
    label_font_size=22,
    major_label_font_size=24,
    value_font_size=14,
    font_family="sans-serif",
)

# Create minimal pygal chart as structural base
chart = pygal.Line(
    width=WIDTH,
    height=HEIGHT,
    style=custom_style,
    title="EGFR Gene Region (chr7) \u00b7 genome-track-multi \u00b7 pygal \u00b7 pyplots.ai",
    show_legend=False,
    show_x_labels=False,
    show_y_labels=False,
    show_x_guides=False,
    show_y_guides=False,
    margin=0,
    margin_top=MARGIN_TOP,
    margin_bottom=MARGIN_BOTTOM,
    margin_left=MARGIN_LEFT,
    margin_right=MARGIN_RIGHT,
)
chart.add("placeholder", [None])

# Render base SVG
svg_str = chart.render(is_unicode=True)

# Build custom track elements
elements = []

# Track background shading
for i in range(n_tracks):
    y = track_top(i)
    bg_color = "#f8f8f8" if i % 2 == 0 else "#ffffff"
    elements.append(
        f'<rect x="{MARGIN_LEFT}" y="{y:.0f}" width="{PLOT_WIDTH}" height="{track_height:.0f}" fill="{bg_color}"/>'
    )

# Track labels
for i, name in enumerate(track_names):
    y = track_top(i) + track_height / 2 + 8
    elements.append(
        f'<text x="{MARGIN_LEFT - 20}" y="{y:.0f}" '
        f'font-family="sans-serif" font-size="28" fill="#333" '
        f'text-anchor="end" font-weight="bold">{name}</text>'
    )

# Track 1: Gene annotations
gene_track_y = track_top(0)
gene_center_y = gene_track_y + track_height / 2

gene_start_x = pos_to_x(exons[0][0])
gene_end_x = pos_to_x(exons[-1][1])

# Intron line
elements.append(
    f'<line x1="{gene_start_x:.1f}" y1="{gene_center_y:.1f}" '
    f'x2="{gene_end_x:.1f}" y2="{gene_center_y:.1f}" '
    f'stroke="{INTRON_COLOR}" stroke-width="3"/>'
)

# Exon rectangles
exon_height = track_height * 0.4
for es, ee in exons:
    x1 = pos_to_x(es)
    x2 = pos_to_x(ee)
    w = max(x2 - x1, 3)
    elements.append(
        f'<rect x="{x1:.1f}" y="{gene_center_y - exon_height / 2:.1f}" '
        f'width="{w:.1f}" height="{exon_height:.1f}" '
        f'fill="{EXON_COLOR}" rx="2" ry="2">'
        f"<title>Exon: {es:,}-{ee:,}</title></rect>"
    )

# Strand direction arrows (+ strand)
arrow_spacing = PLOT_WIDTH / 15
for j in range(1, 14):
    ax = gene_start_x + j * arrow_spacing
    if ax < gene_end_x - 20:
        genomic_pos = region_start + (ax - MARGIN_LEFT) / PLOT_WIDTH * region_length
        in_exon = any(es <= genomic_pos <= ee for es, ee in exons)
        if not in_exon:
            elements.append(
                f'<path d="M{ax - 8:.1f},{gene_center_y + 6:.1f} '
                f"L{ax + 8:.1f},{gene_center_y:.1f} "
                f'L{ax - 8:.1f},{gene_center_y - 6:.1f}" fill="none" '
                f'stroke="{INTRON_COLOR}" stroke-width="2.5"/>'
            )

# Gene name label
label_x = (gene_start_x + gene_end_x) / 2
elements.append(
    f'<text x="{label_x:.1f}" y="{gene_center_y - exon_height / 2 - 14:.1f}" '
    f'font-family="sans-serif" font-size="26" fill="{EXON_COLOR}" '
    f'text-anchor="middle" font-style="italic">{gene_name}</text>'
)

# Track 2: Coverage (filled area)
coverage_track_y = track_top(1)
max_coverage = float(coverage_values.max())
coverage_plot_height = track_height * 0.85
coverage_pad = (track_height - coverage_plot_height) / 2

path_points = []
for i, (pos, val) in enumerate(zip(coverage_positions, coverage_values, strict=True)):
    x = pos_to_x(pos)
    y = coverage_track_y + coverage_pad + coverage_plot_height - (val / max_coverage) * coverage_plot_height
    path_points.append(f"{'M' if i == 0 else 'L'}{x:.1f},{y:.1f}")

baseline_y = coverage_track_y + coverage_pad + coverage_plot_height
first_x = pos_to_x(coverage_positions[0])
last_x = pos_to_x(coverage_positions[-1])
area_path = " ".join(path_points) + f" L{last_x:.1f},{baseline_y:.1f} L{first_x:.1f},{baseline_y:.1f} Z"
elements.append(
    f'<path d="{area_path}" fill="{COVERAGE_COLOR}" fill-opacity="0.3" stroke="{COVERAGE_COLOR}" stroke-width="1.5"/>'
)

# Coverage y-axis ticks
for tick_val in [0, int(max_coverage / 2), int(max_coverage)]:
    tick_y = coverage_track_y + coverage_pad + coverage_plot_height - (tick_val / max_coverage) * coverage_plot_height
    elements.append(
        f'<text x="{MARGIN_LEFT - 10}" y="{tick_y + 6:.1f}" '
        f'font-family="sans-serif" font-size="18" fill="#999" '
        f'text-anchor="end">{tick_val}</text>'
    )

# Track 3: Variants (lollipop plot)
variant_track_y = track_top(2)
variant_baseline_y = variant_track_y + track_height * 0.85
max_quality = max(v["quality"] for v in variants)

for v in variants:
    x = pos_to_x(v["pos"])
    stem_height = (v["quality"] / max_quality) * track_height * 0.7
    stem_top_y = variant_baseline_y - stem_height
    color = SNP_COLOR if v["type"] == "SNP" else INDEL_COLOR
    radius = 8 if v["type"] == "SNP" else 10

    # Stem
    elements.append(
        f'<line x1="{x:.1f}" y1="{variant_baseline_y:.1f}" '
        f'x2="{x:.1f}" y2="{stem_top_y:.1f}" '
        f'stroke="{color}" stroke-width="2.5"/>'
    )
    # Head
    if v["type"] == "SNP":
        elements.append(
            f'<circle cx="{x:.1f}" cy="{stem_top_y:.1f}" r="{radius}" fill="{color}" '
            f'stroke="white" stroke-width="1.5">'
            f"<title>SNP at {v['pos']:,} (Q={v['quality']})</title></circle>"
        )
    else:
        elements.append(
            f'<rect x="{x - radius:.1f}" y="{stem_top_y - radius:.1f}" '
            f'width="{2 * radius}" height="{2 * radius}" fill="{color}" '
            f'stroke="white" stroke-width="1.5" rx="2">'
            f"<title>Indel at {v['pos']:,} (Q={v['quality']})</title></rect>"
        )

# Variant legend
legend_x = MARGIN_LEFT + PLOT_WIDTH - 300
legend_y = variant_track_y + 25
elements.append(f'<circle cx="{legend_x}" cy="{legend_y}" r="6" fill="{SNP_COLOR}"/>')
elements.append(
    f'<text x="{legend_x + 14}" y="{legend_y + 6}" font-family="sans-serif" font-size="20" fill="#333">SNP</text>'
)
elements.append(f'<rect x="{legend_x + 70}" y="{legend_y - 7}" width="14" height="14" fill="{INDEL_COLOR}" rx="2"/>')
elements.append(
    f'<text x="{legend_x + 90}" y="{legend_y + 6}" font-family="sans-serif" font-size="20" fill="#333">Indel</text>'
)

# Track 4: Regulatory elements
reg_track_y = track_top(3)
reg_center_y = reg_track_y + track_height / 2
reg_height = track_height * 0.45
reg_colors = {"Promoter": PROMOTER_COLOR, "Enhancer": ENHANCER_COLOR, "CTCF": CTCF_COLOR}

for reg in regulatory:
    x1 = pos_to_x(reg["start"])
    x2 = pos_to_x(reg["end"])
    w = max(x2 - x1, 4)
    color = reg_colors[reg["type"]]
    elements.append(
        f'<rect x="{x1:.1f}" y="{reg_center_y - reg_height / 2:.1f}" '
        f'width="{w:.1f}" height="{reg_height:.1f}" '
        f'fill="{color}" fill-opacity="0.8" rx="3" ry="3">'
        f"<title>{reg['type']}: {reg['start']:,}-{reg['end']:,}</title></rect>"
    )
    label_x = (x1 + x2) / 2
    elements.append(
        f'<text x="{label_x:.1f}" y="{reg_center_y + 6:.1f}" '
        f'font-family="sans-serif" font-size="18" fill="#333" '
        f'text-anchor="middle">{reg["type"]}</text>'
    )

# Regulatory legend
reg_legend_x = MARGIN_LEFT + PLOT_WIDTH - 460
reg_legend_y = reg_track_y + 25
for j, (rtype, rcolor) in enumerate(reg_colors.items()):
    lx = reg_legend_x + j * 155
    elements.append(f'<rect x="{lx}" y="{reg_legend_y - 8}" width="16" height="16" fill="{rcolor}" rx="2"/>')
    elements.append(
        f'<text x="{lx + 22}" y="{reg_legend_y + 6}" font-family="sans-serif" font-size="20" fill="#333">{rtype}</text>'
    )

# Track separator lines
for i in range(1, n_tracks):
    y = track_top(i) - track_gap / 2
    elements.append(
        f'<line x1="{MARGIN_LEFT}" y1="{y:.0f}" x2="{MARGIN_LEFT + PLOT_WIDTH}" y2="{y:.0f}" '
        f'stroke="#ddd" stroke-width="1.5"/>'
    )

# X-axis: genomic coordinates
x_axis_y = MARGIN_TOP + PLOT_HEIGHT + 10
tick_interval = 25_000
tick_start = ((region_start // tick_interval) + 1) * tick_interval

for tick_pos in range(tick_start, region_end, tick_interval):
    x = pos_to_x(tick_pos)
    elements.append(
        f'<line x1="{x:.1f}" y1="{x_axis_y}" x2="{x:.1f}" y2="{x_axis_y + 12}" stroke="#333" stroke-width="2"/>'
    )
    # Vertical guide (subtle)
    elements.append(
        f'<line x1="{x:.1f}" y1="{MARGIN_TOP}" x2="{x:.1f}" y2="{MARGIN_TOP + PLOT_HEIGHT}" '
        f'stroke="#e8e8e8" stroke-width="1" stroke-dasharray="4,4"/>'
    )
    label = f"{tick_pos / 1_000_000:.2f} Mb"
    elements.append(
        f'<text x="{x:.1f}" y="{x_axis_y + 40}" '
        f'font-family="sans-serif" font-size="22" fill="#333" '
        f'text-anchor="middle">{label}</text>'
    )

# X-axis label
elements.append(
    f'<text x="{MARGIN_LEFT + PLOT_WIDTH / 2}" y="{x_axis_y + 80}" '
    f'font-family="sans-serif" font-size="28" fill="#333" '
    f'text-anchor="middle">Genomic Position ({chrom})</text>'
)

# Inject custom elements before </svg>
all_elements = "\n".join(elements)
svg_output = svg_str.replace("</svg>", f"{all_elements}\n</svg>")
svg_output = svg_output.replace(">No data<", "><")

# Save PNG
cairosvg.svg2png(bytestring=svg_output.encode("utf-8"), write_to="plot.png")

# Save interactive HTML
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
