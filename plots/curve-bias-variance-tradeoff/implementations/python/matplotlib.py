""" pyplots.ai
curve-bias-variance-tradeoff: Bias-Variance Tradeoff Curve
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 94/100 | Created: 2026-01-26
"""

import matplotlib.pyplot as plt
import numpy as np


# Data: Generate theoretical bias-variance tradeoff curves
complexity = np.linspace(0.1, 10, 100)

# Bias squared: decreases with complexity (high at low complexity = underfitting)
bias_squared = 4 / (1 + complexity)

# Variance: increases with complexity (high at high complexity = overfitting)
variance = 0.3 * complexity

# Irreducible error: constant noise floor
irreducible_error = np.ones_like(complexity) * 0.5

# Total error: sum of all components
total_error = bias_squared + variance + irreducible_error

# Find optimal complexity (minimum total error)
optimal_idx = np.argmin(total_error)
optimal_complexity = complexity[optimal_idx]
optimal_error = total_error[optimal_idx]

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Plot curves with distinct colors and line styles
ax.plot(complexity, bias_squared, color="#306998", linewidth=3, linestyle="-", label="Bias²")
ax.plot(complexity, variance, color="#FFD43B", linewidth=3, linestyle="-", label="Variance")
ax.plot(complexity, irreducible_error, color="#888888", linewidth=2.5, linestyle="--", label="Irreducible Error")
ax.plot(complexity, total_error, color="#E74C3C", linewidth=4, linestyle="-", label="Total Error")

# Mark optimal complexity point
ax.axvline(x=optimal_complexity, color="#2ECC71", linewidth=2.5, linestyle=":", alpha=0.8)
ax.scatter([optimal_complexity], [optimal_error], color="#2ECC71", s=250, zorder=5, edgecolors="white", linewidths=2)
ax.annotate(
    "Optimal\nComplexity",
    xy=(optimal_complexity, optimal_error),
    xytext=(optimal_complexity + 1.5, optimal_error + 0.8),
    fontsize=16,
    ha="left",
    arrowprops={"arrowstyle": "->", "color": "#2ECC71", "lw": 2},
)

# Add shaded regions for underfitting and overfitting zones
ax.axvspan(0, optimal_complexity, alpha=0.08, color="#306998", label="_nolegend_")
ax.axvspan(optimal_complexity, 10, alpha=0.08, color="#FFD43B", label="_nolegend_")

# Zone labels
ax.text(
    optimal_complexity / 2,
    ax.get_ylim()[1] * 0.85,
    "Underfitting\n(High Bias)",
    fontsize=16,
    ha="center",
    va="top",
    color="#306998",
    fontweight="bold",
)
ax.text(
    (optimal_complexity + 10) / 2,
    ax.get_ylim()[1] * 0.85,
    "Overfitting\n(High Variance)",
    fontsize=16,
    ha="center",
    va="top",
    color="#B8860B",
    fontweight="bold",
)

# Direct curve labels
ax.text(1.0, bias_squared[10] + 0.3, "Bias²", fontsize=16, color="#306998", fontweight="bold")
ax.text(8.5, variance[85] + 0.3, "Variance", fontsize=16, color="#B8860B", fontweight="bold")
ax.text(8.5, total_error[85] + 0.3, "Total Error", fontsize=16, color="#E74C3C", fontweight="bold")
ax.text(8.5, irreducible_error[85] - 0.4, "Irreducible Error", fontsize=16, color="#888888", fontweight="bold")

# Add formula annotation
ax.text(
    0.98,
    0.02,
    "Total Error = Bias² + Variance + Irreducible Error",
    transform=ax.transAxes,
    fontsize=16,
    ha="right",
    va="bottom",
    bbox={"boxstyle": "round,pad=0.5", "facecolor": "white", "edgecolor": "#cccccc", "alpha": 0.9},
)

# Styling
ax.set_xlabel("Model Complexity", fontsize=20)
ax.set_ylabel("Prediction Error", fontsize=20)
ax.set_title("curve-bias-variance-tradeoff · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.set_xlim(0, 10)
ax.set_ylim(0, 5)

# Custom x-axis labels to show Low/High
ax.set_xticks([0.5, 5, 9.5])
ax.set_xticklabels(["Low", "Medium", "High"], fontsize=16)

ax.grid(True, alpha=0.3, linestyle="--")
ax.legend(fontsize=16, loc="upper center", ncol=4, framealpha=0.9)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
