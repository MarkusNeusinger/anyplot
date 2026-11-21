"""anyplot.ai
andrews-curves: Andrews Curves for Multivariate Data
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-15
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette, canonical order (first series always #009E73)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

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

# Column constants
VARIABLES = ["sepal_length", "sepal_width", "petal_length", "petal_width"]  # role: variable_
SPECIES = "species"  # role: category
T = "t"  # role: extra
CURVE = "f(t)"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("measurements.csv")
df = sns.load_dataset("iris")[[*VARIABLES, SPECIES]]

# Plot
# Normalize variables to similar scales so no single variable dominates
z = (df[VARIABLES] - df[VARIABLES].mean()) / df[VARIABLES].std()

# Andrews basis: 1/sqrt(2), sin(t), cos(t), sin(2t), cos(2t), ...
t = np.linspace(-np.pi, np.pi, 400)
basis = np.vstack(
    [np.full_like(t, 1 / np.sqrt(2))]
    + [np.sin((i + 1) // 2 * t) if i % 2 else np.cos(i // 2 * t) for i in range(1, len(VARIABLES))]
)
values = z.to_numpy() @ basis  # one row per observation, one column per t

curves = pd.DataFrame(values, index=df.index, columns=t).rename_axis(columns=T)
curves[SPECIES] = df[SPECIES]
curves["obs"] = df.index
curves = curves.melt(id_vars=[SPECIES, "obs"], var_name=T, value_name=CURVE)

groups = df[SPECIES].unique()
palette = dict(zip(groups, IMPRINT_PALETTE[: len(groups)], strict=False))

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)

# Individual curves: faint, so bundles read as darker bands
sns.lineplot(
    data=curves,
    x=T,
    y=CURVE,
    hue=SPECIES,
    palette=palette,
    units="obs",
    estimator=None,
    alpha=0.3,
    linewidth=0.9,
    legend=False,
    ax=ax,
)
# Bold per-species mean curve over the faint bundle
sns.lineplot(
    data=curves, x=T, y=CURVE, hue=SPECIES, palette=palette, estimator="mean", errorbar=None, linewidth=3.2, ax=ax
)

ax.set_xlabel(T, fontsize=10)
ax.set_ylabel(CURVE, fontsize=10)
ax.set_title("andrews-curves · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.set_xlim(-np.pi, np.pi)
ax.set_xticks([-np.pi, -np.pi / 2, 0, np.pi / 2, np.pi], ["-π", "-π/2", "0", "π/2", "π"])
ax.legend(title="Species (bold = mean)", fontsize=8, title_fontsize=9, loc="upper right", framealpha=0.95)
ax.grid(True, linewidth=0.5)
sns.despine(ax=ax)

fig.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
