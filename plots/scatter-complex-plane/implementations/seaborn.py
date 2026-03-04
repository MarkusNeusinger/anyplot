""" pyplots.ai
scatter-complex-plane: Complex Plane Visualization (Argand Diagram)
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-04
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

magnitudes = [abs(z) for z in all_points]

df = pd.DataFrame(
    {
        "real": [z.real for z in all_points],
        "imaginary": [z.imag for z in all_points],
        "label": labels,
        "category": categories,
        "magnitude": magnitudes,
    }
)

# Seaborn theme and style
sns.set_theme(style="white", context="talk", font_scale=1.1)
palette = sns.color_palette(["#306998", "#D4752E", "#8B5CF6"])
cat_colors = {"Roots of Unity": palette[0], "Sum of Roots": palette[1], "Arbitrary Points": palette[2]}
markers = {"Roots of Unity": "D", "Sum of Roots": "X", "Arbitrary Points": "o"}

# Use JointGrid for seaborn-distinctive marginal distributions
g = sns.JointGrid(data=df, x="real", y="imaginary", height=14, ratio=6, space=0.15)

# Main scatter with hue, style, and size encoding
sns.scatterplot(
    data=df,
    x="real",
    y="imaginary",
    hue="category",
    style="category",
    size="magnitude",
    sizes=(150, 450),
    markers=markers,
    palette=cat_colors,
    edgecolor="white",
    linewidth=1.5,
    zorder=5,
    ax=g.ax_joint,
    legend="full",
)

# Marginal KDE plots — distinctively seaborn
for cat, color in cat_colors.items():
    subset = df[df["category"] == cat]
    sns.kdeplot(
        data=subset, x="real", color=color, fill=True, alpha=0.3, linewidth=1.5, ax=g.ax_marg_x, warn_singular=False
    )
    sns.kdeplot(
        data=subset,
        y="imaginary",
        color=color,
        fill=True,
        alpha=0.3,
        linewidth=1.5,
        ax=g.ax_marg_y,
        warn_singular=False,
    )

# Remove marginal axis labels and ticks for clean look
g.ax_marg_x.set_xlabel("")
g.ax_marg_x.set_ylabel("")
g.ax_marg_y.set_xlabel("")
g.ax_marg_y.set_ylabel("")
g.ax_marg_x.tick_params(left=False, labelleft=False)
g.ax_marg_y.tick_params(bottom=False, labelbottom=False)

ax = g.ax_joint

# Vectors from origin to each point
for _, row in df.iterrows():
    color = cat_colors[row["category"]]
    ax.annotate(
        "",
        xy=(row["real"], row["imaginary"]),
        xytext=(0, 0),
        arrowprops={"arrowstyle": "->", "color": color, "lw": 2.0, "alpha": 0.5},
    )

# Annotations with rectangular form
offsets = {
    "$\\omega_0$": (20, -28),
    "$\\omega_1$": (-95, 18),
    "$\\omega_2$": (-95, -26),
    "$\\Sigma\\omega_k$": (-85, -30),
}

for _, row in df.iterrows():
    r = row["real"]
    i = row["imaginary"]
    if abs(r) < 0.01:
        r_str = "0"
    else:
        r_str = f"{r:.1f}"
    if abs(i) < 0.01:
        rect_form = f"{r_str}+0.0i"
    elif i >= 0:
        rect_form = f"{r_str}+{i:.1f}i"
    else:
        rect_form = f"{r_str}{i:.1f}i"

    offset = offsets.get(row["label"], (16, 16))

    ax.annotate(
        f"{row['label']}\n{rect_form}",
        xy=(r, i),
        xytext=offset,
        textcoords="offset points",
        fontsize=13,
        color="#2C2C2C",
        fontweight="medium",
        bbox={
            "boxstyle": "round,pad=0.3",
            "facecolor": "white",
            "edgecolor": "#CCCCCC",
            "alpha": 0.9,
            "linewidth": 0.5,
        },
        zorder=6,
    )

# Connect roots of unity to show equilateral triangle
root_reals = [z.real for z in roots_of_unity] + [roots_of_unity[0].real]
root_imags = [z.imag for z in roots_of_unity] + [roots_of_unity[0].imag]
ax.plot(root_reals, root_imags, ls="-", color=palette[0], lw=2.0, alpha=0.4, zorder=3, label="Roots Triangle")

# Unit circle
theta = np.linspace(0, 2 * np.pi, 200)
ax.plot(np.cos(theta), np.sin(theta), ls="--", color="#888888", lw=1.8, alpha=0.6, label="Unit Circle")

# Style
ax.set_aspect("equal")
ax.set_title("scatter-complex-plane · seaborn · pyplots.ai", fontsize=24, fontweight="medium", pad=20)
ax.tick_params(axis="both", labelsize=16)

ax.axhline(0, color="#AAAAAA", lw=1.0, zorder=0)
ax.axvline(0, color="#AAAAAA", lw=1.0, zorder=0)

sns.despine(ax=ax, left=True, bottom=True)
sns.despine(ax=g.ax_marg_x, left=True, bottom=True)
sns.despine(ax=g.ax_marg_y, left=True, bottom=True)

ax.xaxis.grid(True, alpha=0.15, linewidth=0.8)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8)

limit = 3.8
ax.set_xlim(-limit, limit)
ax.set_ylim(-limit, limit)

ax.set_xlabel("Re(z)", fontsize=20, labelpad=12)
ax.set_ylabel("Im(z)", fontsize=20, labelpad=12)

# Adjust legend — keep category + unit circle, remove size entries
handles, leg_labels = ax.get_legend_handles_labels()
keep = []
skip_keys = {"magnitude", "", "category"}
for handle, lbl in zip(handles, leg_labels, strict=False):
    if lbl not in skip_keys:
        try:
            float(lbl)
        except ValueError:
            keep.append((handle, lbl))
filtered_handles, filtered_labels = zip(*keep, strict=False) if keep else ([], [])
ax.legend(
    filtered_handles, filtered_labels, fontsize=14, loc="upper left", framealpha=0.95, edgecolor="none", fancybox=True
)

plt.tight_layout()

# Save
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
