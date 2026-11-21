"""anyplot.ai
timeseries-decomposition: Time Series Decomposition Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-14
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.tsa.seasonal import seasonal_decompose


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette (canonical order, first series is brand green)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
SEASONAL_PERIOD = 12  # monthly data, annual cycle

DATE = "Date"  # role: date
SALES = "Sales (USD)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("sales.csv")
np.random.seed(42)
n_months = 72
dates = pd.date_range(start="2018-01-01", periods=n_months, freq="MS")
trend = np.linspace(100, 180, n_months) + np.cumsum(np.random.randn(n_months) * 0.5)
seasonal = 25 * np.sin(2 * np.pi * np.arange(n_months) / 12)
holiday_bump = np.array([15 if (i + 1) % 12 == 0 else 0 for i in range(n_months)])
seasonal = seasonal + holiday_bump
residual = np.random.randn(n_months) * 8
df = pd.DataFrame({DATE: dates, SALES: trend + seasonal + residual})

# Plot
series = df.set_index(DATE)[SALES]
series = series.interpolate(limit_direction="both")
period = min(SEASONAL_PERIOD, max(2, len(series) // 2))  # decomposition needs two full cycles
decomposition = seasonal_decompose(series, model="additive", period=period)
components = [
    ("Original", series),
    ("Trend", decomposition.trend),
    ("Seasonal", decomposition.seasonal),
    ("Residual", decomposition.resid),
]

fig, axes = plt.subplots(4, 1, figsize=(8, 4.5), dpi=400, sharex=True, facecolor=PAGE_BG)
for i, (ax, (name, comp)) in enumerate(zip(axes, components, strict=True)):
    ax.set_facecolor(PAGE_BG)
    ax.plot(comp.index, comp.values, color=IMPRINT_PALETTE[i], linewidth=2.0)
    ax.set_ylabel(f"{name}\n(USD)", fontsize=9, color=INK)
    ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
    ax.grid(True, alpha=0.15, linewidth=0.6, color=INK)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(INK_SOFT)

axes[-1].axhline(0, color=INK_SOFT, linewidth=0.8, alpha=0.4)
axes[-1].set_xlabel(DATE, fontsize=10, color=INK)
axes[0].set_title(
    "timeseries-decomposition · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK
)

fig.subplots_adjust(left=0.1, right=0.98, top=0.93, bottom=0.11, hspace=0.3)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
