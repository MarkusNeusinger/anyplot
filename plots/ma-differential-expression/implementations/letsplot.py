""" pyplots.ai
ma-differential-expression: MA Plot for Differential Expression
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-20
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Data
np.random.seed(42)
n_genes = 15000

mean_expression = np.random.uniform(0.5, 15, n_genes)

log_fold_change = np.random.normal(0, 0.3, n_genes)
low_expr_bias = 0.4 * np.exp(-0.3 * mean_expression)
log_fold_change += np.random.normal(0, low_expr_bias)

n_up = 420
n_down = 380
up_idx = np.random.choice(np.where(mean_expression > 2)[0], n_up, replace=False)
down_idx = np.random.choice(np.setdiff1d(np.where(mean_expression > 2)[0], up_idx), n_down, replace=False)
log_fold_change[up_idx] = np.random.uniform(1.2, 5.5, n_up)
log_fold_change[down_idx] = np.random.uniform(-5.5, -1.2, n_down)

p_values = np.ones(n_genes)
p_values[up_idx] = np.random.uniform(1e-20, 0.01, n_up)
p_values[down_idx] = np.random.uniform(1e-20, 0.01, n_down)

significant = p_values < 0.05
status = np.where(~significant, "Not significant", np.where(log_fold_change > 0, "Up-regulated", "Down-regulated"))

# Realistic gene symbols for top genes
real_gene_names_up = ["FOXM1", "CDK1", "MYC", "EGFR"]
real_gene_names_down = ["CDKN1A", "RB1", "BRCA2", "TP53"]

top_up = up_idx[np.argsort(log_fold_change[up_idx])[-4:]]
top_down = down_idx[np.argsort(log_fold_change[down_idx])[:4]]

# Unified DataFrame
df = pd.DataFrame(
    {
        "A": mean_expression,
        "M": log_fold_change,
        "status": pd.Categorical(status, categories=["Down-regulated", "Not significant", "Up-regulated"]),
        "neg_log10p": -np.log10(np.clip(p_values, 1e-300, 1)),
    }
)

# Labels DataFrame with staggered nudge to avoid overlap
top_genes_idx = np.concatenate([top_up, top_down])
gene_labels = real_gene_names_up + real_gene_names_down
# Custom per-label nudge to prevent overlap (sorted by M descending for up, ascending for down)
# Up: idx order from argsort[-4:] gives ascending M, so positions 0-3
# Down: idx order from argsort[:4] gives ascending M (most negative first)
up_nudges = [(-1.2, 0.6), (0.8, 0.9), (-0.6, 1.2), (1.0, 0.5)]  # spread apart close genes
down_nudges = [(0.8, -0.6), (-1.0, -0.9), (-0.5, -1.2), (0.8, -0.5)]
all_nudges = up_nudges + down_nudges
nudge_x = [n[0] for n in all_nudges]
nudge_y = [n[1] for n in all_nudges]

df_labels = pd.DataFrame(
    {
        "A": mean_expression[top_genes_idx],
        "M": log_fold_change[top_genes_idx],
        "gene": gene_labels,
        "nudge_x": nudge_x,
        "nudge_y": nudge_y,
        "label_y": log_fold_change[top_genes_idx] + np.array(nudge_y),
        "label_x": mean_expression[top_genes_idx] + np.array(nudge_x),
    }
)

# Separate for layered plotting with unified data
df_nonsig = df[df["status"] == "Not significant"]
df_sig = df[df["status"] != "Not significant"]

# Plot
plot = (
    ggplot()  # noqa: F405
    + geom_hline(yintercept=0, color="#3C3C3C", size=0.8)  # noqa: F405
    + geom_hline(yintercept=1, color="#999999", size=0.5, linetype="dashed")  # noqa: F405
    + geom_hline(yintercept=-1, color="#999999", size=0.5, linetype="dashed")  # noqa: F405
    + geom_point(  # noqa: F405
        aes(x="A", y="M"),  # noqa: F405
        data=df_nonsig,
        color="#D5D5D5",
        size=1.2,
        alpha=0.25,
    )
    + geom_point(  # noqa: F405
        aes(x="A", y="M", color="status"),  # noqa: F405
        data=df_sig,
        size=2.5,
        alpha=0.65,
        tooltips=layer_tooltips()  # noqa: F405
        .line("@status")
        .line("Mean expr: @A")
        .line("Log₂FC: @M")
        .format("A", ".1f")
        .format("M", ".2f"),
    )
    + geom_smooth(  # noqa: F405
        aes(x="A", y="M"),  # noqa: F405
        data=df,
        color="#D4881C",
        size=1.8,
        se=False,
        method="loess",
        span=0.3,
    )
    + geom_segment(  # noqa: F405
        aes(x="A", y="M", xend="label_x", yend="label_y"),  # noqa: F405
        data=df_labels,
        color="#555555",
        size=0.4,
        linetype="dotted",
    )
    + geom_label(  # noqa: F405
        aes(x="label_x", y="label_y", label="gene", color="regulation"),  # noqa: F405
        data=df_labels.assign(regulation=["Up-regulated"] * 4 + ["Down-regulated"] * 4),
        size=8,
        fill="white",
        alpha=0.85,
        label_padding=0.3,
        label_r=0.2,
        label_size=0.5,
        show_legend=False,
    )
    + scale_color_manual(  # noqa: F405
        values={"Up-regulated": "#C23B22", "Down-regulated": "#306998"}, name="Regulation"
    )
    + labs(  # noqa: F405
        x="Mean Expression (A)",
        y="Log\u2082 Fold Change (M)",
        title="ma-differential-expression \u00b7 letsplot \u00b7 pyplots.ai",
    )
    + coord_cartesian(xlim=[0, 16])  # noqa: F405
    + ggsize(1600, 900)  # noqa: F405
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        plot_title=element_text(size=24, face="bold"),  # noqa: F405
        axis_title=element_text(size=20),  # noqa: F405
        axis_text=element_text(size=16),  # noqa: F405
        legend_title=element_text(size=16, face="bold"),  # noqa: F405
        legend_text=element_text(size=15),  # noqa: F405
        legend_position="bottom",
        panel_grid_major_x=element_blank(),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
        plot_margin=[30, 20, 10, 20],
    )
)

# Save
export_ggsave(plot, filename="plot.png", path=".", scale=3)
export_ggsave(plot, filename="plot.html", path=".")
