"""pyplots.ai
line-arrhenius: Arrhenius Plot for Reaction Kinetics
Library: plotnine 0.15.3 | Python 3.14.3
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
    geom_point,
    geom_smooth,
    ggplot,
    labs,
    scale_x_continuous,
    theme,
    theme_minimal,
)


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

# Tick labels with temperature reference
tick_positions = inv_T.tolist()
tick_labels = [f"{v:.2e}\n({1 / v:.0f} K)" for v in inv_T]

# Annotation placement
anno_x = inv_T.mean()
anno_y_top = ln_k.max() - 0.2

# Plot — leveraging geom_smooth for idiomatic plotnine regression
plot = (
    ggplot(df, aes(x="inv_T", y="ln_k"))
    + geom_smooth(method="lm", color="#4a90d9", size=1.8, alpha=0.15, fill="#4a90d9")
    + geom_point(color="#1a3a5c", fill="#306998", size=6, stroke=1.2, shape="o")
    + scale_x_continuous(breaks=tick_positions, labels=tick_labels)
    + annotate(
        "text",
        x=anno_x,
        y=anno_y_top,
        label=f"R² = {r_squared:.4f}",
        size=16,
        color="#1a3a5c",
        fontweight="bold",
        ha="center",
    )
    + annotate(
        "text", x=anno_x, y=anno_y_top - 0.85, label=f"Eₐ = {Ea_kJ:.1f} kJ/mol", size=15, color="#333333", ha="center"
    )
    + annotate(
        "text",
        x=anno_x,
        y=anno_y_top - 1.6,
        label=f"slope = −Eₐ/R = {slope:.0f} K",
        size=13,
        color="#777777",
        ha="center",
    )
    + labs(x="1/T (K⁻¹)", y="ln(k)", title="line-arrhenius · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold", color="#1a3a5c"),
        axis_title=element_text(size=20, color="#333333"),
        axis_text=element_text(size=16, color="#444444"),
        axis_text_x=element_text(size=14),
        plot_background=element_rect(fill="#fafafa", color="none"),
        panel_background=element_rect(fill="#fafafa", color="none"),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color="#e0e0e0", size=0.4, alpha=0.6),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
