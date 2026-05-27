""" anyplot.ai
bar-stacked-percent: 100% Stacked Bar Chart
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-08
"""

import os
import sys

sys.path = [p for p in sys.path if os.path.abspath(p) != os.getcwd()]

import pandas as pd  # noqa: E402
from plotnine import (  # noqa: E402
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_bar,
    ggplot,
    labs,
    position_fill,
    scale_fill_manual,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data - Market share by quarter for tech companies
quarters = ["Q1 2023", "Q2 2023", "Q3 2023", "Q4 2023", "Q1 2024", "Q2 2024"]
companies_ordered = ["Others", "Xiaomi", "Samsung", "Apple"]
data = {
    "Quarter": quarters * 4,
    "Company": (["Apple"] * 6 + ["Samsung"] * 6 + ["Xiaomi"] * 6 + ["Others"] * 6),
    "Share": [
        # Apple
        23,
        21,
        20,
        22,
        21,
        20,
        # Samsung
        22,
        21,
        20,
        19,
        20,
        19,
        # Xiaomi
        12,
        13,
        14,
        14,
        15,
        16,
        # Others
        43,
        45,
        46,
        45,
        44,
        45,
    ],
}
df = pd.DataFrame(data)

# Set categorical ordering for proper display
df["Quarter"] = pd.Categorical(df["Quarter"], categories=quarters, ordered=True)
df["Company"] = pd.Categorical(df["Company"], categories=companies_ordered, ordered=True)

# Color mapping with Okabe-Ito palette
color_map = {"Others": IMPRINT[3], "Xiaomi": IMPRINT[2], "Samsung": IMPRINT[1], "Apple": IMPRINT[0]}

# Theme-adaptive colors for legend and text
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
    panel_grid_minor=element_blank(),
    panel_border=element_rect(color=INK_SOFT, fill=None, size=0.5),
    axis_title=element_text(color=INK, size=20),
    axis_text=element_text(color=INK_SOFT, size=16),
    axis_line=element_line(color=INK_SOFT, size=0.5),
    plot_title=element_text(color=INK, size=24, weight="bold"),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_title=element_text(color=INK, size=16),
    legend_text=element_text(color=INK_SOFT, size=16),
    legend_position="right",
    figure_size=(16, 9),
)

# Create 100% stacked bar chart
plot = (
    ggplot(df, aes(x="Quarter", y="Share", fill="Company"))
    + geom_bar(stat="identity", position=position_fill(), width=0.65)
    + scale_fill_manual(values=color_map)
    + labs(title="bar-stacked-percent · plotnine · anyplot.ai", x="Quarter", y="Market Share (%)", fill="Company")
    + theme_minimal()
    + anyplot_theme
)

# Save
plot.save(f"plot-{THEME}.png", dpi=300, verbose=False)
