""" anyplot.ai
andrews-curves: Andrews Curves for Multivariate Data
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-15
"""

import os

import matplotlib.pyplot as plt
import numpy as np
from sklearn.datasets import load_iris
from sklearn.preprocessing import StandardScaler


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data
np.random.seed(42)
iris = load_iris()
X = iris.data
y = iris.target
species_names = ["Setosa", "Versicolor", "Virginica"]

# Normalize data to prevent dominant variables
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Generate t values from -π to π
t = np.linspace(-np.pi, np.pi, 200)

# Build Andrews curve transformation matrix
# f(t) = x1/sqrt(2) + x2*sin(t) + x3*cos(t) + x4*sin(2t) + ...
n_features = X_scaled.shape[1]
basis = np.zeros((len(t), n_features))
basis[:, 0] = 1 / np.sqrt(2)
for i in range(1, n_features):
    freq = (i + 1) // 2
    if i % 2 == 1:
        basis[:, i] = np.sin(freq * t)
    else:
        basis[:, i] = np.cos(freq * t)

# Compute all Andrews curves: each row of X_scaled dot basis.T gives one curve
curves = X_scaled @ basis.T  # shape: (150, 200)

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Plot Andrews curves for each observation
for i in range(len(curves)):
    ax.plot(t, curves[i], color=IMPRINT[y[i]], alpha=0.4, linewidth=2.5)

# Create legend with sample lines
for idx, species in enumerate(species_names):
    ax.plot([], [], color=IMPRINT[idx], linewidth=3, label=species, alpha=0.4)

# Style
ax.set_xlabel("t (radians)", fontsize=20, color=INK)
ax.set_ylabel("f(t)", fontsize=20, color=INK)
ax.set_title("andrews-curves · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)

# Legend styling
leg = ax.legend(fontsize=16, loc="upper right")
if leg:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    leg.get_frame().set_linewidth(0.8)
    plt.setp(leg.get_texts(), color=INK_SOFT)

# Set x-axis ticks at meaningful positions
ax.set_xticks([-np.pi, -np.pi / 2, 0, np.pi / 2, np.pi])
ax.set_xticklabels(["-π", "-π/2", "0", "π/2", "π"], fontsize=16)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
