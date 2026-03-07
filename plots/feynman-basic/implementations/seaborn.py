"""pyplots.ai
feynman-basic: Feynman Diagram for Particle Interactions
Library: seaborn | Python 3.13
Quality: pending | Created: 2026-03-07
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.lines import Line2D


# Setup
sns.set_context("talk", font_scale=1.2)
sns.set_style("white")
fig, ax = plt.subplots(figsize=(16, 9))

# Vertices for e- e+ -> gamma -> mu- mu+ (s-channel annihilation)
v1 = np.array([0.3, 0.5])
v2 = np.array([0.7, 0.5])

# Fermion endpoints
e_minus_start = np.array([0.05, 0.85])
e_plus_start = np.array([0.05, 0.15])
mu_minus_end = np.array([0.95, 0.85])
mu_plus_end = np.array([0.95, 0.15])

# Arrow style for fermion lines
fermion_arrow = {"arrowstyle": "-|>", "color": "#306998", "lw": 3, "mutation_scale": 25}

# Draw incoming fermions (arrows toward vertex)
ax.annotate("", xy=v1, xytext=e_minus_start, arrowprops=fermion_arrow)
ax.annotate("", xy=v1, xytext=e_plus_start, arrowprops=fermion_arrow)

# Draw outgoing fermions (arrows away from vertex)
ax.annotate("", xy=mu_minus_end, xytext=v2, arrowprops=fermion_arrow)
ax.annotate("", xy=mu_plus_end, xytext=v2, arrowprops=fermion_arrow)

# Draw virtual photon (wavy line between vertices)
n_waves = 8
t = np.linspace(0, 1, 500)
direction = v2 - v1
length = np.linalg.norm(direction)
perp = np.array([-direction[1], direction[0]]) / length
amplitude = 0.025
wave_x = v1[0] + t * direction[0] + amplitude * np.sin(2 * np.pi * n_waves * t) * perp[0]
wave_y = v1[1] + t * direction[1] + amplitude * np.sin(2 * np.pi * n_waves * t) * perp[1]
ax.plot(wave_x, wave_y, color="#D4442A", lw=3, solid_capstyle="round")

# Vertex dots
for v in [v1, v2]:
    ax.plot(v[0], v[1], "o", color="#306998", markersize=12, zorder=5)

# Particle labels
label_kwargs = {"fontsize": 22, "fontweight": "bold", "ha": "center", "va": "center"}
ax.text(e_minus_start[0] - 0.02, e_minus_start[1] + 0.06, r"$e^-$", color="#306998", **label_kwargs)
ax.text(e_plus_start[0] - 0.02, e_plus_start[1] - 0.06, r"$e^+$", color="#306998", **label_kwargs)
ax.text(0.5, 0.57, r"$\gamma$", color="#D4442A", fontsize=24, fontweight="bold", ha="center", va="bottom")
ax.text(mu_minus_end[0] + 0.02, mu_minus_end[1] + 0.06, r"$\mu^-$", color="#306998", **label_kwargs)
ax.text(mu_plus_end[0] + 0.02, mu_plus_end[1] - 0.06, r"$\mu^+$", color="#306998", **label_kwargs)

# Time axis indicator
ax.annotate(
    "",
    xy=(0.92, 0.02),
    xytext=(0.08, 0.02),
    arrowprops={"arrowstyle": "-|>", "color": "#999999", "lw": 1.5, "mutation_scale": 18},
)
ax.text(0.5, 0.0, "time", fontsize=16, color="#999999", ha="center", va="bottom", style="italic")

# Legend for line styles
legend_elements = [
    Line2D([0], [0], color="#306998", lw=3, label="Fermion (solid + arrow)"),
    Line2D([0], [0], color="#D4442A", lw=3, label="Photon (wavy)"),
]
ax.legend(handles=legend_elements, loc="upper center", fontsize=14, frameon=False, ncol=2)

# Style
ax.set_title("feynman-basic \u00b7 seaborn \u00b7 pyplots.ai", fontsize=24, fontweight="medium", pad=20)
ax.set_xlim(-0.05, 1.05)
ax.set_ylim(-0.08, 1.05)
ax.set_aspect("equal")
ax.axis("off")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
