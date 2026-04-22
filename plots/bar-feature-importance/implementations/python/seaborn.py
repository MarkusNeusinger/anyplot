""" pyplots.ai
bar-feature-importance: Feature Importance Bar Chart
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-26
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data: Simulated feature importances from a Random Forest model
np.random.seed(42)

features = [
    "Annual Income",
    "Credit Score",
    "Employment Years",
    "Debt-to-Income Ratio",
    "Age",
    "Number of Accounts",
    "Loan Amount",
    "Payment History",
    "Credit Utilization",
    "Home Ownership",
    "Education Level",
    "Marital Status",
    "Monthly Expenses",
    "Savings Balance",
    "Previous Defaults",
]

# Generate realistic importance values (sum to 1.0 for interpretability)
raw_importance = np.array([0.18, 0.15, 0.12, 0.11, 0.09, 0.08, 0.07, 0.06, 0.05, 0.03, 0.02, 0.015, 0.01, 0.008, 0.007])
importance = raw_importance / raw_importance.sum()

# Standard deviation for error bars (ensemble variability)
std = np.random.uniform(0.005, 0.025, len(features))

# Create DataFrame and sort by importance
df = pd.DataFrame({"feature": features, "importance": importance, "std": std})
df = df.sort_values("importance", ascending=True).reset_index(drop=True)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Create color palette based on importance values (sequential gradient)
colors = sns.color_palette("Blues", n_colors=len(df))

# Plot horizontal bars using seaborn
sns.barplot(
    data=df,
    x="importance",
    y="feature",
    hue="feature",
    palette=colors,
    legend=False,
    ax=ax,
    edgecolor="#306998",
    linewidth=1.5,
)

# Add error bars manually for ensemble variability
ax.errorbar(
    df["importance"], range(len(df)), xerr=df["std"], fmt="none", color="#306998", capsize=4, capthick=2, linewidth=2
)

# Add value annotations at the end of bars
for i, (imp, std_val) in enumerate(zip(df["importance"], df["std"], strict=True)):
    ax.text(
        imp + std_val + 0.008, i, f"{imp:.3f}", va="center", ha="left", fontsize=14, color="#306998", fontweight="bold"
    )

# Styling
ax.set_xlabel("Feature Importance", fontsize=20)
ax.set_ylabel("Feature", fontsize=20)
ax.set_title("bar-feature-importance · seaborn · pyplots.ai", fontsize=24, fontweight="bold", pad=20)
ax.tick_params(axis="both", labelsize=16)
ax.set_xlim(0, df["importance"].max() + df["std"].max() + 0.05)

# Subtle grid on x-axis only
ax.grid(True, axis="x", alpha=0.3, linestyle="--")
ax.set_axisbelow(True)

# Remove top and right spines for cleaner look
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
