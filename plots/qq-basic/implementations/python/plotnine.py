""" pyplots.ai
qq-basic: Basic Q-Q Plot
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import numpy as np
import pandas as pd
from plotnine import aes, element_text, geom_abline, geom_point, ggplot, labs, theme, theme_minimal
from scipy import stats


# Data - generate sample with slight right skew to show Q-Q diagnostic capability
np.random.seed(42)
n_points = 100
sample = np.concatenate(
    [
        np.random.randn(80) * 15 + 50,  # Main normal component
        np.random.randn(20) * 10 + 75,  # Slight right tail
    ]
)

# Calculate theoretical quantiles (normal distribution)
sample_sorted = np.sort(sample)
n = len(sample_sorted)
theoretical_quantiles = stats.norm.ppf((np.arange(1, n + 1) - 0.5) / n)

# Standardize sample for comparison
sample_mean = np.mean(sample_sorted)
sample_std = np.std(sample_sorted, ddof=1)
sample_quantiles = (sample_sorted - sample_mean) / sample_std

df = pd.DataFrame({"theoretical": theoretical_quantiles, "sample": sample_quantiles})

# Plot
plot = (
    ggplot(df, aes(x="theoretical", y="sample"))
    + geom_abline(intercept=0, slope=1, color="#FFD43B", size=1.5, linetype="dashed")
    + geom_point(color="#306998", alpha=0.7, size=4)
    + labs(x="Theoretical Quantiles", y="Sample Quantiles", title="qq-basic · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
