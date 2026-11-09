"""anyplot.ai
manhattan-gwas: Manhattan Plot for GWAS
Library: plotly 7.1.0 | Python 3.14.9
Quality: 89/100 | Updated: 2026-11-09
"""

import os
import sys

import numpy as np
import pandas as pd


# Remove current directory from path to avoid shadowing plotly package
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir in sys.path:
    sys.path.remove(current_dir)

import plotly.graph_objects as go  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
CHROM_COLORS = [IMPRINT_PALETTE[0], IMPRINT_PALETTE[2]]  # alternating green / blue chromosomes
HIGHLIGHT_COLOR = IMPRINT_PALETTE[1]  # lavender for significant SNPs, distinct from both chromosome colors

# Constants
GENOME_WIDE_P = 5e-8  # genome-wide significance threshold
SUGGESTIVE_P = 1e-5  # suggestive threshold

# Columns: set these to your table's column names
CHROMOSOME = "Chromosome"  # role: chromosome
POSITION = "Position (bp)"  # role: position
P_VALUE = "p-value"  # role: p_value

# Data: replace this block with your own table, for example df = pd.read_csv("gwas_results.csv")
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

frames = []
for chrom, length in chr_lengths.items():
    # Number of SNPs proportional to chromosome length
    n_snps = int(length * 40)
    positions = np.sort(np.random.uniform(0, length * 1e6, n_snps))

    # Mostly null p-values, with association peaks on chromosomes 2, 8 and 15
    pvalues = np.random.uniform(0, 1, n_snps)
    if chrom == "2":
        peak_idx = np.abs(positions - 100e6).argmin()
        pvalues[peak_idx - 5 : peak_idx + 5] = 10 ** (-np.random.uniform(8, 12, 10))
    elif chrom == "8":
        peak_idx = np.abs(positions - 70e6).argmin()
        pvalues[peak_idx - 3 : peak_idx + 3] = 10 ** (-np.random.uniform(7.5, 10, 6))
    elif chrom == "15":
        peak_idx = np.abs(positions - 50e6).argmin()
        pvalues[peak_idx - 4 : peak_idx + 4] = 10 ** (-np.random.uniform(9, 14, 8))

    frames.append(pd.DataFrame({CHROMOSOME: chrom, POSITION: positions.round().astype(int), P_VALUE: pvalues}))

df = pd.concat(frames, ignore_index=True)

# Plot: reads only df and the constants above
neg_log_p = -np.log10(df[P_VALUE].astype(float))
chrom_span = df.groupby(CHROMOSOME, sort=False)[POSITION].max().astype(float)
chrom_offset = chrom_span.cumsum().shift(fill_value=0)
chrom_center = chrom_offset + chrom_span / 2
cumulative_pos = df[POSITION].astype(float) + df[CHROMOSOME].map(chrom_offset).astype(float)
is_significant = neg_log_p > -np.log10(GENOME_WIDE_P)

fig = go.Figure()

# Background band in WebGL for speed; significant variants are drawn once, by the highlight trace
for i, chrom in enumerate(chrom_span.index):
    mask = (df[CHROMOSOME] == chrom) & ~is_significant
    fig.add_trace(
        go.Scattergl(
            x=cumulative_pos[mask],
            y=neg_log_p[mask],
            mode="markers",
            marker={"size": 3, "color": CHROM_COLORS[i % 2], "opacity": 0.7},
            name=f"Chr {chrom}",
            showlegend=False,
            customdata=df.loc[mask, [POSITION]].to_numpy(),
            hovertemplate=(
                f"Chr {chrom}<br>Position: %{{customdata[0]:,.0f}} bp<br>-log₁₀(p): %{{y:.2f}}<extra></extra>"
            ),
        )
    )


def p_label(p):
    mantissa, exponent = f"{p:.0e}".split("e")
    superscript = str(int(exponent)).translate(str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹"))
    return f"10{superscript}" if mantissa == "1" else f"{mantissa}×10{superscript}"


# Threshold lines across all chromosomes
for p, name, dash in [
    (GENOME_WIDE_P, "Genome-wide significance", "dash"),
    (SUGGESTIVE_P, "Suggestive threshold", "dot"),
]:
    y = -np.log10(p)
    fig.add_hline(y=y, line={"color": INK_MUTED, "width": 1.5, "dash": dash})
    fig.add_annotation(
        text=f"{name} (p = {p_label(p)})",
        font={"size": 10, "color": INK_MUTED},
        xref="paper",
        x=0.99,
        xanchor="right",
        y=y,
        yanchor="bottom",
        showarrow=False,
    )

# Highlight significant SNPs
significant = df[is_significant]
if len(significant) > 0:
    fig.add_trace(
        go.Scatter(
            x=cumulative_pos[significant.index],
            y=neg_log_p[significant.index],
            mode="markers",
            marker={"size": 7, "color": HIGHLIGHT_COLOR, "symbol": "diamond", "line": {"color": INK, "width": 0.75}},
            name="Significant SNPs",
            customdata=significant[[CHROMOSOME, POSITION]].to_numpy(),
            hovertemplate=(
                "Significant SNP<br>Chr %{customdata[0]}<br>"
                "Position: %{customdata[1]:,.0f} bp<br>-log₁₀(p): %{y:.2f}<extra></extra>"
            ),
        )
    )

# Style
fig.update_layout(
    autosize=False,
    width=800,
    height=450,
    title={
        "text": "manhattan-gwas · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": CHROMOSOME, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 9, "color": INK_SOFT},
        "tickangle": 0,
        "tickmode": "array",
        "tickvals": chrom_center.to_numpy(),
        "ticktext": [str(c) for c in chrom_center.index],
        "range": [0, chrom_span.sum()],
        "showgrid": False,
        "zeroline": False,
        "linecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": "-log₁₀(p-value)", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "gridwidth": 1,
        "zeroline": False,
        "linecolor": INK_SOFT,
        "rangemode": "tozero",
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    legend={
        "yanchor": "top",
        "y": 0.99,
        "xanchor": "left",
        "x": 0.01,
        "font": {"size": 10, "color": INK_SOFT},
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
    },
    margin={"l": 60, "r": 20, "t": 60, "b": 50},
    hovermode="closest",
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
