""" anyplot.ai
line-arrhenius: Arrhenius Plot for Reaction Kinetics
Library: plotnine 0.15.7 | Python 3.13.14
Quality: 91/100 | Updated: 2026-06-24
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
    geom_line,
    geom_point,
    geom_ribbon,
    ggplot,
    labs,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from scipy.stats import t as t_dist


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — first series always #009E73, position 3 for fit line
BRAND = "#009E73"
BLUE = "#4467A3"

# Data — first-order decomposition, 300–600 K with realistic experimental scatter
temperature_K = np.array([300, 350, 400, 450, 500, 550, 600])
noise = np.array([0.22, -0.18, 0.25, -0.14, 0.19, -0.21, 0.15])
rate_constant_k = np.exp(-4878.0 / temperature_K + 9.5 + noise)

inv_T = 1.0 / temperature_K
ln_k = np.log(rate_constant_k)

# Regression statistics
coeffs = np.polyfit(inv_T, ln_k, 1)
slope, intercept = coeffs
ln_k_pred = np.polyval(coeffs, inv_T)
ss_res = np.sum((ln_k - ln_k_pred) ** 2)
ss_tot = np.sum((ln_k - ln_k.mean()) ** 2)
r_squared = 1 - ss_res / ss_tot

R_gas = 8.314
Ea_kJ = -slope * R_gas / 1000

df = pd.DataFrame({"inv_T": inv_T, "ln_k": ln_k})

# Regression line with 95% confidence band
inv_T_fine = np.linspace(inv_T.min(), inv_T.max(), 200)
ln_k_fit = np.polyval(coeffs, inv_T_fine)

n = len(inv_T)
se_residual = np.sqrt(ss_res / (n - 2))
inv_T_mean = inv_T.mean()
inv_T_ss = np.sum((inv_T - inv_T_mean) ** 2)
se_fit = se_residual * np.sqrt(1.0 / n + (inv_T_fine - inv_T_mean) ** 2 / inv_T_ss)
t_val = t_dist.ppf(0.975, n - 2)
ci_lower = ln_k_fit - t_val * se_fit
ci_upper = ln_k_fit + t_val * se_fit

df_fit = pd.DataFrame({"inv_T": inv_T_fine, "ln_k_fit": ln_k_fit, "ci_lower": ci_lower, "ci_upper": ci_upper})

# X-axis ticks with dual annotation (1/T + temperature in K)
tick_temps = [300, 400, 500, 600]
tick_positions = [1.0 / t for t in tick_temps]
tick_labels = [f"{1.0 / t:.2e}\n({t} K)" for t in tick_temps]

# Annotation placement — upper-left quadrant
anno_x = inv_T.min() + 0.35 * (inv_T.max() - inv_T.min())
anno_y_top = ln_k.max() - 0.2

anno_r2 = f"R² = {r_squared:.4f}"
anno_ea = f"Eₐ = {Ea_kJ:.1f} kJ/mol"
anno_slope = f"slope = −Eₐ/R = {slope:.0f} K"

title = "line-arrhenius · python · plotnine · anyplot.ai"

# Plot
plot = (
    ggplot(df, aes(x="inv_T", y="ln_k"))
    + geom_ribbon(
        aes(x="inv_T", ymin="ci_lower", ymax="ci_upper"), data=df_fit, fill=BRAND, alpha=0.12, inherit_aes=False
    )
    + geom_line(aes(x="inv_T", y="ln_k_fit"), data=df_fit, color=BLUE, size=1.5, inherit_aes=False)
    + geom_point(color=BRAND, size=4.5, stroke=0.8, shape="o")
    + scale_x_continuous(breaks=tick_positions, labels=tick_labels, expand=(0.05, 0))
    + scale_y_continuous(expand=(0.08, 0))
    + annotate(
        "label",
        x=anno_x,
        y=anno_y_top,
        label=anno_r2,
        size=4.5,
        color=INK,
        fontweight="bold",
        ha="center",
        fill=ELEVATED_BG,
        alpha=0.92,
        label_padding=0.4,
        label_size=0,
    )
    + annotate("text", x=anno_x, y=anno_y_top - 0.9, label=anno_ea, size=4.0, color=INK, fontweight="bold", ha="center")
    + annotate(
        "text",
        x=anno_x,
        y=anno_y_top - 1.65,
        label=anno_slope,
        size=4.0,
        color=INK_MUTED,
        fontstyle="italic",
        ha="center",
    )
    + labs(x="1/T (K⁻¹)", y="ln(k)", title=title)
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_title=element_text(size=12, weight="bold", color=INK, margin={"b": 10}),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        axis_ticks=element_line(color=INK_SOFT, size=0.3),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color=INK, size=0.3, alpha=0.15),
        axis_ticks_minor=element_blank(),
        plot_margin=0.08,
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
