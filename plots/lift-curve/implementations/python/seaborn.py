""" anyplot.ai
lift-curve: Model Lift Chart
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-10
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito colors
BRAND = "#009E73"  # bluish green - first series
SECONDARY = "#C475FD"  # vermillion

# Set seaborn theme with theme-adaptive colors
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

# Data - simulate customer response prediction for marketing campaign
np.random.seed(42)
n_samples = 1000
base_response_rate = 0.10  # 10% overall response rate

# Create a model with good predictive power
latent_propensity = np.random.normal(0, 1, n_samples)

# Model score approximates the latent propensity with some noise
y_score = latent_propensity + np.random.normal(0, 0.3, n_samples)
y_score = (y_score - y_score.min()) / (y_score.max() - y_score.min())

# Actual responses based on latent propensity (strong correlation)
response_threshold = np.percentile(latent_propensity, 100 * (1 - base_response_rate))
y_true = (latent_propensity >= response_threshold).astype(int)

# Calculate lift curve data
sorted_indices = np.argsort(y_score)[::-1]
y_true_sorted = y_true[sorted_indices]

n_positives = y_true.sum()
cumulative_positives = np.cumsum(y_true_sorted)
population_percentages = np.arange(1, n_samples + 1) / n_samples * 100

cumulative_positive_rate = cumulative_positives / np.arange(1, n_samples + 1)
baseline_rate = n_positives / n_samples
lift = cumulative_positive_rate / baseline_rate

# Create dataframe for seaborn
df = pd.DataFrame({"Population Targeted (%)": population_percentages, "Cumulative Lift": lift})

# Create plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)

# Plot lift curve using seaborn lineplot
sns.lineplot(
    data=df, x="Population Targeted (%)", y="Cumulative Lift", ax=ax, color=BRAND, linewidth=3, label="Model Lift"
)

# Add baseline reference line (random selection = lift of 1)
ax.axhline(y=1, color=INK_SOFT, linestyle="--", linewidth=2.5, label="Random (No Lift)", zorder=3)

# Add decile markers with improved spacing
decile_percentages = [10, 20, 30, 40, 50]
for pct in decile_percentages:
    idx = int(n_samples * pct / 100) - 1
    pop_pct = population_percentages[idx]
    lift_val = lift[idx]
    ax.plot(pop_pct, lift_val, "o", color=BRAND, markersize=12, zorder=5)

    # Alternate annotation positions to avoid cramping
    offset_y = 25 if pct % 20 == 10 else 10
    ax.annotate(
        f"{lift_val:.2f}x",
        (pop_pct, lift_val),
        textcoords="offset points",
        xytext=(0, offset_y),
        ha="center",
        fontsize=14,
        fontweight="bold",
        color=INK,
    )

# Styling
ax.set_xlabel("Population Targeted (%)", fontsize=20, color=INK)
ax.set_ylabel("Cumulative Lift Ratio", fontsize=20, color=INK)
ax.set_title("lift-curve · seaborn · anyplot.ai", fontsize=24, fontweight="bold", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Remove top and right spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

# Subtle grid
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)

# Set axis limits
ax.set_xlim(0, 100)
ax.set_ylim(0, max(lift) * 1.1)

# Legend styling
legend = ax.legend(fontsize=16, loc="upper right", framealpha=0.95)
legend.get_frame().set_facecolor(ELEVATED_BG)
legend.get_frame().set_edgecolor(INK_SOFT)

# Tight layout
plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
