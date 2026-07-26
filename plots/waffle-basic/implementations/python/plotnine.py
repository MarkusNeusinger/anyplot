"""anyplot.ai
waffle-basic: Basic Waffle Chart
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 79/100 | Created: 2026-05-05
"""

import os
import sys

import pandas as pd


sys.path.pop(0)
from plotnine import (
    aes,
    coord_equal,
    element_rect,
    element_text,
    geom_tile,
    ggplot,
    guide_legend,
    guides,
    labs,
    scale_fill_manual,
    theme,
    theme_void,
)


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — 8 hues, theme-independent, hybrid-v3 sort
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data — a $5,000 monthly household budget, allocated by category.
# Values sum to exactly 100 (one waffle square = 1% = $50).
categories = ["Housing", "Food", "Transport", "Entertainment"]
values = [39, 28, 20, 13]
monthly_budget = 5000
amounts = [round(v / 100 * monthly_budget) for v in values]
assert sum(values) == 100

# Waffle grid: 10x10 = 100 squares, filled row-major so each category
# forms a contiguous reading-order block.
grid_size = 10
squares = []
square_id = 0
for val, cat in zip(values, categories, strict=True):
    for _ in range(val):
        row = square_id // grid_size
        col = square_id % grid_size
        squares.append({"x": col, "y": grid_size - 1 - row, "category": cat})
        square_id += 1

df = pd.DataFrame(squares)
df["category"] = pd.Categorical(df["category"], categories=categories, ordered=True)

color_map = dict(zip(categories, IMPRINT, strict=True))
value_map = dict(zip(categories, values, strict=True))
amount_map = dict(zip(categories, amounts, strict=True))
legend_labels = {cat: f"{cat} — {value_map[cat]}% (${amount_map[cat]:,})" for cat in categories}

anyplot_theme = theme(
    figure_size=(6, 6),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    plot_title=element_text(size=20, weight="bold", color=INK, ha="center"),
    plot_subtitle=element_text(size=12, color=INK_SOFT, ha="center", style="italic"),
    plot_caption=element_text(size=9, color=INK_MUTED, ha="center"),
    legend_position="bottom",
    legend_direction="horizontal",
    legend_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    legend_key=element_rect(fill=PAGE_BG, color=PAGE_BG),
    legend_title=element_text(size=14, weight="bold", color=INK),
    legend_text=element_text(size=12, color=INK_SOFT),
)

plot = (
    ggplot(df, aes(x="x", y="y", fill="category"))
    + geom_tile(color=PAGE_BG, size=1.4)
    + scale_fill_manual(values=color_map, labels=lambda cats: [legend_labels[c] for c in cats])
    + coord_equal()
    + labs(
        title="waffle-basic · plotnine · anyplot.ai",
        subtitle=f"Monthly Household Budget Allocation — ${monthly_budget:,} Total",
        caption="Each square represents 1% of the total monthly budget",
        fill="Category",
    )
    + guides(fill=guide_legend(ncol=1))
    + theme_void()
    + anyplot_theme
)

plot.save(f"plot-{THEME}.png", dpi=400, width=6, height=6, units="in", verbose=False)
