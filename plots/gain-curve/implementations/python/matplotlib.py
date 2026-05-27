""" anyplot.ai
gain-curve: Cumulative Gains Chart
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 95/100 | Updated: 2026-05-11
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

BRAND = "#009E73"  # Okabe-Ito position 1
SECONDARY = "#C475FD"  # Okabe-Ito position 2
NEUTRAL = INK_MUTED

# Data: Generate synthetic classification data (customer response model)
np.random.seed(42)
n_samples = 1000

# Create customer features that influence response
customer_value = np.random.randn(n_samples)
customer_engagement = np.random.randn(n_samples)

# True underlying probability (strong signal)
latent_score = 1.5 * customer_value + 1.0 * customer_engagement
true_prob = 1 / (1 + np.exp(-latent_score))
y_true = (np.random.rand(n_samples) < true_prob).astype(int)

# Model predicted probabilities (captures signal well with some noise)
y_score = 1 / (1 + np.exp(-(latent_score + np.random.randn(n_samples) * 0.5)))

# Calculate cumulative gains curve
sorted_indices = np.argsort(y_score)[::-1]
y_true_sorted = y_true[sorted_indices]

# Cumulative gains: percentage of population vs percentage of positives captured
total_positives = np.sum(y_true)
cumulative_positives = np.cumsum(y_true_sorted)
gains = cumulative_positives / total_positives * 100

# Percentage of population targeted
population_percentage = np.arange(1, n_samples + 1) / n_samples * 100

# Add origin point (0, 0) for proper plotting
population_percentage = np.insert(population_percentage, 0, 0)
gains = np.insert(gains, 0, 0)

# Create perfect model curve (captures all positives immediately)
positive_rate = total_positives / n_samples * 100
perfect_x = np.array([0, positive_rate, 100])
perfect_y = np.array([0, 100, 100])

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Plot model gains curve (brand green - first series)
ax.plot(population_percentage, gains, color=BRAND, linewidth=3, label="Model", zorder=3)

# Plot random baseline (diagonal)
ax.plot([0, 100], [0, 100], color=INK_SOFT, linewidth=2, linestyle="--", label="Random (Baseline)", zorder=2)

# Plot perfect model
ax.plot(perfect_x, perfect_y, color=INK_MUTED, linewidth=2, linestyle=":", label="Perfect Model", zorder=2)

# Fill area between model and random baseline
ax.fill_between(population_percentage, gains, population_percentage, alpha=0.15, color=BRAND, zorder=1)

# Styling
ax.set_xlabel("Population Targeted (%)", fontsize=20, color=INK)
ax.set_ylabel("Positive Cases Captured (%)", fontsize=20, color=INK)
ax.set_title("gain-curve · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)

ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.set_aspect("equal")

ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

ax.grid(True, alpha=0.10, linewidth=0.8, color=INK)

leg = ax.legend(fontsize=16, loc="lower right")
if leg:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    leg.get_frame().set_linewidth(0.8)
    plt.setp(leg.get_texts(), color=INK_SOFT)

# Add annotation showing key insight
idx_20 = np.searchsorted(population_percentage, 20)
gain_at_20 = gains[idx_20]
ax.annotate(
    f"Top 20% captures {gain_at_20:.0f}%\nof positive cases",
    xy=(20, gain_at_20),
    xytext=(35, gain_at_20 - 15),
    fontsize=14,
    color=INK,
    arrowprops={"arrowstyle": "->", "color": BRAND, "lw": 2},
    bbox={"boxstyle": "round,pad=0.3", "facecolor": ELEVATED_BG, "edgecolor": INK_SOFT, "alpha": 0.9},
)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
