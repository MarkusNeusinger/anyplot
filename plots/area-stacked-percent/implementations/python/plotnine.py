""" anyplot.ai
area-stacked-percent: 100% Stacked Area Chart
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 83/100 | Updated: 2026-05-12
"""

import os
import sys


sys.path = [p for p in sys.path if p != os.path.dirname(__file__)]

import pandas as pd  # noqa: E402
from plotnine import (  # noqa: E402
    aes,
    element_line,
    element_rect,
    element_text,
    geom_area,
    ggplot,
    labs,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette - first position is ALWAYS #009E73
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data - Market share evolution with more dramatic proportion shifts
years = list(range(2015, 2025))

# Generate category data with realistic and dramatic trends
smartphones = [50, 48, 44, 40, 35, 32, 28, 25, 22, 20]
tablets = [28, 26, 22, 18, 15, 12, 10, 8, 6, 5]
wearables = [4, 8, 14, 20, 26, 32, 38, 42, 46, 48]
laptops = [18, 18, 20, 22, 24, 24, 24, 25, 26, 27]

# Create DataFrame in long format for plotnine
df_list = []
for i, year in enumerate(years):
    total = smartphones[i] + tablets[i] + wearables[i] + laptops[i]
    df_list.append(
        {"Year": year, "Category": "Smartphones", "Value": smartphones[i], "Percent": smartphones[i] / total * 100}
    )
    df_list.append({"Year": year, "Category": "Tablets", "Value": tablets[i], "Percent": tablets[i] / total * 100})
    df_list.append(
        {"Year": year, "Category": "Wearables", "Value": wearables[i], "Percent": wearables[i] / total * 100}
    )
    df_list.append({"Year": year, "Category": "Laptops", "Value": laptops[i], "Percent": laptops[i] / total * 100})

df = pd.DataFrame(df_list)

# Set category order for stacking
df["Category"] = pd.Categorical(
    df["Category"], categories=["Smartphones", "Tablets", "Wearables", "Laptops"], ordered=True
)

# Create plot
plot = (
    ggplot(df, aes(x="Year", y="Percent", fill="Category"))
    + geom_area(position="stack", alpha=0.85)
    + scale_fill_manual(values=IMPRINT)
    + scale_x_continuous(breaks=range(2015, 2025, 2))
    + scale_y_continuous(breaks=[0, 25, 50, 75, 100], labels=["0%", "25%", "50%", "75%", "100%"])
    + labs(
        title="area-stacked-percent · plotnine · anyplot.ai", x="Year", y="Market Share (%)", fill="Product Category"
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
        panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
        panel_border=element_rect(color=INK_SOFT, fill=None),
        plot_title=element_text(size=24, weight="bold", color=INK),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.4),
        legend_position="bottom",
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(size=16, color=INK_SOFT),
        legend_title=element_text(size=18, color=INK),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=300, verbose=False)
