""" anyplot.ai
area-stacked: Stacked Area Chart
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-07
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    geom_area,
    ggplot,
    labs,
    scale_fill_manual,
    scale_x_date,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data: Website traffic sources over 24 months
np.random.seed(42)

dates = pd.date_range(start="2023-01-01", periods=24, freq="MS")

# Generate realistic traffic data with trends
base_direct = 15000 + np.cumsum(np.random.randn(24) * 500)
base_organic = 25000 + np.cumsum(np.random.randn(24) * 800) + np.arange(24) * 300
base_referral = 10000 + np.cumsum(np.random.randn(24) * 400)
base_social = 8000 + np.cumsum(np.random.randn(24) * 600) + np.arange(24) * 200

# Ensure all values are positive
direct = np.maximum(base_direct, 5000)
organic = np.maximum(base_organic, 10000)
referral = np.maximum(base_referral, 3000)
social = np.maximum(base_social, 2000)

# Create long-format DataFrame for stacking
df = pd.DataFrame(
    {
        "Date": np.tile(dates, 4),
        "Visitors": np.concatenate([direct, organic, referral, social]),
        "Source": (["Direct"] * 24 + ["Organic Search"] * 24 + ["Referral"] * 24 + ["Social Media"] * 24),
    }
)

# Order categories by average size (largest at bottom for easier reading)
source_order = ["Organic Search", "Direct", "Referral", "Social Media"]
df["Source"] = pd.Categorical(df["Source"], categories=source_order, ordered=True)

# Okabe-Ito palette
colors = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Theme
anyplot_theme = theme(
    figure_size=(16, 9),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
    panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
    plot_title=element_text(size=24, weight="bold", color=INK),
    axis_title=element_text(size=20, color=INK),
    axis_text=element_text(size=16, color=INK_SOFT),
    axis_text_x=element_text(angle=45, hjust=1),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(size=16, color=INK_SOFT),
    legend_title=element_text(size=18, color=INK),
)

# Create stacked area chart
plot = (
    ggplot(df, aes(x="Date", y="Visitors", fill="Source"))
    + geom_area(alpha=0.85, position="stack")
    + scale_fill_manual(values=colors)
    + scale_x_date(date_labels="%b %Y", date_breaks="3 months")
    + labs(
        title="area-stacked · plotnine · anyplot.ai", x="Month", y="Monthly Visitors (thousands)", fill="Traffic Source"
    )
    + theme_minimal()
    + anyplot_theme
)

# Save
plot.save(f"plot-{THEME}.png", dpi=300, verbose=False)
