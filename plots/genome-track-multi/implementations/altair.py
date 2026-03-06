"""pyplots.ai
genome-track-multi: Genome Track Viewer
Library: altair | Python 3.13
Quality: pending | Created: 2026-03-06
"""

import altair as alt
import numpy as np
import pandas as pd


# Data: Genomic region on chr7 (~50kb window)
np.random.seed(42)
chrom = "chr7"
region_start = 55_140_000
region_end = 55_190_000

# Gene track data: two genes with exon/intron structure
gene_bodies = pd.DataFrame(
    {
        "start": [55_142_000, 55_160_000],
        "end": [55_155_000, 55_178_000],
        "gene": ["EGFR", "VOPP1"],
        "strand": ["+", "-"],
        "y_pos": [1, 0],
    }
)

exons = pd.DataFrame(
    {
        "start": [
            55_142_000,
            55_144_500,
            55_148_000,
            55_152_000,
            55_160_000,
            55_163_000,
            55_167_000,
            55_171_000,
            55_175_000,
        ],
        "end": [
            55_143_200,
            55_145_800,
            55_149_500,
            55_154_800,
            55_161_500,
            55_164_200,
            55_168_800,
            55_172_500,
            55_177_800,
        ],
        "gene": ["EGFR", "EGFR", "EGFR", "EGFR", "VOPP1", "VOPP1", "VOPP1", "VOPP1", "VOPP1"],
        "y_pos": [1, 1, 1, 1, 0, 0, 0, 0, 0],
    }
)

# Coverage track data: simulated read depth
coverage_positions = np.arange(region_start, region_end, 200)
base_coverage = np.random.exponential(15, len(coverage_positions))
for _, row in exons.iterrows():
    mask = (coverage_positions >= row["start"]) & (coverage_positions <= row["end"])
    base_coverage[mask] += np.random.uniform(30, 60, mask.sum())
coverage_df = pd.DataFrame({"position": coverage_positions, "depth": base_coverage})

# Variant track data
n_variants = 18
variant_positions = np.sort(np.random.randint(region_start + 1000, region_end - 1000, n_variants))
variant_df = pd.DataFrame(
    {
        "position": variant_positions,
        "quality": np.random.uniform(20, 100, n_variants),
        "variant_type": np.random.choice(["SNP", "Indel"], n_variants, p=[0.8, 0.2]),
    }
)

# Regulatory track data
regulatory_df = pd.DataFrame(
    {
        "start": [55_140_500, 55_143_800, 55_158_000, 55_169_500, 55_180_000],
        "end": [55_141_800, 55_144_400, 55_159_500, 55_170_800, 55_182_000],
        "element_type": ["Promoter", "Enhancer", "Promoter", "Enhancer", "Enhancer"],
        "y_pos": [0, 0, 0, 0, 0],
    }
)

# Shared x scale
x_domain = [region_start, region_end]

# Track 1: Gene annotations
intron_lines = (
    alt.Chart(gene_bodies)
    .mark_rule(strokeWidth=2)
    .encode(
        x=alt.X("start:Q", scale=alt.Scale(domain=x_domain), axis=None),
        x2="end:Q",
        y=alt.Y("y_pos:Q", scale=alt.Scale(domain=[-0.5, 1.5]), axis=None),
        color=alt.value("#306998"),
    )
)

exon_bars = (
    alt.Chart(exons)
    .mark_bar(height=20)
    .encode(
        x=alt.X("start:Q", scale=alt.Scale(domain=x_domain)),
        x2="end:Q",
        y=alt.Y("y_pos:Q", scale=alt.Scale(domain=[-0.5, 1.5]), axis=None),
        color=alt.value("#306998"),
        tooltip=[alt.Tooltip("gene:N", title="Gene")],
    )
)

gene_names = (
    alt.Chart(gene_bodies)
    .mark_text(fontSize=16, fontWeight="bold", align="left", dx=5, dy=-16)
    .encode(
        x=alt.X("start:Q", scale=alt.Scale(domain=x_domain)),
        y=alt.Y("y_pos:Q", scale=alt.Scale(domain=[-0.5, 1.5]), axis=None),
        text=alt.Text("gene:N"),
        color=alt.value("#1a1a1a"),
    )
)

