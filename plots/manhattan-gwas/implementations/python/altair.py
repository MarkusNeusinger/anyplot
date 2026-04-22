""" pyplots.ai
manhattan-gwas: Manhattan Plot for GWAS
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Simulated GWAS data with random p-values and significant peaks
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
chrom_label_df = pd.DataFrame(
    [{"chrom_label": chrom, "center": center, "y_pos": -0.5} for chrom, center in chrom_centers.items()]
)

# Define color scheme - alternating for chromosomes
color_scale = alt.Scale(
    domain=[str(i) for i in range(1, 23)],
    range=["#306998", "#7F7F7F"] * 11,  # Alternating Python blue and gray
)

# Main scatter plot
points = (
    alt.Chart(df)
    .mark_circle(opacity=0.7)
    .encode(
        x=alt.X(
            "cumulative_position:Q",
            axis=alt.Axis(title="Chromosome", labels=False, ticks=False, titleFontSize=22),
            scale=alt.Scale(domain=[0, cumulative_pos]),
        ),
        y=alt.Y(
            "neg_log_p:Q",
            title="-log₁₀(p-value)",
            axis=alt.Axis(titleFontSize=22, labelFontSize=16),
            scale=alt.Scale(domain=[0, max(df["neg_log_p"]) + 1]),
        ),
        color=alt.Color("chromosome:N", scale=color_scale, legend=None),
        size=alt.condition(
            alt.datum.neg_log_p > genome_wide_threshold,
            alt.value(100),  # Larger for significant hits
            alt.value(30),  # Smaller for others
        ),
        tooltip=["chromosome:N", "position:Q", "p_value:Q", "neg_log_p:Q"],
    )
)

# Genome-wide significance threshold line
gw_line = (
    alt.Chart(pd.DataFrame({"y": [genome_wide_threshold]}))
    .mark_rule(strokeDash=[8, 4], color="#E74C3C", strokeWidth=2)
    .encode(y="y:Q")
)

# Suggestive threshold line
sug_line = (
    alt.Chart(pd.DataFrame({"y": [suggestive_threshold]}))
    .mark_rule(strokeDash=[4, 4], color="#F39C12", strokeWidth=2)
    .encode(y="y:Q")
)

# Chromosome labels as text marks at bottom
chrom_text = (
    alt.Chart(chrom_label_df)
    .mark_text(fontSize=14, fontWeight="bold", baseline="top", dy=5)
    .encode(x=alt.X("center:Q", scale=alt.Scale(domain=[0, cumulative_pos])), text="chrom_label:N")
)

# Combine layers - points with threshold lines
main_chart = alt.layer(points, gw_line, sug_line).properties(width=1500, height=750)

# Chromosome labels at bottom
labels_chart = (
    alt.Chart(chrom_label_df)
    .mark_text(fontSize=16, baseline="middle")
    .encode(x=alt.X("center:Q", scale=alt.Scale(domain=[0, cumulative_pos]), axis=None), text="chrom_label:N")
    .properties(width=1500, height=30)
)

# Vertical concat with shared x-axis
chart = (
    alt.vconcat(main_chart, labels_chart, spacing=0)
    .properties(title=alt.Title("manhattan-gwas · altair · pyplots.ai", fontSize=28, anchor="middle"))
    .configure_axis(labelFontSize=16, titleFontSize=22, grid=True, gridOpacity=0.3)
    .configure_view(strokeWidth=0)
)

# Save as PNG and HTML
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
