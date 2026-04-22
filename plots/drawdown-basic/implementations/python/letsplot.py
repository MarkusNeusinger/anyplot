""" pyplots.ai
drawdown-basic: Drawdown Chart
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-20
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_line,
    element_text,
    geom_area,
    geom_hline,
    geom_line,
    geom_point,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_color_manual,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Generate sample price data (simulating ~2 years of daily data)
np.random.seed(42)
n_days = 500
dates = pd.date_range(start="2022-01-01", periods=n_days, freq="B")

# Simulate price movement with trends and volatility that includes recoveries
returns = np.random.normal(0.0005, 0.012, n_days)

# Add drawdown periods followed by recovery rallies
# First drawdown period (days 40-70), then recovery rally (days 70-120)
returns[40:70] = np.random.normal(-0.008, 0.015, 30)
returns[70:120] = np.random.normal(0.012, 0.01, 50)  # Strong recovery

# Second drawdown period (days 180-230), then partial recovery (days 230-300)
returns[180:230] = np.random.normal(-0.006, 0.018, 50)
returns[230:300] = np.random.normal(0.008, 0.012, 70)  # Recovery rally

# Third drawdown period (days 350-400), then final recovery (days 400-450)
returns[350:400] = np.random.normal(-0.007, 0.016, 50)
returns[400:450] = np.random.normal(0.009, 0.01, 50)  # Recovery

price = 100 * np.cumprod(1 + returns)

# Calculate drawdown
running_max = np.maximum.accumulate(price)
drawdown = (price - running_max) / running_max * 100

# Create DataFrame
df = pd.DataFrame({"date": dates, "price": price, "drawdown": drawdown, "day_num": np.arange(n_days)})

# Find maximum drawdown point
max_dd_idx = int(np.argmin(drawdown))
max_dd_value = drawdown[max_dd_idx]

# Find recovery points (where drawdown returns to zero after being negative)
recovery_mask = (drawdown == 0) & (np.roll(drawdown, 1) < 0)
recovery_points = df[recovery_mask].copy()
recovery_points["marker_type"] = "Recovery Point"

# DataFrame for maximum drawdown point
max_dd_df = df.iloc[[max_dd_idx]].copy()
max_dd_df["marker_type"] = "Max Drawdown"

# Combine markers for legend
markers_df = pd.concat([max_dd_df, recovery_points], ignore_index=True)

# Create the drawdown chart with tooltips for interactivity
plot = (
    ggplot(df, aes(x="day_num", y="drawdown"))
    + geom_area(fill="#DC2626", alpha=0.35, tooltips="none")
    + geom_line(color="#DC2626", size=1.5, tooltips="none")
    + geom_hline(yintercept=0, color="#1F2937", size=1.2, linetype="dashed")
    + geom_point(
        data=markers_df,
        mapping=aes(x="day_num", y="drawdown", color="marker_type"),
        size=8,
        stroke=2.5,
        shape=21,
        fill="white",
    )
    + scale_color_manual(name="Markers", values={"Max Drawdown": "#7C2D12", "Recovery Point": "#166534"})
    + labs(
        x="Trading Days",
        y="Drawdown (%)",
        title="drawdown-basic · letsplot · pyplots.ai",
        caption=f"Max Drawdown: {max_dd_value:.1f}% on Day {max_dd_idx}",
    )
    + theme_minimal()
    + theme(
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        plot_caption=element_text(size=14),
        panel_grid=element_line(color="#E5E5E5", size=0.5),
        legend_position="top",
        legend_title=element_text(size=16),
        legend_text=element_text(size=14),
    )
    + ggsize(1600, 900)
)

# Save PNG (scale 3x to get 4800 x 2700 px)
ggsave(plot, filename="plot.png", path=".", scale=3)

# Save HTML for interactive version
ggsave(plot, filename="plot.html", path=".")
