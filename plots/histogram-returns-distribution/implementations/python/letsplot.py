"""anyplot.ai
histogram-returns-distribution: Returns Distribution Histogram
Library: letsplot | Python 3.13
Quality: pending | Created: 2026-05-20
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

OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442"]

# Data
np.random.seed(42)
n_days = 252

# Simulate realistic daily stock returns with slight fat tails
base_returns = np.random.normal(loc=0.0003, scale=0.012, size=n_days)
outlier_mask = np.random.random(n_days) < 0.05
outliers = np.random.normal(loc=0, scale=0.035, size=n_days)
returns = np.where(outlier_mask, outliers, base_returns)

# Calculate statistics
mean_ret = np.mean(returns) * 100
std_ret = np.std(returns) * 100
skewness = stats.skew(returns)
kurtosis = stats.kurtosis(returns)

# Create DataFrame for plotting (convert to percentage)
df = pd.DataFrame({"returns": returns * 100})

# Define tail thresholds (beyond 2 standard deviations)
lower_tail = mean_ret - 2 * std_ret
upper_tail = mean_ret + 2 * std_ret

df["region"] = np.where(
    df["returns"] < lower_tail,
    "Tail (beyond ±2σ)",
    np.where(df["returns"] > upper_tail, "Tail (beyond ±2σ)", "Normal Range (±2σ)"),
)

# Generate normal distribution curve for overlay
x_min, x_max = df["returns"].min(), df["returns"].max()
x_range = np.linspace(x_min - 0.5, x_max + 0.5, 200)
normal_pdf = stats.norm.pdf(x_range, loc=mean_ret, scale=std_ret)
df_normal = pd.DataFrame({"x": x_range, "density": normal_pdf})

# Statistics text for annotation
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
    ggplot(df, aes(x="returns", fill="region"))  # noqa: F405
    + geom_histogram(  # noqa: F405
        aes(y="..density.."),  # noqa: F405
        bins=30,
        alpha=0.85,
        color=PAGE_BG,
        size=0.5,
        tooltips=layer_tooltips().line("@region").line("Density: @{..density..|.4f}"),  # noqa: F405
    )
    + geom_line(  # noqa: F405
        data=df_normal,
        mapping=aes(x="x", y="density"),  # noqa: F405
        color=INK,
        size=1.5,
        linetype="dashed",
        inherit_aes=False,
    )
    + geom_vline(xintercept=lower_tail, color=OKABE_ITO[1], size=1, linetype="dotted", alpha=0.8)  # noqa: F405
    + geom_vline(xintercept=upper_tail, color=OKABE_ITO[1], size=1, linetype="dotted", alpha=0.8)  # noqa: F405
    + scale_fill_manual(  # noqa: F405
        values={"Normal Range (±2σ)": OKABE_ITO[0], "Tail (beyond ±2σ)": OKABE_ITO[1]}, name="Region"
    )
    + labs(  # noqa: F405
        x="Daily Returns (%)", y="Density", title="histogram-returns-distribution · python · letsplot · anyplot.ai"
    )
    + theme_minimal()  # noqa: F405
    + anyplot_theme
    + ggsize(800, 450)  # noqa: F405
    + geom_label(  # noqa: F405
        x=x_max - 0.5,
        y=normal_pdf.max() * 0.95,
        label=stats_text,
        size=10,
        hjust=1,
        fill=ELEVATED_BG,
        color=INK,
        alpha=0.9,
        label_padding=0.5,
    )
)

# Save PNG (scale 4x → 3200 × 1800 px)
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)

# Save HTML (lets-plot interactive hover tooltips work natively in the HTML output)
ggsave(plot, f"plot-{THEME}.html", path=".")