strand_df = gene_bodies.copy()
strand_df["arrow"] = strand_df["strand"].map({"+": ">>>", "-": "<<<"})

strand_marks = (
    alt.Chart(strand_df)
    .mark_text(fontSize=13, align="right", dx=-5)
    .encode(
        x=alt.X("end:Q", scale=alt.Scale(domain=x_domain)),
        y=alt.Y("y_pos:Q", scale=alt.Scale(domain=[-0.5, 1.5]), axis=None),
        text="arrow:N",
        color=alt.value("#306998"),
    )
)

gene_track = (intron_lines + exon_bars + gene_names + strand_marks).properties(
    width=1600, height=80, title=alt.Title("Genes", anchor="start", fontSize=18, color="#555")
)

# Track 2: Coverage (area plot)
coverage_track = (
    alt.Chart(coverage_df)
    .mark_area(interpolate="monotone", opacity=0.5, line={"color": "#306998", "strokeWidth": 1.5})
    .encode(
        x=alt.X("position:Q", scale=alt.Scale(domain=x_domain), axis=None),
        y=alt.Y("depth:Q", axis=alt.Axis(title="Read Depth", labelFontSize=14, titleFontSize=16, grid=False)),
        color=alt.value("#306998"),
        tooltip=[
            alt.Tooltip("position:Q", title="Position", format=","),
            alt.Tooltip("depth:Q", title="Depth", format=".1f"),
        ],
    )
    .properties(width=1600, height=160, title=alt.Title("Coverage", anchor="start", fontSize=18, color="#555"))
)

# Track 3: Variants (circles with quality on y-axis)
variant_color_scale = alt.Scale(domain=["SNP", "Indel"], range=["#E8590C", "#306998"])

variant_track = (
    alt.Chart(variant_df)
    .mark_circle(size=200)
    .encode(
        x=alt.X("position:Q", scale=alt.Scale(domain=x_domain), axis=None),
        y=alt.Y("quality:Q", axis=alt.Axis(title="Quality", labelFontSize=14, titleFontSize=16, grid=False)),
        color=alt.Color(
            "variant_type:N",
            scale=variant_color_scale,
            legend=alt.Legend(title="Type", labelFontSize=14, titleFontSize=16),
        ),
        tooltip=[
            alt.Tooltip("position:Q", title="Position", format=","),
            alt.Tooltip("quality:Q", title="Quality", format=".1f"),
            alt.Tooltip("variant_type:N", title="Type"),
        ],
    )
    .properties(width=1600, height=140, title=alt.Title("Variants", anchor="start", fontSize=18, color="#555"))
)

# Track 4: Regulatory elements
reg_color_scale = alt.Scale(domain=["Promoter", "Enhancer"], range=["#7B2D8E", "#228B22"])

regulatory_track = (
    alt.Chart(regulatory_df)
    .mark_bar(height=18, cornerRadius=3)
    .encode(
        x=alt.X(
            "start:Q",
            scale=alt.Scale(domain=x_domain),
            axis=alt.Axis(
                title=f"Genomic Position ({chrom})",
                labelFontSize=16,
                titleFontSize=20,
                labelExpr="format(datum.value, ',.0f')",
            ),
        ),
        x2="end:Q",
        y=alt.Y("y_pos:Q", scale=alt.Scale(domain=[-0.5, 0.5]), axis=None),
        color=alt.Color(
            "element_type:N",
            scale=reg_color_scale,
            legend=alt.Legend(title="Element", labelFontSize=14, titleFontSize=16),
        ),
        tooltip=[
            alt.Tooltip("element_type:N", title="Type"),
            alt.Tooltip("start:Q", title="Start", format=","),
            alt.Tooltip("end:Q", title="End", format=","),
        ],
    )
    .properties(width=1600, height=60, title=alt.Title("Regulatory", anchor="start", fontSize=18, color="#555"))
)

# Combine all tracks vertically
chart = (
    alt.vconcat(gene_track, coverage_track, variant_track, regulatory_track, spacing=15)
    .resolve_scale(color="independent")
    .properties(title=alt.Title("genome-track-multi · altair · pyplots.ai", fontSize=28, anchor="middle"))
    .configure_axis(labelFontSize=16, titleFontSize=20)
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
