""" pyplots.ai
histogram-returns-distribution: Returns Distribution Histogram
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-16
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_blank,
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


# Data - Generate synthetic daily returns (252 trading days)
np.random.seed(42)
n_days = 252

# Simulate realistic daily stock returns with slight fat tails
# Using mixture of normals to create fat-tailed distribution
normal_returns = np.random.normal(0.0005, 0.015, int(n_days * 0.9))
fat_tail_returns = np.random.normal(0, 0.04, int(n_days * 0.1))
returns = np.concatenate([normal_returns, fat_tail_returns])
np.random.shuffle(returns)
returns = returns[:n_days]

# Convert to percentage
returns_pct = returns * 100

# Calculate statistics
mean_ret = np.mean(returns_pct)
std_ret = np.std(returns_pct)
skewness = stats.skew(returns_pct)
kurtosis = stats.kurtosis(returns_pct)

# Define tail thresholds (2 standard deviations)
lower_tail = mean_ret - 2 * std_ret
upper_tail = mean_ret + 2 * std_ret

# Create histogram data
df = pd.DataFrame({"returns": returns_pct})

# Create normal distribution overlay data
x_range = np.linspace(returns_pct.min() - 1, returns_pct.max() + 1, 200)
normal_pdf = stats.norm.pdf(x_range, mean_ret, std_ret)

# Scale normal PDF to match histogram density
bin_width = (returns_pct.max() - returns_pct.min()) / 30
normal_scaled = normal_pdf * len(returns_pct) * bin_width

df_normal = pd.DataFrame({"x": x_range, "y": normal_scaled})

# Categorize returns for tail highlighting
df["tail_region"] = pd.cut(
    df["returns"], bins=[-np.inf, lower_tail, upper_tail, np.inf], labels=["Left Tail", "Center", "Right Tail"]
)

# Plot
plot = (
    ggplot(df, aes(x="returns", fill="tail_region"))
    + geom_histogram(bins=30, color="white", alpha=0.8, size=0.3)
    + geom_line(data=df_normal, mapping=aes(x="x", y="y"), color="#306998", size=2, inherit_aes=False)
    + geom_vline(xintercept=mean_ret, linetype="dashed", color="#333333", size=1)
    + geom_vline(xintercept=lower_tail, linetype="dotted", color="#D62728", size=0.8)
    + geom_vline(xintercept=upper_tail, linetype="dotted", color="#D62728", size=0.8)
    + scale_fill_manual(values={"Left Tail": "#D62728", "Center": "#FFD43B", "Right Tail": "#2CA02C"}, name="Region")
    + annotate(
        "label",
        x=returns_pct.max() - 1,
        y=max(normal_scaled) * 0.95,
        label=f"Mean: {mean_ret:.2f}%\nStd: {std_ret:.2f}%\nSkewness: {skewness:.2f}\nKurtosis: {kurtosis:.2f}",
        ha="right",
        va="top",
        size=14,
        fill="white",
        alpha=0.9,
        label_padding=0.5,
    )
    + labs(x="Daily Returns (%)", y="Frequency", title="histogram-returns-distribution · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_title=element_text(size=16),
        legend_text=element_text(size=14),
        legend_position="right",
        panel_grid_minor=element_blank(),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
