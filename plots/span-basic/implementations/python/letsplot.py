""" anyplot.ai
span-basic: Basic Span Plot (Highlighted Region)
Library: letsplot 4.11.0 | Python 3.13.14
Quality: 85/100 | Updated: 2026-07-25
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
    geom_line,
    geom_rect,
    geom_text,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_fill_manual,
    scale_x_continuous,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Imprint palette position 1 — ALWAYS first series
ANYPLOT_AMBER = "#DDCC77"  # warning / caution semantic anchor — fits a highlighted span

# Data - simulated economic indicator over time (2006-2011)
np.random.seed(42)
months = pd.date_range("2006-01", periods=72, freq="ME")
# Economic cycle: growth -> recession dip -> recovery
base = np.linspace(105, 90, 24).tolist() + np.linspace(90, 75, 18).tolist() + np.linspace(75, 115, 30).tolist()
noise = np.random.randn(72) * 2.5
values = np.array(base) + noise

df = pd.DataFrame({"date": months, "index": values})
df["date_num"] = np.arange(len(df))

# Year labels for x-axis
year_positions = [0, 12, 24, 36, 48, 60]
year_labels = ["2006", "2007", "2008", "2009", "2010", "2011"]

# Span region - recession period (Jan 2008 to Jun 2009)
recession_start = 24
recession_end = 42

spans = pd.DataFrame(
    {
        "xmin": [recession_start],
        "xmax": [recession_end],
        "ymin": [df["index"].min() - 8],
        "ymax": [df["index"].max() + 8],
        "label": ["Recession Period"],
    }
)

# Label position for span annotation
span_label = pd.DataFrame(
    {"x": [(recession_start + recession_end) / 2], "y": [df["index"].max() + 4], "text": ["Recession 2008-2009"]}
)

# Theme-adaptive chrome (see prompts/library/letsplot.md "Theme-adaptive Chrome")
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major_x=element_blank(),
    panel_grid_minor_x=element_blank(),
    panel_grid_major_y=element_line(color=INK, size=0.3),
    panel_grid_minor_y=element_blank(),
    axis_title=element_text(color=INK, size=12),
    axis_text=element_text(color=INK_SOFT, size=10),
    axis_line=element_line(color=INK_SOFT),
    plot_title=element_text(color=INK, size=16),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=10),
    legend_title=element_text(color=INK, size=10),
)

# Plot
plot = (
    ggplot()
    # Vertical span for the recession period, semi-transparent to keep the line visible
    + geom_rect(
        data=spans,
        mapping=aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="label"),
        color=ANYPLOT_AMBER,
        alpha=0.25,
    )
    # Economic indicator line
    + geom_line(data=df, mapping=aes(x="date_num", y="index"), color=BRAND, size=1.8)
    # Span label annotation
    + geom_text(data=span_label, mapping=aes(x="x", y="y", label="text"), size=4, color=INK)
    + labs(x="Year", y="Economic Index", title="span-basic · python · letsplot · anyplot.ai")
    + scale_fill_manual(values=[ANYPLOT_AMBER], name="Highlighted Region")
    + scale_x_continuous(breaks=year_positions, labels=year_labels)
    + theme_minimal()
    + anyplot_theme
    + ggsize(800, 450)
)

# Save PNG (scale 4x gives 3200 x 1800 px) + HTML
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
