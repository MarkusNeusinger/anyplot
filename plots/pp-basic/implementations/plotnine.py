"""pyplots.ai
pp-basic: Probability-Probability (P-P) Plot
Library: plotnine | Python 3.13
Quality: pending | Created: 2026-03-15
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_blank,
    element_line,
    element_text,
    geom_abline,
    geom_point,
    ggplot,
    labs,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from scipy import stats


# Data
np.random.seed(42)
n = 200
observed = np.concatenate([np.random.normal(50, 12, 160), np.random.normal(70, 8, 40)])

sorted_data = np.sort(observed)
mu, sigma = np.mean(sorted_data), np.std(sorted_data)
empirical_cdf = np.arange(1, n + 1) / (n + 1)
theoretical_cdf = stats.norm.cdf(sorted_data, loc=mu, scale=sigma)

df = pd.DataFrame({"theoretical": theoretical_cdf, "empirical": empirical_cdf})

# Plot
plot = (
    ggplot(df, aes(x="theoretical", y="empirical"))
    + geom_abline(intercept=0, slope=1, color="#CCCCCC", size=1.2, linetype="dashed")
    + geom_point(color="#306998", size=3, alpha=0.7, stroke=0.3, fill="#306998")
    + labs(
        x="Theoretical Cumulative Probability",
        y="Empirical Cumulative Probability",
        title="pp-basic · plotnine · pyplots.ai",
    )
    + scale_x_continuous(limits=(0, 1), breaks=np.arange(0, 1.1, 0.2))
    + scale_y_continuous(limits=(0, 1), breaks=np.arange(0, 1.1, 0.2))
    + coord_fixed(ratio=1)
    + theme_minimal()
    + theme(
        figure_size=(10, 10),
        plot_title=element_text(size=24, weight="medium"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        panel_grid_major=element_line(color="#E0E0E0", size=0.5, alpha=0.2),
        panel_grid_minor=element_blank(),
    )
)

# Save
plot.save("plot.png", dpi=360, verbose=False)
