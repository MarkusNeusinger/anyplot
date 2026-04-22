""" pyplots.ai
drawdown-basic: Drawdown Chart
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-20
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_line,
    element_text,
    geom_hline,
    geom_line,
    geom_point,
    geom_ribbon,
    ggplot,
    labs,
    scale_x_datetime,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Generate synthetic portfolio data with realistic drawdown patterns
np.random.seed(42)
n_days = 500
dates = pd.date_range(start="2022-01-01", periods=n_days, freq="D")

# Create price series with realistic volatility and recovery patterns
returns = np.random.normal(0.0005, 0.011, n_days)

# Add drawdown periods
returns[60:85] = np.random.normal(-0.004, 0.015, 25)  # First correction
returns[180:230] = np.random.normal(-0.006, 0.016, 50)  # Main drawdown
returns[300:320] = np.random.normal(-0.003, 0.012, 20)  # Small correction

# Add recovery after main drawdown
returns[230:300] = np.random.normal(0.002, 0.012, 70)
returns[400:500] = np.random.normal(0.001, 0.010, 100)

price = 100 * np.cumprod(1 + returns)

# Create DataFrame
df = pd.DataFrame({"date": dates, "price": price})

# Calculate running maximum and drawdown percentage
df["running_max"] = df["price"].cummax()
df["drawdown"] = (df["price"] - df["running_max"]) / df["running_max"] * 100

# Find maximum drawdown point
max_dd_idx = df["drawdown"].idxmin()
max_dd_value = df.loc[max_dd_idx, "drawdown"]
max_dd_date = df.loc[max_dd_idx, "date"]

# Calculate statistics
max_drawdown = df["drawdown"].min()

# Calculate max drawdown duration
df["in_drawdown"] = df["drawdown"] < -0.5
drawdown_groups = (df["in_drawdown"] != df["in_drawdown"].shift()).cumsum()
drawdown_durations = df[df["in_drawdown"]].groupby(drawdown_groups).size()
max_duration = drawdown_durations.max() if len(drawdown_durations) > 0 else 0

# Create DataFrame for max drawdown point marker
max_dd_df = df[df.index == max_dd_idx].copy()

# Create the plot
plot = (
    ggplot(df, aes(x="date", y="drawdown"))
    # Filled area from drawdown to zero baseline
    + geom_ribbon(aes(ymin="drawdown", ymax=0), fill="#d62728", alpha=0.4)
    # Drawdown line
    + geom_line(color="#d62728", size=1.2)
    # Zero baseline reference
    + geom_hline(yintercept=0, linetype="dashed", color="#333333", size=1)
    # Mark maximum drawdown point
    + geom_point(aes(x="date", y="drawdown"), data=max_dd_df, color="#8b0000", size=5)
    # Annotation for maximum drawdown
    + annotate(
        geom="text",
        x=max_dd_date + pd.Timedelta(days=30),
        y=max_dd_value + 3,
        label=f"Max Drawdown: {max_drawdown:.1f}%",
        size=11,
        color="#8b0000",
        ha="left",
    )
    # Labels and title
    + labs(
        x="Date",
        y="Drawdown (%)",
        title="drawdown-basic · plotnine · pyplots.ai",
        caption=f"Max Drawdown: {max_drawdown:.1f}% | Max Duration: {max_duration} days",
    )
    # Scales
    + scale_x_datetime(date_breaks="3 months", date_labels="%b %Y")
    + scale_y_continuous(breaks=range(-35, 5, 5))
    # Theme styling
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        axis_text_x=element_text(angle=45, ha="right"),
        plot_title=element_text(size=24),
        plot_caption=element_text(size=14, color="#666666"),
        panel_grid_major=element_line(color="#cccccc", size=0.5),
        panel_grid_minor=element_line(color="#eeeeee", size=0.3),
    )
)

# Save the plot
plot.save("plot.png", dpi=300, width=16, height=9)
