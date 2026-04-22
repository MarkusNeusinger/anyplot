""" pyplots.ai
curve-bias-variance-tradeoff: Bias-Variance Tradeoff Curve
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 93/100 | Created: 2026-01-26
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data - Theoretical curves for bias-variance tradeoff
complexity = np.linspace(0.5, 10, 100)

# Bias squared: decreases with complexity (high bias = underfitting)
bias_squared = 2.5 / (1 + 0.5 * complexity)

# Variance: increases with complexity (high variance = overfitting)
variance = 0.05 * complexity**1.5

# Irreducible error: constant noise floor
irreducible_error = np.full_like(complexity, 0.3)

# Total error = Bias² + Variance + Irreducible Error
total_error = bias_squared + variance + irreducible_error

# Find optimal complexity (minimum total error)
optimal_idx = np.argmin(total_error)
optimal_complexity = complexity[optimal_idx]
optimal_error = total_error[optimal_idx]

# Create DataFrame for seaborn
df = pd.DataFrame(
    {
        "Model Complexity": np.tile(complexity, 4),
        "Error": np.concatenate([bias_squared, variance, irreducible_error, total_error]),
        "Component": (
            ["Bias²"] * len(complexity)
            + ["Variance"] * len(complexity)
            + ["Irreducible Error"] * len(complexity)
            + ["Total Error"] * len(complexity)
        ),
    }
)

# Create plot
sns.set_context("talk", font_scale=1.2)
fig, ax = plt.subplots(figsize=(16, 9))

# Define colors and line styles
palette = {"Bias²": "#306998", "Variance": "#FFD43B", "Irreducible Error": "#808080", "Total Error": "#E74C3C"}
line_styles = {"Bias²": "-", "Variance": "-", "Irreducible Error": "--", "Total Error": "-"}
line_widths = {"Bias²": 3, "Variance": 3, "Irreducible Error": 2.5, "Total Error": 4}

# Plot each component
for component in ["Bias²", "Variance", "Irreducible Error", "Total Error"]:
    subset = df[df["Component"] == component]
    ax.plot(
        subset["Model Complexity"],
        subset["Error"],
        color=palette[component],
        linestyle=line_styles[component],
        linewidth=line_widths[component],
        label=component,
    )

# Add shaded regions for underfitting and overfitting zones
ax.axvspan(0.5, optimal_complexity, alpha=0.1, color="#306998", label="_nolegend_")
ax.axvspan(optimal_complexity, 10, alpha=0.1, color="#FFD43B", label="_nolegend_")

# Mark optimal point
ax.axvline(x=optimal_complexity, color="#2ECC71", linestyle=":", linewidth=2.5, alpha=0.8)
ax.scatter([optimal_complexity], [optimal_error], s=200, color="#2ECC71", zorder=5, edgecolor="white", linewidth=2)

# Add annotations for curves (positioned at the end of each curve)
ax.annotate("Bias²", xy=(1.5, bias_squared[10] + 0.15), fontsize=16, color="#306998", fontweight="bold")
ax.annotate("Variance", xy=(8.5, variance[85] + 0.15), fontsize=16, color="#B8860B", fontweight="bold")
ax.annotate("Total Error", xy=(8, total_error[75] + 0.25), fontsize=16, color="#E74C3C", fontweight="bold")
ax.annotate("Irreducible Error", xy=(7, 0.42), fontsize=14, color="#606060", fontweight="bold")

# Add zone labels
ax.text(2.0, 3.2, "Underfitting\n(High Bias)", fontsize=14, ha="center", color="#306998", alpha=0.8, fontweight="bold")
ax.text(
    8.0, 3.2, "Overfitting\n(High Variance)", fontsize=14, ha="center", color="#B8860B", alpha=0.8, fontweight="bold"
)

# Add optimal point annotation
ax.annotate(
    "Optimal\nComplexity",
    xy=(optimal_complexity, optimal_error),
    xytext=(optimal_complexity + 1.2, optimal_error + 0.6),
    fontsize=14,
    ha="left",
    color="#2ECC71",
    fontweight="bold",
    arrowprops={"arrowstyle": "->", "color": "#2ECC71", "lw": 2},
)

# Add formula as text box
formula_text = r"Total Error = Bias² + Variance + $\epsilon$"
ax.text(
    0.98,
    0.98,
    formula_text,
    transform=ax.transAxes,
    fontsize=16,
    verticalalignment="top",
    horizontalalignment="right",
    bbox={"boxstyle": "round,pad=0.5", "facecolor": "white", "edgecolor": "gray", "alpha": 0.9},
)

# Labels and styling
ax.set_xlabel("Model Complexity", fontsize=20)
ax.set_ylabel("Prediction Error", fontsize=20)
ax.set_title("curve-bias-variance-tradeoff · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.set_xlim(0.5, 10)
ax.set_ylim(0, 3.8)

# Custom x-axis labels
ax.set_xticks([1, 3, 5, 7, 9])
ax.set_xticklabels(["Low", "", "Medium", "", "High"])

# Add subtle grid
ax.grid(True, alpha=0.3, linestyle="--")

# Legend
ax.legend(loc="upper center", fontsize=14, ncol=4, framealpha=0.9)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
