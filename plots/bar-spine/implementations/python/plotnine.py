""" anyplot.ai
bar-spine: Spine Plot for Two-Variable Proportions
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 91/100 | Created: 2026-05-08
"""

import os

import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_rect,
    geom_text,
    ggplot,
    labs,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]

# Data — customer churn by subscription tier
data = {
    "tier": ["Basic", "Basic", "Standard", "Standard", "Premium", "Premium", "Enterprise", "Enterprise"],
    "status": ["Retained", "Churned", "Retained", "Churned", "Retained", "Churned", "Retained", "Churned"],
    "count": [720, 280, 605, 195, 460, 90, 165, 35],
}
df = pd.DataFrame(data)

tier_order = ["Basic", "Standard", "Premium", "Enterprise"]
status_order = ["Retained", "Churned"]

# Marginal totals and bar widths (width ∝ tier count)
tier_totals = df.groupby("tier", sort=False)["count"].sum().reindex(tier_order).reset_index()
tier_totals.columns = ["tier", "total"]
grand_total = tier_totals["total"].sum()
tier_totals["width"] = tier_totals["total"] / grand_total
tier_totals["xmax"] = tier_totals["width"].cumsum()
tier_totals["xmin"] = tier_totals["xmax"] - tier_totals["width"]
tier_totals["xcenter"] = (tier_totals["xmin"] + tier_totals["xmax"]) / 2

# Merge widths into main dataframe
df = df.merge(tier_totals[["tier", "total", "xmin", "xmax", "xcenter"]], on="tier")
df["prop"] = df["count"] / df["total"]

# Sort and compute cumulative y positions (conditional proportions)
df["tier"] = pd.Categorical(df["tier"], categories=tier_order, ordered=True)
df["status"] = pd.Categorical(df["status"], categories=status_order, ordered=True)
df = df.sort_values(["tier", "status"]).reset_index(drop=True)
df["ymax"] = df.groupby("tier", observed=True)["prop"].cumsum()
df["ymin"] = df["ymax"] - df["prop"]
df["ylabel"] = (df["ymin"] + df["ymax"]) / 2
df["label"] = df["prop"].apply(lambda p: f"{p:.0%}" if p >= 0.06 else "")

# X-axis: one tick per tier, centered under each variable-width bar
x_breaks = tier_totals["xcenter"].tolist()
x_labels = [f"{t}\n(n={tot:,})" for t, tot in zip(tier_totals["tier"], tier_totals["total"], strict=True)]

anyplot_theme = theme(
    figure_size=(16, 9),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_blank(),
    panel_grid_minor=element_blank(),
    panel_border=element_rect(color=INK_SOFT, fill=None, size=0.5),
    axis_title=element_text(color=INK, size=20),
    axis_text=element_text(color=INK_SOFT, size=16),
    axis_ticks=element_line(color=INK_SOFT),
    plot_title=element_text(color=INK, size=24, weight="bold"),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=16),
    legend_title=element_text(color=INK, size=16),
    legend_key=element_rect(fill=ELEVATED_BG),
)

# Plot
plot = (
    ggplot(df)
    + geom_rect(aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="status"), color=PAGE_BG, size=0.5)
    + geom_text(aes(x="xcenter", y="ylabel", label="label"), color="white", size=11, fontweight="bold")
    + scale_fill_manual(values={"Retained": IMPRINT[0], "Churned": IMPRINT[1]}, name="Status")
    + scale_x_continuous(breaks=x_breaks, labels=x_labels, limits=(0, 1), expand=(0, 0))
    + scale_y_continuous(
        breaks=[0, 0.25, 0.5, 0.75, 1.0], labels=["0%", "25%", "50%", "75%", "100%"], limits=(0, 1), expand=(0, 0)
    )
    + labs(
        x="Subscription Tier  (bar width ∝ customer count)",
        y="Proportion of Customers",
        title="Churn Rate by Tier · bar-spine · plotnine · anyplot.ai",
    )
    + anyplot_theme
)

# Save
plot.save(f"plot-{THEME}.png", dpi=300)
