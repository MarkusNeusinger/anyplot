""" pyplots.ai
genome-track-multi: Genome Track Viewer
Library: plotly 6.6.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-06
"""

import copy

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


np.random.seed(42)

# Genomic region: chr7, EGFR locus
chrom = "chr7"
region_start = 55_086_000
region_end = 55_280_000

# Gene track data - EGFR gene structure
gene_name = "EGFR"
strand = "+"
exons = [
    (55_086_714, 55_087_058),
    (55_152_580, 55_152_770),
    (55_154_000, 55_154_200),
    (55_155_830, 55_156_100),
    (55_160_100, 55_160_450),
    (55_165_300, 55_165_600),
    (55_168_500, 55_168_800),
    (55_174_700, 55_175_100),
    (55_181_300, 55_181_600),
    (55_191_700, 55_192_100),
    (55_198_700, 55_199_200),
    (55_200_700, 55_201_100),
    (55_209_900, 55_210_300),
    (55_211_000, 55_211_400),
    (55_218_900, 55_219_200),
    (55_220_200, 55_220_600),
    (55_223_500, 55_224_000),
    (55_227_900, 55_228_500),
    (55_229_200, 55_229_600),
    (55_231_400, 55_231_800),
    (55_233_800, 55_234_300),
    (55_236_300, 55_236_700),
    (55_238_800, 55_239_200),
    (55_240_500, 55_241_000),
    (55_249_000, 55_249_400),
    (55_259_400, 55_259_800),
    (55_266_400, 55_266_800),
    (55_268_800, 55_270_500),
]
gene_start = exons[0][0]
gene_end = exons[-1][1]

# Coverage track data - simulated RNA-seq read depth
positions = np.linspace(region_start, region_end, 2000)
base_coverage = np.random.exponential(5, 2000)
for ex_start, ex_end in exons:
    mask = (positions >= ex_start) & (positions <= ex_end)
    base_coverage[mask] += np.random.exponential(40, mask.sum())
coverage = np.convolve(base_coverage, np.ones(15) / 15, mode="same")

# Variant track data - SNPs and indels
variant_positions = [
    55_092_000,
    55_155_900,
    55_160_250,
    55_174_800,
    55_191_800,
    55_199_100,
    55_210_200,
    55_220_400,
    55_228_200,
    55_240_700,
    55_249_200,
    55_259_600,
    55_269_000,
]
variant_types = ["SNP", "SNP", "Indel", "SNP", "SNP", "SNP", "Indel", "SNP", "SNP", "SNP", "SNP", "Indel", "SNP"]
variant_quality = np.random.uniform(20, 99, len(variant_positions))
variant_labels = [
    "rs121434568",
    "rs28929495",
    "ins_3bp",
    "rs121913229",
    "rs1050171",
    "rs2227983",
    "del_2bp",
    "rs121434569",
    "rs56289927",
    "rs17290699",
    "rs10241451",
    "ins_5bp",
    "rs11543848",
]

# Regulatory track data - enhancers, promoters, CTCF sites
reg_elements = [
    (55_084_500, 55_086_700, "Promoter"),
    (55_100_000, 55_103_000, "Enhancer"),
    (55_130_000, 55_133_000, "CTCF"),
    (55_148_000, 55_151_000, "Enhancer"),
    (55_170_000, 55_172_500, "Enhancer"),
    (55_205_000, 55_208_000, "CTCF"),
    (55_245_000, 55_248_000, "Enhancer"),
    (55_272_000, 55_275_000, "Promoter"),
]

# Colors
python_blue = "#306998"
exon_color = "#306998"
intron_color = "#8FB0CC"
coverage_color = "#306998"
snp_color = "#D4763A"
indel_color = "#8B3A8B"
promoter_color = "#8E44AD"
enhancer_color = "#2980B9"
ctcf_color = "#F39C12"

# Plot - 4 tracks with shared x-axis
fig = make_subplots(
    rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.06, row_heights=[0.2, 0.35, 0.2, 0.2], subplot_titles=None
)

