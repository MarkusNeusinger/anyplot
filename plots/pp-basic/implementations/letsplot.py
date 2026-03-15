"""pyplots.ai
pp-basic: Probability-Probability (P-P) Plot
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 81/100 | Created: 2026-03-15
"""

from math import erf, sqrt

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Data
np.random.seed(42)
n_samples = 200

# Generate slightly skewed data (right-skewed via mixture)
normal_component = np.random.normal(50, 12, 160)
skew_component = np.random.exponential(8, 40) + 40
observed = np.concatenate([normal_component, skew_component])
observed = observed[:n_samples]

# Sort observed data
observed_sorted = np.sort(observed)

# Compute empirical CDF using plotting position formula i/(n+1)
empirical_cdf = np.arange(1, n_samples + 1) / (n_samples + 1)

# Fit normal distribution (MLE: mean and std of data)
mu = np.mean(observed_sorted)
sigma = np.std(observed_sorted, ddof=0)

# Compute theoretical CDF values (normal CDF inline)
z_scores = (observed_sorted - mu) / (sigma * sqrt(2))
theoretical_cdf = 0.5 * (1 + np.vectorize(erf)(z_scores))

# Compute deviation from perfect fit for color mapping
deviation = empirical_cdf - theoretical_cdf

# Create dataframe for P-P plot points
df_pp = pd.DataFrame(
    {
        "theoretical": theoretical_cdf,
        "empirical": empirical_cdf,
        "deviation": deviation,
        "abs_deviation": np.abs(deviation),
    }
)

# Confidence envelope around diagonal (approximate 95% Kolmogorov band)
ks_band = 1.36 / sqrt(n_samples)
envelope_x = np.linspace(0, 1, 100)
df_envelope = pd.DataFrame(
    {
        "x": envelope_x,
        "y_upper": np.minimum(envelope_x + ks_band, 1.0),
        "y_lower": np.maximum(envelope_x - ks_band, 0.0),
    }
)

# Reference line (perfect fit diagonal)
df_ref = pd.DataFrame({"x": [0, 1], "y": [0, 1]})

# Plot with color-mapped deviation for visual storytelling
plot = (
    ggplot()
    + geom_ribbon(
        aes(x="x", ymin="y_lower", ymax="y_upper"),
        data=df_envelope,
        fill="#306998",
        color="#B0C4DE",
        alpha=0.08,
        size=0.5,
    )
    + geom_line(aes(x="x", y="y"), data=df_ref, color="#8C9EAF", size=1.2, linetype="dashed")
    + geom_point(
        aes(x="theoretical", y="empirical", color="deviation", size="abs_deviation"), data=df_pp, alpha=0.75, shape=16
    )
    + scale_color_gradient2(low="#C44E52", mid="#306998", high="#4C72B0", midpoint=0, name="Deviation")
    + scale_size(range=[3, 7], guide="none")
    + labs(x="Theoretical CDF (Normal)", y="Empirical CDF", title="pp-basic · letsplot · pyplots.ai")
    + scale_x_continuous(limits=[0, 1], breaks=[0, 0.2, 0.4, 0.6, 0.8, 1.0])
    + scale_y_continuous(limits=[0, 1], breaks=[0, 0.2, 0.4, 0.6, 0.8, 1.0])
    + coord_fixed(ratio=1)
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold", color="#2C3E50"),
        axis_title=element_text(size=20, color="#34495E"),
        axis_text=element_text(size=16, color="#566573"),
        panel_grid_major=element_line(color="#ECF0F1", size=0.4),
        panel_grid_minor=element_blank(),
        legend_title=element_text(size=16),
        legend_text=element_text(size=14),
        legend_position="right",
        plot_background=element_rect(color="white", fill="white"),
        panel_background=element_rect(fill="#FAFBFC", color="#FAFBFC"),
    )
    + ggsize(1200, 1200)
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
