""" pyplots.ai
volcano-basic: Volcano Plot for Statistical Significance
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-31
"""

import numpy as np
import plotly.graph_objects as go


# Data - Simulated differential gene expression results
np.random.seed(42)
n_genes = 500

# Generate log2 fold changes (centered around 0, with some extreme values)
log2_fold_change = np.random.normal(0, 1.5, n_genes)

# Generate p-values (most non-significant, some significant)
# Use a mixture: mostly high p-values, some low
base_pvalues = np.random.beta(1, 3, n_genes)
# Genes with larger fold changes tend to have lower p-values
effect_boost = np.abs(log2_fold_change) / 5
pvalues = base_pvalues * np.exp(-effect_boost * 3)
pvalues = np.clip(pvalues, 1e-20, 1)

# Transform to -log10 scale
neg_log10_pvalue = -np.log10(pvalues)

# Define significance thresholds
fc_threshold = 1.0  # log2 fold change threshold (2-fold)
pval_threshold = 0.05  # p-value threshold
neg_log10_threshold = -np.log10(pval_threshold)

# Classify points
sig_up = (log2_fold_change > fc_threshold) & (neg_log10_pvalue > neg_log10_threshold)
sig_down = (log2_fold_change < -fc_threshold) & (neg_log10_pvalue > neg_log10_threshold)
non_sig = ~(sig_up | sig_down)

# Gene names for top hits
gene_names = [f"Gene_{i}" for i in range(n_genes)]

# Create figure
fig = go.Figure()

# Non-significant points (gray)
fig.add_trace(
    go.Scatter(
        x=log2_fold_change[non_sig],
        y=neg_log10_pvalue[non_sig],
        mode="markers",
        marker=dict(size=10, color="#888888", opacity=0.5),
        name="Not Significant",
        hovertemplate="%{text}<br>log2FC: %{x:.2f}<br>-log10(p): %{y:.2f}<extra></extra>",
        text=[gene_names[i] for i in np.where(non_sig)[0]],
    )
)

# Significant down-regulated (blue)
fig.add_trace(
    go.Scatter(
        x=log2_fold_change[sig_down],
        y=neg_log10_pvalue[sig_down],
        mode="markers",
        marker=dict(size=12, color="#306998", opacity=0.8),
        name="Down-regulated",
        hovertemplate="%{text}<br>log2FC: %{x:.2f}<br>-log10(p): %{y:.2f}<extra></extra>",
        text=[gene_names[i] for i in np.where(sig_down)[0]],
    )
)

# Significant up-regulated (using a warm color - Python Yellow-ish orange)
fig.add_trace(
    go.Scatter(
        x=log2_fold_change[sig_up],
        y=neg_log10_pvalue[sig_up],
        mode="markers",
        marker=dict(size=12, color="#D35400", opacity=0.8),
        name="Up-regulated",
        hovertemplate="%{text}<br>log2FC: %{x:.2f}<br>-log10(p): %{y:.2f}<extra></extra>",
        text=[gene_names[i] for i in np.where(sig_up)[0]],
    )
)

# Horizontal threshold line (p-value = 0.05)
x_range = [min(log2_fold_change) - 0.5, max(log2_fold_change) + 0.5]
fig.add_trace(
    go.Scatter(
        x=x_range,
        y=[neg_log10_threshold, neg_log10_threshold],
        mode="lines",
        line=dict(color="#333333", width=2, dash="dash"),
        name=f"p = {pval_threshold}",
        showlegend=True,
    )
)

# Vertical threshold lines (fold change = ±1)
y_range = [0, max(neg_log10_pvalue) * 1.05]
fig.add_trace(
    go.Scatter(
        x=[-fc_threshold, -fc_threshold],
        y=y_range,
        mode="lines",
        line=dict(color="#333333", width=2, dash="dash"),
        name=f"log2FC = -{fc_threshold}",
        showlegend=False,
    )
)
fig.add_trace(
    go.Scatter(
        x=[fc_threshold, fc_threshold],
        y=y_range,
        mode="lines",
        line=dict(color="#333333", width=2, dash="dash"),
        name=f"log2FC = {fc_threshold}",
        showlegend=True,
    )
)

# Label top significant genes
top_indices = np.argsort(neg_log10_pvalue)[-5:]  # Top 5 most significant
annotations = []
for idx in top_indices:
    if sig_up[idx] or sig_down[idx]:
        annotations.append(
            dict(
                x=log2_fold_change[idx],
                y=neg_log10_pvalue[idx],
                text=gene_names[idx],
                showarrow=True,
                arrowhead=2,
                arrowsize=1,
                arrowwidth=1.5,
                ax=30,
                ay=-30,
                font=dict(size=16, color="#333333"),
            )
        )

# Update layout
fig.update_layout(
    title=dict(text="volcano-basic · plotly · pyplots.ai", font=dict(size=28), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="log₂ Fold Change", font=dict(size=22)),
        tickfont=dict(size=18),
        zeroline=True,
        zerolinewidth=1,
        zerolinecolor="#CCCCCC",
        gridcolor="rgba(0,0,0,0.1)",
    ),
    yaxis=dict(
        title=dict(text="-log₁₀(p-value)", font=dict(size=22)), tickfont=dict(size=18), gridcolor="rgba(0,0,0,0.1)"
    ),
    template="plotly_white",
    legend=dict(
        font=dict(size=18), x=0.02, y=0.98, bgcolor="rgba(255,255,255,0.8)", bordercolor="#CCCCCC", borderwidth=1
    ),
    annotations=annotations,
    margin=dict(l=80, r=40, t=80, b=80),
)

# Save as PNG (4800 x 2700 px)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save interactive HTML version
fig.write_html("plot.html", include_plotlyjs=True, full_html=True)
