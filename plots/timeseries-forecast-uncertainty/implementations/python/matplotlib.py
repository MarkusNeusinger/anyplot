""" anyplot.ai
timeseries-forecast-uncertainty: Time Series Forecast with Uncertainty Band
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-22
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: position 1 (historical), 2 (forecast), 6 (confidence bands)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
HISTORICAL_COLOR = IMPRINT_PALETTE[0]
FORECAST_COLOR = IMPRINT_PALETTE[1]
CI_COLOR = IMPRINT_PALETTE[5]

# Constants
Z_80 = 1.28  # z-score of the 80% interval
Z_95 = 1.96  # z-score of the 95% interval

# Columns: set these to your table's column names
DATE = "Date"  # role: date
ACTUAL = "Monthly Sales (thousands)"  # role: actual
FORECAST = "Forecast (thousands)"  # role: forecast
LOWER_80 = "Lower 80% (thousands)"  # role: lower_80
UPPER_80 = "Upper 80% (thousands)"  # role: upper_80
LOWER_95 = "Lower 95% (thousands)"  # role: lower_95
UPPER_95 = "Upper 95% (thousands)"  # role: upper_95

# Data: replace this block with your own table, for example df = pd.read_csv("sales.csv", parse_dates=[DATE])
# Monthly retail sales, 3-year history + 12-month ARIMA-style forecast (one overlapping month)
np.random.seed(42)
n_historical = 36
n_forecast = 12
n_total = n_historical + n_forecast - 1

t = np.arange(n_historical)
actual = 100 + t * 1.2 + 15 * np.sin(2 * np.pi * t / 12) + np.random.normal(0, 5, n_historical)

t_forecast = np.arange(n_forecast)
forecast_values = actual[-1] + t_forecast * 1.2 + 15 * np.sin(2 * np.pi * (t[-1] + t_forecast) / 12)
spread = 8 * np.sqrt(1 + t_forecast * 0.5)

pad_hist = np.full(n_historical - 1, np.nan)
df = pd.DataFrame(
    {
        DATE: pd.date_range(start="2022-01-01", periods=n_total, freq="MS"),
        ACTUAL: np.concatenate([actual, np.full(n_forecast - 1, np.nan)]),
        FORECAST: np.concatenate([pad_hist, forecast_values]),
        LOWER_80: np.concatenate([pad_hist, forecast_values - Z_80 * spread]),
        UPPER_80: np.concatenate([pad_hist, forecast_values + Z_80 * spread]),
        LOWER_95: np.concatenate([pad_hist, forecast_values - Z_95 * spread]),
        UPPER_95: np.concatenate([pad_hist, forecast_values + Z_95 * spread]),
    }
)

# Plot
hist = df.dropna(subset=[ACTUAL])
fc = df.dropna(subset=[FORECAST])
has_forecast = not fc.empty

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)
ax.set_axisbelow(True)

y_top = max(df[ACTUAL].max(), df[UPPER_95].max()) + 12
y_bottom = min(df[ACTUAL].min(), df[LOWER_95].min()) - 10

if has_forecast:
    forecast_start = fc[DATE].iloc[0]

    # Subtle forecast region tint
    ax.axvspan(forecast_start, fc[DATE].iloc[-1], color=INK, alpha=0.03, zorder=0)

    # CI bands: outer 95% first, then 80% on top
    ax.fill_between(fc[DATE], fc[LOWER_95], fc[UPPER_95], color=CI_COLOR, alpha=0.20, zorder=1)
    ax.fill_between(fc[DATE], fc[LOWER_80], fc[UPPER_80], color=CI_COLOR, alpha=0.30, zorder=2)

(hist_line,) = ax.plot(
    hist[DATE],
    hist[ACTUAL],
    color=HISTORICAL_COLOR,
    linewidth=2.5,
    solid_capstyle="round",
    zorder=4,
    label="Historical Data",
)
handles = [hist_line]

if has_forecast:
    (fc_line,) = ax.plot(
        fc[DATE],
        fc[FORECAST],
        color=FORECAST_COLOR,
        linewidth=2.5,
        linestyle="--",
        dash_capstyle="round",
        zorder=4,
        label="Forecast",
    )

    # Forecast start marker
    ax.axvline(x=forecast_start, color=INK_SOFT, linewidth=1.2, linestyle=":", alpha=0.8, zorder=3)
    ax.text(forecast_start, y_top, "Forecast →", color=INK_MUTED, fontsize=10, va="top", ha="left", fontstyle="italic")

    # Peak of the forecast
    peak = fc.loc[fc[FORECAST].idxmax()]
    ax.plot(
        peak[DATE],
        peak[FORECAST],
        "o",
        color=FORECAST_COLOR,
        markersize=6,
        zorder=6,
        markeredgecolor=PAGE_BG,
        markeredgewidth=1.5,
    )
    ax.annotate(
        f"Peak ≈ {peak[FORECAST]:.0f}k",
        xy=(peak[DATE], peak[FORECAST]),
        xytext=(0, 16),
        textcoords="offset points",
        color=INK_MUTED,
        fontsize=10,
        ha="center",
        va="bottom",
        fontstyle="italic",
    )

    # Legend: patch alphas match the stacked band appearance so 80% and 95% stay distinct
    handles += [
        fc_line,
        Line2D([0], [0], color=INK_SOFT, linestyle=":", linewidth=1.2, label="Forecast Start"),
        Patch(facecolor=CI_COLOR, alpha=0.55, label="80% CI"),
        Patch(facecolor=CI_COLOR, alpha=0.25, label="95% CI"),
    ]

# Style
ax.set_xlabel(DATE, fontsize=10, color=INK)
ax.set_ylabel(ACTUAL, fontsize=10, color=INK)
ax.set_title(
    "timeseries-forecast-uncertainty · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK
)
ax.tick_params(axis="both", labelsize=9, colors=INK_SOFT)

# Date axis: semi-annual major ticks
tick_dates = pd.date_range(start=df[DATE].min(), end=df[DATE].max(), freq="6MS")
ax.set_xticks(tick_dates)
ax.set_xticklabels([d.strftime("%b %Y") for d in tick_dates], rotation=30, ha="right")

ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
for spine in ("top", "right"):
    ax.spines[spine].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)

ax.set_ylim(y_bottom, y_top + 5)
ax.set_xlim(df[DATE].min() - pd.DateOffset(months=1), df[DATE].max() + pd.DateOffset(months=2))

leg = ax.legend(handles=handles, fontsize=9, loc="upper left", framealpha=0.95)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
