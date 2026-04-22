""" pyplots.ai
manhattan-gwas: Manhattan Plot for GWAS
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-31
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Data - Simulated GWAS results
np.random.seed(42)

# Chromosome lengths (simplified, in Mb)
chr_lengths = {
    "1": 249,
    "2": 243,
    "3": 198,
    "4": 191,
    "5": 182,
    "6": 171,
    "7": 159,
    "8": 146,
    "9": 141,
    "10": 136,
    "11": 135,
    "12": 134,
    "13": 115,
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
chr_centers = {}

for chrom, length in chr_lengths.items():
    # Number of SNPs proportional to chromosome length
    n_snps = int(length * 40)
    positions = np.sort(np.random.uniform(0, length * 1e6, n_snps))

    # Generate p-values (mostly non-significant, with some peaks)
    pvalues = np.random.uniform(0, 1, n_snps)

    # Add significant peaks on chromosomes 2, 8, and 15
    if chrom == "2":
        peak_idx = np.abs(positions - 100e6).argmin()
        pvalues[peak_idx - 5 : peak_idx + 5] = 10 ** (-np.random.uniform(8, 12, 10))
    elif chrom == "8":
        peak_idx = np.abs(positions - 70e6).argmin()
        pvalues[peak_idx - 3 : peak_idx + 3] = 10 ** (-np.random.uniform(7.5, 10, 6))
    elif chrom == "15":
        peak_idx = np.abs(positions - 50e6).argmin()
        pvalues[peak_idx - 4 : peak_idx + 4] = 10 ** (-np.random.uniform(9, 14, 8))

    # Calculate cumulative position
    cumulative_positions = positions + cumulative_pos
    chr_centers[chrom] = cumulative_pos + (length * 1e6) / 2

    for i in range(n_snps):
        data.append(
            {
                "chromosome": chrom,
                "position": positions[i],
                "cumulative_pos": cumulative_positions[i],
                "p_value": pvalues[i],
                "neg_log_p": -np.log10(pvalues[i]),
            }
        )

    cumulative_pos += length * 1e6

df = pd.DataFrame(data)

# Alternating colors for chromosomes (Python Blue and a gray variant)
colors = {"odd": "#306998", "even": "#7A9FBF"}

# Create figure
fig = go.Figure()

# Add scatter traces for each chromosome
for i, chrom in enumerate(chr_lengths.keys()):
    chr_data = df[df["chromosome"] == chrom]
    color = colors["odd"] if int(chrom) % 2 == 1 else colors["even"]

    fig.add_trace(
        go.Scatter(
            x=chr_data["cumulative_pos"],
            y=chr_data["neg_log_p"],
            mode="markers",
            marker=dict(size=5, color=color, opacity=0.7),
            name=f"Chr {chrom}",
            showlegend=False,
            hovertemplate=(
                f"Chr {chrom}<br>Position: %{{customdata[0]:,.0f}} bp<br>-log₁₀(p): %{{y:.2f}}<extra></extra>"
            ),
            customdata=chr_data[["position"]].values,
        )
    )

# Genome-wide significance threshold (-log10(5e-8) ≈ 7.3)
significance_threshold = -np.log10(5e-8)
fig.add_shape(
    type="line",
    x0=0,
    x1=1,
    xref="paper",
    y0=significance_threshold,
    y1=significance_threshold,
    line=dict(color="#E53935", width=2, dash="dash"),
)
fig.add_annotation(
    text="Genome-wide significance (p = 5×10⁻⁸)",
    font=dict(size=16, color="#E53935"),
    xref="paper",
    x=0.99,
    xanchor="right",
    yref="y",
    y=significance_threshold,
    showarrow=False,
    yshift=15,
)

# Suggestive threshold (-log10(1e-5) = 5)
suggestive_threshold = 5
fig.add_shape(
    type="line",
    x0=0,
    x1=1,
    xref="paper",
    y0=suggestive_threshold,
    y1=suggestive_threshold,
    line=dict(color="#FFD43B", width=2, dash="dot"),
)
fig.add_annotation(
    text="Suggestive threshold (p = 10⁻⁵)",
    font=dict(size=16, color="#B8860B"),
    xref="paper",
    x=0.99,
    xanchor="right",
    yref="y",
    y=suggestive_threshold,
    showarrow=False,
    yshift=15,
)

# Highlight significant SNPs
significant_snps = df[df["neg_log_p"] > significance_threshold]
if len(significant_snps) > 0:
    fig.add_trace(
        go.Scatter(
            x=significant_snps["cumulative_pos"],
            y=significant_snps["neg_log_p"],
            mode="markers",
            marker=dict(size=10, color="#E53935", symbol="diamond", line=dict(color="white", width=1)),
            name="Significant SNPs",
            showlegend=True,
            hovertemplate=(
                "Significant SNP<br>"
                "Chr %{customdata[0]}<br>"
                "Position: %{customdata[1]:,.0f} bp<br>"
                "-log₁₀(p): %{y:.2f}<extra></extra>"
            ),
            customdata=significant_snps[["chromosome", "position"]].values,
        )
    )

# Chromosome tick positions and labels
chr_positions = [chr_centers[chrom] for chrom in chr_lengths.keys()]
chr_labels = list(chr_lengths.keys())

# Layout
fig.update_layout(
    title=dict(text="manhattan-gwas · plotly · pyplots.ai", font=dict(size=32), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Chromosome", font=dict(size=24)),
        tickfont=dict(size=16),
        tickmode="array",
        tickvals=chr_positions,
        ticktext=chr_labels,
        showgrid=False,
        zeroline=False,
    ),
    yaxis=dict(
        title=dict(text="-log₁₀(p-value)", font=dict(size=24)),
        tickfont=dict(size=18),
        gridcolor="rgba(0,0,0,0.1)",
        gridwidth=1,
        zeroline=False,
    ),
    template="plotly_white",
    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01, font=dict(size=16), bgcolor="rgba(255,255,255,0.8)"),
    margin=dict(l=80, r=50, t=80, b=80),
    plot_bgcolor="white",
)

# Save as PNG (4800 x 2700 px)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save as interactive HTML
fig.write_html("plot.html", include_plotlyjs="cdn")
