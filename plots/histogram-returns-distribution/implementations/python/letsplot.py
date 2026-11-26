"""anyplot.ai
histogram-returns-distribution: Returns Distribution Histogram
Library: letsplot 4.10.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-20
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave
from scipy import stats


LetsPlot.setup_html()  # noqa: F405

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID_COLOR = "#D9D8D1" if THEME == "light" else "#3A3A37"

IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
SIGMA_BAND = 2  # tail regions start beyond this many standard deviations
NORMAL_LABEL = "Normal Range (±2σ)"
TAIL_LABEL = "Tail (beyond ±2σ)"

# Columns: set these to your table's column names
DATE = "Date"  # role: date
RETURNS = "Daily returns (%)"  # role: returns
REGION = "Region"  # role: extra
DENSITY = "Density"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("returns.csv")
np.random.seed(42)
n_days = 252

# Simulate realistic daily stock returns with slight fat tails
base_returns = np.random.normal(loc=0.0003, scale=0.012, size=n_days)
outlier_mask = np.random.random(n_days) < 0.05
outliers = np.random.normal(loc=0, scale=0.035, size=n_days)
returns = np.where(outlier_mask, outliers, base_returns)

df = pd.DataFrame({DATE: pd.bdate_range("2025-01-02", periods=n_days), RETURNS: returns * 100})

# Plot: reads only df and the constants above
mean_ret = df[RETURNS].mean()
std_ret = df[RETURNS].std(ddof=0)
skewness = stats.skew(df[RETURNS])
kurtosis = stats.kurtosis(df[RETURNS])

lower_tail = mean_ret - SIGMA_BAND * std_ret
upper_tail = mean_ret + SIGMA_BAND * std_ret
in_tail = (df[RETURNS] < lower_tail) | (df[RETURNS] > upper_tail)
df[REGION] = np.where(in_tail, TAIL_LABEL, NORMAL_LABEL)

# Normal distribution curve fitted to the data
x_range = np.linspace(df[RETURNS].min() - 0.5 * std_ret, df[RETURNS].max() + 0.5 * std_ret, 200)
normal_pdf = stats.norm.pdf(x_range, loc=mean_ret, scale=std_ret)
df_normal = pd.DataFrame({RETURNS: x_range, DENSITY: normal_pdf})

stats_text = f"Mean: {mean_ret:.3f}%\nStd Dev: {std_ret:.3f}%\nSkewness: {skewness:.2f}\nKurtosis: {kurtosis:.2f}"

# Build theme
anyplot_theme = theme(  # noqa: F405
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),  # noqa: F405
    panel_background=element_rect(fill=PAGE_BG),  # noqa: F405
    panel_grid_major_y=element_line(color=GRID_COLOR, size=0.5),  # noqa: F405
    panel_grid_major_x=element_blank(),  # noqa: F405
    panel_grid_minor=element_blank(),  # noqa: F405
    panel_border=element_blank(),  # noqa: F405
    axis_title=element_text(color=INK, size=12),  # noqa: F405
    axis_text=element_text(color=INK_SOFT, size=10),  # noqa: F405
    axis_line=element_line(color=INK_SOFT),  # noqa: F405
    axis_ticks=element_line(color=INK_SOFT),  # noqa: F405
    plot_title=element_text(color=INK, size=16),  # noqa: F405
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),  # noqa: F405
    legend_text=element_text(color=INK_SOFT, size=10),  # noqa: F405
    legend_title=element_text(color=INK, size=10),  # noqa: F405
    legend_position=[0.15, 0.85],
)

# Plot — histogram with tail highlighting and lets-plot hover tooltips (LF-01)
plot = (
    ggplot(df, aes(x=RETURNS, fill=REGION))  # noqa: F405
    + geom_histogram(  # noqa: F405
        aes(y="..density.."),  # noqa: F405
        bins=30,
        alpha=0.85,
        color=PAGE_BG,
        size=0.5,
        tooltips=layer_tooltips().line(f"@{{{REGION}}}").line("Density: @{..density..|.4f}"),  # noqa: F405
    )
    + geom_line(  # noqa: F405
        data=df_normal,
        mapping=aes(x=RETURNS, y=DENSITY),  # noqa: F405
        color=INK,
        size=1.5,
        linetype="dashed",
        inherit_aes=False,
    )
    + geom_vline(xintercept=lower_tail, color=IMPRINT_PALETTE[1], size=1, linetype="dotted", alpha=0.8)  # noqa: F405
    + geom_vline(xintercept=upper_tail, color=IMPRINT_PALETTE[1], size=1, linetype="dotted", alpha=0.8)  # noqa: F405
    + scale_fill_manual(  # noqa: F405
        values={NORMAL_LABEL: IMPRINT_PALETTE[0], TAIL_LABEL: IMPRINT_PALETTE[1]}, name=REGION
    )
    + labs(  # noqa: F405
        x=RETURNS, y=DENSITY, title="histogram-returns-distribution · python · letsplot · anyplot.ai"
    )
    + theme_minimal()  # noqa: F405
    + anyplot_theme
    + ggsize(800, 450)  # noqa: F405
    + geom_label(  # noqa: F405
        x=upper_tail + 1.75 * std_ret,
        y=normal_pdf.max() * 1.35,
        label=stats_text,
        size=10,
        hjust=0.5,
        fill=ELEVATED_BG,
        color=INK,
        alpha=0.9,
        label_padding=0.5,
        label_size=0.3,
    )
)

# Save PNG (scale 4x → 3200 × 1800 px)
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)

# Save HTML (lets-plot interactive hover tooltips work natively in the HTML output)
ggsave(plot, f"plot-{THEME}.html", path=".")
