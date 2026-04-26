"""anyplot.ai
lollipop-basic: Basic Lollipop Chart
Library: plotnine 0.15.3 | Python 3.14.4
"""

import os

import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    geom_point,
    geom_segment,
    ggplot,
    ggsave,
    labs,
    theme,
    theme_minimal,
)


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

# Data - Product sales by category, sorted by value
data = {
    "category": [
        "Electronics",
        "Furniture",
        "Clothing",
        "Groceries",
        "Sports",
        "Books",
        "Toys",
        "Beauty",
        "Garden",
        "Automotive",
    ],
    "value": [245, 198, 176, 152, 134, 118, 95, 87, 72, 58],
}

df = pd.DataFrame(data)
df = df.sort_values("value", ascending=True).reset_index(drop=True)
df["category"] = pd.Categorical(df["category"], categories=df["category"], ordered=True)

# Plot
plot = (
    ggplot(df, aes(x="category", y="value"))
    + geom_segment(aes(x="category", xend="category", y=0, yend="value"), color=BRAND, size=1.5)
    + geom_point(color=BRAND, size=6, fill=BRAND)
    + labs(x="Product Category", y="Sales (thousands $)", title="lollipop-basic · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        text=element_text(size=14, color=INK),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_text_x=element_text(angle=45, ha="right", color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        plot_title=element_text(size=24, color=INK),
        panel_grid_minor=element_line(alpha=0),
        panel_grid_major_x=element_line(alpha=0),
        panel_grid_major_y=element_line(color=INK, alpha=0.15, size=0.3),
    )
)

ggsave(plot, filename=f"plot-{THEME}.png", dpi=300, width=16, height=9)
