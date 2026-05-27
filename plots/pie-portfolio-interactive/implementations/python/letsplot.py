"""anyplot.ai
pie-portfolio-interactive: Interactive Portfolio Allocation Chart
Library: letsplot 4.10.1 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-27
"""

import os

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_rect,
    element_text,
    geom_label,
    geom_pie,
    ggbunch,
    ggplot,
    ggsize,
    labs,
    layer_labels,
    layer_tooltips,
    scale_fill_manual,
    theme,
    theme_void,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Anyplot palette — semantic mapping for asset classes
# Equities → green (growth/profit), Fixed Income → blue (safe/conservative)
# Alternatives → purple, Cash → ochre (store of value)
CATEGORY_COLORS = {"Equities": "#009E73", "Fixed Income": "#4467A3", "Alternatives": "#C475FD", "Cash": "#BD8233"}

# Anyplot palette positions 1→8 for individual holdings
HOLDING_COLORS = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Portfolio data — institutional multi-asset allocation
portfolio_data = {
    "asset": [
        "Apple Inc.",
        "Microsoft Corp.",
        "Amazon.com",
        "NVIDIA Corp.",
        "US Treasury 10Y",
        "Corporate Bonds AAA",
        "Municipal Bonds",
        "Real Estate Fund",
        "Gold ETF",
        "Private Equity",
        "Cash Reserves",
    ],
    "weight": [12.0, 10.0, 8.0, 7.0, 18.0, 12.0, 8.0, 10.0, 6.0, 5.0, 4.0],
    "category": [
        "Equities",
        "Equities",
        "Equities",
        "Equities",
        "Fixed Income",
        "Fixed Income",
        "Fixed Income",
        "Alternatives",
        "Alternatives",
        "Alternatives",
        "Cash",
    ],
}
df = pd.DataFrame(portfolio_data)

# Aggregate by category
category_weights = df.groupby("category", as_index=False)["weight"].sum()
category_weights = category_weights.sort_values("weight", ascending=False)
category_order = category_weights["category"].tolist()

# Enrich for tooltips
category_weights["holdings_count"] = category_weights["category"].apply(lambda c: len(df[df["category"] == c]))
category_weights["holdings_preview"] = category_weights["category"].apply(
    lambda c: ", ".join(df[df["category"] == c]["asset"].tolist())
)
# Suppress slice labels for very small segments (< 5%) to avoid cramped text
category_weights["pct_label"] = category_weights["weight"].apply(lambda w: f"{w:.1f}%" if w >= 5.0 else "")

center_df = pd.DataFrame({"x": [0.0], "y": [0.0], "label": ["Portfolio\n100%"]})

# Shared theme — theme_void base + anyplot chrome tokens
chart_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    plot_title=element_text(size=13, hjust=0.5, face="bold", color=INK),
    plot_subtitle=element_text(size=10, hjust=0.5, color=INK_SOFT),
    legend_title=element_text(size=11, color=INK),
    legend_text=element_text(size=10, color=INK_SOFT),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_position="right",
    plot_caption=element_text(size=9, hjust=0.5, face="bold", color="#4467A3"),
    plot_margin=[20, 15, 10, 15],
)

# Overview pie — all asset classes, interactive tooltips with holdings preview
plot_overview = (
    ggplot(category_weights)
    + geom_pie(
        aes(slice="weight", fill="category"),
        stat="identity",
        size=45,
        hole=0.35,
        stroke=1.5,
        color=PAGE_BG,
        tooltips=layer_tooltips()
        .title("@category")
        .line("Allocation: @weight%")
        .line("Holdings: @holdings_count assets")
        .line("@holdings_preview")
        .format("weight", ".1f"),
        labels=layer_labels().line("@pct_label").size(7),
    )
    + geom_label(
        aes(x="x", y="y", label="label"), data=center_df, size=9, fill=ELEVATED_BG, color=INK, label_padding=0.5
    )
    + scale_fill_manual(values=list(CATEGORY_COLORS.values()), limits=list(CATEGORY_COLORS.keys()))
    + labs(
        title="pie-portfolio-interactive · python · letsplot · anyplot.ai",
        subtitle="Hover for details · Drill-down panels in HTML",
        caption="★  Fixed Income leads at 38% — the largest asset class in this portfolio",
        fill="Asset Class",
    )
    + ggsize(600, 600)
    + theme_void()
    + chart_theme
)

# Drill-down plots — one per asset class, showing individual holdings
drill_down_plots = {}
for cat in category_order:
    cat_df = df[df["category"] == cat].copy().sort_values("weight", ascending=False)
    cat_total = cat_df["weight"].sum()
    cat_df["relative_weight"] = (cat_df["weight"] / cat_total * 100).round(1)
    n = len(cat_df)
    cat_colors = HOLDING_COLORS[:n]
    center_cat_df = pd.DataFrame({"x": [0.0], "y": [0.0], "label": [f"{cat}\n{cat_total:.0f}%"]})

    drill_down_plots[cat] = (
        ggplot(cat_df)
        + geom_pie(
            aes(slice="weight", fill="asset"),
            stat="identity",
            size=18,
            hole=0.35,
            stroke=1.5,
            color=PAGE_BG,
            tooltips=layer_tooltips()
            .title("@asset")
            .line("Portfolio weight: @weight%")
            .line("Category share: @relative_weight%")
            .format("weight", ".1f")
            .format("relative_weight", ".1f"),
            labels=layer_labels().line("@weight%").format("weight", ".1f").size(7),
        )
        + geom_label(
            aes(x="x", y="y", label="label"), data=center_cat_df, size=9, fill=ELEVATED_BG, color=INK, label_padding=0.5
        )
        + scale_fill_manual(values=cat_colors, limits=cat_df["asset"].tolist())
        + labs(title=f"{cat} Holdings", subtitle=f"Total: {cat_total:.0f}% of portfolio", fill="Holding")
        + ggsize(600, 600)
        + theme_void()
        + chart_theme
    )

# PNG — static overview, square canvas: 600×600 × scale=4 → 2400×2400
ggsave(plot_overview, filename=f"plot-{THEME}.png", path=".", scale=4)

# HTML — overview + all four drill-down panels in a ggbunch layout
# Overview left (40%), drill-downs in 2×2 grid on right (30%+30%)
plots = [plot_overview] + list(drill_down_plots.values())
regions = [(0.0, 0.0, 0.4, 1.0)]
for i in range(len(drill_down_plots)):
    col = i % 2
    row = i // 2
    regions.append((0.4 + col * 0.3, row * 0.5, 0.3, 0.5))

bunch = ggbunch(plots, regions) + ggsize(1200, 700)
ggsave(bunch, filename=f"plot-{THEME}.html", path=".")
