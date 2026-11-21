"""anyplot.ai
andrews-curves: Andrews Curves for Multivariate Data
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-15
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.datasets import load_iris
from sklearn.preprocessing import StandardScaler


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
VARIABLES = ["Sepal length (cm)", "Sepal width (cm)", "Petal length (cm)", "Petal width (cm)"]  # role: variable_
SPECIES = "Species"  # role: category

# Data: replace this block with your own table, for example df = pd.read_csv("iris.csv")
iris = load_iris()
df = pd.DataFrame(iris.data, columns=VARIABLES)
df[SPECIES] = pd.Categorical.from_codes(iris.target, ["Setosa", "Versicolor", "Virginica"]).astype(str)

# Plot: reads only df and the constants above
# Normalize variables so no single one dominates the curves
scaled = StandardScaler().fit_transform(df[VARIABLES].to_numpy(dtype=float))

# One full period of the Fourier basis
t = np.linspace(-np.pi, np.pi, 200)

# f(t) = x1/sqrt(2) + x2*sin(t) + x3*cos(t) + x4*sin(2t) + ...
basis = np.zeros((len(t), len(VARIABLES)))
basis[:, 0] = 1 / np.sqrt(2)
for i in range(1, len(VARIABLES)):
    freq = (i + 1) // 2
    basis[:, i] = np.sin(freq * t) if i % 2 == 1 else np.cos(freq * t)

# One curve per observation: shape (n_observations, len(t))
curves = scaled @ basis.T

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

for i, (species, rows) in enumerate(df.groupby(SPECIES, sort=False)):
    color = IMPRINT_PALETTE[i]
    for curve in curves[rows.index.to_numpy()]:
        ax.plot(t, curve, color=color, alpha=0.4, linewidth=1.25)
    ax.plot([], [], color=color, linewidth=2, label=species, alpha=0.8)

# Style
ax.set_title("andrews-curves · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel("t (radians)", fontsize=10, color=INK)
ax.set_ylabel("f(t)", fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax.set_xlim(t.min(), t.max())
ax.set_xticks([t.min(), t.min() / 2, 0, t.max() / 2, t.max()], ["-π", "-π/2", "0", "π/2", "π"])

leg = ax.legend(title=SPECIES, fontsize=8, title_fontsize=8, loc="upper right")
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
leg.get_frame().set_linewidth(0.8)
plt.setp(leg.get_texts(), color=INK_SOFT)
leg.get_title().set_color(INK_SOFT)

fig.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
