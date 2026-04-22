""" pyplots.ai
pp-basic: Probability-Probability (P-P) Plot
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 93/100 | Created: 2026-03-15
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    coord_fixed,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_abline,
    geom_point,
    geom_ribbon,
    ggplot,
    labs,
    scale_color_gradient2,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from scipy import stats


# Data: Quality control — tensile strength of steel rods (MPa)
# Mixture reflects a manufacturing process with occasional batch variation
np.random.seed(42)
n = 200
main_batch = np.random.normal(loc=520, scale=35, size=160)
variant_batch = np.random.normal(loc=580, scale=20, size=40)
tensile_strength = np.concatenate([main_batch, variant_batch])

sorted_data = np.sort(tensile_strength)
mu, sigma = np.mean(sorted_data), np.std(sorted_data)
empirical_cdf = np.arange(1, n + 1) / (n + 1)
theoretical_cdf = stats.norm.cdf(sorted_data, loc=mu, scale=sigma)

# Deviation from diagonal for storytelling color mapping
deviation = empirical_cdf - theoretical_cdf

df = pd.DataFrame(
    {
        "theoretical": theoretical_cdf,
        "empirical": empirical_cdf,
        "deviation": deviation,
        "abs_deviation": np.abs(deviation),
    }
)

# Confidence envelope: approximate 95% band under null (Kolmogorov-Smirnov)
ks_band = 1.36 / np.sqrt(n)
envelope_t = np.linspace(0, 1, 300)
envelope_df = pd.DataFrame(
    {
        "theoretical": envelope_t,
        "upper": np.minimum(envelope_t + ks_band, 1.0),
        "lower": np.maximum(envelope_t - ks_band, 0.0),
    }
)

# Plot using plotnine's grammar of graphics with layered composition
plot = (
    ggplot()
    # Layer 1: KS confidence envelope via geom_ribbon (distinctive plotnine feature)
    + geom_ribbon(aes(x="theoretical", ymin="lower", ymax="upper"), data=envelope_df, fill="#306998", alpha=0.08)
    # Layer 2: Reference diagonal
    + geom_abline(intercept=0, slope=1, color="#999999", size=0.8, linetype="dashed")
    # Layer 3: Points colored by deviation — visual storytelling
    + geom_point(aes(x="theoretical", y="empirical", color="deviation"), data=df, size=3.5, alpha=0.75, stroke=0)
    # Color scale: diverging gradient emphasizing departures from diagonal
    + scale_color_gradient2(low="#2166AC", mid="#306998", high="#B2182B", midpoint=0, name="Deviation\nfrom fit")
    # Annotation: highlight the deviation story
    + annotate(
        "text",
        x=0.05,
        y=0.92,
        label="Tensile strength of 200 steel rods\nvs. normal reference distribution",
        ha="left",
        va="top",
        size=13,
        color="#444444",
        fontstyle="italic",
    )
    + annotate(
        "text",
        x=0.62,
        y=0.48,
        label="← S-curve reveals\n     batch variation",
        ha="left",
        va="top",
        size=11,
        color="#B2182B",
        fontweight="bold",
    )
    + annotate(
        "label",
        x=0.5,
        y=0.05,
        label="95% KS confidence band",
        ha="center",
        size=10,
        color="#306998",
        fill="#F0F4F8",
        alpha=0.9,
        label_size=0,
    )
    + labs(
        x="Theoretical Cumulative Probability (Normal CDF)",
        y="Empirical Cumulative Probability",
        title="pp-basic · plotnine · pyplots.ai",
    )
    + scale_x_continuous(limits=(0, 1), breaks=np.arange(0, 1.1, 0.2))
    + scale_y_continuous(limits=(0, 1), breaks=np.arange(0, 1.1, 0.2))
    + coord_fixed(ratio=1)
    + theme_minimal()
    + theme(
        figure_size=(10, 10),
        plot_title=element_text(size=24, weight="bold", color="#222222"),
        axis_title=element_text(size=20, color="#444444"),
        axis_text=element_text(size=16, color="#666666"),
        panel_grid_major=element_line(color="#EEEEEE", size=0.4),
        panel_grid_minor=element_blank(),
        legend_title=element_text(size=14),
        legend_text=element_text(size=12),
        legend_position=(0.88, 0.22),
        legend_background=element_rect(fill="#FFFFFF", alpha=0.8, color="#DDDDDD"),
        plot_background=element_rect(fill="#FAFAFA", color="none"),
    )
)

# Save
plot.save("plot.png", dpi=360, verbose=False)
