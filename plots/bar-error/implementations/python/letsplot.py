"""anyplot.ai
bar-error: Bar Chart with Error Bars
Library: letsplot 4.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-10
"""

import os

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_line,
    element_rect,
    element_text,
    geom_bar,
    geom_errorbar,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_fill_manual,
    theme,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID_COLOR = "rgba(26,26,23,0.08)" if THEME == "light" else "rgba(240,239,232,0.08)"

# Imprint palette - first series is brand green
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
GROUP = "Test group"  # role: category
RATE = "Conversion rate (%)"  # role: value
ERROR = "Lower error (%)"  # role: error
ERROR_UPPER = "Upper error (%)"  # role: extra

# Data: A/B test conversion rates with asymmetric 95% CI arms; replace with your own table, e.g. pd.read_csv("ab_test.csv")
df = pd.DataFrame(
    {
        GROUP: ["Control", "Variant A", "Variant B", "Variant C", "Variant D"],
        RATE: [12.3, 14.8, 11.2, 16.5, 13.9],
        ERROR: [1.2, 1.5, 1.0, 1.8, 1.4],
        ERROR_UPPER: [1.4, 1.6, 1.1, 2.0, 1.5],
    }
)

# Plot: reads only df and the constants above
ERR_MIN, ERR_MAX = "ymin", "ymax"
bounds = df.copy()
bounds[ERR_MIN] = df[RATE] - df[ERROR]
bounds[ERR_MAX] = df[RATE] + df[ERROR_UPPER]

plot = (
    ggplot(bounds, aes(x=GROUP, y=RATE, fill=GROUP))
    + geom_bar(stat="identity", width=0.68, show_legend=False, alpha=0.92)
    + geom_errorbar(aes(ymin=ERR_MIN, ymax=ERR_MAX), width=0.23, size=1.0, color=INK_SOFT)
    + scale_fill_manual(values=IMPRINT_PALETTE)
    + labs(title="bar-error · python · letsplot · anyplot.ai", caption="Error bars show the 95% confidence interval")
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major_y=element_line(color=GRID_COLOR, size=0.22),
        panel_grid_major_x=element_line(color="transparent"),
        panel_grid_minor=element_line(color="transparent"),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        plot_title=element_text(size=16, color=INK),
        plot_caption=element_text(size=10, color=INK_SOFT),
    )
    + ggsize(800, 450)
)

# Save as PNG and HTML with theme suffix
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
