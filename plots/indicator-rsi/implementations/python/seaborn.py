""" anyplot.ai
indicator-rsi: RSI Technical Indicator Chart
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 87/100 | Updated: 2026-11-09
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: the RSI line in brand green, the zones in matte red (overbought) and blue (oversold)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
RSI_COLOR = IMPRINT_PALETTE[0]
OVERBOUGHT_COLOR = IMPRINT_PALETTE[4]
OVERSOLD_COLOR = IMPRINT_PALETTE[2]

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
OVERBOUGHT = 70
OVERSOLD = 30
CENTERLINE = 50
RSI_MIN, RSI_MAX = 0, 100  # the RSI scale is fixed
INSTRUMENT = "Northwind Logistics (NWL) Daily RSI"
ZONE_LABEL_X = 1.01  # axes fraction: zone labels sit in the right margin, clear of the line

# Columns: set these to your table's column names
DATE = "Date"  # role: date
RSI = "RSI (14-period)"  # role: rsi

# Data: replace this block with your own table, for example df = pd.read_csv("rsi.csv")
LOOKBACK = 14
np.random.seed(42)
n_prices = 134
drift = np.zeros(n_prices)
drift[20:40] = 0.012  # rally into overbought
drift[60:78] = -0.013  # sell-off into oversold
drift[100:115] = 0.009  # recovery rally
close = pd.Series(100 * np.exp(np.cumsum(drift + np.random.randn(n_prices) * 0.011)))
change = close.diff()
# Wilder smoothing of average gains and losses over the lookback
avg_gain = change.clip(lower=0).ewm(alpha=1 / LOOKBACK, min_periods=LOOKBACK, adjust=False).mean()
avg_loss = (-change.clip(upper=0)).ewm(alpha=1 / LOOKBACK, min_periods=LOOKBACK, adjust=False).mean()
rsi_values = 100 - 100 / (1 + avg_gain / avg_loss)
dates = pd.date_range(start="2024-01-02", periods=n_prices, freq="B")
df = pd.DataFrame({DATE: dates, RSI: rsi_values}).dropna().reset_index(drop=True)

# Plot: reads only df and the constants above
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)

ax.axhspan(OVERBOUGHT, RSI_MAX, color=OVERBOUGHT_COLOR, alpha=0.10, linewidth=0)
ax.axhspan(RSI_MIN, OVERSOLD, color=OVERSOLD_COLOR, alpha=0.10, linewidth=0)
ax.axhline(OVERBOUGHT, color=OVERBOUGHT_COLOR, linestyle="--", linewidth=1.2, alpha=0.9)
ax.axhline(OVERSOLD, color=OVERSOLD_COLOR, linestyle="--", linewidth=1.2, alpha=0.9)
ax.axhline(CENTERLINE, color=INK_MUTED, linestyle=":", linewidth=1.0, alpha=0.8)

sns.lineplot(data=df, x=DATE, y=RSI, ax=ax, color=RSI_COLOR, linewidth=2.5, zorder=4)

# Zone labels in the right margin, outside the data area, in axes fractions along x
label_style = {"transform": ax.get_yaxis_transform(), "ha": "left", "va": "center", "fontsize": 8}
ax.text(ZONE_LABEL_X, (OVERBOUGHT + RSI_MAX) / 2, f"Overbought\n(>{OVERBOUGHT})", color=OVERBOUGHT_COLOR, **label_style)
ax.text(ZONE_LABEL_X, OVERSOLD / 2, f"Oversold\n(<{OVERSOLD})", color=OVERSOLD_COLOR, **label_style)
ax.text(ZONE_LABEL_X, CENTERLINE, f"Neutral\n({CENTERLINE})", color=INK_MUTED, **label_style)

# Style
ax.set_ylim(RSI_MIN, RSI_MAX)
ax.set_xlim(df[DATE].min(), df[DATE].max())
ax.set_yticks([RSI_MIN, OVERSOLD, CENTERLINE, OVERBOUGHT, RSI_MAX])
ax.set_xlabel(DATE, fontsize=10)
ax.set_ylabel(RSI, fontsize=10)
ax.set_title(f"{INSTRUMENT} · indicator-rsi · python · seaborn · anyplot.ai", fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, length=0)
ax.yaxis.grid(True, linewidth=0.6)
sns.despine(ax=ax)
fig.autofmt_xdate(rotation=30)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
