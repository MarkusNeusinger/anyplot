""" anyplot.ai
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

# Okabe-Ito palette
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442"]
COLOR_HISTORICAL = OKABE_ITO[0]
COLOR_FORECAST = OKABE_ITO[1]

# Higher alpha in dark mode — orange over near-black otherwise looks brownish
ALPHA_95 = 0.30 if THEME == "dark" else 0.22
ALPHA_80 = 0.42 if THEME == "dark" else 0.30

np.random.seed(42)

# Data — stock price with ~3-month history and 4-week forecast
n_historical = 60
n_forecast = 20
dates = pd.date_range(start="2025-01-01", periods=n_historical + n_forecast, freq="B")

t = np.arange(n_historical)
historical_prices = 150 + 0.15 * t + 2.5 * np.sin(2 * np.pi * t / 20) + np.random.normal(0, 1.5, n_historical)

t_fc = np.arange(n_historical, n_historical + n_forecast)
forecast_prices = 150 + 0.15 * t_fc + 2.5 * np.sin(2 * np.pi * t_fc / 20)

horizon = np.arange(1, n_forecast + 1)
std_growth = 1.5 * np.sqrt(horizon)
lower_95 = forecast_prices - 1.96 * std_growth
upper_95 = forecast_prices + 1.96 * std_growth
lower_80 = forecast_prices - 1.28 * std_growth
upper_80 = forecast_prices + 1.28 * std_growth

# Wide-form for CI bands; long-form for seaborn's data-aware lineplot
df_wide = pd.DataFrame(
    {
        "date": dates,
        "actual": list(historical_prices) + [np.nan] * n_forecast,
        "forecast": [np.nan] * (n_historical - 1) + [historical_prices[-1]] + list(forecast_prices),
        "lower_80": [np.nan] * (n_historical - 1) + [historical_prices[-1]] + list(lower_80),
        "upper_80": [np.nan] * (n_historical - 1) + [historical_prices[-1]] + list(upper_80),
        "lower_95": [np.nan] * (n_historical - 1) + [historical_prices[-1]] + list(lower_95),
        "upper_95": [np.nan] * (n_historical - 1) + [historical_prices[-1]] + list(upper_95),
    }
)

long_data = pd.concat(
    [
        df_wide[["date", "actual"]].rename(columns={"actual": "price"}).assign(series="Historical"),
        df_wide[["date", "forecast"]].rename(columns={"forecast": "price"}).assign(series="Forecast"),
    ]
).dropna()

# Configure seaborn theme
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

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Subtle forecast-region shading to visually separate forecast from history
ax.axvspan(dates[n_historical - 1], dates[-1], alpha=0.04, color=INK, zorder=0)

# Confidence interval bands (95% outermost/lightest, 80% inner/more opaque — nested)
ax.fill_between(df_wide["date"], df_wide["lower_95"], df_wide["upper_95"], alpha=ALPHA_95, color=COLOR_FORECAST)
ax.fill_between(df_wide["date"], df_wide["lower_80"], df_wide["upper_80"], alpha=ALPHA_80, color=COLOR_FORECAST)

# Seaborn lineplot — idiomatic long-form API with hue + style + dashes
sns.lineplot(
    data=long_data,
    x="date",
    y="price",
    hue="series",
    style="series",
    palette={"Historical": COLOR_HISTORICAL, "Forecast": COLOR_FORECAST},
    dashes={"Historical": (1, 0), "Forecast": (6, 2)},
    linewidth=3,
    ax=ax,
    legend=False,
)

# Forecast boundary marker
ax.axvline(x=dates[n_historical - 1], color=INK_SOFT, linestyle=":", linewidth=1.5, alpha=0.5)
ax.text(
    dates[n_historical - 1],
    0.97,
    "  Forecast →",
    transform=ax.get_xaxis_transform(),
    color=INK_SOFT,
    fontsize=8,
    va="top",
)

# Style — title at 11pt, axes at 10pt for clear typographic hierarchy
ax.set_title(
    "timeseries-forecast-uncertainty · python · seaborn · anyplot.ai",
    fontsize=11,
    fontweight="medium",
    color=INK,
    pad=8,
)
ax.set_xlabel("Date", fontsize=10, color=INK)
ax.set_ylabel("Stock Price ($)", fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)

sns.despine(ax=ax)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax.set_axisbelow(True)

# Combined legend: line handles + CI band patches
legend_elements = [
    Line2D([0], [0], color=COLOR_HISTORICAL, linewidth=3, label="Historical"),
    Line2D([0], [0], color=COLOR_FORECAST, linewidth=3, linestyle=(0, (6, 2)), label="Forecast"),
    Patch(facecolor=COLOR_FORECAST, alpha=ALPHA_80, label="80% Confidence"),
    Patch(facecolor=COLOR_FORECAST, alpha=ALPHA_95, label="95% Confidence"),
]
ax.legend(handles=legend_elements, fontsize=8, loc="upper left", framealpha=1.0, fancybox=False, edgecolor=INK_SOFT)

plt.tight_layout()

# Save
plt.savefig(f"plot-{THEME}.png", dpi=400, bbox_inches="tight", facecolor=PAGE_BG)
