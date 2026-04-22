""" pyplots.ai
parallel-basic: Basic Parallel Coordinates Plot
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


# Set seaborn style
sns.set_theme(style="whitegrid")

# Data - Iris dataset for multivariate demonstration
df = pd.read_csv("https://raw.githubusercontent.com/mwaskom/seaborn-data/master/iris.csv")

# Define numeric columns and normalize to [0, 1] for fair comparison
numeric_cols = ["sepal_length", "sepal_width", "petal_length", "petal_width"]
df_norm = df.copy()
for col in numeric_cols:
    min_val = df[col].min()
    max_val = df[col].max()
    df_norm[col] = (df[col] - min_val) / (max_val - min_val)

# Add row index to track individual observations and reshape for seaborn lineplot
df_norm["observation"] = range(len(df_norm))
df_long = df_norm.melt(
    id_vars=["species", "observation"], value_vars=numeric_cols, var_name="dimension", value_name="normalized_value"
)

# Create figure (4800x2700 px at 300 dpi)
fig, ax = plt.subplots(figsize=(16, 9))

# Define color palette using Python colors + a third
palette = {"setosa": "#306998", "versicolor": "#FFD43B", "virginica": "#4CAF50"}

# Plot parallel coordinates using seaborn lineplot
sns.lineplot(
    data=df_long,
    x="dimension",
    y="normalized_value",
    hue="species",
    units="observation",
    estimator=None,
    palette=palette,
    alpha=0.5,
    linewidth=2,
    ax=ax,
)

# Create custom x-axis labels with original scale ranges
labels = [
    f"Sepal Length\n({df['sepal_length'].min():.1f}-{df['sepal_length'].max():.1f} cm)",
    f"Sepal Width\n({df['sepal_width'].min():.1f}-{df['sepal_width'].max():.1f} cm)",
    f"Petal Length\n({df['petal_length'].min():.1f}-{df['petal_length'].max():.1f} cm)",
    f"Petal Width\n({df['petal_width'].min():.1f}-{df['petal_width'].max():.1f} cm)",
]
ax.set_xticks(range(len(numeric_cols)))
ax.set_xticklabels(labels, fontsize=18)

# Axis labels and title
ax.set_xlabel("")
ax.set_ylabel("Normalized Value", fontsize=20)
ax.set_title("parallel-basic · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="y", labelsize=16)

# Customize legend
ax.legend(title="Species", title_fontsize=18, fontsize=16, loc="upper right", framealpha=0.9)

# Adjust y-axis limits
ax.set_ylim(-0.05, 1.05)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
