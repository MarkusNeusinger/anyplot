""" pyplots.ai
scatter-complex-plane: Complex Plane Visualization (Argand Diagram)
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 83/100 | Created: 2026-03-04
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data
roots_of_unity = [np.exp(2j * np.pi * k / 3) for k in range(3)]
root_sum = sum(roots_of_unity)

arbitrary_points = [2.5 + 1.5j, -1.8 + 2.2j, 1.0 - 2.0j, -2.5 - 1.0j, 0.5 + 2.8j, -1.2 - 2.5j, 3.0 + 0.0j]

all_points = roots_of_unity + [root_sum] + arbitrary_points

labels = (
    [f"$\\omega_{k}$" for k in range(3)]
    + ["$\\Sigma\\omega_k$"]
    + [f"$z_{{{i + 1}}}$" for i in range(len(arbitrary_points))]
)

categories = ["Roots of Unity"] * 3 + ["Sum of Roots"] * 1 + ["Arbitrary Points"] * len(arbitrary_points)

df = pd.DataFrame(
    {
        "real": [z.real for z in all_points],
        "imaginary": [z.imag for z in all_points],
        "label": labels,
        "category": categories,
    }
)

# Plot
palette = {"Roots of Unity": "#306998", "Sum of Roots": "#E74C3C", "Arbitrary Points": "#2ECC71"}
markers = {"Roots of Unity": "D", "Sum of Roots": "X", "Arbitrary Points": "o"}

fig, ax = plt.subplots(figsize=(16, 16))

sns.scatterplot(
    data=df,
    x="real",
    y="imaginary",
    hue="category",
    style="category",
    markers=markers,
    palette=palette,
    s=300,
    edgecolor="white",
    linewidth=1.2,
    zorder=5,
    ax=ax,
)

# Vectors from origin to each point
for _, row in df.iterrows():
    color = palette[row["category"]]
    ax.annotate(
        "",
        xy=(row["real"], row["imaginary"]),
        xytext=(0, 0),
        arrowprops={"arrowstyle": "->", "color": color, "lw": 2.0, "alpha": 0.6},
    )

# Annotations with rectangular form
offsets = {
    "$\\omega_0$": (16, -20),
    "$\\omega_1$": (-80, 10),
    "$\\omega_2$": (-80, -20),
    "$\\Sigma\\omega_k$": (16, -22),
}

for _, row in df.iterrows():
    r = row["real"]
    i = row["imaginary"]
    if abs(r) < 0.01:
        r_str = "0"
    else:
        r_str = f"{r:.1f}"
    if i >= 0:
        rect_form = f"{r_str}+{i:.1f}i"
    else:
        rect_form = f"{r_str}{i:.1f}i"

    offset = offsets.get(row["label"], (14, 14))

    ax.annotate(
        f"{row['label']}\n{rect_form}",
        xy=(r, i),
        xytext=offset,
        textcoords="offset points",
        fontsize=12,
        color="#333333",
        fontweight="medium",
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "none", "alpha": 0.85},
        zorder=6,
    )

# Unit circle
theta = np.linspace(0, 2 * np.pi, 200)
ax.plot(np.cos(theta), np.sin(theta), ls="--", color="#999999", lw=1.8, alpha=0.7, label="Unit Circle")

# Style
ax.set_aspect("equal")
ax.set_title("scatter-complex-plane · seaborn · pyplots.ai", fontsize=24, fontweight="medium", pad=20)
ax.tick_params(axis="both", labelsize=16)

ax.axhline(0, color="#aaaaaa", lw=1.0, zorder=0)
ax.axvline(0, color="#aaaaaa", lw=1.0, zorder=0)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_visible(False)
ax.spines["bottom"].set_visible(False)

ax.xaxis.grid(True, alpha=0.15, linewidth=0.8)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8)

limit = 3.8
ax.set_xlim(-limit, limit)
ax.set_ylim(-limit, limit)

ax.set_xlabel("Real Axis", fontsize=20, labelpad=12)
ax.set_ylabel("Imaginary Axis", fontsize=20, labelpad=12)

ax.legend(fontsize=14, loc="upper left", framealpha=0.9, edgecolor="none")

plt.tight_layout()

# Save
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
