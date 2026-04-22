""" pyplots.ai
bubble-basic: Basic Bubble Chart
Library: letsplot 4.8.2 | Python 3.14.3
Quality: 86/100 | Updated: 2026-02-16
"""

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

# Data - market analysis: companies by revenue, growth rate, and market share
np.random.seed(42)

sectors = {
    "Technology": {"n": 10, "rev": (15, 120), "growth_base": 28, "growth_slope": -0.10, "share_mean": 10},
    "Healthcare": {"n": 10, "rev": (20, 140), "growth_base": 18, "growth_slope": -0.04, "share_mean": 14},
    "Finance": {"n": 9, "rev": (50, 200), "growth_base": 10, "growth_slope": -0.02, "share_mean": 20},
    "Energy": {"n": 8, "rev": (60, 195), "growth_base": 7, "growth_slope": -0.01, "share_mean": 22},
    "Consumer Goods": {"n": 8, "rev": (10, 130), "growth_base": 15, "growth_slope": -0.05, "share_mean": 12},
}

rows = []
for sector, spec in sectors.items():
    rev = np.random.uniform(*spec["rev"], spec["n"])
    growth = spec["growth_base"] + spec["growth_slope"] * rev + np.random.randn(spec["n"]) * 2.5
    share = np.clip(np.random.randn(spec["n"]) * 5 + spec["share_mean"], 2, 30)
    for r, g, s in zip(rev, growth, share, strict=True):
        rows.append({"revenue": r, "growth_rate": g, "market_share": s, "sector": sector})

df = pd.DataFrame(rows)

# Palette: Python Blue first, colorblind-safe complementary colors
palette = ["#306998", "#E5883E", "#2A9D8F", "#8B5CF6", "#E63946"]

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
        color="#444444",
        size=1.5,
        alpha=0.12,
        inherit_aes=False,
        show_legend=False,
    )
    + scale_size_area(max_size=24, name="Market Share (%)", breaks=[5, 10, 15, 20, 25])
    + scale_color_manual(values=palette, name="Sector")
    + scale_x_continuous(expand=[0.02, 10])
    + guides(
        color=guide_legend(override_aes={"size": 7}), size=guide_legend(override_aes={"color": "#306998", "alpha": 0.7})
    )
    + labs(x="Revenue (Million USD)", y="Growth Rate (%)", title="bubble-basic · letsplot · pyplots.ai")
    + theme_minimal()
    + theme(
        axis_title=element_text(size=20, margin=[10, 10, 10, 10]),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24, margin=[0, 0, 12, 0]),
        plot_margin=[30, 20, 20, 20],
        legend_title=element_text(size=16),
        legend_text=element_text(size=14),
        legend_background=element_rect(fill="#FAFAFA", color="#E8E8E8", size=0.5),
        panel_grid_major=element_line(size=0.3, color="#E0E0E0"),
        panel_grid_minor=element_blank(),
        legend_position="right",
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
plot.to_html("plot.html")
