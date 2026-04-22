""" pyplots.ai
scatter-categorical: Categorical Scatter Plot
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 95/100 | Created: 2025-12-30
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data - Iris-like flower measurements with species categories
np.random.seed(42)

# Create data for three flower species with distinct patterns
n_per_group = 50

# Species A: smaller petals, tight cluster
species_a_x = np.random.normal(1.5, 0.3, n_per_group)
species_a_y = np.random.normal(0.3, 0.1, n_per_group)

# Species B: medium petals, wider spread
species_b_x = np.random.normal(4.5, 0.8, n_per_group)
species_b_y = np.random.normal(1.4, 0.3, n_per_group)

# Species C: larger petals, elongated cluster
species_c_x = np.random.normal(5.8, 0.6, n_per_group)
species_c_y = np.random.normal(2.1, 0.4, n_per_group)

df = pd.DataFrame(
    {
        "Petal Length (cm)": np.concatenate([species_a_x, species_b_x, species_c_x]),
        "Petal Width (cm)": np.concatenate([species_a_y, species_b_y, species_c_y]),
        "Species": ["Setosa"] * n_per_group + ["Versicolor"] * n_per_group + ["Virginica"] * n_per_group,
    }
)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Custom colorblind-safe palette using Python colors first
custom_palette = ["#306998", "#FFD43B", "#6A9F58"]

sns.scatterplot(
    data=df,
    x="Petal Length (cm)",
    y="Petal Width (cm)",
    hue="Species",
    palette=custom_palette,
    s=200,
    alpha=0.7,
    edgecolor="white",
    linewidth=0.5,
    ax=ax,
)

# Styling
ax.set_title("scatter-categorical · seaborn · pyplots.ai", fontsize=24, fontweight="bold", pad=20)
ax.set_xlabel("Petal Length (cm)", fontsize=20)
ax.set_ylabel("Petal Width (cm)", fontsize=20)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--")

# Legend styling
ax.legend(title="Species", fontsize=16, title_fontsize=18, loc="upper left", framealpha=0.9)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
