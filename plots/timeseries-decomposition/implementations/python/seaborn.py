"""anyplot.ai
timeseries-decomposition: Time Series Decomposition Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 97/100 | Updated: 2026-05-14
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette, canonical order (first series is always #009E73)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

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

# Constants
PERIOD = 12  # observations per seasonal cycle (monthly data)

# Columns
DATE = "Date"  # role: date
VALUE = "Consumption (kWh)"  # role: value
COMPONENT = "Component"  # role: group

# Data: monthly electricity consumption (kWh) over 8 years, additive decomposition
np.random.seed(42)
n_months = 96
dates = pd.date_range(start="2016-01-01", periods=n_months, freq="MS")
seasonal_pattern = np.array([1.25, 1.20, 1.05, 0.95, 0.85, 0.90, 1.10, 1.15, 1.05, 0.95, 1.10, 1.20])
raw = np.linspace(5000, 7500, n_months) * np.tile(seasonal_pattern, n_months // PERIOD)
raw = raw + np.random.normal(0, 100, n_months)

series = pd.Series(raw, index=dates)
trend = series.rolling(window=PERIOD, center=True, min_periods=1).mean()
detrended = series - trend
seasonal = detrended.groupby(detrended.index.month).transform("mean")
components = {"Original": series, "Trend": trend, "Seasonal": seasonal, "Residual": detrended - seasonal}
df = pd.concat(
    [pd.DataFrame({DATE: dates, VALUE: part.values, COMPONENT: name}) for name, part in components.items()],
    ignore_index=True,
)

# Plot
names = list(df[COMPONENT].unique())
fig, axes = plt.subplots(len(names), 1, figsize=(8, 4.5), dpi=400, sharex=True, squeeze=False)

for ax, name, color in zip(axes.flat, names, IMPRINT_PALETTE, strict=False):
    part = df[df[COMPONENT] == name]
    sns.lineplot(data=part, x=DATE, y=VALUE, ax=ax, color=color, linewidth=1.4)
    if part[VALUE].min() < 0:
        ax.axhline(0, color=INK_SOFT, linestyle="--", linewidth=0.6, alpha=0.5)
    ax.set_title(name, fontsize=9, fontweight="medium", loc="left", color=INK, pad=2)
    ax.set_ylabel(f"{name} (kWh)", fontsize=8)
    ax.tick_params(axis="both", labelsize=7)
    ax.grid(True, alpha=0.1, linewidth=0.5)
    sns.despine(ax=ax)

axes.flat[-1].set_xlabel(DATE, fontsize=9)
fig.suptitle("timeseries-decomposition · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
fig.subplots_adjust(left=0.1, right=0.98, top=0.9, bottom=0.1, hspace=0.55)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
