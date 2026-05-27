""" anyplot.ai
kagi-basic: Basic Kagi Chart
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-17
"""

import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Data colors (Okabe-Ito palette, theme-independent)
COLOR_YANG = "#009E73"  # imprint green — bullish
COLOR_YIN = "#AE3030"  # imprint red — bearish

# Generate synthetic stock price data
np.random.seed(42)
n_days = 250
initial_price = 100.0

# Create realistic price movements using geometric brownian motion
daily_returns = np.random.normal(0.0003, 0.015, n_days)
prices = initial_price * np.cumprod(1 + daily_returns)

# Kagi chart construction
reversal_pct = 0.04  # 4% reversal threshold

# Initialize Kagi data structures
kagi_x = [0]
kagi_y = [prices[0]]
kagi_colors = []
kagi_widths = []

current_direction = None  # 'up' or 'down'
current_price = prices[0]
last_high = prices[0]
last_low = prices[0]
is_yang = True  # Start as yang (thick line)
x_pos = 0

for price in prices[1:]:
    reversal_amount = current_price * reversal_pct

    if current_direction is None:
        # Initialize direction based on first significant move
        if price >= current_price + reversal_amount:
            current_direction = "up"
            is_yang = True
            kagi_x.append(x_pos)
            kagi_y.append(price)
            kagi_colors.append(COLOR_YANG)
            kagi_widths.append(4)
            current_price = price
            last_high = price
        elif price <= current_price - reversal_amount:
            current_direction = "down"
            is_yang = False
            kagi_x.append(x_pos)
            kagi_y.append(price)
            kagi_colors.append(COLOR_YIN)
            kagi_widths.append(2)
            current_price = price
            last_low = price

    elif current_direction == "up":
        if price > current_price:
            # Continue upward - extend line
            kagi_y[-1] = price
            current_price = price
            # Check if we broke previous high -> become yang
            if price > last_high:
                is_yang = True
                kagi_colors[-1] = COLOR_YANG
                kagi_widths[-1] = 4
                last_high = price
        elif price <= current_price - reversal_amount:
            # Reversal down - draw horizontal then vertical
            x_pos += 1
            # Horizontal shoulder line
            kagi_x.append(x_pos)
            kagi_y.append(current_price)
            kagi_colors.append(COLOR_YANG if is_yang else COLOR_YIN)
            kagi_widths.append(4 if is_yang else 2)
            # New vertical down line
            kagi_x.append(x_pos)
            kagi_y.append(price)
            # Check if we broke previous low -> become yin
            if price < last_low:
                is_yang = False
                last_low = price
            kagi_colors.append(COLOR_YANG if is_yang else COLOR_YIN)
            kagi_widths.append(4 if is_yang else 2)
            current_direction = "down"
            current_price = price

    elif current_direction == "down":
        if price < current_price:
            # Continue downward - extend line
            kagi_y[-1] = price
            current_price = price
            # Check if we broke previous low -> become yin
            if price < last_low:
                is_yang = False
                kagi_colors[-1] = COLOR_YIN
                kagi_widths[-1] = 2
                last_low = price
        elif price >= current_price + reversal_amount:
            # Reversal up - draw horizontal then vertical
            x_pos += 1
            # Horizontal waist line
            kagi_x.append(x_pos)
            kagi_y.append(current_price)
            kagi_colors.append(COLOR_YANG if is_yang else COLOR_YIN)
            kagi_widths.append(4 if is_yang else 2)
            # New vertical up line
            kagi_x.append(x_pos)
            kagi_y.append(price)
            # Check if we broke previous high -> become yang
            if price > last_high:
                is_yang = True
                last_high = price
            kagi_colors.append(COLOR_YANG if is_yang else COLOR_YIN)
            kagi_widths.append(4 if is_yang else 2)
            current_direction = "up"
            current_price = price

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Draw Kagi lines segment by segment
for i in range(len(kagi_colors)):
    ax.plot(
        [kagi_x[i], kagi_x[i + 1]],
        [kagi_y[i], kagi_y[i + 1]],
        color=kagi_colors[i],
        linewidth=kagi_widths[i],
        solid_capstyle="round",
    )

# Style
ax.set_xlabel("Kagi Line Index", fontsize=20, color=INK)
ax.set_ylabel("Price ($)", fontsize=20, color=INK)
ax.set_title("kagi-basic · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)

# Legend
legend_elements = [
    Line2D([0], [0], color=COLOR_YANG, linewidth=4, label="Yang (Bullish)"),
    Line2D([0], [0], color=COLOR_YIN, linewidth=2, label="Yin (Bearish)"),
]
leg = ax.legend(handles=legend_elements, fontsize=16, loc="upper left")
if leg:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    plt.setp(leg.get_texts(), color=INK_SOFT)

# Annotation explaining reversal threshold
ax.text(
    0.98,
    0.02,
    f"Reversal threshold: {reversal_pct * 100:.0f}%",
    transform=ax.transAxes,
    fontsize=14,
    ha="right",
    va="bottom",
    color=INK,
    bbox={"boxstyle": "round", "facecolor": ELEVATED_BG, "edgecolor": INK_SOFT, "alpha": 0.9},
)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
