""" pyplots.ai
ma-differential-expression: MA Plot for Differential Expression
Library: plotly 6.6.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-20
"""

import numpy as np
import plotly.graph_objects as go
from scipy.signal import savgol_filter


# Data - Simulated RNA-seq differential expression results
np.random.seed(42)
n_genes = 15000

# Mean expression (A values) - log2 scale, bimodal distribution
mean_expression = np.concatenate([np.random.normal(4, 1.5, 5000), np.random.normal(9, 2.5, 10000)])
mean_expression = np.clip(mean_expression, 0.5, 16)

# Log fold change (M values) - most genes near zero, some DE genes
log_fold_change = np.random.normal(0, 0.3, n_genes)

# Add truly differentially expressed genes (~8%)
n_de = 1200
de_indices = np.random.choice(n_genes, n_de, replace=False)
log_fold_change[de_indices] = np.random.choice([-1, 1], n_de) * (np.random.exponential(0.8, n_de) + 1.0)

# Expression-dependent variance (higher variance at low expression)
noise_scale = 0.5 / (1 + mean_expression * 0.3)
log_fold_change += np.random.normal(0, noise_scale)

# Significance (adjusted p-value < 0.05)
significant = np.abs(log_fold_change) > 1.0
significant &= mean_expression > 2.0
significant[de_indices] = np.abs(log_fold_change[de_indices]) > 0.8

# Gene names for top DE genes
gene_names = [f"Gene{i}" for i in range(n_genes)]
top_gene_names = ["BRCA1", "TP53", "MYC", "EGFR", "VEGFA", "IL6", "TNF", "STAT3", "KRAS", "CDK2"]
top_de = np.argsort(np.abs(log_fold_change[significant]))[-10:]
sig_indices = np.where(significant)[0]
for i, name in zip(top_de, top_gene_names, strict=False):
    gene_names[sig_indices[i]] = name

# Separate data
non_sig_mask = ~significant
sig_mask = significant

# LOESS-like smoothing curve
sort_idx = np.argsort(mean_expression)
sorted_expr = mean_expression[sort_idx]
sorted_lfc = log_fold_change[sort_idx]
window = min(501, len(sorted_lfc) // 4 * 2 + 1)
smoothed = savgol_filter(sorted_lfc, window, 3)

# Color palette - refined, distinctive
COLOR_NONSIG = "#B0B8C4"
COLOR_SIG = "#0E8A7A"
COLOR_LOESS = "#306998"
COLOR_REFLINE = "#5A5A6E"
COLOR_THRESHOLD = "#9E9EAE"
COLOR_LABEL = "#2B2B3D"

# Plot
fig = go.Figure()

# Non-significant genes
fig.add_trace(
    go.Scatter(
        x=mean_expression[non_sig_mask],
        y=log_fold_change[non_sig_mask],
        mode="markers",
        marker={"size": 8, "color": COLOR_NONSIG, "opacity": 0.25, "line": {"width": 0}},
        name="Not significant",
        hovertemplate="A: %{x:.1f}<br>M: %{y:.2f}<extra>Not significant</extra>",
    )
)

# Significant genes
fig.add_trace(
    go.Scatter(
        x=mean_expression[sig_mask],
        y=log_fold_change[sig_mask],
        mode="markers",
        marker={"size": 10, "color": COLOR_SIG, "opacity": 0.6, "line": {"width": 0.5, "color": "white"}},
        name="Significant (padj < 0.05)",
        hovertemplate="A: %{x:.1f}<br>M: %{y:.2f}<extra>Significant</extra>",
    )
)

# Smoothing curve
fig.add_trace(
    go.Scatter(
        x=sorted_expr,
        y=smoothed,
        mode="lines",
        line={"color": COLOR_LOESS, "width": 3.5},
        name="LOESS trend",
        hoverinfo="skip",
    )
)

# Reference line at y=0 (distinct from LOESS)
fig.add_hline(y=0, line={"color": COLOR_REFLINE, "width": 1.5, "dash": "dot"})

# Fold-change threshold lines with annotations
fig.add_hline(y=1, line={"color": COLOR_THRESHOLD, "width": 1.5, "dash": "dash"})
fig.add_hline(y=-1, line={"color": COLOR_THRESHOLD, "width": 1.5, "dash": "dash"})

fig.add_annotation(
    x=15.5,
    y=1,
    text="2-fold up",
    showarrow=False,
    font={"size": 14, "color": COLOR_THRESHOLD},
    xanchor="right",
    yshift=14,
)
fig.add_annotation(
    x=15.5,
    y=-1,
    text="2-fold down",
    showarrow=False,
    font={"size": 14, "color": COLOR_THRESHOLD},
    xanchor="right",
    yshift=-14,
)

# Label top DE genes
label_indices = [sig_indices[i] for i in top_de]
fig.add_trace(
    go.Scatter(
        x=mean_expression[label_indices],
        y=log_fold_change[label_indices],
        mode="text",
        text=[gene_names[i] for i in label_indices],
        textposition="top center",
        textfont={"size": 16, "color": COLOR_LABEL, "family": "Arial Black, sans-serif"},
        showlegend=False,
        hoverinfo="skip",
    )
)

# Layout
fig.update_layout(
    title={
        "text": "ma-differential-expression · plotly · pyplots.ai",
        "font": {"size": 28, "color": "#2B2B3D", "family": "Arial, sans-serif"},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Mean Expression (A)", "font": {"size": 22, "color": "#3A3A4A"}},
        "tickfont": {"size": 18, "color": "#4A4A5A"},
        "showgrid": False,
        "zeroline": False,
    },
    yaxis={
        "title": {"text": "Log₂ Fold Change (M)", "font": {"size": 22, "color": "#3A3A4A"}},
        "tickfont": {"size": 18, "color": "#4A4A5A"},
        "gridcolor": "rgba(0,0,0,0.06)",
        "showgrid": True,
        "zeroline": False,
    },
    template="plotly_white",
    legend={
        "font": {"size": 16, "color": "#3A3A4A"},
        "x": 0.98,
        "y": 0.98,
        "xanchor": "right",
        "bgcolor": "rgba(255,255,255,0.85)",
        "bordercolor": "rgba(0,0,0,0.1)",
        "borderwidth": 1,
    },
    margin={"l": 100, "r": 80, "t": 100, "b": 100},
    plot_bgcolor="white",
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
