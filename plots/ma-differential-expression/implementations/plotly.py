""" pyplots.ai
ma-differential-expression: MA Plot for Differential Expression
Library: plotly 6.6.0 | Python 3.14.3
Quality: 83/100 | Created: 2026-03-20
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

# Plot
fig = go.Figure()

# Non-significant genes
fig.add_trace(
    go.Scatter(
        x=mean_expression[non_sig_mask],
        y=log_fold_change[non_sig_mask],
        mode="markers",
        marker={"size": 7, "color": "#BBBBBB", "opacity": 0.3, "line": {"width": 0.5, "color": "white"}},
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
        marker={"size": 9, "color": "#D64545", "opacity": 0.5, "line": {"width": 0.5, "color": "white"}},
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
        line={"color": "#306998", "width": 3},
        name="LOESS trend",
        hoverinfo="skip",
    )
)

# Reference lines
fig.add_hline(y=0, line={"color": "#306998", "width": 2})
fig.add_hline(y=1, line={"color": "#888888", "width": 1.5, "dash": "dash"})
fig.add_hline(y=-1, line={"color": "#888888", "width": 1.5, "dash": "dash"})

# Label top DE genes
label_indices = [sig_indices[i] for i in top_de]
fig.add_trace(
    go.Scatter(
        x=mean_expression[label_indices],
        y=log_fold_change[label_indices],
        mode="text",
        text=[gene_names[i] for i in label_indices],
        textposition="top center",
        textfont={"size": 13, "color": "#333333"},
        showlegend=False,
        hoverinfo="skip",
    )
)

# Layout
fig.update_layout(
    title={
        "text": "ma-differential-expression · plotly · pyplots.ai",
        "font": {"size": 28},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Mean Expression (A)", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "gridcolor": "rgba(0,0,0,0.08)",
        "showgrid": True,
        "zeroline": False,
    },
    yaxis={
        "title": {"text": "Log₂ Fold Change (M)", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "gridcolor": "rgba(0,0,0,0.08)",
        "showgrid": True,
        "zeroline": False,
    },
    template="plotly_white",
    legend={"font": {"size": 16}, "x": 0.02, "y": 0.98, "bgcolor": "rgba(255,255,255,0.8)"},
    margin={"l": 100, "r": 60, "t": 100, "b": 100},
    plot_bgcolor="white",
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
