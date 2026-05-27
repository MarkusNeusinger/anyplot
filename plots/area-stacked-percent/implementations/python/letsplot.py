""" anyplot.ai
area-stacked-percent: 100% Stacked Area Chart
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-12
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
    geom_area,
    ggplot,
    ggsize,
    labs,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID_COLOR = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette (first series is always #009E73)
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data - Market share evolution over 8 years
np.random.seed(42)

years = list(range(2016, 2024))

# Simulate market share trends (values will be normalized to 100%)
company_a = [40, 38, 42, 45, 48, 52, 55, 58]  # Growing leader
company_b = [35, 36, 33, 30, 28, 25, 23, 22]  # Declining
company_c = [15, 16, 15, 16, 15, 14, 13, 12]  # Stable small player
company_d = [10, 10, 10, 9, 9, 9, 9, 8]  # Smallest, slight decline

# Normalize to 100%
totals = [a + b + c + d for a, b, c, d in zip(company_a, company_b, company_c, company_d, strict=False)]
company_a_pct = [a / t * 100 for a, t in zip(company_a, totals, strict=False)]
company_b_pct = [b / t * 100 for b, t in zip(company_b, totals, strict=False)]
company_c_pct = [c / t * 100 for c, t in zip(company_c, totals, strict=False)]
company_d_pct = [d / t * 100 for d, t in zip(company_d, totals, strict=False)]

# Create long-format dataframe for lets-plot
df = pd.DataFrame(
    {
        "Year": years * 4,
        "Share": company_a_pct + company_b_pct + company_c_pct + company_d_pct,
        "Company": ["Company A"] * 8 + ["Company B"] * 8 + ["Company C"] * 8 + ["Company D"] * 8,
    }
)

# Set category order for proper stacking
df["Company"] = pd.Categorical(
    df["Company"], categories=["Company D", "Company C", "Company B", "Company A"], ordered=True
)

# Plot
plot = (
    ggplot(df, aes(x="Year", y="Share", fill="Company"))
    + geom_area(position="fill", alpha=0.85)
    + scale_fill_manual(values=IMPRINT)
    + scale_x_continuous(breaks=list(range(2016, 2024)))
    + scale_y_continuous(format=".0%")
    + labs(x="Year", y="Market Share (%)", title="area-stacked-percent · letsplot · anyplot.ai")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=GRID_COLOR, size=0.3),
        panel_grid_minor=element_blank(),
        plot_title=element_text(size=24, color=INK),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(size=16, color=INK_SOFT),
        legend_title=element_text(size=16, color=INK),
    )
    + ggsize(1600, 900)
)

# Save PNG (scale=3 gives 4800x2700)
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)

# Save HTML for interactivity
ggsave(plot, f"plot-{THEME}.html", path=".")
