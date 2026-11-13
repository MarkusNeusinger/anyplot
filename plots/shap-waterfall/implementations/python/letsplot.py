"""anyplot.ai
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
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: red for positive SHAP (raises risk), blue for negative (lowers risk)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
POS_COLOR = IMPRINT_PALETTE[4]
NEG_COLOR = IMPRINT_PALETTE[2]

# Columns: set these to your table's column names
FEATURE = "Feature"  # role: feature
SHAP_VALUE = "SHAP value (change in readmission probability)"  # role: shap_value
BASE_VALUE = "Base value"  # role: base_value

# Data: replace this block with your own table, for example df = pd.read_csv("shap.csv")
# One patient's 30-day hospital readmission risk, explained feature by feature
df = pd.DataFrame(
    {
        FEATURE: [
            "Prior Admissions (12 mo)",
            "Home Care Arranged",
            "Age",
            "Comorbidity Count",
            "Length of Stay",
            "Medication Count",
            "Discharge Weekday",
            "Hemoglobin Level",
            "Insurance Type",
            "Emergency Admission",
            "Distance to Hospital",
            "Smoking Status",
        ],
        SHAP_VALUE: [0.09, -0.07, 0.06, 0.05, -0.04, 0.04, -0.03, 0.03, -0.02, 0.02, -0.01, 0.01],
        BASE_VALUE: 0.15,
    }
)

# Plot: reads only df and the constants above
table = df.reindex(df[SHAP_VALUE].abs().sort_values(ascending=False, kind="stable").index).reset_index(drop=True)
n = len(table)
base_value = float(table[BASE_VALUE].iloc[0])
final_value = base_value + float(table[SHAP_VALUE].sum())

# Cumulative waterfall positions; the largest contributor sits at the top
ends = base_value + table[SHAP_VALUE].cumsum()
starts = ends - table[SHAP_VALUE]
chain = np.concatenate([[base_value], ends.to_numpy()])
span = chain.max() - chain.min()

half = 0.38
table["y"] = np.arange(n, 0, -1)
table["ymin"] = table["y"] - half
table["ymax"] = table["y"] + half
table["xmin"] = np.minimum(starts, ends)
table["xmax"] = np.maximum(starts, ends)
table["direction"] = np.where(table[SHAP_VALUE] >= 0, "positive", "negative")
table["label"] = table[SHAP_VALUE].map(lambda v: f"{v:+.2f}")
table["text_x"] = np.where(table[SHAP_VALUE] >= 0, table["xmax"] + 0.02 * span, table["xmin"] - 0.02 * span)
df_pos = table[table[SHAP_VALUE] >= 0]
df_neg = table[table[SHAP_VALUE] < 0]

# Dotted connectors in the gap between consecutive bars
df_conn = pd.DataFrame(
    {"x": ends.to_numpy()[:-1], "y": table["y"].to_numpy()[:-1] - half, "yend": table["y"].to_numpy()[1:] + half}
)

# Reference-line labels above the top bar
label_y = n + 1.0
df_ref_base = pd.DataFrame({"x": [base_value - 0.02 * span], "y": [label_y], "label": [f"Base = {base_value:.2f}"]})
df_ref_pred = pd.DataFrame(
    {"x": [final_value + 0.02 * span], "y": [label_y], "label": [f"Predicted = {final_value:.2f}"]}
)

title = "Hospital Readmission Risk  ·  shap-waterfall  ·  python  ·  letsplot  ·  anyplot.ai"
title_size = round(16 * min(1.0, 67 / len(title)))

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_border=element_blank(),
    panel_grid_major_x=element_line(color=INK_MUTED, size=0.15),
    panel_grid_major_y=element_blank(),
    panel_grid_minor=element_blank(),
    axis_title=element_text(color=INK, size=12),
    axis_text_y=element_text(color=INK_SOFT, size=11),
    axis_text_x=element_text(color=INK_SOFT, size=10),
    axis_line_x=element_line(color=INK_SOFT, size=0.5),
    axis_line_y=element_blank(),
    axis_ticks=element_blank(),
    plot_title=element_text(color=INK, size=title_size),
    legend_position="none",
)

plot = (
    ggplot()
    + geom_vline(xintercept=base_value, color=INK_SOFT, size=0.5, linetype="dashed")
    + geom_rect(data=table, mapping=aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="direction"))
    + geom_segment(
        data=df_conn, mapping=aes(x="x", xend="x", y="y", yend="yend"), color=INK_SOFT, size=0.4, linetype="dotted"
    )
    + geom_text(data=df_pos, mapping=aes(x="text_x", y="y", label="label"), color=INK_SOFT, size=4.5, hjust=0)
    + geom_text(data=df_neg, mapping=aes(x="text_x", y="y", label="label"), color=INK_SOFT, size=4.5, hjust=1)
    + geom_text(data=df_ref_base, mapping=aes(x="x", y="y", label="label"), color=INK, size=5, hjust=1)
    + geom_text(data=df_ref_pred, mapping=aes(x="x", y="y", label="label"), color=INK, size=5, hjust=0)
    + geom_vline(xintercept=final_value, color=INK, size=0.7)
    + scale_fill_manual(values={"positive": POS_COLOR, "negative": NEG_COLOR})
    + scale_x_continuous(limits=[chain.min() - 0.45 * span, chain.max() + 0.45 * span], expand=[0, 0])
    + scale_y_continuous(breaks=table["y"].tolist(), labels=table[FEATURE].tolist(), limits=[0.5, n + 1.5])
    + labs(x=SHAP_VALUE, y="", title=title)
    + ggsize(800, 450)
    + theme_minimal()
    + anyplot_theme
)

ggsave(plot, f"plot-{THEME}.png", scale=4, path=".")
ggsave(plot, f"plot-{THEME}.html", path=".")
