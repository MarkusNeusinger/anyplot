""" anyplot.ai
bar-spine: Spine Plot for Two-Variable Proportions
Library: letsplot 4.11.0 | Python 3.13.15
Quality: 90/100 | Updated: 2026-09-27
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_hline,
    geom_rect,
    geom_text,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)


LetsPlot.setup_html()

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]
ANYPLOT_AMBER = "#DDCC77"
BORDER_COLOR = "rgba(128, 128, 128, 0.35)"  # theme-neutral separator, stays visible on both surfaces

# Data: customer churn by subscription tier
tiers = ["Basic", "Standard", "Premium", "Enterprise"]
retained_counts = [120, 400, 320, 180]
churned_counts = [180, 200, 80, 20]

totals = [r + c for r, c in zip(retained_counts, churned_counts, strict=True)]
grand_total = sum(totals)

widths = [t / grand_total for t in totals]
x_starts = np.concatenate([[0.0], np.cumsum(widths[:-1])])
x_ends = np.cumsum(widths)
x_mids = (x_starts + x_ends) / 2

# Build rectangle segments for each tier x status combination
records = []
for i, tier in enumerate(tiers):
    total = totals[i]
    retain_prop = retained_counts[i] / total
    churn_prop = churned_counts[i] / total

    records.append(
        {
            "tier": tier,
            "status": "Retained",
            "xmin": float(x_starts[i]),
            "xmax": float(x_ends[i]),
            "ymin": 0.0,
            "ymax": retain_prop,
            "x_mid": float(x_mids[i]),
            "y_mid": retain_prop / 2,
            "segment_height": retain_prop,
            "label": f"{retain_prop:.0%}",
        }
    )
    records.append(
        {
            "tier": tier,
            "status": "Churned",
            "xmin": float(x_starts[i]),
            "xmax": float(x_ends[i]),
            "ymin": retain_prop,
            "ymax": 1.0,
            "x_mid": float(x_mids[i]),
            "y_mid": retain_prop + churn_prop / 2,
            "segment_height": churn_prop,
            "label": f"{churn_prop:.0%}",
        }
    )

df = pd.DataFrame(records)
df_labels = df[df["segment_height"] >= 0.08].copy()

# Enterprise has the lowest churn rate; a benchmark line at that level lets
# every other tier's much taller churned segment be read against it directly.
best_churn_rate = churned_counts[-1] / totals[-1]
benchmark_y = 1.0 - best_churn_rate
benchmark_label = pd.DataFrame(
    {
        "x": [x_starts[0] + 0.01],
        "y": [benchmark_y + 0.035],
        "label": [f"Enterprise-level churn ({best_churn_rate:.0%})"],
    }
)

# Theme
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid=element_blank(),
    axis_title=element_text(color=INK, size=12),
    axis_text=element_text(color=INK_SOFT, size=10),
    axis_line=element_line(color=INK_SOFT),
    axis_ticks=element_blank(),
    plot_title=element_text(color=INK, size=16),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=10),
    legend_title=element_text(color=INK, size=12),
)

# Plot
plot = (
    ggplot(df)
    + geom_rect(aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="status"), color=BORDER_COLOR, size=1.2)
    + geom_hline(yintercept=benchmark_y, linetype="dashed", color=ANYPLOT_AMBER, size=1)
    + geom_text(
        data=benchmark_label, mapping=aes(x="x", y="y", label="label"), color=INK, size=4, hjust=0, fontface="bold"
    )
    + geom_text(data=df_labels, mapping=aes(x="x_mid", y="y_mid", label="label"), color="#FAFAFA", size=5)
    + scale_fill_manual(values={"Retained": IMPRINT[0], "Churned": IMPRINT[1]}, name="Status")
    + scale_x_continuous(expand=[0, 0], breaks=list(x_mids), labels=tiers)
    + scale_y_continuous(expand=[0, 0], breaks=[0.0, 0.25, 0.5, 0.75, 1.0], labels=["0%", "25%", "50%", "75%", "100%"])
    + labs(x="Subscription Tier", y="Customer Proportion", title="bar-spine · python · letsplot · anyplot.ai")
    + anyplot_theme
    + ggsize(800, 450)
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
