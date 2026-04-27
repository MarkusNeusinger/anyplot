"""anyplot.ai
parallel-basic: Basic Parallel Coordinates Plot
Library: seaborn | Python 3.13
Quality: pending | Created: 2026-04-27
"""

import os
import sys


# Prevent local matplotlib.py from shadowing the installed matplotlib package
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]

import matplotlib.pyplot as plt
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442"]

sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK,
        "grid.alpha": 0.10,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Data
df = sns.load_dataset("iris")

numeric_cols = ["sepal_length", "sepal_width", "petal_length", "petal_width"]
df_norm = df.copy()
for col in numeric_cols:
    col_min = df[col].min()
    col_max = df[col].max()
    df_norm[col] = (df[col] - col_min) / (col_max - col_min)

df_norm["observation"] = range(len(df_norm))
df_long = df_norm.melt(
    id_vars=["species", "observation"], value_vars=numeric_cols, var_name="dimension", value_name="normalized_value"
)

# Plot
species_order = ["setosa", "versicolor", "virginica"]
palette = {sp: OKABE_ITO[i] for i, sp in enumerate(species_order)}

fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

sns.lineplot(
    data=df_long,
    x="dimension",
    y="normalized_value",
    hue="species",
    hue_order=species_order,
    units="observation",
    estimator=None,
    palette=palette,
    alpha=0.45,
    linewidth=1.5,
    ax=ax,
)

# Vertical axis lines at each dimension for the parallel coord effect
for i in range(len(numeric_cols)):
    ax.axvline(x=i, color=INK_SOFT, linewidth=1.0, alpha=0.4, zorder=0)

# Style
labels = [
    f"Sepal Length\n({df['sepal_length'].min():.1f}–{df['sepal_length'].max():.1f} cm)",
    f"Sepal Width\n({df['sepal_width'].min():.1f}–{df['sepal_width'].max():.1f} cm)",
    f"Petal Length\n({df['petal_length'].min():.1f}–{df['petal_length'].max():.1f} cm)",
    f"Petal Width\n({df['petal_width'].min():.1f}–{df['petal_width'].max():.1f} cm)",
]
ax.set_xticks(range(len(numeric_cols)))
ax.set_xticklabels(labels, fontsize=18, color=INK_SOFT)
ax.tick_params(axis="y", labelsize=16, colors=INK_SOFT)

ax.set_xlabel("", fontsize=20)
ax.set_ylabel("Normalized Value", fontsize=20, color=INK)
ax.set_title("parallel-basic · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.set_ylim(-0.05, 1.05)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)

legend = ax.legend(
    title="Species",
    title_fontsize=18,
    fontsize=16,
    loc="upper right",
    framealpha=0.92,
    facecolor=ELEVATED_BG,
    edgecolor=INK_SOFT,
)
legend.get_title().set_color(INK)
for text in legend.get_texts():
    text.set_color(INK_SOFT)

# Add min/max tick annotations on left axis
for val, label in [(0.0, "Min"), (1.0, "Max")]:
    ax.text(
        -0.08, val, label, transform=ax.get_yaxis_transform(), fontsize=14, color=INK_MUTED, ha="right", va="center"
    )

plt.tight_layout()

# Save
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
