""" anyplot.ai
mosaic-categorical: Mosaic Plot for Categorical Association Analysis
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-19
"""

import os

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_rect,
    geom_text,
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
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Okabe-Ito palette — first series always #009E73
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7"]

# Data — Titanic survival cross-tabulated by passenger class
categories_1 = ["First Class", "Second Class", "Third Class", "Crew"]
categories_2 = ["Survived", "Did Not Survive"]

frequencies = {"First Class": [202, 123], "Second Class": [118, 167], "Third Class": [178, 528], "Crew": [212, 673]}

# Column widths proportional to category_1 marginals
cat1_totals = {cat: sum(freqs) for cat, freqs in frequencies.items()}
grand_total = sum(cat1_totals.values())
cat1_widths = {cat: total / grand_total * 100 for cat, total in cat1_totals.items()}

# Build rectangle coordinates for the mosaic
rects = []
x_pos = 0
gap = 0.8

for cat1 in categories_1:
    col_width = cat1_widths[cat1] - gap
    col_freqs = frequencies[cat1]
    col_total = cat1_totals[cat1]

    y_pos = 0
    for i, cat2 in enumerate(categories_2):
        freq = col_freqs[i]
        segment_height = (freq / col_total) * 100

        rects.append(
            {
                "category_1": cat1,
                "category_2": cat2,
                "frequency": freq,
                "xmin": x_pos + gap / 2,
                "xmax": x_pos + col_width + gap / 2,
                "ymin": y_pos + 0.3,
                "ymax": y_pos + segment_height - 0.3,
                "x_center": x_pos + cat1_widths[cat1] / 2,
                "y_center": y_pos + segment_height / 2,
            }
        )
        y_pos += segment_height

    x_pos += cat1_widths[cat1]

df = pd.DataFrame(rects)

# X-axis breaks at column centres
x_breaks = []
x_pos = 0
for cat1 in categories_1:
    x_breaks.append(x_pos + cat1_widths[cat1] / 2)
    x_pos += cat1_widths[cat1]

# Plot
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_blank(),
    panel_grid_minor=element_blank(),
    axis_line=element_line(color=INK_SOFT),
    axis_title=element_text(color=INK, size=20),
    axis_text=element_text(color=INK_SOFT, size=16),
    axis_text_x=element_text(color=INK_SOFT, size=16),
    axis_text_y=element_text(color=INK_SOFT, size=16),
    plot_title=element_text(color=INK, size=24, hjust=0.5),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=16),
    legend_title=element_text(color=INK, size=18),
    legend_position="right",
)

plot = (
    ggplot(df)
    + geom_rect(aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="category_2"), color=PAGE_BG, size=0.5)
    + geom_text(aes(x="x_center", y="y_center", label="frequency"), size=14, color="white", fontface="bold")
    + scale_fill_manual(values=OKABE_ITO[:2], name="Survival Status")
    + scale_x_continuous(name="Passenger Class  (width ∝ count)", breaks=x_breaks, labels=categories_1, limits=[0, 100])
    + scale_y_continuous(name="Survival Rate (%)", limits=[0, 100], breaks=[0, 25, 50, 75, 100])
    + labs(title="mosaic-categorical · python · letsplot · anyplot.ai")
    + theme_minimal()
    + anyplot_theme
    + ggsize(1600, 900)
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)
ggsave(plot, f"plot-{THEME}.html", path=".")
