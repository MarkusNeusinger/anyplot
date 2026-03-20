"""pyplots.ai
bifurcation-basic: Bifurcation Diagram for Dynamical Systems
Library: seaborn | Python 3.13
Quality: pending | Created: 2026-03-20
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Data - Logistic map: x(n+1) = r * x(n) * (1 - x(n))
r_values = np.linspace(2.5, 4.0, 5000)
transient = 300
n_plot = 200

r_all = np.empty(len(r_values) * n_plot)
x_all = np.empty(len(r_values) * n_plot)

idx = 0
for r in r_values:
    x = 0.5
    for _ in range(transient):
        x = r * x * (1.0 - x)
    for _ in range(n_plot):
        x = r * x * (1.0 - x)
        r_all[idx] = r
        x_all[idx] = x
        idx += 1

# Plot
sns.set_theme(
    style="ticks",
    context="talk",
    font_scale=1.1,
    rc={"font.family": "sans-serif", "axes.edgecolor": "#888888", "axes.linewidth": 0.8},
)

fig, ax = plt.subplots(figsize=(16, 9))

ax.plot(r_all, x_all, ",", color="#102a43", alpha=0.6, rasterized=True)

# Style
ax.set_title("bifurcation-basic · seaborn · pyplots.ai", fontsize=24, fontweight="medium", color="#333333", pad=16)
ax.set_xlabel("Growth Rate (r)", fontsize=20, color="#444444")
ax.set_ylabel("Steady-State Population (x)", fontsize=20, color="#444444")
ax.set_xlim(2.5, 4.0)
ax.set_ylim(0, 1)
ax.tick_params(axis="both", labelsize=16, colors="#555555")
sns.despine(ax=ax)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
