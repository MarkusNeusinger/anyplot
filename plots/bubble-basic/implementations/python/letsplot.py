"""anyplot.ai
bubble-basic: Basic Bubble Chart
Library: letsplot | Python 3.13
Quality: pending | Updated: 2026-05-28
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
    geom_point,
    geom_smooth,
    ggplot,
    ggsave,
    ggsize,
    guide_legend,
    guides,
    labs,
    layer_tooltips,
    scale_color_manual,
    scale_size_area,
    scale_x_continuous,
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
RULE = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

ANYPLOT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030"]

# Data - market analysis: companies by revenue, growth rate, and market share
np.random.seed(42)

sectors = ["Technology", "Healthcare", "Finance", "Energy", "Consumer Goods"]
rev_ranges = [(15, 120), (20, 140), (50, 200), (60, 195), (10, 130)]
growth_params = [(28, -0.10), (18, -0.04), (10, -0.02), (7, -0.01), (15, -0.05)]
share_means = [10, 14, 20, 22, 12]
counts = [10, 10, 9, 8, 8]

rows = []
for sector, (rev_lo, rev_hi), (g_base, g_slope), s_mean, n in zip(
    sectors, rev_ranges, growth_params, share_means, counts, strict=True
):
    rev = np.random.uniform(rev_lo, rev_hi, n)
    growth = g_base + g_slope * rev + np.random.randn(n) * 2.5
    share = np.clip(np.random.randn(n) * 5 + s_mean, 2, 30)
    for r, g, s in zip(rev, growth, share, strict=True):
        rows.append({"revenue": r, "growth_rate": g, "market_share": s, "sector": sector})

df = pd.DataFrame(rows)

# Plot
plot = (
    ggplot(df, aes(x="revenue", y="growth_rate", size="market_share", color="sector"))
    + geom_point(
        alpha=0.7,
        tooltips=layer_tooltips()
        .format("revenue", "${.1f}M")
        .format("growth_rate", "{.1f}%")
        .format("market_share", "{.1f}%")
        .line("@sector")
        .line("Revenue|@revenue")
        .line("Growth|@growth_rate")
        .line("Market Share|@market_share"),
    )
    + geom_smooth(
        aes(x="revenue", y="growth_rate"),
        method="loess",
        color=INK_SOFT,
        size=1.5,
        alpha=0.12,
        inherit_aes=False,
        show_legend=False,
    )
    + scale_size_area(max_size=22, name="Market Share (%)", breaks=[5, 10, 15, 20, 25])
    + scale_color_manual(values=ANYPLOT_PALETTE, name="Sector")
    + scale_x_continuous(expand=[0.02, 10])
    + guides(
        color=guide_legend(nrow=1, override_aes={"size": 7}),
        size=guide_legend(nrow=1, override_aes={"color": ANYPLOT_PALETTE[0], "alpha": 0.7}),
    )
    + labs(x="Revenue (Million USD)", y="Growth Rate (%)", title="bubble-basic · python · letsplot · anyplot.ai")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        plot_title=element_text(size=16, color=INK),
        plot_margin=[30, 20, 20, 20],
        legend_title=element_text(size=10, color=INK),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT, size=0.5),
        panel_grid_major=element_line(size=0.3, color=RULE),
        panel_grid_minor=element_blank(),
        legend_position="bottom",
    )
    + ggsize(800, 450)
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
