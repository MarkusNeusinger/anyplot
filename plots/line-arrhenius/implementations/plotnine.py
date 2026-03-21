""" pyplots.ai
line-arrhenius: Arrhenius Plot for Reaction Kinetics
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-21
"""

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


# Data — first-order decomposition with slight experimental scatter
temperature_K = np.array([300, 350, 400, 450, 500, 550, 600])
rate_constant_k = np.array([0.0013, 0.0091, 0.054, 0.19, 0.72, 1.75, 4.2])

inv_T = 1.0 / temperature_K
ln_k = np.log(rate_constant_k)

# Compute regression statistics for annotations
coeffs = np.polyfit(inv_T, ln_k, 1)
slope, intercept = coeffs
ln_k_pred = np.polyval(coeffs, inv_T)
ss_res = np.sum((ln_k - ln_k_pred) ** 2)
ss_tot = np.sum((ln_k - ln_k.mean()) ** 2)
r_squared = 1 - ss_res / ss_tot

R = 8.314
Ea_kJ = -slope * R / 1000

df = pd.DataFrame({"inv_T": inv_T, "ln_k": ln_k})

# Regression line data for manual ribbon + line (tighter control than geom_smooth)
inv_T_fine = np.linspace(inv_T.min() - 0.0001, inv_T.max() + 0.0001, 200)
ln_k_fit = np.polyval(coeffs, inv_T_fine)

# Compute residual SE for narrow confidence band
n = len(inv_T)
se_residual = np.sqrt(ss_res / (n - 2))
inv_T_mean = inv_T.mean()
inv_T_ss = np.sum((inv_T - inv_T_mean) ** 2)
se_fit = se_residual * np.sqrt(1.0 / n + (inv_T_fine - inv_T_mean) ** 2 / inv_T_ss)
t_val = t_dist.ppf(0.975, n - 2)
ci_lower = ln_k_fit - t_val * se_fit
ci_upper = ln_k_fit + t_val * se_fit

df_fit = pd.DataFrame({"inv_T": inv_T_fine, "ln_k_fit": ln_k_fit, "ci_lower": ci_lower, "ci_upper": ci_upper})

# Tick labels with temperature reference — select subset for clean spacing
tick_temps = [300, 400, 500, 600]
tick_positions = [1.0 / t for t in tick_temps]
tick_labels = [f"{1.0 / t:.2e}\n({t} K)" for t in tick_temps]

# Annotation placement — upper-left region for better balance
anno_x = inv_T.min() + 0.35 * (inv_T.max() - inv_T.min())
anno_y_top = ln_k.max() - 0.15

# Combined annotation text block for polished typography
anno_line1 = f"R² = {r_squared:.4f}"
anno_line2 = f"Eₐ = {Ea_kJ:.1f} kJ/mol"
anno_line3 = f"slope = −Eₐ/R = {slope:.0f} K"

# Plot — manual ribbon + line for tight CI, geom_point for markers
plot = (
    ggplot(df, aes(x="inv_T", y="ln_k"))
    # Confidence ribbon — narrow band from manual calculation
    + geom_ribbon(
        aes(x="inv_T", ymin="ci_lower", ymax="ci_upper"), data=df_fit, fill="#4a90d9", alpha=0.12, inherit_aes=False
    )
    # Regression line
    + geom_line(aes(x="inv_T", y="ln_k_fit"), data=df_fit, color="#4a90d9", size=2.0, inherit_aes=False)
    # Data points with filled markers
    + geom_point(color="#0d2240", fill="#306998", size=7, stroke=1.4, shape="o")
    + scale_x_continuous(breaks=tick_positions, labels=tick_labels)
    + scale_y_continuous(expand=(0.08, 0))
    # Annotation block — stacked text with visual hierarchy
    + annotate(
        "label",
        x=anno_x,
        y=anno_y_top,
        label=anno_line1,
        size=17,
        color="#0d2240",
        fontweight="bold",
        ha="center",
        fill="#ffffff",
        alpha=0.75,
        label_padding=0.4,
        label_size=0,
    )
    + annotate(
        "text", x=anno_x, y=anno_y_top - 0.9, label=anno_line2, size=15, color="#1a3a5c", fontweight="bold", ha="center"
    )
    + annotate(
        "text",
        x=anno_x,
        y=anno_y_top - 1.65,
        label=anno_line3,
        size=13,
        color="#667788",
        fontstyle="italic",
        ha="center",
    )
    + labs(x="1/T (K⁻¹)", y="ln(k)", title="line-arrhenius · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=26, weight="bold", color="#0d2240", margin={"b": 15}),
        axis_title_x=element_text(size=20, color="#333333", margin={"t": 10}),
        axis_title_y=element_text(size=20, color="#333333", margin={"r": 10}),
        axis_text=element_text(size=16, color="#444444"),
        axis_ticks=element_line(color="#cccccc", size=0.5),
        plot_background=element_rect(fill="#f7f7f7", color="none"),
        panel_background=element_rect(fill="#f7f7f7", color="none"),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color="#dcdcdc", size=0.3, linetype="dashed"),
        plot_margin=0.05,
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
