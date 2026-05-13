"""anyplot.ai
errorbar-asymmetric: Asymmetric Error Bars Plot
Library: letsplot | Python 3.13
Quality: 93/100 | Updated: 2025-05-13
"""
# ruff: noqa: F405

import os

import pandas as pd
from lets_plot import *  # noqa: F403, F401
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Okabe-Ito position 1

# Data - Quarterly sales performance with asymmetric confidence intervals
quarters = ["Q1", "Q2", "Q3", "Q4"]
sales = [85, 92, 78, 105]
error_lower = [8, 5, 12, 7]  # Lower error (downside risk)
error_upper = [15, 18, 6, 22]  # Upper error (upside potential)

df = pd.DataFrame(
    {
        "quarter": quarters,
        "sales": sales,
        "ymin": [s - el for s, el in zip(sales, error_lower, strict=True)],
        "ymax": [s + eu for s, eu in zip(sales, error_upper, strict=True)],
    }
)

# Plot
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK_SOFT, size=0.2),
    panel_grid_minor=element_blank(),
    axis_title=element_text(color=INK, size=20),
    axis_text=element_text(color=INK_SOFT, size=16),
    axis_line=element_line(color=INK_SOFT, size=0.5),
    plot_title=element_text(color=INK, size=24, face="bold"),
    plot_caption=element_text(color=INK_SOFT, size=14),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=16),
)

plot = (
    ggplot(df, aes(x="quarter", y="sales"))
    + geom_point(
        size=6,
        color=BRAND,
        alpha=0.9,
        tooltips=layer_tooltips().line("Quarter|@quarter").line("Sales|@sales").line("Min|@ymin").line("Max|@ymax"),
    )
    + geom_errorbar(aes(ymin="ymin", ymax="ymax"), width=0.3, size=1.5, color=BRAND)
    + labs(
        x="Quarter",
        y="Sales (thousands USD)",
        title="errorbar-asymmetric · letsplot · anyplot.ai",
        caption="Error bars represent 10th-90th percentile forecast range",
    )
    + scale_y_continuous(limits=[50, 140])
    + theme_minimal()
    + anyplot_theme
    + ggsize(1600, 900)
)

# Save
ggsave(plot, filename=f"plot-{THEME}.png", path=".")
ggsave(plot, filename=f"plot-{THEME}.html", path=".")
