""" anyplot.ai
kagi-basic: Basic Kagi Chart
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: 81/100 | Updated: 2026-11-22
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
COLOR_YANG = IMPRINT_PALETTE[0]  # green: yang, bullish, thick line
COLOR_YIN = IMPRINT_PALETTE[4]  # red: yin, bearish, thin line

# Constants
REVERSAL_PCT = 0.04  # a Kagi line turns only when price reverses by this share
WIDTH_YANG = 3.6
WIDTH_YIN = 1.4

# Columns: set these to your table's column names
DATE = "Date"  # role: date
CLOSE = "Close price ($)"  # role: close

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
rng = np.random.RandomState(42)
n_days = 250
daily_returns = rng.normal(0.0003, 0.015, n_days)
df = pd.DataFrame({DATE: pd.bdate_range("2024-01-02", periods=n_days), CLOSE: 100.0 * np.cumprod(1 + daily_returns)})

# Plot: reads only df and the constants above
prices = df[CLOSE].to_numpy()

# Kagi construction: x is the line index, advancing one column per reversal
kagi_x = [0]
kagi_y = [prices[0]]
kagi_yang = []  # one flag per segment: True = yang (thick), False = yin (thin)

rising = None  # None until the first reversal-sized move, then True (up) or False (down)
current = prices[0]
last_high = prices[0]
last_low = prices[0]
is_yang = True
x_pos = 0

for price in prices[1:]:
    threshold = current * REVERSAL_PCT

    if rising is None:
        if price >= current + threshold:
            rising, is_yang, last_high = True, True, price
        elif price <= current - threshold:
            rising, is_yang, last_low = False, False, price
        else:
            continue
        kagi_x.append(x_pos)
        kagi_y.append(price)
        kagi_yang.append(is_yang)
        current = price

    elif rising:
        if price > current:
            kagi_y[-1] = price
            current = price
            if price > last_high:
                is_yang = True
                kagi_yang[-1] = True
                last_high = price
        elif price <= current - threshold:
            x_pos += 1
            # shoulder: horizontal step at the top of the finished up-move
            kagi_x.append(x_pos)
            kagi_y.append(current)
            kagi_yang.append(is_yang)
            # new down-move
            kagi_x.append(x_pos)
            kagi_y.append(price)
            if price < last_low:
                is_yang = False
                last_low = price
            kagi_yang.append(is_yang)
            rising = False
            current = price

    else:
        if price < current:
            kagi_y[-1] = price
            current = price
            if price < last_low:
                is_yang = False
                kagi_yang[-1] = False
                last_low = price
        elif price >= current + threshold:
            x_pos += 1
            # waist: horizontal step at the bottom of the finished down-move
            kagi_x.append(x_pos)
            kagi_y.append(current)
            kagi_yang.append(is_yang)
            # new up-move
            kagi_x.append(x_pos)
            kagi_y.append(price)
            if price > last_high:
                is_yang = True
                last_high = price
            kagi_yang.append(is_yang)
            rising = True
            current = price

title = "kagi-basic · python · matplotlib · anyplot.ai"
title_fontsize = max(8, round(12 * 67 / len(title))) if len(title) > 67 else 12

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

for i, yang in enumerate(kagi_yang):
    ax.plot(
        kagi_x[i : i + 2],
        kagi_y[i : i + 2],
        color=COLOR_YANG if yang else COLOR_YIN,
        linewidth=WIDTH_YANG if yang else WIDTH_YIN,
        solid_capstyle="round",
    )

# Style
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK)
ax.set_xlabel("Kagi line index", fontsize=10, color=INK)
ax.set_ylabel(CLOSE, fontsize=10, color=INK)
ax.xaxis.set_major_locator(MaxNLocator(integer=True))
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
for side in ("left", "bottom"):
    ax.spines[side].set_color(INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)

legend_handles = [
    Line2D([0], [0], color=COLOR_YANG, linewidth=WIDTH_YANG, label="Yang (bullish)"),
    Line2D([0], [0], color=COLOR_YIN, linewidth=WIDTH_YIN, label="Yin (bearish)"),
]
leg = ax.legend(handles=legend_handles, fontsize=8, loc="lower right")
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

fig.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
