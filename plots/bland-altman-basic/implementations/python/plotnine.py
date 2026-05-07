"""anyplot.ai
bland-altman-basic: Bland-Altman Agreement Plot
Library: plotnine | Python 3.13
Quality: pending | Created: 2026-05-07
"""

import os
import pathlib
import sys


script_dir = str(pathlib.Path(__file__).parent)
sys.path = [p for p in sys.path if os.path.abspath(p) != os.path.abspath(script_dir)]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from plotnine import (  # noqa: E402
    aes,
    element_line,
    element_rect,
    element_text,
    geom_hline,
    geom_point,
    geom_text,
    ggplot,
    ggsave,
    labs,
    theme,
)


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

np.random.seed(42)
n = 100
method1 = np.random.normal(loc=130, scale=15, size=n)
method2 = method1 + np.random.normal(loc=2, scale=8, size=n)

mean_values = (method1 + method2) / 2
differences = method1 - method2

mean_diff = np.mean(differences)
std_diff = np.std(differences, ddof=1)
upper_limit = mean_diff + 1.96 * std_diff
lower_limit = mean_diff - 1.96 * std_diff

df = pd.DataFrame({"mean": mean_values, "difference": differences})

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
    panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
    panel_border=element_rect(color=INK_SOFT, fill=None),
    axis_title=element_text(size=20, color=INK),
    axis_text=element_text(size=16, color=INK_SOFT),
    axis_line=element_line(color=INK_SOFT),
    plot_title=element_text(size=24, color=INK),
    figure_size=(16, 9),
    legend_position="none",
)

plot = (
    ggplot(df, aes(x="mean", y="difference"))
    + geom_point(color=BRAND, size=3, alpha=0.6)
    + geom_hline(yintercept=mean_diff, color=INK_SOFT, linetype="solid", size=1)
    + geom_hline(yintercept=upper_limit, color=INK_SOFT, linetype="dashed", size=0.8, alpha=0.7)
    + geom_hline(yintercept=lower_limit, color=INK_SOFT, linetype="dashed", size=0.8, alpha=0.7)
    + geom_text(
        aes(x=np.max(df["mean"]) * 0.98, y=mean_diff + 1),
        label=f"Mean: {mean_diff:.2f}",
        size=14,
        color=INK_SOFT,
        ha="right",
    )
    + geom_text(
        aes(x=np.max(df["mean"]) * 0.98, y=upper_limit + 1.5),
        label=f"+1.96 SD: {upper_limit:.2f}",
        size=14,
        color=INK_SOFT,
        ha="right",
    )
    + geom_text(
        aes(x=np.max(df["mean"]) * 0.98, y=lower_limit - 1.5),
        label=f"-1.96 SD: {lower_limit:.2f}",
        size=14,
        color=INK_SOFT,
        ha="right",
    )
    + labs(
        x="Mean of Two Methods (mmHg)",
        y="Difference (Method 1 - Method 2, mmHg)",
        title="bland-altman-basic · plotnine · anyplot.ai",
    )
    + anyplot_theme
)

output_path = os.path.join(os.path.dirname(__file__), f"plot-{THEME}.png")
ggsave(plot, filename=output_path, dpi=300, width=16, height=9)
