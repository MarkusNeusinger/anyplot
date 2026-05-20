"""anyplot.ai
histogram-returns-distribution: Returns Distribution Histogram
Library: plotnine | Python 3.13
Quality: pending | Created: 2026-05-20
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_histogram,
    geom_line,
    geom_vline,
    ggplot,
    labs,
    scale_fill_manual,
    theme,
    theme_minimal,
)
from scipy import stats


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442"]

# Data - 252 trading days with slight fat tails (mixture of normals)
np.random.seed(42)
n_days = 252
normal_returns = np.random.normal(0.0005, 0.015, int(n_days * 0.9))
fat_tail_returns = np.random.normal(0, 0.04, int(n_days * 0.1))
returns = np.concatenate([normal_returns, fat_tail_returns])
np.random.shuffle(returns)
returns = returns[:n_days]
returns_pct = returns * 100

mean_ret = np.mean(returns_pct)
std_ret = np.std(returns_pct)
skewness = stats.skew(returns_pct)
kurtosis = stats.kurtosis(returns_pct)

lower_tail = mean_ret - 2 * std_ret
upper_tail = mean_ret + 2 * std_ret

df = pd.DataFrame({"returns": returns_pct})
df["region"] = pd.cut(
    df["returns"], bins=[-np.inf, lower_tail, upper_tail, np.inf], labels=["Left Tail", "Center", "Right Tail"]
)

# Normal distribution overlay (count scale to match histogram)
x_range = np.linspace(returns_pct.min() - 1, returns_pct.max() + 1, 300)
normal_pdf = stats.norm.pdf(x_range, mean_ret, std_ret)
bin_width = (returns_pct.max() - returns_pct.min()) / 30
normal_scaled = normal_pdf * len(returns_pct) * bin_width
df_normal = pd.DataFrame({"x": x_range, "y": normal_scaled})

stats_label = f"Mean: {mean_ret:.2f}%\nStd Dev: {std_ret:.2f}%\nSkewness: {skewness:.2f}\nExc. Kurtosis: {kurtosis:.2f}"

# Okabe-Ito fill: center green (pos 1), both tails vermillion (pos 2)
fill_colors = {"Left Tail": OKABE_ITO[1], "Center": OKABE_ITO[0], "Right Tail": OKABE_ITO[1]}

# Plot
plot = (
    ggplot(df, aes(x="returns", fill="region"))
    + geom_histogram(bins=30, color=PAGE_BG, alpha=0.85, size=0.3)
    + geom_line(data=df_normal, mapping=aes(x="x", y="y"), color=OKABE_ITO[2], size=1.2, inherit_aes=False)
    + geom_vline(xintercept=mean_ret, linetype="dashed", color=INK, size=0.8)
    + geom_vline(xintercept=lower_tail, linetype="dotted", color=OKABE_ITO[1], size=0.8)
    + geom_vline(xintercept=upper_tail, linetype="dotted", color=OKABE_ITO[1], size=0.8)
    + scale_fill_manual(values=fill_colors, name="Region")
    + annotate(
        "label",
        x=returns_pct.max() - 0.5,
        y=max(normal_scaled) * 0.92,
        label=stats_label,
        ha="right",
        va="top",
        size=8,
        fill=ELEVATED_BG,
        color=INK,
        label_size=0.3,
        label_padding=0.4,
    )
    + labs(
        x="Daily Returns (%)", y="Frequency", title="histogram-returns-distribution · python · plotnine · anyplot.ai"
    )
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_border=element_blank(),
        axis_line=element_line(color=INK_SOFT),
        panel_grid_major=element_line(color=INK_SOFT, size=0.3, alpha=0.10),
        panel_grid_minor=element_blank(),
        plot_title=element_text(color=INK, size=12),
        axis_title=element_text(color=INK, size=10),
        axis_text=element_text(color=INK_SOFT, size=8),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(color=INK_SOFT, size=8),
        legend_title=element_text(color=INK, size=8),
        legend_position="right",
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
