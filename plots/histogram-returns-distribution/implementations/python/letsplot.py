""" pyplots.ai
histogram-returns-distribution: Returns Distribution Histogram
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-16
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403, F405
from scipy import stats


LetsPlot.setup_html()

# Data - Generate synthetic daily returns for 1 year
np.random.seed(42)
n_days = 252

# Simulate realistic daily stock returns with slight fat tails
# Using mixture of normal for realistic returns (mostly normal with some outliers)
base_returns = np.random.normal(loc=0.0003, scale=0.012, size=n_days)
# Add a few larger moves (fat tails)
outlier_mask = np.random.random(n_days) < 0.05
outliers = np.random.normal(loc=0, scale=0.035, size=n_days)
returns = np.where(outlier_mask, outliers, base_returns)

# Calculate statistics
mean_ret = np.mean(returns) * 100
std_ret = np.std(returns) * 100
skewness = stats.skew(returns)
kurtosis = stats.kurtosis(returns)

# Create DataFrame for plotting (convert to percentage)
df = pd.DataFrame({"returns": returns * 100})

# Define tail thresholds (beyond 2 standard deviations)
lower_tail = mean_ret - 2 * std_ret
upper_tail = mean_ret + 2 * std_ret

# Add tail indicator to data
df["region"] = np.where(
    df["returns"] < lower_tail,
    "Tail (beyond ±2σ)",
    np.where(df["returns"] > upper_tail, "Tail (beyond ±2σ)", "Normal Range (±2σ)"),
)

# Generate normal distribution curve for overlay
x_min, x_max = df["returns"].min(), df["returns"].max()
x_range = np.linspace(x_min - 0.5, x_max + 0.5, 200)
normal_pdf = stats.norm.pdf(x_range, loc=mean_ret, scale=std_ret)
df_normal = pd.DataFrame({"x": x_range, "density": normal_pdf})

# Statistics text for annotation
stats_text = f"Mean: {mean_ret:.3f}%\nStd Dev: {std_ret:.3f}%\nSkewness: {skewness:.2f}\nKurtosis: {kurtosis:.2f}"

# Create histogram with tail highlighting
plot = (
    ggplot(df, aes(x="returns", fill="region"))
    + geom_histogram(aes(y="..density.."), bins=30, alpha=0.85, color="white", size=0.5)
    + geom_line(
        data=df_normal, mapping=aes(x="x", y="density"), color="#1a1a1a", size=1.5, linetype="dashed", inherit_aes=False
    )
    + geom_vline(xintercept=lower_tail, color="#DC2626", size=1, linetype="dotted", alpha=0.7)
    + geom_vline(xintercept=upper_tail, color="#DC2626", size=1, linetype="dotted", alpha=0.7)
    + scale_fill_manual(values={"Normal Range (±2σ)": "#306998", "Tail (beyond ±2σ)": "#DC2626"}, name="Region")
    + labs(x="Daily Returns (%)", y="Density", title="histogram-returns-distribution · letsplot · pyplots.ai")
    + theme_minimal()
    + theme(
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        legend_text=element_text(size=14),
        legend_title=element_text(size=16),
        legend_position=[0.85, 0.85],
    )
    + ggsize(1600, 900)
    # Add statistics annotation
    + geom_label(
        x=x_max - 0.5,
        y=normal_pdf.max() * 0.95,
        label=stats_text,
        size=12,
        hjust=1,
        fill="white",
        alpha=0.9,
        label_padding=0.5,
    )
)

# Save plot (scale 3x for 4800 x 2700 px)
ggsave(plot, "plot.png", path=".", scale=3)

# Also save HTML for interactive version
ggsave(plot, "plot.html", path=".")
