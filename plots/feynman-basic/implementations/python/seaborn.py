""" pyplots.ai
feynman-basic: Feynman Diagram for Particle Interactions
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-07
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Seaborn theming and colorblind-safe palette
sns.set_context("talk", font_scale=1.2)
sns.set_style("white")
pal = sns.color_palette("colorblind")
FERMION = pal[0]  # blue
PHOTON = pal[3]  # red/vermillion
GLUON = pal[2]  # green
BOSON_S = pal[4]  # purple (scalar boson, distinct from photon)

fig, ax = plt.subplots(figsize=(16, 9))

# === Main Diagram: e- e+ -> gamma -> mu- mu+ (s-channel annihilation) ===

v1 = np.array([0.30, 0.58])  # left vertex
v2 = np.array([0.70, 0.58])  # right vertex

e_minus = np.array([0.05, 0.92])
e_plus = np.array([0.05, 0.24])
mu_minus = np.array([0.95, 0.92])
mu_plus = np.array([0.95, 0.24])

# Fermion lines with arrows (annotate needed for arrowheads)
# Convention: particle arrows forward in time, antiparticle arrows backward
arrow_kw = {"arrowstyle": "-|>", "color": FERMION, "lw": 3, "mutation_scale": 25}
# Particles (e-, mu-): arrow forward in time (toward/away from vertex)
ax.annotate("", xy=v1, xytext=e_minus, arrowprops=arrow_kw)  # e- into vertex
ax.annotate("", xy=mu_minus, xytext=v2, arrowprops=arrow_kw)  # mu- out of vertex
# Antiparticles (e+, mu+): arrow backward in time (reversed direction)
ax.annotate("", xy=e_plus, xytext=v1, arrowprops=arrow_kw)  # e+ arrow backward
ax.annotate("", xy=v2, xytext=mu_plus, arrowprops=arrow_kw)  # mu+ arrow backward

# Photon wavy line drawn with sns.lineplot + DataFrame
t = np.linspace(0, 1, 500)
d = v2 - v1
perp = np.array([-d[1], d[0]]) / np.linalg.norm(d)
photon_df = pd.DataFrame(
    {
        "x": v1[0] + t * d[0] + 0.022 * np.sin(2 * np.pi * 8 * t) * perp[0],
        "y": v1[1] + t * d[1] + 0.022 * np.sin(2 * np.pi * 8 * t) * perp[1],
    }
)
sns.lineplot(data=photon_df, x="x", y="y", ax=ax, color=PHOTON, linewidth=3, sort=False, legend=False)

# Vertex dots drawn with sns.scatterplot + DataFrame with hue for vertex type
vertex_df = pd.DataFrame({"x": [v1[0], v2[0]], "y": [v1[1], v2[1]], "vertex": ["QED vertex", "QED vertex"]})
sns.scatterplot(
    data=vertex_df,
    x="x",
    y="y",
    hue="vertex",
    ax=ax,
    palette=[FERMION],
    s=250,
    zorder=5,
    legend=False,
    edgecolor="none",
)

# Particle labels
lkw = {"fontsize": 22, "fontweight": "bold", "ha": "center", "va": "center"}
ax.text(e_minus[0] - 0.03, e_minus[1] + 0.04, r"$e^-$", color=FERMION, **lkw)
ax.text(e_plus[0] - 0.03, e_plus[1] - 0.04, r"$e^+$", color=FERMION, **lkw)
ax.text(0.50, 0.65, r"$\gamma$", color=PHOTON, fontsize=24, fontweight="bold", ha="center")
ax.text(mu_minus[0] + 0.03, mu_minus[1] + 0.04, r"$\mu^-$", color=FERMION, **lkw)
ax.text(mu_plus[0] + 0.03, mu_plus[1] - 0.04, r"$\mu^+$", color=FERMION, **lkw)

# Time arrow
ax.annotate(
    "",
    xy=(0.92, 0.13),
    xytext=(0.08, 0.13),
    arrowprops={"arrowstyle": "-|>", "color": "#999999", "lw": 1.5, "mutation_scale": 18},
)
ax.text(0.50, 0.10, "time", fontsize=16, color="#999999", ha="center", style="italic")

# === Particle Line Styles Reference (all 4 types) ===
ax.plot([0.03, 0.97], [0.05, 0.05], color="#DDDDDD", lw=0.5)

ref_y = -0.06
ref_spans = [(0.04, 0.17), (0.29, 0.42), (0.54, 0.67), (0.79, 0.92)]
ref_names = ["Fermion\n(solid + arrow)", "Photon\n(wavy)", "Gluon\n(curly)", "Scalar Boson\n(dashed)"]
ref_cols = [FERMION, PHOTON, GLUON, BOSON_S]

# 1. Fermion: solid + arrow
ax.annotate(
    "",
    xy=(ref_spans[0][1], ref_y),
    xytext=(ref_spans[0][0], ref_y),
    arrowprops={"arrowstyle": "-|>", "color": FERMION, "lw": 3, "mutation_scale": 20},
)

# 2. Photon: wavy line via sns.lineplot
tr = np.linspace(0, 1, 300)
xs0, xs1 = ref_spans[1]
photon_ref = pd.DataFrame({"x": xs0 + tr * (xs1 - xs0), "y": ref_y + 0.018 * np.sin(2 * np.pi * 4 * tr)})
sns.lineplot(data=photon_ref, x="x", y="y", ax=ax, color=PHOTON, linewidth=3, sort=False, legend=False)

# 3. Gluon: curly/looped line via sns.lineplot (cycloid parameterization)
tg = np.linspace(0, 1, 1000)
xs0, xs1 = ref_spans[2]
span_g = xs1 - xs0
n_coils = 4
r_coil = span_g / (2 * np.pi * n_coils) * 4.0
phase_g = 2 * np.pi * n_coils * tg
gluon_ref = pd.DataFrame(
    {"x": xs0 + tg * span_g + r_coil * np.sin(phase_g), "y": ref_y + r_coil * (1 - np.cos(phase_g))}
)
sns.lineplot(data=gluon_ref, x="x", y="y", ax=ax, color=GLUON, linewidth=3, sort=False, legend=False)

# 4. Scalar boson: dashed line via sns.lineplot
xs0, xs1 = ref_spans[3]
boson_ref = pd.DataFrame({"x": [xs0, xs1], "y": [ref_y, ref_y]})
sns.lineplot(data=boson_ref, x="x", y="y", ax=ax, color=BOSON_S, linewidth=3, linestyle="--", legend=False)

# Reference labels
for (xs0, xs1), name, col in zip(ref_spans, ref_names, ref_cols, strict=True):
    ax.text((xs0 + xs1) / 2, ref_y - 0.03, name, fontsize=16, ha="center", va="top", color=col, fontweight="bold")

# Title and cleanup
ax.set_title("feynman-basic \u00b7 seaborn \u00b7 pyplots.ai", fontsize=24, fontweight="medium", pad=20)
ax.set_xlim(-0.05, 1.05)
ax.set_ylim(-0.20, 1.02)
ax.axis("off")
sns.despine(ax=ax, left=True, bottom=True)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
