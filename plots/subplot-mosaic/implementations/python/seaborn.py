""" anyplot.ai
subplot-mosaic: Mosaic Subplot Layout with Varying Sizes
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 83/100 | Updated: 2026-11-09
"""

import os

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.ticker import EngFormatter, MaxNLocator


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions; single-series panels take the brand green
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
        "grid.alpha": 0.15,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Constants
# Mosaic layout: a wide overview (A) and a wide detail (C), each beside one narrow panel, over three small metrics
MOSAIC = "AAB;CCD;EFG"

# Columns: set these to your table's column names
DATE = "Date"  # role: x
REVENUE = "Revenue ($)"  # role: y
SPEND = "Marketing spend ($)"  # role: z
CONVERSIONS = "Conversions"  # role: extra
RESPONSE = "Response time (ms)"  # role: extra
CHANNEL = "Channel"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("store_daily.csv")
# 100 days of an online store, one row per day and sales channel
np.random.seed(42)
dates = pd.date_range("2024-01-01", periods=100, freq="D")
channels = {
    # channel: (daily revenue base, mean response time in ms)
    "Online": (4500, 45),
    "Retail": (3200, 50),
    "Partner": (1800, 120),
    "Direct": (2750, 40),
}
rows = []
for channel, (base, latency) in channels.items():
    trend = np.cumsum(np.random.randn(len(dates)) * 0.02 + 0.003)
    spend = np.random.uniform(200, 1500, len(dates))
    rows.append(
        pd.DataFrame(
            {
                DATE: dates,
                CHANNEL: channel,
                REVENUE: base * np.exp(trend) * np.random.uniform(0.9, 1.1, len(dates)),
                SPEND: spend,
                CONVERSIONS: np.round(spend * 0.06 + np.random.randn(len(dates)) * 12 + 20).clip(0),
                RESPONSE: np.random.gamma(16, latency / 16, len(dates)),
            }
        )
    )
df = pd.concat(rows, ignore_index=True)

# Plot: reads only df and the constants above
daily = df.groupby(DATE, sort=True).agg({REVENUE: "sum", CONVERSIONS: "sum"}).reset_index()
order_value = "Per conversion"
daily[order_value] = daily[REVENUE] / daily[CONVERSIONS].replace(0, np.nan)
n_channels = df[CHANNEL].nunique()
channel_palette = IMPRINT_PALETTE[:n_channels]

fig, axes = plt.subplot_mosaic(
    MOSAIC, figsize=(8, 4.5), dpi=400, height_ratios=[1.35, 1, 0.85], layout="constrained", facecolor=PAGE_BG
)

# A: primary panel, total daily revenue over all channels
sns.lineplot(data=daily, x=DATE, y=REVENUE, ax=axes["A"], color=IMPRINT_PALETTE[0], linewidth=1.8)
axes["A"].set_title("Total daily revenue", fontsize=10, fontweight="bold", loc="left")

# B: marketing spend against conversions, one point per day and channel
sns.scatterplot(
    data=df,
    x=SPEND,
    y=CONVERSIONS,
    ax=axes["B"],
    color=IMPRINT_PALETTE[0],
    s=10,
    alpha=0.55,
    edgecolor=PAGE_BG,
    linewidth=0.3,
)
axes["B"].set_title("Marketing ROI", fontsize=9, fontweight="bold", loc="left")

# C: revenue summed per channel
sns.barplot(
    data=df,
    x=CHANNEL,
    y=REVENUE,
    hue=CHANNEL,
    palette=channel_palette,
    estimator="sum",
    errorbar=None,
    edgecolor=PAGE_BG,
    legend=False,
    ax=axes["C"],
)
axes["C"].set_title("Revenue by channel", fontsize=9, fontweight="bold", loc="left")
axes["C"].set_ylabel(f"Total {REVENUE.lower()}")

# D: distribution of daily response times
sns.histplot(data=df, x=RESPONSE, bins=30, color=IMPRINT_PALETTE[0], edgecolor=PAGE_BG, linewidth=0.4, ax=axes["D"])
axes["D"].set_title("Response times", fontsize=9, fontweight="bold", loc="left")
axes["D"].set_ylabel("Channel-days")

# E, F, G: small supporting metrics
sns.lineplot(data=daily, x=DATE, y=CONVERSIONS, ax=axes["E"], color=IMPRINT_PALETTE[0], linewidth=1.2)
axes["E"].set_title("Daily conversions", fontsize=8, fontweight="bold", loc="left")

sns.lineplot(data=daily, x=DATE, y=order_value, ax=axes["F"], color=IMPRINT_PALETTE[0], linewidth=1.2)
axes["F"].set_title("Revenue per conversion", fontsize=8, fontweight="bold", loc="left")

sns.boxplot(
    data=df,
    x=CHANNEL,
    y=RESPONSE,
    hue=CHANNEL,
    palette=channel_palette,
    legend=False,
    width=0.6,
    linewidth=0.7,
    fliersize=1.5,
    linecolor=INK_SOFT,
    ax=axes["G"],
)
axes["G"].set_title("Response time by channel", fontsize=8, fontweight="bold", loc="left")

# Style
fig.suptitle("subplot-mosaic · python · seaborn · anyplot.ai", fontsize=12, fontweight="bold", color=INK)
for key in ("A", "E", "F"):
    locator = mdates.AutoDateLocator(maxticks=6 if key == "A" else 3)
    axes[key].xaxis.set_major_locator(locator)
    axes[key].xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
    axes[key].set_xlabel("")
    axes[key].xaxis.get_offset_text().set_size(6)
for key in ("A", "C"):
    axes[key].yaxis.set_major_formatter(EngFormatter(sep=""))
for key, ax in axes.items():
    small = key in "EFG"
    ax.tick_params(axis="both", labelsize=6 if small else 7, length=2)
    ax.xaxis.label.set_size(7 if small else 8)
    ax.yaxis.label.set_size(7 if small else 8)
    ax.yaxis.set_major_locator(MaxNLocator(4 if small else 5))
    ax.yaxis.grid(True, linewidth=0.5)
    ax.set_axisbelow(True)
    sns.despine(ax=ax)
for key in ("E", "F", "G"):
    axes[key].set_ylabel(axes[key].get_ylabel(), labelpad=2)
axes["C"].set_xlabel("")
axes["G"].set_xlabel("")
fig.get_layout_engine().set(h_pad=0.05, w_pad=0.06, hspace=0.04, wspace=0.04)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
