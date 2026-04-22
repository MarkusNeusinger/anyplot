""" pyplots.ai
dashboard-synchronized-crosshair: Synchronized Multi-Chart Dashboard
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 90/100 | Created: 2026-01-20
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_text,
    facet_wrap,
    geom_label,
    geom_line,
    geom_point,
    geom_vline,
    ggplot,
    labs,
    scale_x_datetime,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data - Stock-like data with 3 metrics over 200 trading days
np.random.seed(42)
n_points = 200
dates = pd.date_range("2024-01-01", periods=n_points, freq="B")  # Business days

# Series 1: Price (cumulative returns starting at 100)
returns = np.random.normal(0.001, 0.02, n_points)
price = 100 * np.cumprod(1 + returns)

# Series 2: Volume (random with some correlation to price movements)
base_volume = 1000000
volume = base_volume + np.abs(returns) * 50000000 + np.random.normal(0, 200000, n_points)
volume = np.maximum(volume, 100000)

# Series 3: RSI-like indicator (bounded 30-70 for realistic mid-range)
rsi_raw = 50 + np.cumsum(np.random.normal(0, 3, n_points))
rsi = np.clip(rsi_raw, 30, 70)

# Use categorical ordering for facets (Price at top, Volume middle, RSI bottom)
metric_order = pd.CategoricalDtype(categories=["Price ($)", "Volume (M)", "RSI"], ordered=True)

# Create long-format dataframe for faceting
df = pd.DataFrame(
    {
        "date": np.tile(dates, 3),
        "value": np.concatenate([price, volume / 1000000, rsi]),  # Scale volume to millions
        "metric": (["Price ($)"] * n_points + ["Volume (M)"] * n_points + ["RSI"] * n_points),
    }
)
df["metric"] = df["metric"].astype(metric_order)

# Define crosshair position (demonstrate synchronized crosshair at a specific point)
crosshair_idx = 100
crosshair_date = dates[crosshair_idx]
crosshair_price = price[crosshair_idx]
crosshair_volume = volume[crosshair_idx] / 1000000
crosshair_rsi = rsi[crosshair_idx]

# Create annotation data for crosshair points
annotation_df = pd.DataFrame(
    {
        "date": [crosshair_date] * 3,
        "value": [crosshair_price, crosshair_volume, crosshair_rsi],
        "metric": ["Price ($)", "Volume (M)", "RSI"],
    }
)
annotation_df["metric"] = annotation_df["metric"].astype(metric_order)

# Create label data for each panel (different labels per metric)
label_df = pd.DataFrame(
    {
        "date": [crosshair_date] * 3,
        "value": [crosshair_price * 1.06, crosshair_volume + 0.6, crosshair_rsi + 5],
        "metric": ["Price ($)", "Volume (M)", "RSI"],
        "label_text": [f"${crosshair_price:.2f}", f"{crosshair_volume:.2f}M", f"RSI: {crosshair_rsi:.1f}"],
    }
)
label_df["metric"] = label_df["metric"].astype(metric_order)

# Plot
plot = (
    ggplot(df, aes(x="date", y="value"))
    + geom_line(color="#306998", size=1.5, alpha=0.85)
    + geom_vline(xintercept=crosshair_date, color="#E74C3C", size=1.2, linetype="dashed", alpha=0.85)
    + geom_point(data=annotation_df, mapping=aes(x="date", y="value"), color="#E74C3C", size=6, alpha=0.9)
    + geom_label(
        data=label_df,
        mapping=aes(x="date", y="value", label="label_text"),
        color="#E74C3C",
        fill="white",
        size=12,
        alpha=0.95,
    )
    + facet_wrap("~metric", ncol=1, scales="free_y")
    + scale_x_datetime(date_breaks="1 month", date_labels="%b %Y")
    + scale_y_continuous()
    + labs(title="dashboard-synchronized-crosshair · plotnine · pyplots.ai", x="Date", y="")
    + theme_minimal()
    + theme(
        figure_size=(16, 12),
        plot_title=element_text(size=24, weight="bold", ha="center"),
        axis_title_x=element_text(size=18),
        axis_title_y=element_blank(),
        axis_text=element_text(size=14),
        axis_text_x=element_text(angle=45, ha="right"),
        strip_text=element_text(size=18, weight="bold"),
        panel_spacing=0.15,
        panel_grid_minor=element_blank(),
        panel_grid_major=element_line(color="#cccccc", alpha=0.4),
    )
)

plot.save("plot.png", dpi=300, verbose=False)
