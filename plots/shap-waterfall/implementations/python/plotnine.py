"""anyplot.ai
shap-waterfall: SHAP Waterfall Plot for Feature Attribution
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-11-17
"""

import os

import pandas as pd
from plotnine import (
    aes,
    coord_cartesian,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_rect,
    geom_segment,
    geom_text,
    geom_vline,
    ggplot,
    labs,
    scale_fill_manual,
    scale_y_continuous,
    theme,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID_COLOR = "#C8C7C0" if THEME == "light" else "#2E2E2B"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants: semantic colors of a SHAP plot (red pushes the prediction up, blue pushes it down)
COLOR_POS = IMPRINT_PALETTE[4]
COLOR_NEG = IMPRINT_PALETTE[2]

# Columns: set these to your table's column names
FEATURE = "Feature"  # role: feature
SHAP = "SHAP Value (Feature Contribution)"  # role: shap_value
BASE = "Base value"  # role: base_value

# Data: replace this block with your own table, for example df = pd.read_csv("shap.csv")
# Credit scoring model, explaining a single loan approval prediction
df = pd.DataFrame(
    {
        FEATURE: [
            "Annual Income",
            "Credit Score",
            "Debt-to-Income",
            "Employment Years",
            "Loan Amount",
            "Payment History",
            "Num Credit Lines",
            "Savings Balance",
            "Age",
            "Recent Inquiries",
            "Education Level",
            "Home Ownership",
        ],
        SHAP: [0.18, 0.14, -0.12, 0.09, -0.08, 0.06, -0.05, 0.05, 0.04, -0.03, 0.02, -0.01],
        BASE: [0.34] * 12,
    }
)

# Plot: reads only df and the constants above
base_value = df[BASE].iloc[0]
final_value = base_value + df[SHAP].sum()

# Largest |SHAP| first (top of the chart), then the cumulative chain from base to final
d = df.reindex(df[SHAP].abs().sort_values(ascending=False, kind="stable").index).reset_index(drop=True)
n = len(d)
d["start"] = base_value + d[SHAP].cumsum().shift(1).fillna(0)
d["end"] = d["start"] + d[SHAP]
d["y_pos"] = range(n, 0, -1)
d["direction"] = d[SHAP].apply(lambda v: "Positive" if v >= 0 else "Negative")
d["bar_label"] = d[SHAP].apply(lambda v: f"{v:+.3f}")

BAR_H = 0.65
d["ymin"] = d["y_pos"] - BAR_H / 2
d["ymax"] = d["y_pos"] + BAR_H / 2

# Dashed connectors between adjacent bars at their shared boundary
conn = pd.DataFrame(
    {"x": d["end"].iloc[:-1].to_numpy(), "y0": d["ymax"].iloc[1:].to_numpy(), "y1": d["ymin"].iloc[:-1].to_numpy()}
)

# Labeled reference points for the base value and the final prediction
ann_base = pd.DataFrame({"x": [base_value], "y": [n + 0.85], "label": [f"Base = {base_value:.2f}"]})
ann_final = pd.DataFrame({"x": [final_value], "y": [0.15], "label": [f"Pred = {final_value:.2f}"]})

# Bar labels: right of positive bar ends, left of negative ones
pos_bars = d[d[SHAP] >= 0]
neg_bars = d[d[SHAP] < 0]
span = max(d["start"].max(), d["end"].max()) - min(d["start"].min(), d["end"].min())
nudge = span * 0.015

x_left = min(d["start"].min(), d["end"].min()) - span * 0.12
x_right = max(d["start"].max(), d["end"].max()) + span * 0.2

anyplot_theme = theme(
    figure_size=(8, 4.5),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major_x=element_line(color=GRID_COLOR, size=0.3),
    panel_grid_major_y=element_blank(),
    panel_grid_minor=element_blank(),
    panel_border=element_blank(),
    axis_title_x=element_text(color=INK, size=10),
    axis_title_y=element_blank(),
    axis_text_x=element_text(color=INK_SOFT, size=8),
    axis_text_y=element_text(color=INK, size=8),
    axis_line_x=element_line(color=INK_SOFT),
    axis_line_y=element_blank(),
    axis_ticks_major_x=element_blank(),
    axis_ticks_major_y=element_blank(),
    plot_title=element_text(color=INK, size=12, ha="left"),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=8),
    legend_title=element_text(color=INK, size=9),
    legend_position="right",
)

plot = (
    ggplot(d)
    + geom_rect(aes(xmin="start", xmax="end", ymin="ymin", ymax="ymax", fill="direction"))
    + geom_segment(
        data=conn, mapping=aes(x="x", xend="x", y="y0", yend="y1"), color=INK_SOFT, linetype="dashed", size=0.4
    )
    + geom_vline(xintercept=base_value, color=INK_SOFT, linetype="dotted", size=0.6)
    + geom_vline(xintercept=final_value, color=INK_SOFT, linetype="dotted", size=0.6)
    + geom_text(
        data=pos_bars, mapping=aes(x="end", y="y_pos", label="bar_label"), nudge_x=nudge, ha="left", color=INK, size=7
    )
    + geom_text(
        data=neg_bars, mapping=aes(x="end", y="y_pos", label="bar_label"), nudge_x=-nudge, ha="right", color=INK, size=7
    )
    + geom_text(
        data=ann_base,
        mapping=aes(x="x", y="y", label="label"),
        nudge_x=nudge,
        ha="left",
        va="bottom",
        color=INK_SOFT,
        size=7.5,
    )
    + geom_text(
        data=ann_final,
        mapping=aes(x="x", y="y", label="label"),
        nudge_x=nudge,
        ha="left",
        va="top",
        color=INK_SOFT,
        size=7.5,
    )
    + scale_fill_manual(values={"Positive": COLOR_POS, "Negative": COLOR_NEG}, name="Contribution")
    + scale_y_continuous(breaks=d["y_pos"].tolist(), labels=d[FEATURE].tolist(), expand=(0.05, 0))
    + coord_cartesian(xlim=(x_left, x_right), ylim=(-0.2, n + 1.5))
    + labs(x=SHAP, y="", title="Loan Approval · shap-waterfall · python · plotnine · anyplot.ai")
    + anyplot_theme
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
