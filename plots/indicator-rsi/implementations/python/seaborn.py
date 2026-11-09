""" anyplot.ai
indicator-rsi: RSI Technical Indicator Chart
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 77/100 | Updated: 2026-11-09
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

# Columns: set these to your table's column names
DATE = "Date"  # role: date
RSI = "RSI (14-period)"  # role: rsi

# Data: replace this block with your own table, for example df = pd.read_csv("rsi.csv")
np.random.seed(42)
n_periods = 120
dates = pd.date_range(start="2024-01-02", periods=n_periods, freq="B")
rsi_values = np.zeros(n_periods)
rsi_values[0] = 50
for i in range(1, n_periods):
    # Mean-reverting random walk with momentum
    rsi_values[i] = np.clip(rsi_values[i - 1] + 0.05 * (50 - rsi_values[i - 1]) + np.random.randn() * 5, 5, 95)
rsi_values[15:25] += 18  # Bull run into overbought
rsi_values[45:55] -= 15  # Bear drop into oversold
rsi_values[80:90] += 12  # Another overbought push
df = pd.DataFrame({DATE: dates, RSI: np.clip(rsi_values, 15, 85)})

# Plot: reads only df and the constants above
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)

ax.axhspan(OVERBOUGHT, RSI_MAX, color=OVERBOUGHT_COLOR, alpha=0.10, linewidth=0)
ax.axhspan(RSI_MIN, OVERSOLD, color=OVERSOLD_COLOR, alpha=0.10, linewidth=0)
ax.axhline(OVERBOUGHT, color=OVERBOUGHT_COLOR, linestyle="--", linewidth=1.2, alpha=0.9)
ax.axhline(OVERSOLD, color=OVERSOLD_COLOR, linestyle="--", linewidth=1.2, alpha=0.9)
ax.axhline(CENTERLINE, color=INK_MUTED, linestyle=":", linewidth=1.0, alpha=0.8)

sns.lineplot(data=df, x=DATE, y=RSI, ax=ax, color=RSI_COLOR, linewidth=2.5, zorder=4)

# Mark the periods spent in the overbought and oversold zones
sns.scatterplot(
    data=df[df[RSI] >= OVERBOUGHT],
    x=DATE,
    y=RSI,
    ax=ax,
    color=OVERBOUGHT_COLOR,
    s=40,
    edgecolor=PAGE_BG,
    linewidth=0.6,
    zorder=5,
    legend=False,
)
sns.scatterplot(
    data=df[df[RSI] <= OVERSOLD],
    x=DATE,
    y=RSI,
    ax=ax,
    color=OVERSOLD_COLOR,
    s=40,
    edgecolor=PAGE_BG,
    linewidth=0.6,
    zorder=5,
    legend=False,
)

# Zone labels at the right edge, in axes fractions along x
label_style = {"transform": ax.get_yaxis_transform(), "ha": "right", "va": "center", "fontsize": 8}
ax.text(0.995, (OVERBOUGHT + RSI_MAX) / 2, f"Overbought (>{OVERBOUGHT})", color=OVERBOUGHT_COLOR, **label_style)
ax.text(0.995, OVERSOLD / 2, f"Oversold (<{OVERSOLD})", color=OVERSOLD_COLOR, **label_style)
ax.text(0.995, CENTERLINE + 3, f"Neutral ({CENTERLINE})", color=INK_MUTED, **label_style)

# Style
ax.set_ylim(RSI_MIN, RSI_MAX)
ax.set_xlim(df[DATE].min(), df[DATE].max())
ax.set_yticks([RSI_MIN, OVERSOLD, CENTERLINE, OVERBOUGHT, RSI_MAX])
ax.set_xlabel(DATE, fontsize=10)
ax.set_ylabel(RSI, fontsize=10)
ax.set_title("indicator-rsi · python · seaborn · anyplot.ai", fontsize=12, color=INK)
ax.tick_params(axis="both", labelsize=8, length=0)
ax.yaxis.grid(True, linewidth=0.6)
sns.despine(ax=ax)
fig.autofmt_xdate(rotation=30)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
