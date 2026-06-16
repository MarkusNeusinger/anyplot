""" anyplot.ai
shap-waterfall: SHAP Waterfall Plot for Feature Attribution
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 88/100 | Created: 2026-05-07
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

POS_COLOR = "#AE3030"  # imprint red — positive SHAP (increases predicted risk)
NEG_COLOR = "#4467A3"  # Okabe-Ito blue — negative SHAP (decreases predicted risk)

# Data — loan default risk model explaining one applicant's prediction
# Features already sorted by absolute SHAP magnitude (largest at top)
feature_names = [
    "Payment History",
    "Debt-to-Income Ratio",
    "Annual Income",
    "Credit Score",
    "Loan Amount",
    "Employment Years",
    "Age",
    "Open Accounts",
    "Housing Status",
    "Loan Purpose",
    "Savings Balance",
    "Marital Status",
]
shap_values = np.array([0.18, 0.12, -0.11, -0.09, 0.08, -0.06, -0.05, 0.04, -0.03, 0.02, -0.02, 0.01])
base_value = 0.35
final_value = round(base_value + float(shap_values.sum()), 4)

n = len(feature_names)
y_pos = list(range(n, 0, -1))  # largest contributor at top (y=n), smallest at bottom (y=1)

# Cumulative waterfall positions
cumulative = base_value
bar_starts = np.empty(n)
bar_ends = np.empty(n)
for i, sv in enumerate(shap_values):
    bar_starts[i] = cumulative
    cumulative += sv
    bar_ends[i] = cumulative

# Main bars DataFrame
df_bars = pd.DataFrame(
    {
        "y": y_pos,
        "ymin": [y - 0.38 for y in y_pos],
        "ymax": [y + 0.38 for y in y_pos],
        "xmin": np.minimum(bar_starts, bar_ends),
        "xmax": np.maximum(bar_starts, bar_ends),
        "direction": ["positive" if sv >= 0 else "negative" for sv in shap_values],
        "shap_value": shap_values,
        "feature": feature_names,
    }
)

# SHAP value labels: positive bars get text to the right, negative to the left
df_bars["text_x"] = np.where(
    shap_values >= 0, np.maximum(bar_starts, bar_ends) + 0.007, np.minimum(bar_starts, bar_ends) - 0.007
)
df_bars["label"] = [f"+{sv:.3f}" if sv >= 0 else f"{sv:.3f}" for sv in shap_values]

df_pos = df_bars[df_bars["shap_value"] >= 0]
df_neg = df_bars[df_bars["shap_value"] < 0]

# Vertical connector segments in the gap between consecutive bars
df_conn = pd.DataFrame(
    {
        "x": bar_ends[:-1],
        "xend": bar_ends[:-1],
        "y": [y - 0.38 for y in y_pos[:-1]],
        "yend": [y + 0.38 for y in y_pos[1:]],
    }
)

# Reference line annotation labels (floated above all bars)
# Base: left-aligned from reference line; Predicted: centered over its line
df_ref_base = pd.DataFrame({"x": [base_value + 0.003], "y": [n + 1.1], "label": [f"Base = {base_value:.2f}"]})
df_ref_pred = pd.DataFrame({"x": [final_value], "y": [n + 1.1], "label": [f"Predicted = {final_value:.2f}"]})

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_border=element_blank(),
    panel_grid_major_x=element_line(color=INK_MUTED, size=0.15),
    panel_grid_major_y=element_blank(),
    panel_grid_minor=element_blank(),
    axis_title=element_text(color=INK, size=20),
    axis_text_y=element_text(color=INK_SOFT, size=16),
    axis_text_x=element_text(color=INK_SOFT, size=14),
    axis_line_x=element_line(color=INK_SOFT, size=0.5),
    axis_line_y=element_blank(),
    axis_ticks=element_blank(),
    plot_title=element_text(color=INK, size=24),
    legend_position="none",
)

plot = (
    ggplot()
    + geom_vline(xintercept=float(base_value), color=INK_SOFT, size=0.9, linetype="dashed")
    + geom_rect(data=df_bars, mapping=aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="direction"))
    + geom_segment(
        data=df_conn, mapping=aes(x="x", xend="xend", y="y", yend="yend"), color=INK_SOFT, size=0.5, linetype="dotted"
    )
    + geom_text(data=df_pos, mapping=aes(x="text_x", y="y", label="label"), color=INK_MUTED, size=10, hjust=0)
    + geom_text(data=df_neg, mapping=aes(x="text_x", y="y", label="label"), color=INK_MUTED, size=10, hjust=1)
    + geom_text(data=df_ref_base, mapping=aes(x="x", y="y", label="label"), color=INK, size=11, hjust=0)
    + geom_text(data=df_ref_pred, mapping=aes(x="x", y="y", label="label"), color=INK, size=11, hjust=0.5)
    + geom_vline(xintercept=float(final_value), color=INK, size=1.2)
    + scale_fill_manual(values={"positive": POS_COLOR, "negative": NEG_COLOR})
    + scale_x_continuous(limits=[0.28, 0.72], expand=[0, 0])
    + scale_y_continuous(breaks=y_pos, labels=feature_names, limits=[0.5, n + 1.5])
    + labs(
        x="SHAP Value  ·  Impact on Predicted Default Probability",
        y="",
        title="Credit Default Risk  ·  shap-waterfall  ·  letsplot  ·  anyplot.ai",
    )
    + ggsize(1600, 900)
    + theme_minimal()
    + anyplot_theme
)

ggsave(plot, f"plot-{THEME}.png", scale=3, path=".")
ggsave(plot, f"plot-{THEME}.html", path=".")
