""" pyplots.ai
ma-differential-expression: MA Plot for Differential Expression
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 85/100 | Created: 2026-03-20
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_text,
    geom_hline,
    geom_line,
    geom_point,
    geom_text,
    ggplot,
    guides,
    labs,
    scale_alpha_manual,
    scale_color_manual,
    theme,
    theme_minimal,
)
from statsmodels.nonparametric.smoothers_lowess import lowess


# Data
np.random.seed(42)
n_genes = 15000

mean_expression = np.random.uniform(0, 15, n_genes)
log_fold_change = np.random.normal(0, 0.5, n_genes)
log_fold_change += 0.15 * np.sin(mean_expression * 0.3)

n_sig = int(n_genes * 0.08)
sig_indices = np.random.choice(n_genes, n_sig, replace=False)
log_fold_change[sig_indices] *= np.random.uniform(2.5, 5.0, n_sig)

significant = np.abs(log_fold_change) > 1.0
significant[sig_indices[: n_sig // 2]] = True

gene_names = [f"Gene{i}" for i in range(n_genes)]
top_genes = ["BRCA1", "TP53", "MYC", "EGFR", "KRAS", "PTEN", "RB1", "APC"]
top_idx = np.argsort(np.abs(log_fold_change))[-len(top_genes) :]
for i, idx in enumerate(top_idx):
    gene_names[idx] = top_genes[i]

df = pd.DataFrame(
    {
        "mean_expression": mean_expression,
        "log_fold_change": log_fold_change,
        "significant": significant,
        "gene_name": gene_names,
    }
)
df["group"] = df["significant"].map({True: "Significant", False: "Not significant"})

df_labels = df.loc[top_idx].copy()

lowess_result = lowess(df["log_fold_change"], df["mean_expression"], frac=0.3)
df_lowess = pd.DataFrame({"mean_expression": lowess_result[:, 0], "log_fold_change": lowess_result[:, 1]})

# Plot
plot = (
    ggplot(df, aes(x="mean_expression", y="log_fold_change", color="group", alpha="group"))
    + geom_point(size=1.5, stroke=0)
    + geom_hline(yintercept=0, color="#333333", size=0.8)
    + geom_hline(yintercept=1, linetype="dashed", color="#888888", size=0.6)
    + geom_hline(yintercept=-1, linetype="dashed", color="#888888", size=0.6)
    + geom_line(
        aes(x="mean_expression", y="log_fold_change"), data=df_lowess, color="#306998", size=1.2, inherit_aes=False
    )
    + geom_text(aes(label="gene_name"), data=df_labels, color="#222222", size=9, nudge_y=0.3, alpha=1)
    + scale_color_manual(values={"Significant": "#D64045", "Not significant": "#BBBBBB"})
    + scale_alpha_manual(values={"Significant": 0.6, "Not significant": 0.2})
    + labs(
        x="Mean Expression (A)",
        y="Log₂ Fold Change (M)",
        title="ma-differential-expression · plotnine · pyplots.ai",
        color="",
    )
    + guides(alpha=False)
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_text=element_text(size=16),
        legend_title=element_blank(),
        legend_position="top",
        panel_grid_major=element_line(color="#E0E0E0", size=0.4),
        panel_grid_minor=element_blank(),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
