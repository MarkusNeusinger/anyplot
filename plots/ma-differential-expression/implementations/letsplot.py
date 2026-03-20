""" pyplots.ai
ma-differential-expression: MA Plot for Differential Expression
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 82/100 | Created: 2026-03-20
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

gene_names = [f"Gene_{i}" for i in range(n_genes)]
top_up = up_idx[np.argsort(log_fold_change[up_idx])[-4:]]
top_down = down_idx[np.argsort(log_fold_change[down_idx])[:4]]
top_genes_idx = np.concatenate([top_up, top_down])

df_nonsig = pd.DataFrame(
    {
        "mean_expression": mean_expression[~significant],
        "log_fold_change": log_fold_change[~significant],
        "status": status[~significant],
    }
)

df_sig = pd.DataFrame(
    {
        "mean_expression": mean_expression[significant],
        "log_fold_change": log_fold_change[significant],
        "status": status[significant],
    }
)

df_labels = pd.DataFrame(
    {
        "mean_expression": mean_expression[top_genes_idx],
        "log_fold_change": log_fold_change[top_genes_idx],
        "gene_name": [gene_names[i] for i in top_genes_idx],
    }
)

df_all = pd.DataFrame({"mean_expression": mean_expression, "log_fold_change": log_fold_change})

# Plot
plot = (
    ggplot()  # noqa: F405
    + geom_hline(yintercept=0, color="#444444", size=0.8)  # noqa: F405
    + geom_hline(yintercept=1, color="#888888", size=0.5, linetype="dashed")  # noqa: F405
    + geom_hline(yintercept=-1, color="#888888", size=0.5, linetype="dashed")  # noqa: F405
    + geom_point(  # noqa: F405
        aes(x="mean_expression", y="log_fold_change"),  # noqa: F405
        data=df_nonsig,
        color="#CCCCCC",
        size=1.5,
        alpha=0.3,
    )
    + geom_point(  # noqa: F405
        aes(x="mean_expression", y="log_fold_change", color="status"),  # noqa: F405
        data=df_sig,
        size=2.5,
        alpha=0.6,
    )
    + geom_smooth(  # noqa: F405
        aes(x="mean_expression", y="log_fold_change"),  # noqa: F405
        data=df_all,
        color="#E8A838",
        size=1.5,
        se=False,
        method="loess",
        span=0.3,
    )
    + geom_text(  # noqa: F405
        aes(x="mean_expression", y="log_fold_change", label="gene_name"),  # noqa: F405
        data=df_labels,
        size=9,
        nudge_y=0.35,
        color="#222222",
    )
    + scale_color_manual(values={"Up-regulated": "#D64045", "Down-regulated": "#306998"})  # noqa: F405
    + labs(  # noqa: F405
        x="Mean Expression (A)",
        y="Log\u2082 Fold Change (M)",
        title="ma-differential-expression \u00b7 letsplot \u00b7 pyplots.ai",
        color="",
    )
    + ggsize(1600, 900)  # noqa: F405
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        plot_title=element_text(size=24, face="bold"),  # noqa: F405
        axis_title=element_text(size=20),  # noqa: F405
        axis_text=element_text(size=16),  # noqa: F405
        legend_text=element_text(size=16),  # noqa: F405
        legend_position="bottom",
        panel_grid_major_x=element_blank(),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
    )
)

# Save
export_ggsave(plot, filename="plot.png", path=".", scale=3)
export_ggsave(plot, filename="plot.html", path=".")
