""" anyplot.ai
bar-grouped: Grouped Bar Chart
Library: plotnine 0.15.7 | Python 3.13.14
Quality: 93/100 | Updated: 2026-08-05
"""

import os

import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_col,
    geom_text,
    ggplot,
    ggsave,
    labs,
    position_dodge,
    scale_fill_manual,
    scale_y_continuous,
    theme,
)


# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette (first series always #009E73)
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data - Regional sales across product categories, ordered by total revenue
# so the chart reads as a declining performance story left to right
regions = ["North America", "Europe", "Asia Pacific", "Latin America", "Middle East"]
data = {
    "Region": regions * 3,
    "Category": ["Electronics"] * 5 + ["Apparel"] * 5 + ["Home Goods"] * 5,
    "Revenue": [145, 118, 162, 68, 52, 78, 95, 54, 42, 31, 62, 71, 48, 35, 28],
}
df = pd.DataFrame(data)

# Order regions by total revenue (descending) and categories to match the Imprint order
df["Region"] = pd.Categorical(df["Region"], categories=regions, ordered=True)
df["Category"] = pd.Categorical(df["Category"], categories=["Electronics", "Apparel", "Home Goods"], ordered=True)

# Highlight the single top-performing region/category pairing as the chart's focal point
top = df.loc[df["Revenue"].idxmax()]
subtitle = f"{top.Region} leads all groups at ${top.Revenue:.0f}M in {top.Category}"

# Theme-adaptive chrome
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_border=element_blank(),
    axis_line_x=element_line(color=INK_SOFT, size=0.8),
    axis_line_y=element_line(color=INK_SOFT, size=0.8),
    axis_ticks_major=element_blank(),
    panel_grid_major_x=element_blank(),
    panel_grid_minor=element_blank(),
    panel_grid_major_y=element_line(color=INK, size=0.3, alpha=0.12),
    axis_title=element_text(size=10, color=INK),
    axis_text=element_text(size=8, color=INK_SOFT),
    plot_title=element_text(size=12, color=INK),
    plot_subtitle=element_text(size=9, color=INK_SOFT),
    legend_background=element_rect(fill=ELEVATED_BG, color=ELEVATED_BG),
    legend_key=element_rect(fill=ELEVATED_BG, color=ELEVATED_BG),
    legend_text=element_text(size=8, color=INK_SOFT),
    legend_title=element_text(size=9, color=INK),
    figure_size=(8, 4.5),
)

# Plot
plot = (
    ggplot(df, aes(x="Region", y="Revenue", fill="Category"))
    + geom_col(position=position_dodge(width=0.75), width=0.65)
    + geom_text(
        aes(label="Revenue"),
        position=position_dodge(width=0.75),
        format_string="${:.0f}",
        va="bottom",
        size=2.8,
        color=INK_SOFT,
    )
    + scale_fill_manual(values=IMPRINT)
    + scale_y_continuous(labels=lambda ticks: [f"${v:.0f}M" for v in ticks], expand=(0, 0, 0.12, 0))
    + labs(
        x="Region",
        y="Revenue ($M)",
        title="bar-grouped · python · plotnine · anyplot.ai",
        subtitle=subtitle,
        fill="Product Category",
    )
    + anyplot_theme
)

# Save
ggsave(plot, filename=f"plot-{THEME}.png", dpi=400, width=8, height=4.5)
