""" anyplot.ai
bar-grouped: Grouped Bar Chart
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 83/100 | Updated: 2026-05-06
"""

import os

import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    geom_bar,
    ggplot,
    ggsave,
    labs,
    position_dodge,
    scale_fill_manual,
    theme,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (first series always #009E73)
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data - Quarterly revenue by product line
data = {
    "Quarter": ["Q1", "Q1", "Q1", "Q2", "Q2", "Q2", "Q3", "Q3", "Q3", "Q4", "Q4", "Q4"],
    "Product": [
        "Software",
        "Hardware",
        "Services",
        "Software",
        "Hardware",
        "Services",
        "Software",
        "Hardware",
        "Services",
        "Software",
        "Hardware",
        "Services",
    ],
    "Revenue": [120, 85, 45, 135, 92, 52, 148, 78, 61, 165, 88, 70],
}
df = pd.DataFrame(data)

# Ensure categorical order matches Okabe-Ito palette order
df["Product"] = pd.Categorical(df["Product"], categories=["Software", "Hardware", "Services"], ordered=True)

# Theme-adaptive chrome
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK_SOFT, size=0.3, alpha=0.10),
    panel_border=element_rect(color=INK_SOFT, fill=None),
    axis_title=element_text(size=20, color=INK),
    axis_text=element_text(size=16, color=INK_SOFT),
    axis_line=element_line(color=INK_SOFT),
    plot_title=element_text(size=24, color=INK),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(size=16, color=INK_SOFT),
    legend_title=element_text(size=18, color=INK),
    figure_size=(16, 9),
)

# Plot
plot = (
    ggplot(df, aes(x="Quarter", y="Revenue", fill="Product"))
    + geom_bar(stat="identity", position=position_dodge(width=0.8), width=0.7)
    + scale_fill_manual(values=IMPRINT)
    + labs(x="Quarter", y="Revenue ($ millions)", title="bar-grouped · plotnine · anyplot.ai", fill="Product Line")
    + anyplot_theme
)

# Save
ggsave(plot, filename=f"plot-{THEME}.png", dpi=300, width=16, height=9)
