""" pyplots.ai
parallel-basic: Basic Parallel Coordinates Plot
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Data - Iris dataset for multivariate demonstration (embedded for reproducibility)
np.random.seed(42)

# Create Iris-like dataset with realistic measurements
data = {
    "sepal_length": np.concatenate(
        [
            np.random.normal(5.0, 0.35, 50),  # Setosa
            np.random.normal(5.9, 0.52, 50),  # Versicolor
            np.random.normal(6.6, 0.64, 50),  # Virginica
        ]
    ),
    "sepal_width": np.concatenate(
        [
            np.random.normal(3.4, 0.38, 50),  # Setosa
            np.random.normal(2.8, 0.31, 50),  # Versicolor
            np.random.normal(3.0, 0.32, 50),  # Virginica
        ]
    ),
    "petal_length": np.concatenate(
        [
            np.random.normal(1.5, 0.17, 50),  # Setosa
            np.random.normal(4.3, 0.47, 50),  # Versicolor
            np.random.normal(5.5, 0.55, 50),  # Virginica
        ]
    ),
    "petal_width": np.concatenate(
        [
            np.random.normal(0.2, 0.11, 50),  # Setosa
            np.random.normal(1.3, 0.20, 50),  # Versicolor
            np.random.normal(2.0, 0.27, 50),  # Virginica
        ]
    ),
    "species": ["setosa"] * 50 + ["versicolor"] * 50 + ["virginica"] * 50,
}
df = pd.DataFrame(data)

# Ensure realistic bounds
df["sepal_length"] = df["sepal_length"].clip(4.3, 7.9)
df["sepal_width"] = df["sepal_width"].clip(2.0, 4.4)
df["petal_length"] = df["petal_length"].clip(1.0, 6.9)
df["petal_width"] = df["petal_width"].clip(0.1, 2.5)

# Define numeric columns and normalize to [0, 1] for fair comparison
numeric_cols = ["sepal_length", "sepal_width", "petal_length", "petal_width"]
df_norm = df.copy()
for col in numeric_cols:
    min_val = df[col].min()
    max_val = df[col].max()
    df_norm[col] = (df[col] - min_val) / (max_val - min_val)

# Create figure (4800x2700 px at 300 dpi)
fig, ax = plt.subplots(figsize=(16, 9))

# Define colors for species - Python Blue and Yellow first, then accessible green
colors = {"setosa": "#306998", "versicolor": "#FFD43B", "virginica": "#4CAF50"}

# Plot parallel coordinates - each line connects values across axes
x = range(len(numeric_cols))
for _, row in df_norm.iterrows():
    y = [row[col] for col in numeric_cols]
    ax.plot(x, y, color=colors[row["species"]], alpha=0.5, linewidth=2)

# Axis labels with original scale ranges
ax.set_xticks(x)
labels = [
    f"Sepal Length\n({df['sepal_length'].min():.1f}-{df['sepal_length'].max():.1f} cm)",
    f"Sepal Width\n({df['sepal_width'].min():.1f}-{df['sepal_width'].max():.1f} cm)",
    f"Petal Length\n({df['petal_length'].min():.1f}-{df['petal_length'].max():.1f} cm)",
    f"Petal Width\n({df['petal_width'].min():.1f}-{df['petal_width'].max():.1f} cm)",
]
ax.set_xticklabels(labels, fontsize=18)
ax.set_ylabel("Normalized Value", fontsize=20)
ax.set_title("parallel-basic · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="y", labelsize=16)

# Add legend for species
legend_handles = [
    plt.Line2D([0], [0], color=colors["setosa"], linewidth=3, label="Setosa"),
    plt.Line2D([0], [0], color=colors["versicolor"], linewidth=3, label="Versicolor"),
    plt.Line2D([0], [0], color=colors["virginica"], linewidth=3, label="Virginica"),
]
ax.legend(handles=legend_handles, fontsize=16, loc="upper right")

# Styling
ax.set_ylim(-0.05, 1.05)
ax.grid(True, alpha=0.3, linestyle="--", axis="y")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
