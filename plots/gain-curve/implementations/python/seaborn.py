""" anyplot.ai
gain-curve: Cumulative Gains Chart
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-11
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (first series always #009E73)
OI_BRAND = "#009E73"
OI_2 = "#C475FD"
OI_3 = "#4467A3"
OI_NEUTRAL = "#1A1A1A" if THEME == "light" else "#E8E8E0"

# Configure seaborn theme
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

# Set seed for reproducibility
np.random.seed(42)

# Generate synthetic classification data (customer churn scenario)
n_samples = 1000

# Create synthetic true labels with ~30% positive class (churners)
y_true = np.random.choice([0, 1], size=n_samples, p=[0.7, 0.3])

# Create correlated prediction scores (simulating a reasonably good model)
noise = np.random.normal(0, 0.15, n_samples)
y_score = np.clip(0.3 + 0.4 * y_true + noise, 0, 1)

# Calculate cumulative gains curve
sorted_indices = np.argsort(y_score)[::-1]
y_true_sorted = y_true[sorted_indices]

total_positives = np.sum(y_true)
cum_positives = np.cumsum(y_true_sorted)
gains = cum_positives / total_positives * 100

# Population percentage (x-axis)
population_pct = np.arange(1, len(y_true) + 1) / len(y_true) * 100

# Add origin point for complete curve
population_pct = np.insert(population_pct, 0, 0)
gains = np.insert(gains, 0, 0)

# Calculate perfect model curve
positive_rate = total_positives / len(y_true) * 100
perfect_gains = np.minimum(population_pct / positive_rate * 100, 100)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Plot model gain curve using Okabe-Ito brand color
sns.lineplot(x=population_pct, y=gains, ax=ax, color=OI_BRAND, linewidth=3.5, label="Churn Prediction Model")

# Plot random baseline (diagonal) using neutral color
sns.lineplot(
    x=[0, 100], y=[0, 100], ax=ax, color=OI_NEUTRAL, linewidth=2.5, linestyle="--", label="Random Selection (Baseline)"
)

# Plot perfect model curve using secondary Okabe-Ito color
sns.lineplot(x=population_pct, y=perfect_gains, ax=ax, color=OI_2, linewidth=2.5, linestyle=":", label="Perfect Model")

# Fill area between model and baseline to show model lift
ax.fill_between(population_pct, gains, population_pct, alpha=0.2, color=OI_BRAND)

# Styling
ax.set_xlabel("Customers Targeted (%)", fontsize=20, color=INK)
ax.set_ylabel("Churners Captured (%)", fontsize=20, color=INK)
ax.set_title("gain-curve · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Set axis limits
ax.set_xlim(0, 100)
ax.set_ylim(0, 105)

# Remove top and right spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

# Subtle grid
ax.yaxis.grid(True, alpha=0.1, linewidth=0.8, color=INK)

# Legend in upper left to avoid data overlap
ax.legend(fontsize=16, loc="upper left", framealpha=0.95)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