# Track 1: Gene annotations
gene_y = 0.5
# Intron line (full gene span)
fig.add_trace(
    go.Scatter(
        x=[gene_start, gene_end],
        y=[gene_y, gene_y],
        mode="lines",
        line={"color": intron_color, "width": 2},
        showlegend=False,
        hoverinfo="skip",
    ),
    row=1,
    col=1,
)

# Exon rectangles
for ex_start, ex_end in exons:
    fig.add_shape(
        type="rect",
        x0=ex_start,
        x1=ex_end,
        y0=0.2,
        y1=0.8,
        fillcolor=exon_color,
        line={"color": exon_color, "width": 1},
        row=1,
        col=1,
    )

# Strand direction arrows
arrow_positions = np.linspace(gene_start + 5000, gene_end - 5000, 12)
for pos in arrow_positions:
    in_exon = any(es <= pos <= ee for es, ee in exons)
    if not in_exon:
        fig.add_annotation(
            x=pos,
            y=gene_y,
            ax=pos - 2000,
            ay=gene_y,
            xref="x",
            yref="y",
            axref="x",
            ayref="y",
            showarrow=True,
            arrowhead=2,
            arrowsize=1.5,
            arrowwidth=1.5,
            arrowcolor=intron_color,
            row=1,
            col=1,
        )

# Gene label
fig.add_annotation(
    x=(gene_start + gene_end) / 2,
    y=1.1,
    text=f"<b>{gene_name}</b> ({strand})",
    showarrow=False,
    font={"size": 16, "color": exon_color},
    xref="x",
    yref="y",
    row=1,
    col=1,
)

# Track 2: Coverage
fig.add_trace(
    go.Scatter(
        x=positions,
        y=coverage,
        mode="lines",
        fill="tozeroy",
        fillcolor="rgba(48, 105, 152, 0.3)",
        line={"color": coverage_color, "width": 1.5},
        showlegend=False,
        hovertemplate="Position: %{x:,.0f}<br>Coverage: %{y:.1f}x<extra></extra>",
    ),
    row=2,
    col=1,
)

# Track 3: Variants (lollipop plot)
for _i, (pos, vtype, qual, label) in enumerate(
    zip(variant_positions, variant_types, variant_quality, variant_labels, strict=False)
):
    color = snp_color if vtype == "SNP" else indel_color
    # Stem
    fig.add_trace(
        go.Scatter(
            x=[pos, pos],
            y=[0, qual],
            mode="lines",
            line={"color": color, "width": 2},
            showlegend=False,
            hoverinfo="skip",
        ),
        row=3,
        col=1,
    )
    # Head
    fig.add_trace(
        go.Scatter(
            x=[pos],
            y=[qual],
            mode="markers",
            marker={
                "size": 10 if vtype == "SNP" else 12,
                "color": color,
                "symbol": "circle" if vtype == "SNP" else "diamond",
                "line": {"color": "white", "width": 1},
            },
            showlegend=False,
            hovertemplate=(f"{label}<br>Type: {vtype}<br>Position: {pos:,}<br>Quality: {qual:.1f}<extra></extra>"),
        ),
        row=3,
        col=1,
    )

# Variant legend entries
fig.add_trace(
    go.Scatter(
        x=[None], y=[None], mode="markers", marker={"size": 10, "color": snp_color, "symbol": "circle"}, name="SNP"
    ),
    row=3,
    col=1,
)
fig.add_trace(
    go.Scatter(
        x=[None], y=[None], mode="markers", marker={"size": 12, "color": indel_color, "symbol": "diamond"}, name="Indel"
    ),
    row=3,
    col=1,
)

# Track 4: Regulatory elements
reg_color_map = {"Promoter": promoter_color, "Enhancer": enhancer_color, "CTCF": ctcf_color}
added_legend = set()
for reg_start, reg_end, reg_type in reg_elements:
    show = reg_type not in added_legend
    added_legend.add(reg_type)
    fig.add_trace(
        go.Scatter(
            x=[reg_start, reg_start, reg_end, reg_end, reg_start],
            y=[0.1, 0.9, 0.9, 0.1, 0.1],
            fill="toself",
            fillcolor=reg_color_map[reg_type],
            line={"color": reg_color_map[reg_type], "width": 1},
            opacity=0.8,
            name=reg_type,
            showlegend=show,
            hovertemplate=(f"{reg_type}<br>{reg_start:,} - {reg_end:,}<extra></extra>"),
        ),
        row=4,
        col=1,
    )

