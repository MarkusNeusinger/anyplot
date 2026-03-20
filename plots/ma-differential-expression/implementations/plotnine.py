"""pyplots.ai
ma-differential-expression: MA Plot for Differential Expression
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 85/100 | Created: 2026-03-20
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_hline,
    geom_point,
    geom_text,
    ggplot,
    guide_legend,
    guides,
    labs,
    scale_alpha_manual,
    scale_color_manual,
    scale_size_manual,
    stat_smooth,
    theme,
    theme_minimal,
)


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

# Categorize into up/down/not significant for richer storytelling
category = np.where(~significant, "Not significant", np.where(log_fold_change > 0, "Upregulated", "Downregulated"))

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
        "category": pd.Categorical(
            category, categories=["Downregulated", "Not significant", "Upregulated"], ordered=True
        ),
    }
)

df_labels = df.loc[top_idx].copy()
# Position labels offset from data points to avoid overlap
nudge = np.where(df_labels["log_fold_change"] > 0, 0.8, -0.8)

# Detect close labels within same direction and stagger them
for direction in [1, -1]:
    mask = (nudge * direction) > 0
    subset = df_labels[mask].sort_values("mean_expression")
    for j in range(1, len(subset)):
        prev_x = subset.iloc[j - 1]["mean_expression"]
        curr_x = subset.iloc[j]["mean_expression"]
        if abs(curr_x - prev_x) < 2.0:
            idx_curr = subset.index[j]
            nudge[df_labels.index.get_loc(idx_curr)] *= 2.0

df_labels["label_y"] = df_labels["log_fold_change"] + nudge

# Split labels by direction for separate geom_text layers
df_labels_up = df_labels[df_labels["log_fold_change"] > 0].copy()
df_labels_down = df_labels[df_labels["log_fold_change"] < 0].copy()

# Plot
plot = (
    ggplot(df, aes(x="mean_expression", y="log_fold_change", color="category"))
    + geom_point(aes(alpha="category", size="category"), stroke=0)
    + geom_hline(yintercept=0, color="#2C3E50", size=1.0, alpha=0.8)
    + geom_hline(yintercept=1, linetype="dashed", color="#95A5A6", size=0.6)
    + geom_hline(yintercept=-1, linetype="dashed", color="#95A5A6", size=0.6)
    + annotate(
        "label",
        x=14.5,
        y=1.0,
        label=" ±2-fold threshold ",
        size=11,
        color="#555555",
        fill="#FAFAFA",
        alpha=0.9,
        label_size=0,
        ha="right",
        va="center",
    )
    + stat_smooth(aes(group=1), method="lowess", color="#306998", size=1.4, se=False, span=0.3, linetype="solid")
    + geom_text(
        aes(x="mean_expression", y="label_y", label="gene_name"),
        data=df_labels_up,
        color="#1A1A2E",
        size=14,
        fontstyle="italic",
        alpha=1,
        inherit_aes=False,
        show_legend=False,
    )
    + geom_text(
        aes(x="mean_expression", y="label_y", label="gene_name"),
        data=df_labels_down,
        color="#1A1A2E",
        size=14,
        fontstyle="italic",
        alpha=1,
        inherit_aes=False,
        show_legend=False,
    )
    + scale_color_manual(values={"Upregulated": "#D45E00", "Not significant": "#C0C0C0", "Downregulated": "#306998"})
    + scale_alpha_manual(values={"Upregulated": 0.8, "Not significant": 0.15, "Downregulated": 0.8})
    + scale_size_manual(values={"Upregulated": 2.0, "Not significant": 1.0, "Downregulated": 2.0})
    + labs(
        x="Mean Expression (A)",
        y="Log₂ Fold Change (M)",
        title="ma-differential-expression · plotnine · pyplots.ai",
        color="",
    )
    + guides(color=guide_legend(override_aes={"alpha": 1, "size": 4}), alpha="none", size="none")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold", color="#1A1A2E"),
        plot_subtitle=element_text(size=16, color="#555555"),
        axis_title=element_text(size=20, color="#2C3E50"),
        axis_text=element_text(size=16, color="#555555"),
        legend_text=element_text(size=16),
        legend_title=element_blank(),
        legend_position="top",
        legend_background=element_rect(fill="white", alpha=0.8),
        panel_grid_major_x=element_blank(),
        panel_grid_major_y=element_line(color="#ECECEC", size=0.3),
        panel_grid_minor=element_blank(),
        plot_background=element_rect(fill="#FAFAFA", color="none"),
        panel_background=element_rect(fill="#FAFAFA", color="none"),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
