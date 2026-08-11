""" anyplot.ai
scatter-regression-polynomial: Scatter Plot with Polynomial Regression
Library: plotnine 0.15.7 | Python 3.13.14
Quality: 92/100 | Updated: 2026-08-11
"""

import os

import numpy as np
import pandas as pd
from mizani.formatters import label_dollar
from plotnine import (
    aes,
    annotate,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_point,
    geom_rug,
    geom_smooth,
    ggplot,
    labs,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
BRAND = "#009E73"
TREND = "#C475FD"

# Diminishing-returns marketing economics: ad spend growth outpaces revenue
# growth as budgets scale, a concave (monotonic, saturating) curve rather
# than the U-shaped minimum used by the temperature/energy sibling scenario.
np.random.seed(42)
n_points = 90
spend = np.random.uniform(5, 200, n_points)
revenue = 20 + 3.2 * spend - 0.0075 * spend**2 + np.random.normal(0, 15, n_points)

df = pd.DataFrame({"spend": spend, "revenue": revenue})

coeffs = np.polyfit(spend, revenue, 2)
poly_func = np.poly1d(coeffs)
y_pred = poly_func(spend)
ss_res = np.sum((revenue - y_pred) ** 2)
ss_tot = np.sum((revenue - np.mean(revenue)) ** 2)
r_squared = 1 - (ss_res / ss_tot)

a, b, c = coeffs
b_sign = "+" if b >= 0 else "-"
c_sign = "+" if c >= 0 else "-"
equation_text = f"y = {a:.4f}x² {b_sign} {abs(b):.3f}x {c_sign} {abs(c):.2f}"
r_squared_text = f"R² = {r_squared:.3f}"
annotation_text = f"{equation_text}\n{r_squared_text}"

money_fmt = label_dollar(prefix="$", suffix="K", precision=0)

plot = (
    ggplot(df, aes(x="spend", y="revenue"))
    + geom_point(size=4, alpha=0.65, color=BRAND)
    + geom_rug(sides="b", alpha=0.35, color=BRAND, length=0.025)
    + geom_smooth(method="lm", formula="y ~ I(x) + I(x**2)", se=True, color=TREND, fill=INK_MUTED, alpha=0.25, size=2)
    + annotate(
        "label",
        x=195,
        y=55,
        label=annotation_text,
        ha="right",
        va="bottom",
        size=17,
        color=INK,
        fill=ELEVATED_BG,
        label_size=0.6,
        label_padding=0.3,
    )
    + labs(title="scatter-regression-polynomial · plotnine · anyplot.ai", x="Marketing Spend", y="Revenue")
    + scale_x_continuous(labels=money_fmt)
    + scale_y_continuous(labels=money_fmt)
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
        panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
        panel_border=element_blank(),
        text=element_text(size=7, color=INK),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        plot_title=element_text(size=12, color=INK),
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
