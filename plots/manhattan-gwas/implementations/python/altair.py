""" anyplot.ai
manhattan-gwas: Manhattan Plot for GWAS
Library: altair 6.1.0 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-15
"""

import os

import altair as alt
import numpy as np
import pandas as pd


# Theme configuration
THEME = os.getenv("ANYPLOT_THEME", "light")

PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
RULE = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette for alternating chromosomes
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD"]

# Data generation
np.random.seed(42)

# Chromosome lengths (approximate human chromosome sizes in Mb)
chrom_lengths = {
    "1": 249,
    "2": 243,
    "3": 198,
    "4": 191,
    "5": 182,
    "6": 171,
    "7": 159,
    "8": 145,
    "9": 138,
    "10": 134,
    "11": 135,
    "12": 133,
    "13": 114,
    "14": 107,
    "15": 102,
    "16": 90,
    "17": 83,
    "18": 80,
    "19": 59,
    "20": 64,
    "21": 47,
    "22": 51,
}

# Generate SNPs for each chromosome
data = []
cumulative_pos = 0
chrom_centers = {}

for chrom, length in chrom_lengths.items():
    # Number of SNPs proportional to chromosome length
    n_snps = int(length * 20)  # ~20 SNPs per Mb
    positions = np.sort(np.random.randint(1, length * 1_000_000, n_snps))

    # Base p-values (mostly non-significant)
    pvalues = np.random.uniform(0.001, 1.0, n_snps)

    # Add some significant peaks on specific chromosomes
    if chrom in ["2", "6", "8", "15"]:
        n_sig = np.random.randint(5, 15)
        sig_indices = np.random.choice(n_snps, n_sig, replace=False)
        pvalues[sig_indices] = 10 ** np.random.uniform(-10, -7, n_sig)

    # Add suggestive hits on other chromosomes
    if chrom in ["3", "11", "19"]:
        n_sug = np.random.randint(3, 8)
        sug_indices = np.random.choice(n_snps, n_sug, replace=False)
        pvalues[sug_indices] = 10 ** np.random.uniform(-6, -5, n_sug)

    # Calculate cumulative positions
    cum_positions = positions + cumulative_pos
    chrom_centers[chrom] = cumulative_pos + (length * 1_000_000) / 2

    for pos, cum_pos, pval in zip(positions, cum_positions, pvalues, strict=True):
        data.append(
            {
                "chromosome": chrom,
                "position": pos,
                "cumulative_position": cum_pos,
                "p_value": pval,
                "neg_log_p": -np.log10(pval),
            }
        )

    cumulative_pos += length * 1_000_000

df = pd.DataFrame(data)

# Threshold values
genome_wide_threshold = -np.log10(5e-8)  # ~7.3
suggestive_threshold = -np.log10(1e-5)  # 5.0

# Create chromosome label data
chrom_label_df = pd.DataFrame([{"chrom_label": chrom, "center": center} for chrom, center in chrom_centers.items()])

# Create alternating color mapping with Okabe-Ito palette
chrom_list = list(chrom_lengths.keys())
color_mapping = {}
for i, chrom in enumerate(chrom_list):
    color_mapping[chrom] = IMPRINT[i % len(IMPRINT)]

color_scale = alt.Scale(domain=chrom_list, range=[color_mapping[chrom] for chrom in chrom_list])

# Main scatter plot
points = (
    alt.Chart(df)
    .mark_circle(opacity=0.7, size=80)
    .encode(
        x=alt.X(
            "cumulative_position:Q",
            axis=alt.Axis(title="Genomic Position", labels=False, ticks=False, titleFontSize=22, titleColor=INK),
            scale=alt.Scale(domain=[0, cumulative_pos]),
        ),
        y=alt.Y(
            "neg_log_p:Q",
            title="-log₁₀(p-value)",
            axis=alt.Axis(
                titleFontSize=22,
                labelFontSize=18,
                titleColor=INK,
                labelColor=INK_SOFT,
                domainColor=INK_SOFT,
                tickColor=INK_SOFT,
                gridColor=INK,
                gridOpacity=0.10,
            ),
            scale=alt.Scale(domain=[0, max(df["neg_log_p"]) + 1]),
        ),
        color=alt.Color("chromosome:N", scale=color_scale, legend=None),
        size=alt.condition(
            alt.datum.neg_log_p > genome_wide_threshold,
            alt.value(100),  # Larger for significant hits
            alt.value(60),  # Smaller for others
        ),
        tooltip=[
            "chromosome:N",
            alt.Tooltip("position:Q", format=","),
            alt.Tooltip("p_value:Q", format=".2e"),
            "neg_log_p:Q",
        ],
    )
)

# Genome-wide significance threshold line
gw_line = (
    alt.Chart(pd.DataFrame({"y": [genome_wide_threshold]}))
    .mark_rule(strokeDash=[8, 4], color=INK_MUTED, size=2, opacity=0.8)
    .encode(y="y:Q")
)

# Suggestive threshold line
sug_line = (
    alt.Chart(pd.DataFrame({"y": [suggestive_threshold]}))
    .mark_rule(strokeDash=[4, 4], color=INK_MUTED, size=1.5, opacity=0.6)
    .encode(y="y:Q")
)

# Chromosome labels at bottom
chrom_text = (
    alt.Chart(chrom_label_df)
    .mark_text(fontSize=16, baseline="top", dy=10, color=INK_SOFT, fontWeight="normal")
    .encode(x=alt.X("center:Q", axis=None, scale=alt.Scale(domain=[0, cumulative_pos])), text="chrom_label:N")
)

# Combine layers
main_chart = alt.layer(points, gw_line, sug_line).properties(width=1600, height=850)

# Final chart with labels
chart = (
    alt.vconcat(main_chart, chrom_text.properties(width=1600, height=40), spacing=5)
    .properties(
        title=alt.Title(
            "Manhattan Plot: GWAS Results",
            fontSize=28,
            anchor="middle",
            color=INK,
            subtitle="Genome-wide association study with significance thresholds",
        ),
        background=PAGE_BG,
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT, strokeWidth=1)
    .configure_axis(labelFontSize=18, titleFontSize=22, labelColor=INK_SOFT, titleColor=INK)
    .configure_title(fontSize=28, color=INK, subtitleFontSize=16, subtitleColor=INK_SOFT)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

# Save with theme-specific filenames
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
