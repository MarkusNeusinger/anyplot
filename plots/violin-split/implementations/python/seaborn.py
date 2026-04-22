""" pyplots.ai
violin-split: Split Violin Plot
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 94/100 | Created: 2025-12-25
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data - Salary comparison between genders across departments
np.random.seed(42)

departments = ["Engineering", "Marketing", "Sales", "Finance"]
genders = ["Male", "Female"]

data = []
# Create realistic salary distributions with different patterns per department
salary_params = {
    "Engineering": {"Male": (95000, 15000), "Female": (92000, 14000)},
    "Marketing": {"Male": (72000, 12000), "Female": (74000, 11000)},
    "Sales": {"Male": (68000, 18000), "Female": (65000, 16000)},
    "Finance": {"Male": (85000, 14000), "Female": (83000, 13000)},
}

for dept in departments:
    for gender in genders:
        mean, std = salary_params[dept][gender]
        n_samples = np.random.randint(80, 150)
        salaries = np.random.normal(mean, std, n_samples)
        salaries = np.clip(salaries, 30000, 180000)  # Realistic bounds
        for sal in salaries:
            data.append({"Department": dept, "Gender": gender, "Salary": sal})

df = pd.DataFrame(data)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

sns.violinplot(
    data=df,
    x="Department",
    y="Salary",
    hue="Gender",
    split=True,
    inner="quart",
    palette={"Male": "#306998", "Female": "#FFD43B"},
    linewidth=1.5,
    ax=ax,
)

# Style
ax.set_title("violin-split · seaborn · pyplots.ai", fontsize=24, fontweight="bold", pad=20)
ax.set_xlabel("Department", fontsize=20)
ax.set_ylabel("Annual Salary ($)", fontsize=20)
ax.tick_params(axis="both", labelsize=16)

# Format y-axis as currency
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x / 1000:.0f}K"))

# Legend styling
legend = ax.legend(title="Gender", fontsize=16, title_fontsize=18, loc="upper right")
legend.get_frame().set_alpha(0.9)

# Subtle grid
ax.yaxis.grid(True, alpha=0.3, linestyle="--")
ax.set_axisbelow(True)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