# Track labels on left
track_labels = [(1, "Genes"), (2, "Coverage"), (3, "Variants"), (4, "Regulatory")]
for row, label in track_labels:
    fig.update_yaxes(title={"text": f"<b>{label}</b>", "font": {"size": 18}}, row=row, col=1)

# Layout
fig.update_layout(
    title={
        "text": (
            "EGFR Locus (chr7) · genome-track-multi · plotly · pyplots.ai"
            '<br><span style="font-size:16px;color:#666">Multi-track genome browser — chr7:55,086,000–55,280,000</span>'
        ),
        "font": {"size": 30},
        "x": 0.5,
    },
    template="plotly_white",
    height=900,
    width=1600,
    legend={"font": {"size": 16}, "orientation": "h", "yanchor": "top", "y": -0.06, "xanchor": "center", "x": 0.5},
    margin={"l": 100, "r": 40, "t": 100, "b": 110},
)

# X-axis formatting (genomic coordinates)
fig.update_xaxes(
    title={"text": "Genomic Position (bp)", "font": {"size": 22}},
    tickfont={"size": 16},
    tickformat=",",
    range=[region_start - 2000, region_end + 5000],
    rangeslider={"visible": True, "thickness": 0.06},
    row=4,
    col=1,
)
for row in range(1, 4):
    fig.update_xaxes(tickfont={"size": 16}, tickformat=",", showticklabels=False, row=row, col=1)

# Y-axis formatting per track
fig.update_yaxes(range=[-0.2, 1.4], showticklabels=False, showgrid=False, row=1, col=1)
fig.update_yaxes(tickfont={"size": 16}, gridcolor="rgba(200, 210, 220, 0.4)", gridwidth=1, row=2, col=1)
fig.update_yaxes(
    title={"text": "<b>Variants</b><br>Qual. Score", "font": {"size": 18}},
    tickfont={"size": 16},
    range=[-5, 110],
    row=3,
    col=1,
)
fig.update_yaxes(range=[-0.1, 1.1], showticklabels=False, showgrid=False, row=4, col=1)

# Subtle background shading for alternate tracks
for row in [1, 3]:
    fig.add_shape(
        type="rect",
        x0=0,
        x1=1,
        y0=0,
        y1=1,
        xref=f"x{row} domain" if row > 1 else "x domain",
        yref=f"y{row} domain" if row > 1 else "y domain",
        fillcolor="rgba(240, 245, 250, 0.5)",
        line={"width": 0},
        layer="below",
    )

# Colored left-edge accent strips for each track
track_accent_colors = {1: exon_color, 2: coverage_color, 3: snp_color, 4: promoter_color}
for row, accent_color in track_accent_colors.items():
    xref = f"x{row} domain" if row > 1 else "x domain"
    yref = f"y{row} domain" if row > 1 else "y domain"
    fig.add_shape(
        type="rect",
        x0=-0.005,
        x1=0.0,
        y0=0,
        y1=1,
        xref=xref,
        yref=yref,
        fillcolor=accent_color,
        line={"width": 0},
        layer="above",
    )

# Track divider lines for visual separation
for row in range(1, 5):
    yref = f"y{row} domain" if row > 1 else "y domain"
    fig.add_shape(
        type="line",
        x0=0,
        x1=1,
        y0=0,
        y1=0,
        xref=f"x{row} domain" if row > 1 else "x domain",
        yref=yref,
        line={"color": "rgba(180, 190, 200, 0.6)", "width": 1},
    )

# Save static PNG without rangeslider (cleaner layout)
fig_static = copy.deepcopy(fig)
fig_static.update_xaxes(rangeslider={"visible": False}, row=4, col=1)
fig_static.write_image("plot.png", width=1600, height=900, scale=3)

# Save HTML with rangeslider for interactive navigation
fig.write_html("plot.html", include_plotlyjs="cdn")
