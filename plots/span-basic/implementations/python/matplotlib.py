""" anyplot.ai
span-basic: Basic Span Plot (Highlighted Region)
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 91/100 | Updated: 2026-04-30
"""

import os

import matplotlib.pyplot as plt
import numpy as np


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

BRAND = "#009E73"  # Okabe-Ito position 1 — first series
C2 = "#D55E00"  # Okabe-Ito position 2
C3 = "#0072B2"  # Okabe-Ito position 3

# Data — stock prices with a simulated recession dip
np.random.seed(42)
dates = np.arange(2004, 2016, 0.1)

price = 100 + np.cumsum(np.random.randn(len(dates)) * 1.5)
recession_mask = (dates >= 2008) & (dates < 2010)
price[recession_mask] -= np.linspace(0, 35, recession_mask.sum())
price[dates >= 2010] -= 35
price = price - price.min() + 70

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

ax.plot(dates, price, linewidth=3, color=BRAND, label="Stock Price Index")

# Vertical span — recession period (2008–2009)
ax.axvspan(2008, 2010, alpha=0.22, color=C2, label="Recession Period")

# Horizontal span — risk zone (low values)
ax.axhspan(70, 95, alpha=0.18, color=C3, label="Risk Zone")

# Style
ax.set_xlabel("Year", fontsize=20, color=INK)
ax.set_ylabel("Price Index", fontsize=20, color=INK)
ax.set_title("span-basic · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT, labelcolor=INK_SOFT)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)

ax.yaxis.grid(True, alpha=0.12, linewidth=0.8, color=INK)

leg = ax.legend(fontsize=16, loc="upper left")
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
