""" pyplots.ai
scatter-hr-diagram: Hertzsprung-Russell Diagram
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 89/100 | Created: 2026-03-07
"""

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data
np.random.seed(42)

main_seq_temp = np.concatenate(
    [
        np.random.uniform(25000, 40000, 15),
        np.random.uniform(10000, 25000, 40),
        np.random.uniform(6000, 10000, 60),
        np.random.uniform(3500, 6000, 80),
        np.random.uniform(2000, 3500, 55),
    ]
)
main_seq_lum = 10 ** (np.log10(main_seq_temp / 5778) * 3.5 + np.random.normal(0, 0.3, len(main_seq_temp)))

rg_temp = np.random.uniform(3000, 5500, 35)
rg_lum = 10 ** np.random.uniform(1.5, 3.5, 35)

sg_temp = np.random.uniform(3000, 30000, 20)
sg_lum = 10 ** np.random.uniform(3.5, 5.5, 20)

wd_temp = np.random.uniform(5000, 30000, 25)
wd_lum = 10 ** np.random.uniform(-4, -1.5, 25)

temperatures = np.concatenate([main_seq_temp, rg_temp, sg_temp, wd_temp])
luminosities = np.concatenate([main_seq_lum, rg_lum, sg_lum, wd_lum])
regions = (
    ["Main Sequence"] * len(main_seq_temp)
    + ["Red Giants"] * len(rg_temp)
    + ["Supergiants"] * len(sg_temp)
    + ["White Dwarfs"] * len(wd_temp)
)


spectral_types = np.select(
    [
        temperatures >= 30000,
        temperatures >= 10000,
        temperatures >= 7500,
        temperatures >= 6000,
        temperatures >= 5200,
        temperatures >= 3700,
    ],
    ["O", "B", "A", "F", "G", "K"],
    default="M",
)

spectral_colors = {
    "O": "#6B8EFF",
    "B": "#9BB0FF",
    "A": "#CAD7FF",
    "F": "#FFFCE8",
    "G": "#FFD966",
    "K": "#FF9933",
    "M": "#FF4D2E",
}

df = pd.DataFrame(
    {
        "Temperature (K)": temperatures,
        "Luminosity (L☉)": luminosities,
        "Region": regions,
        "Spectral Type": spectral_types,
    }
)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))
fig.patch.set_facecolor("#0D1117")
ax.set_facecolor("#0D1117")

spectral_order = ["O", "B", "A", "F", "G", "K", "M"]
palette = [spectral_colors[s] for s in spectral_order]

sns.scatterplot(
    data=df,
    x="Temperature (K)",
    y="Luminosity (L☉)",
    hue="Spectral Type",
    hue_order=spectral_order,
    palette=palette,
    s=120,
    alpha=0.75,
    edgecolor="white",
    linewidth=0.3,
    ax=ax,
    legend=True,
)

# Sun reference
ax.scatter(5778, 1, s=350, color="#FFD966", edgecolors="white", linewidth=2, zorder=10, marker="*")
ax.annotate(
    "Sun",
    (5778, 1),
    textcoords="offset points",
    xytext=(12, -8),
    fontsize=16,
    color="white",
    fontweight="bold",
    path_effects=[pe.withStroke(linewidth=3, foreground="#0D1117")],
)

# Region labels
text_style = {
    "fontsize": 14,
    "color": "#AAAAAA",
    "fontstyle": "italic",
    "path_effects": [pe.withStroke(linewidth=3, foreground="#0D1117")],
}
ax.text(4000, 3e4, "Supergiants", ha="center", **text_style)
ax.text(3200, 300, "Red Giants", ha="center", **text_style)
ax.text(15000, 1e-3, "White Dwarfs", ha="center", **text_style)
ax.text(
    8000,
    3,
    "Main Sequence",
    ha="center",
    rotation=-42,
    fontsize=13,
    color="#AAAAAA",
    fontstyle="italic",
    path_effects=[pe.withStroke(linewidth=3, foreground="#0D1117")],
)

# Style
ax.set_xscale("log")
ax.set_yscale("log")
ax.invert_xaxis()
ax.set_xlim(45000, 1800)
ax.set_ylim(1e-5, 1e6)

ax.set_xlabel("Surface Temperature (K)", fontsize=20, color="white")
ax.set_ylabel("Luminosity (L☉)", fontsize=20, color="white")
ax.set_title("scatter-hr-diagram · seaborn · pyplots.ai", fontsize=24, fontweight="medium", color="white", pad=20)

ax.tick_params(axis="both", labelsize=16, colors="white")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color("#333333")
ax.spines["bottom"].set_color("#333333")

ax.grid(True, alpha=0.15, linewidth=0.5, color="white")

# Spectral class secondary axis
spec_boundaries = {"O": 35000, "B": 17000, "A": 8500, "F": 6500, "G": 5500, "K": 4200, "M": 2800}
ax2 = ax.twiny()
ax2.set_xscale("log")
ax2.set_xlim(ax.get_xlim())
ax2.set_xticks(list(spec_boundaries.values()))
ax2.set_xticklabels(list(spec_boundaries.keys()))
ax2.tick_params(axis="x", labelsize=16, colors="white", length=0)
ax2.spines["top"].set_color("#333333")
ax2.spines["right"].set_visible(False)
ax2.set_xlabel("Spectral Class", fontsize=16, color="#AAAAAA", labelpad=10)

# Legend
legend = ax.legend(
    title="Spectral Type",
    fontsize=13,
    title_fontsize=15,
    loc="lower left",
    framealpha=0.3,
    facecolor="#1A1F2B",
    edgecolor="#333333",
    labelcolor="white",
)
legend.get_title().set_color("white")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
