""" pyplots.ai
dashboard-synchronized-crosshair: Synchronized Multi-Chart Dashboard
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 90/100 | Created: 2026-01-20
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Data - Stock-like data with price, volume, and RSI indicator
np.random.seed(42)
n_points = 200

dates = pd.date_range("2024-01-01", periods=n_points, freq="B")

# Price series (cumulative random walk)
returns = np.random.normal(0.001, 0.02, n_points)
price = 100 * np.cumprod(1 + returns)

# Volume series (correlated with absolute returns)
base_volume = 1000000
volume = base_volume * (1 + 2 * np.abs(returns)) * np.random.uniform(0.8, 1.2, n_points)

# RSI-like indicator (oscillating between 30-70 mostly)
rsi = 50 + 20 * np.sin(np.linspace(0, 8 * np.pi, n_points)) + np.random.normal(0, 5, n_points)
rsi = np.clip(rsi, 0, 100)

df = pd.DataFrame(
    {
        "date": dates,
        "price": price,
        "volume": volume / 1e6,  # In millions
        "rsi": rsi,
    }
)

# Select a crosshair position at index 100 (mid-point) for demonstration
crosshair_idx = 100
crosshair_date = df["date"].iloc[crosshair_idx]
crosshair_price = df["price"].iloc[crosshair_idx]
crosshair_volume = df["volume"].iloc[crosshair_idx]
crosshair_rsi = df["rsi"].iloc[crosshair_idx]

# Crosshair annotation data - single point for each chart
crosshair_price_df = pd.DataFrame(
    {"date": [crosshair_date], "price": [crosshair_price], "label": [f"${crosshair_price:.2f}"]}
)
crosshair_volume_df = pd.DataFrame(
    {"date": [crosshair_date], "volume": [crosshair_volume], "label": [f"{crosshair_volume:.2f}M"]}
)
crosshair_rsi_df = pd.DataFrame({"date": [crosshair_date], "rsi": [crosshair_rsi], "label": [f"{crosshair_rsi:.1f}"]})

# Vertical line data for crosshair
vline_price_df = pd.DataFrame(
    {"date": [crosshair_date, crosshair_date], "y": [df["price"].min() * 0.98, df["price"].max() * 1.02]}
)
vline_volume_df = pd.DataFrame({"date": [crosshair_date, crosshair_date], "y": [0, df["volume"].max() * 1.1]})
vline_rsi_df = pd.DataFrame({"date": [crosshair_date, crosshair_date], "y": [0, 100]})

# Common theme for all charts
common_theme = theme(  # noqa: F405
    axis_title=element_text(size=18),  # noqa: F405
    axis_text=element_text(size=14),  # noqa: F405
    plot_title=element_text(size=20),  # noqa: F405
    legend_text=element_text(size=14),  # noqa: F405
    axis_line=element_line(size=1),  # noqa: F405
    panel_grid_major=element_line(color="#E0E0E0", size=0.5),  # noqa: F405
    panel_grid_minor=element_blank(),  # noqa: F405
)

# Chart 1: Price with synchronized crosshair
price_chart = (
    ggplot(df, aes(x="date", y="price"))  # noqa: F405
    + geom_line(color="#306998", size=1.5, tooltips=layer_tooltips().line("@date").line("Price|$@price"))  # noqa: F405
    + geom_path(  # noqa: F405
        data=vline_price_df,
        mapping=aes(x="date", y="y"),  # noqa: F405
        color="#E91E63",
        size=1.2,
        alpha=0.8,
    )
    + geom_point(data=crosshair_price_df, mapping=aes(x="date", y="price"), color="#E91E63", size=6)  # noqa: F405
    + geom_text(  # noqa: F405
        data=crosshair_price_df,
        mapping=aes(x="date", y="price", label="label"),  # noqa: F405
        hjust=-0.15,
        vjust=0.5,
        color="#E91E63",
        size=12,
    )
    + labs(x="", y="Price ($)", title="Price")  # noqa: F405
    + theme_minimal()  # noqa: F405
    + common_theme
)

# Chart 2: Volume with synchronized crosshair
volume_chart = (
    ggplot(df, aes(x="date", y="volume"))  # noqa: F405
    + geom_bar(  # noqa: F405
        fill="#FFD43B",
        stat="identity",
        alpha=0.8,
        width=0.8,
        tooltips=layer_tooltips().line("@date").line("Volume|@volume M"),  # noqa: F405
    )
    + geom_path(  # noqa: F405
        data=vline_volume_df,
        mapping=aes(x="date", y="y"),  # noqa: F405
        color="#E91E63",
        size=1.2,
        alpha=0.8,
    )
    + geom_point(data=crosshair_volume_df, mapping=aes(x="date", y="volume"), color="#E91E63", size=6)  # noqa: F405
    + geom_text(  # noqa: F405
        data=crosshair_volume_df,
        mapping=aes(x="date", y="volume", label="label"),  # noqa: F405
        hjust=-0.15,
        vjust=0.5,
        color="#E91E63",
        size=12,
    )
    + labs(x="", y="Volume (M)", title="Volume")  # noqa: F405
    + theme_minimal()  # noqa: F405
    + common_theme
)

# Chart 3: RSI Indicator with synchronized crosshair
rsi_chart = (
    ggplot(df, aes(x="date", y="rsi"))  # noqa: F405
    + geom_line(color="#DC2626", size=1.5, tooltips=layer_tooltips().line("@date").line("RSI|@rsi"))  # noqa: F405
    + geom_hline(yintercept=70, linetype="dashed", color="#888888", size=0.8)  # noqa: F405
    + geom_hline(yintercept=30, linetype="dashed", color="#888888", size=0.8)  # noqa: F405
    + geom_path(  # noqa: F405
        data=vline_rsi_df,
        mapping=aes(x="date", y="y"),  # noqa: F405
        color="#E91E63",
        size=1.2,
        alpha=0.8,
    )
    + geom_point(data=crosshair_rsi_df, mapping=aes(x="date", y="rsi"), color="#E91E63", size=6)  # noqa: F405
    + geom_text(  # noqa: F405
        data=crosshair_rsi_df,
        mapping=aes(x="date", y="rsi", label="label"),  # noqa: F405
        hjust=-0.15,
        vjust=0.5,
        color="#E91E63",
        size=12,
    )
    + labs(  # noqa: F405
        x="Date",
        y="RSI",
        title="RSI Indicator",
        caption=f"■ Synchronized crosshair at {crosshair_date.strftime('%Y-%m-%d')}",
    )
    + scale_y_continuous(limits=[0, 100])  # noqa: F405
    + theme_minimal()  # noqa: F405
    + common_theme
    + theme(plot_caption=element_text(size=14, color="#E91E63", hjust=0))  # noqa: F405
)

# Combine charts using gggrid for vertical stacked layout
# Price chart gets more vertical space (2:1:1 ratio)
combined = (
    gggrid([price_chart, volume_chart, rsi_chart], ncol=1, heights=[2, 1, 1])  # noqa: F405
    + ggsize(1600, 900)  # noqa: F405
    + ggtitle("dashboard-synchronized-crosshair · letsplot · pyplots.ai")  # noqa: F405
)

# Save PNG (scale 3x to get 4800 x 2700 px)
export_ggsave(combined, filename="plot.png", path=".", scale=3)

# Save HTML for interactive version with tooltips
export_ggsave(combined, filename="plot.html", path=".")
