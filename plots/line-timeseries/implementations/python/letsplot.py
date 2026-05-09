""" anyplot.ai
line-timeseries: Time Series Line Plot
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-09
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
ACCENT_SOFT = "#D4A574" if THEME == "light" else "#8B7355"
BRAND = "#009E73"

# Data - Daily temperature readings over one year
np.random.seed(42)
dates = pd.date_range(start="2024-01-01", periods=365, freq="D")

# Simulate realistic temperature data with seasonal pattern
day_of_year = np.arange(365)
seasonal_pattern = 15 * np.sin(2 * np.pi * (day_of_year - 80) / 365)
baseline = 12
noise = np.random.randn(365) * 3
temperature = baseline + seasonal_pattern + noise

df = pd.DataFrame({"date": dates, "temperature": temperature})

# Find peak and trough for visual emphasis
max_idx = df["temperature"].idxmax()
min_idx = df["temperature"].idxmin()
extremes = pd.DataFrame([df.iloc[max_idx], df.iloc[min_idx]])

# Theme-adaptive styling with enhanced refinement
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK_SOFT, size=0.25, linetype="solid"),
    panel_grid_minor=element_blank(),
    axis_title=element_text(size=20, color=INK, face="bold"),
    axis_text=element_text(size=16, color=INK_SOFT),
    axis_text_x=element_text(angle=45, hjust=1),
    plot_title=element_text(size=24, color=INK, face="bold"),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(size=16, color=INK_SOFT),
    legend_title=element_text(size=16, color=INK),
    axis_line=element_line(color=INK_SOFT, size=0.4),
)

# Create plot with layered visual hierarchy
plot = (
    ggplot(df, aes(x="date", y="temperature"))
    + geom_smooth(method="loess", span=0.15, color=ACCENT_SOFT, size=1.2, alpha=0.5, se=False)
    + geom_line(color=BRAND, size=1.0, alpha=0.8)
    + geom_point(color=BRAND, size=1.5, alpha=0.6)
    + geom_point(data=extremes, color=BRAND, size=3.5, alpha=0.95)
    + labs(x="Date", y="Temperature (°C)", title="line-timeseries · letsplot · anyplot.ai")
    + scale_x_datetime(format="%b %Y")
    + ggsize(1600, 900)
    + anyplot_theme
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", w=4800, h=2700, unit="px", dpi=100)
ggsave(plot, f"plot-{THEME}.html", path=".")
