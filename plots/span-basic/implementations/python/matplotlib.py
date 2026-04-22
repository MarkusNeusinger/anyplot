""" pyplots.ai
span-basic: Basic Span Plot (Highlighted Region)
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - Stock prices with highlighted recession period
np.random.seed(42)
dates = np.arange(2006, 2016, 0.1)  # 10 years of data

# Simulate stock price with trend and volatility
price = 100 + np.cumsum(np.random.randn(len(dates)) * 2)

# Add a dip during recession period (2008-2009)
recession_mask = (dates >= 2008) & (dates < 2010)
price[recession_mask] -= np.linspace(0, 30, recession_mask.sum())
price[dates >= 2010] -= 30
price = price + np.abs(price.min()) + 50  # Keep positive

# Create plot (4800x2700 px)
fig, ax = plt.subplots(figsize=(16, 9))

# Plot line data
ax.plot(dates, price, linewidth=3, color="#306998", label="Stock Price")

# Vertical span highlighting recession period (2008-2009)
ax.axvspan(2008, 2009, alpha=0.25, color="#FFD43B", label="Recession Period")

# Horizontal span highlighting danger zone (low values)
ax.axhspan(60, 80, alpha=0.2, color="#D62728", label="Risk Zone")

# Labels and styling
ax.set_xlabel("Year", fontsize=20)
ax.set_ylabel("Price ($)", fontsize=20)
ax.set_title("span-basic · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--")
ax.legend(fontsize=16, loc="upper left")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
