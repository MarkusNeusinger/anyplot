""" anyplot.ai
indicator-macd: MACD Technical Indicator Chart
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-16
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403, F405


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
BRAND = "#009E73"  # First series (green)
SECONDARY = "#BD8233"  # imprint ochre — signal line (categorical contrast)

# Generate realistic stock price data with momentum
np.random.seed(42)
n_days = 120

# Simulate stock prices with trend and volatility (more realistic)
dates = pd.date_range(start="2024-01-01", periods=n_days + 35, freq="B")
returns = np.random.normal(0.0005, 0.015, n_days + 35)
# Add trending behavior
trend = np.sin(np.linspace(0, 4 * np.pi, n_days + 35)) * 0.012
returns = returns + trend
prices = 100 * np.cumprod(1 + returns)

# Calculate EMAs using pandas ewm
ema_12 = pd.Series(prices).ewm(span=12, adjust=False).mean().values
ema_26 = pd.Series(prices).ewm(span=26, adjust=False).mean().values

# Calculate MACD components
macd_line = ema_12 - ema_26
signal_line = pd.Series(macd_line).ewm(span=9, adjust=False).mean().values
histogram = macd_line - signal_line

# Use the last n_days (after warmup period)
start_idx = 35
df = pd.DataFrame(
    {
        "date": dates[start_idx:],
        "macd": macd_line[start_idx:],
        "signal": signal_line[start_idx:],
        "histogram": histogram[start_idx:],
    }
)

# Convert dates to numeric for plotting
df["day_num"] = range(len(df))
df["hist_color"] = np.where(df["histogram"] >= 0, "Positive", "Negative")

# Create separate dataframes for lines
df_lines = pd.melt(
    df[["day_num", "macd", "signal"]],
    id_vars=["day_num"],
    value_vars=["macd", "signal"],
    var_name="line_type",
    value_name="value",
)
df_lines["line_type"] = df_lines["line_type"].map({"macd": "MACD Line", "signal": "Signal Line"})

# Create the MACD chart
plot = (
    ggplot()
    + geom_bar(
        data=df, mapping=aes(x="day_num", y="histogram", fill="hist_color"), stat="identity", width=0.8, alpha=0.8
    )
    + geom_hline(yintercept=0, color=INK_SOFT, size=0.8, linetype="dashed")
    + geom_line(data=df_lines, mapping=aes(x="day_num", y="value", color="line_type"), size=1.5)
    + scale_fill_manual(values={"Positive": "#2ABCCD", "Negative": "#AE3030"}, name="Histogram")  # imprint red for negative bars
    + scale_color_manual(values={"MACD Line": BRAND, "Signal Line": SECONDARY}, name="Lines")
    + labs(x="Trading Day", y="MACD Value", title="indicator-macd · letsplot · anyplot.ai")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major_y=element_line(color=INK_SOFT, size=0.3),
        panel_grid_minor=element_blank(),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        plot_title=element_text(size=24, color=INK),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(size=16, color=INK_SOFT),
        legend_title=element_text(size=18, color=INK),
        legend_position="right",
    )
    + ggsize(1600, 900)
)

# Save as PNG (scale=3 gives 4800x2700)
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)

# Save interactive HTML version
ggsave(plot, f"plot-{THEME}.html", path=".")
