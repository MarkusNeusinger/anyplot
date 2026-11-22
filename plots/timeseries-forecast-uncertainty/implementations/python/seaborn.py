"""anyplot.ai
timeseries-forecast-uncertainty: Time Series Forecast with Uncertainty Band
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-19
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D
from matplotlib.patches import Patch


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
COLOR_HISTORICAL = IMPRINT_PALETTE[0]
COLOR_FORECAST = IMPRINT_PALETTE[1]

# Slightly higher alpha in dark mode so the bands stay visible on the near-black surface
ALPHA_95 = 0.27 if THEME == "dark" else 0.22
ALPHA_80 = 0.38 if THEME == "dark" else 0.30

# Constants
Z_95 = 1.96  # two-sided normal quantile of the 95% interval
Z_80 = 1.28  # two-sided normal quantile of the 80% interval

# Columns: set these to your table's column names
DATE = "Date"  # role: date
ACTUAL = "Historical"  # role: actual
FORECAST = "Forecast"  # role: forecast
LOWER_80 = "Lower 80%"  # role: lower_80
UPPER_80 = "Upper 80%"  # role: upper_80
LOWER_95 = "Lower 95%"  # role: lower_95
UPPER_95 = "Upper 95%"  # role: upper_95
PRICE = "Stock Price ($)"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("forecast.csv")
np.random.seed(42)
n_historical = 60
n_forecast = 20
t = np.arange(n_historical + n_forecast)
trend = 150 + 0.15 * t + 2.5 * np.sin(2 * np.pi * t / 20)
historical_prices = trend[:n_historical] + np.random.normal(0, 1.5, n_historical)
forecast_prices = trend[n_historical:]
std_growth = 1.5 * np.sqrt(np.arange(1, n_forecast + 1))
last = historical_prices[-1]  # the forecast bands start at the last observation
pad = [np.nan] * (n_historical - 1)
df = pd.DataFrame(
    {
        DATE: pd.date_range(start="2025-01-01", periods=n_historical + n_forecast, freq="B"),
        ACTUAL: list(historical_prices) + [np.nan] * n_forecast,
        FORECAST: pad + [last] + list(forecast_prices),
        LOWER_80: pad + [last] + list(forecast_prices - Z_80 * std_growth),
        UPPER_80: pad + [last] + list(forecast_prices + Z_80 * std_growth),
        LOWER_95: pad + [last] + list(forecast_prices - Z_95 * std_growth),
        UPPER_95: pad + [last] + list(forecast_prices + Z_95 * std_growth),
    }
)

# Plot: reads only df and the constants above
boundary = df.loc[df[ACTUAL].notna(), DATE].iloc[-1]  # date where the forecast begins
long_data = df.melt(id_vars=DATE, value_vars=[ACTUAL, FORECAST], var_name="series", value_name=PRICE).dropna()

sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK,
        "grid.alpha": 0.10,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Subtle forecast-region shading to separate forecast from history
ax.axvspan(boundary, df[DATE].iloc[-1], alpha=0.04, color=INK, zorder=0)

# Nested confidence bands: 95% outermost and lightest, 80% inner and darker
ax.fill_between(df[DATE], df[LOWER_95], df[UPPER_95], alpha=ALPHA_95, color=COLOR_FORECAST, linewidth=0)
ax.fill_between(df[DATE], df[LOWER_80], df[UPPER_80], alpha=ALPHA_80, color=COLOR_FORECAST, linewidth=0)

# Long-form lineplot with hue + style: solid history, dashed forecast
sns.lineplot(
    data=long_data,
    x=DATE,
    y=PRICE,
    hue="series",
    style="series",
    palette={ACTUAL: COLOR_HISTORICAL, FORECAST: COLOR_FORECAST},
    dashes={ACTUAL: (1, 0), FORECAST: (6, 2)},
    linewidth=3,
    ax=ax,
    legend=False,
)

# Forecast boundary marker
ax.axvline(x=boundary, color=INK_SOFT, linestyle=":", linewidth=1.5, alpha=0.5)
ax.text(boundary, 0.97, "  Forecast →", transform=ax.get_xaxis_transform(), color=INK_SOFT, fontsize=8, va="top")

# Style
ax.set_title(
    "timeseries-forecast-uncertainty · python · seaborn · anyplot.ai",
    fontsize=11,
    fontweight="medium",
    color=INK,
    pad=8,
)
ax.set_xlabel(DATE, fontsize=10, color=INK)
ax.set_ylabel(PRICE, fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)

sns.despine(ax=ax)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax.set_axisbelow(True)

# Combined legend: line handles + band patches
legend_elements = [
    Line2D([0], [0], color=COLOR_HISTORICAL, linewidth=3, label=ACTUAL),
    Line2D([0], [0], color=COLOR_FORECAST, linewidth=3, linestyle=(0, (6, 2)), label=FORECAST),
    Patch(facecolor=COLOR_FORECAST, alpha=ALPHA_80, label="80% Confidence"),
    Patch(facecolor=COLOR_FORECAST, alpha=ALPHA_95, label="95% Confidence"),
]
ax.legend(handles=legend_elements, fontsize=8, loc="upper left", framealpha=1.0, fancybox=False, edgecolor=INK_SOFT)

fig.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
