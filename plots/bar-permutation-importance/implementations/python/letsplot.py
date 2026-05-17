""" anyplot.ai
bar-permutation-importance: Permutation Feature Importance Plot
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 84/100 | Updated: 2026-05-17
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_flip,
    element_line,
    element_rect,
    element_text,
    geom_bar,
    geom_errorbar,
    geom_hline,
    geom_text,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_fill_gradient,
    scale_x_discrete,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#8A8A7E" if THEME == "light" else "#7A7970"

# Data: Simulated permutation importance from a Random Forest model
np.random.seed(42)

features = [
    "Income Level",
    "Credit Score",
    "Employment Years",
    "Debt Ratio",
    "Account Age",
    "Payment History",
    "Loan Amount",
    "Interest Rate",
    "Property Value",
    "Monthly Expenses",
    "Savings Balance",
    "Number of Accounts",
    "Recent Inquiries",
    "Education Level",
    "Region Code",
]

# Generate importance values - higher for more predictive features
base_importance = np.array(
    [0.15, 0.12, 0.09, 0.08, 0.06, 0.05, 0.04, 0.03, 0.025, 0.02, 0.015, 0.01, 0.008, 0.005, 0.002]
)
# Add some noise
importance_mean = base_importance + np.random.uniform(-0.005, 0.005, len(features))
importance_std = np.random.uniform(0.003, 0.02, len(features))

# Create DataFrame and sort by importance
df = pd.DataFrame({"feature": features, "importance_mean": importance_mean, "importance_std": importance_std})
df = df.sort_values("importance_mean", ascending=True).reset_index(drop=True)

# Create ordered categorical for proper y-axis ordering
df["feature"] = pd.Categorical(df["feature"], categories=df["feature"].tolist(), ordered=True)

# Calculate error bar positions and label format
df["ymin"] = df["importance_mean"] - df["importance_std"]
df["ymax"] = df["importance_mean"] + df["importance_std"]
df["importance_pct"] = (df["importance_mean"] * 100).round(1).astype(str) + "%"
df["label"] = df["importance_mean"].round(4).astype(str)

# Create the plot with enhanced letsplot-specific features
plot = (
    ggplot(df, aes(x="feature", y="importance_mean", fill="importance_mean"))
    + geom_bar(
        stat="identity",
        width=0.75,
        alpha=0.92,
        tooltip=aes(text="<b>@feature</b><br/>Importance: @label<br/>±Std: @importance_std|.0000"),
    )
    + geom_errorbar(aes(ymin="ymin", ymax="ymax"), width=0.3, size=1.0, color=INK_SOFT, alpha=0.8)
    + geom_text(aes(y="importance_mean", label="label"), vjust=-0.6, size=12, color=INK_MUTED, family="monospace")
    + geom_hline(yintercept=0, color=INK_SOFT, size=0.9, linetype="dashed", alpha=0.6)
    + coord_flip()
    + scale_fill_gradient(low="#FFD43B", high="#306998", guide="none")
    + scale_x_discrete()
    + labs(x="Feature", y="Mean Decrease in Model Score", title="bar-permutation-importance · letsplot · anyplot.ai")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major=element_line(color=INK_SOFT, size=0.3),
        panel_grid_minor_x=element_line(color=INK_SOFT, size=0.15),
        plot_title=element_text(size=24, color=INK, face="bold"),
        axis_title=element_text(size=20, color=INK, face="bold"),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_text_y=element_text(size=14, color=INK_SOFT),
    )
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x for 4800x2700)
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)

# Save as HTML for interactive view
ggsave(plot, f"plot-{THEME}.html", path=".")
