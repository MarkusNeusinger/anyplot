"""pyplots.ai
root-locus-basic: Root Locus Plot for Control Systems
Library: seaborn | Python 3.13
Quality: pending | Created: 2026-03-20
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data - Transfer function G(s) = 1 / [s(s+1)(s+3)]
# Open-loop poles at s = 0, -1, -3; no finite zeros
# Characteristic equation: s^3 + 4s^2 + 3s + K = 0
open_loop_poles = np.array([0.0, -1.0, -3.0])
open_loop_zeros = np.array([])

num_coeffs = np.array([1.0])
den_coeffs = np.poly(open_loop_poles)

gains = np.concatenate(
    [
        np.linspace(0, 0.5, 200),
        np.linspace(0.5, 4.0, 400),
        np.linspace(4.0, 12.0, 400),
        np.linspace(12.0, 50.0, 300),
        np.linspace(50.0, 200.0, 200),
    ]
)

n_poles = len(open_loop_poles)
all_real = []
all_imag = []
all_gain = []
all_branch = []

prev_roots = np.sort(open_loop_poles)

for k in gains:
    char_poly = den_coeffs.copy()
    char_poly[-1] += k * num_coeffs[-1]
    roots = np.roots(char_poly)

    # Sort roots to track branches consistently
    # Match each root to the nearest previous root
    sorted_roots = np.empty_like(roots)
    available = list(range(len(roots)))
    for i in range(len(prev_roots)):
        distances = np.abs(roots[available] - prev_roots[i])
        best = np.argmin(distances)
        sorted_roots[i] = roots[available[best]]
        available.pop(best)
    prev_roots = sorted_roots

    for b in range(n_poles):
        all_real.append(sorted_roots[b].real)
        all_imag.append(sorted_roots[b].imag)
        all_gain.append(k)
        all_branch.append(f"Branch {b + 1}")

df = pd.DataFrame({"Real": all_real, "Imaginary": all_imag, "Gain K": all_gain, "Branch": all_branch})

# Find imaginary axis crossings (stability boundary)
# Routh criterion: K_critical = 12 for this system (s^3 + 4s^2 + 3s + K)
# At K=12: roots cross imaginary axis at s = ±j*sqrt(3)
k_crit = 12.0
char_at_crit = den_coeffs.copy()
char_at_crit[-1] += k_crit * num_coeffs[-1]
crit_roots = np.roots(char_at_crit)
imag_crossings = crit_roots[np.abs(crit_roots.real) < 0.05]

# Real axis segments: to the left of an odd number of real poles/zeros
real_features = np.sort(np.concatenate([open_loop_poles, open_loop_zeros]))

# Plot
sns.set_theme(
    style="ticks",
    context="talk",
    font_scale=1.1,
    rc={"font.family": "sans-serif", "axes.edgecolor": "#888888", "axes.linewidth": 0.8},
)

palette = ["#306998", "#E88C30", "#2D8B57"]
fig, ax = plt.subplots(figsize=(16, 9))

# Plot locus branches using seaborn lineplot
sns.lineplot(
    data=df,
    x="Real",
    y="Imaginary",
    hue="Branch",
    palette=palette,
    linewidth=2.5,
    alpha=0.85,
    sort=False,
    ax=ax,
    legend=True,
)

# Add arrows showing direction of increasing gain on each branch
for b_idx, branch_name in enumerate(df["Branch"].unique()):
    branch_data = df[df["Branch"] == branch_name]
    n_pts = len(branch_data)
    # Place arrow at ~40% along the branch
    arrow_idx = int(n_pts * 0.4)
    if arrow_idx + 1 < n_pts:
        x0 = branch_data.iloc[arrow_idx]["Real"]
        y0 = branch_data.iloc[arrow_idx]["Imaginary"]
        x1 = (
            branch_data.iloc[arrow_idx + 5]["Real"]
            if arrow_idx + 5 < n_pts
            else branch_data.iloc[arrow_idx + 1]["Real"]
        )
        y1 = (
            branch_data.iloc[arrow_idx + 5]["Imaginary"]
            if arrow_idx + 5 < n_pts
            else branch_data.iloc[arrow_idx + 1]["Imaginary"]
        )
        dx = x1 - x0
        dy = y1 - y0
        ax.annotate(
            "",
            xy=(x0 + dx * 0.5, y0 + dy * 0.5),
            xytext=(x0, y0),
            arrowprops={"arrowstyle": "-|>", "color": palette[b_idx], "lw": 2.5, "mutation_scale": 25},
        )

# Mark open-loop poles with × markers
sns.scatterplot(
    x=open_loop_poles.real,
    y=open_loop_poles.imag,
    marker="X",
    s=400,
    color="#1a1a1a",
    edgecolor="white",
    linewidth=1.5,
    zorder=10,
    ax=ax,
    label="Open-loop poles",
)

# Mark imaginary axis crossings (stability boundary)
for crossing in imag_crossings:
    if np.abs(crossing.imag) > 0.01:
        sns.scatterplot(
            x=[crossing.real],
            y=[crossing.imag],
            marker="D",
            s=350,
            color="#DC2626",
            edgecolor="white",
            linewidth=1.5,
            zorder=10,
            ax=ax,
        )

# Label the stability crossings
crossing_y = np.sqrt(3)
ax.annotate(
    f"K = {k_crit:.0f}\njω = ±{crossing_y:.2f}",
    xy=(0.0, crossing_y),
    xytext=(1.5, crossing_y + 1.2),
    fontsize=15,
    color="#DC2626",
    fontweight="medium",
    ha="center",
    arrowprops={"arrowstyle": "->", "color": "#DC2626", "lw": 1.5},
)

# Draw real-axis root locus segments
# Segments: (-inf, -3) and (-1, 0) are part of the root locus
ax.plot([-8, -3], [0, 0], color="#306998", linewidth=4, alpha=0.3, solid_capstyle="round")
ax.plot([-1, 0], [0, 0], color="#306998", linewidth=4, alpha=0.3, solid_capstyle="round")

# Constant damping ratio lines (light reference grid)
theta_vals = np.array([0.1, 0.2, 0.3, 0.5, 0.7, 0.9])
r_line = np.linspace(0, 8, 200)
for zeta in theta_vals:
    angle = np.arccos(zeta)
    x_line = -r_line * np.cos(angle)
    y_line = r_line * np.sin(angle)
    ax.plot(x_line, y_line, color="#cbd5e1", linewidth=0.6, linestyle="--", alpha=0.5)
    ax.plot(x_line, -y_line, color="#cbd5e1", linewidth=0.6, linestyle="--", alpha=0.5)

# Label only select damping ratios at the edge of the plot
for zeta in [0.2, 0.5, 0.7, 0.9]:
    angle = np.arccos(zeta)
    label_r = 4.5
    lx = -label_r * np.cos(angle)
    ly = label_r * np.sin(angle)
    if lx > -7:
        ax.text(lx - 0.15, ly + 0.15, f"ζ={zeta}", fontsize=11, color="#94a3b8", alpha=0.8, rotation=-np.degrees(angle))

# Constant natural frequency semicircles
for wn in [1, 2, 3, 4, 5]:
    theta = np.linspace(np.pi / 2, np.pi, 100)
    ax.plot(wn * np.cos(theta), wn * np.sin(theta), color="#cbd5e1", linewidth=0.6, linestyle=":", alpha=0.4)
    ax.plot(wn * np.cos(theta), -wn * np.sin(theta), color="#cbd5e1", linewidth=0.6, linestyle=":", alpha=0.4)

# Style
ax.set_title("root-locus-basic · seaborn · pyplots.ai", fontsize=24, fontweight="medium", color="#333333", pad=16)
ax.set_xlabel("Real Axis (σ)", fontsize=20, color="#444444")
ax.set_ylabel("Imaginary Axis (jω)", fontsize=20, color="#444444")
ax.tick_params(axis="both", labelsize=16, colors="#555555")
ax.set_xlim(-7, 3)
ax.set_ylim(-5, 5)
ax.set_aspect("equal")
ax.axhline(0, color="#888888", linewidth=0.5, alpha=0.5)
ax.axvline(0, color="#888888", linewidth=0.5, alpha=0.5)
sns.despine(ax=ax)

# Refine legend
legend = ax.get_legend()
legend.set_title("G(s) = 1 / [s(s+1)(s+3)]")
legend.get_title().set_fontsize(14)
for text in legend.get_texts():
    text.set_fontsize(13)
legend.set_frame_on(True)
legend.get_frame().set_alpha(0.9)
legend.get_frame().set_edgecolor("#cccccc")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
