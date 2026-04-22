""" pyplots.ai
volcano-basic: Volcano Plot for Statistical Significance
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-31
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Simulated differential expression results
np.random.seed(42)
n_genes = 500

# Generate log2 fold changes (effect sizes)
log2_fc = np.random.normal(0, 1.5, n_genes)

# Generate p-values (most genes not significant)
base_pvalues = np.random.beta(1, 10, n_genes)  # Right-skewed toward 1

# Make genes with large fold changes more likely to be significant
significance_boost = np.exp(-np.abs(log2_fc) * 0.5)
pvalues = base_pvalues * significance_boost
pvalues = np.clip(pvalues, 1e-10, 1)

# Calculate -log10(p-value)
neg_log10_pvalue = -np.log10(pvalues)

# Determine significance categories
fc_threshold = 1.0  # log2(2) = 1, meaning 2-fold change
pval_threshold = 1.3  # -log10(0.05) ≈ 1.3

significant_up = (log2_fc >= fc_threshold) & (neg_log10_pvalue >= pval_threshold)
significant_down = (log2_fc <= -fc_threshold) & (neg_log10_pvalue >= pval_threshold)

category = np.where(significant_up, "Up-regulated", np.where(significant_down, "Down-regulated", "Not Significant"))

# Create dataframe
df = pd.DataFrame({"log2_fold_change": log2_fc, "neg_log10_pvalue": neg_log10_pvalue, "category": category})

# Threshold lines data
vline_data = pd.DataFrame({"x": [-fc_threshold, fc_threshold]})
hline_data = pd.DataFrame({"y": [pval_threshold]})

# Color mapping
color_scale = alt.Scale(
    domain=["Up-regulated", "Down-regulated", "Not Significant"],
    range=["#E74C3C", "#306998", "#999999"],  # Red, Python Blue, Gray
)

# Main scatter plot
scatter = (
    alt.Chart(df)
    .mark_circle(size=80, opacity=0.7)
    .encode(
        x=alt.X("log2_fold_change:Q", title="Log₂ Fold Change", scale=alt.Scale(domain=[-6, 6])),
        y=alt.Y("neg_log10_pvalue:Q", title="-Log₁₀(p-value)"),
        color=alt.Color("category:N", scale=color_scale, title="Significance"),
        tooltip=["log2_fold_change:Q", "neg_log10_pvalue:Q", "category:N"],
    )
)

# Vertical threshold lines
vlines = alt.Chart(vline_data).mark_rule(strokeDash=[8, 4], color="#666666", strokeWidth=2).encode(x="x:Q")

# Horizontal threshold line
hline = alt.Chart(hline_data).mark_rule(strokeDash=[8, 4], color="#666666", strokeWidth=2).encode(y="y:Q")

# Combine all layers
chart = (
    (scatter + vlines + hline)
    .properties(
        width=1600, height=900, title=alt.Title("volcano-basic · altair · pyplots.ai", fontSize=28, anchor="middle")
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, gridOpacity=0.3)
    .configure_legend(titleFontSize=18, labelFontSize=16, symbolSize=200)
    .configure_view(strokeWidth=0)
)

# Save as PNG and HTML
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
