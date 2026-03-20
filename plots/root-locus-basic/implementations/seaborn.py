""" pyplots.ai
root-locus-basic: Root Locus Plot for Control Systems
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 91/100 | Created: 2026-03-20
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

    # Sort roots to track branches consistently via nearest-neighbor matching
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
# Routh criterion: K_critical = 12 for this system
k_crit = 12.0
char_at_crit = den_coeffs.copy()
char_at_crit[-1] += k_crit * num_coeffs[-1]
crit_roots = np.roots(char_at_crit)
imag_crossings = crit_roots[np.abs(crit_roots.real) < 0.05]

# Poles and crossings as DataFrames for seaborn plotting
df_poles = pd.DataFrame({"Real": open_loop_poles.real, "Imaginary": open_loop_poles.imag, "Type": "Open-loop pole"})

crossing_pts = [(c.real, c.imag) for c in imag_crossings if np.abs(c.imag) > 0.01]
df_crossings = pd.DataFrame(crossing_pts, columns=["Real", "Imaginary"])
df_crossings["Type"] = "Stability boundary"

# Build reference grid data as DataFrames for seaborn
r_line = np.linspace(0, 6, 150)
damping_rows = []
for zeta in [0.3, 0.5, 0.7, 0.9]:
    angle = np.arccos(zeta)
    for r in r_line:
        x = -r * np.cos(angle)
        y_pos = r * np.sin(angle)
        damping_rows.append({"Real": x, "Imaginary": y_pos, "zeta": f"ζ={zeta}", "half": "upper"})
        damping_rows.append({"Real": x, "Imaginary": -y_pos, "zeta": f"ζ={zeta}", "half": "lower"})
df_damping = pd.DataFrame(damping_rows)

wn_rows = []
for wn in [2, 4]:
    theta = np.linspace(np.pi / 2, np.pi, 80)
    for t in theta:
        wn_rows.append({"Real": wn * np.cos(t), "Imaginary": wn * np.sin(t), "wn": f"ωn={wn}", "half": "upper"})
        wn_rows.append({"Real": wn * np.cos(t), "Imaginary": -wn * np.sin(t), "wn": f"ωn={wn}", "half": "lower"})
df_wn = pd.DataFrame(wn_rows)

# Plot setup with seaborn theming
sns.set_theme(
    style="ticks",
    context="talk",
    font_scale=1.1,
    rc={"font.family": "sans-serif", "axes.edgecolor": "#999999", "axes.linewidth": 0.8},
)

palette = sns.color_palette(["#306998", "#E88C30", "#2D8B57"])
fig, ax = plt.subplots(figsize=(16, 9))

# Reference grid - damping ratio lines via seaborn
for half in ["upper", "lower"]:
    subset = df_damping[df_damping["half"] == half]
    sns.lineplot(
        data=subset,
        x="Real",
        y="Imaginary",
        hue="zeta",
        palette=["#e2e8f0"] * 4,
        linewidth=0.5,
        linestyle="--",
        alpha=0.45,
        sort=False,
        legend=False,
        ax=ax,
    )

# Reference grid - natural frequency semicircles via seaborn
for half in ["upper", "lower"]:
    subset = df_wn[df_wn["half"] == half]
    sns.lineplot(
        data=subset,
        x="Real",
        y="Imaginary",
        hue="wn",
        palette=["#e2e8f0"] * 2,
        linewidth=0.5,
        linestyle=":",
        alpha=0.35,
        sort=False,
        legend=False,
        ax=ax,
    )

# Real-axis root locus segments
ax.plot([-8, -3], [0, 0], color="#306998", linewidth=4.5, alpha=0.25, solid_capstyle="round")
ax.plot([-1, 0], [0, 0], color="#306998", linewidth=4.5, alpha=0.25, solid_capstyle="round")

# Main locus branches via seaborn lineplot with hue grouping
sns.lineplot(
    data=df,
    x="Real",
    y="Imaginary",
    hue="Branch",
    palette=palette,
    linewidth=2.5,
    alpha=0.9,
    sort=False,
    ax=ax,
    legend=True,
)

# Direction arrows for increasing gain
for b_idx, branch_name in enumerate(df["Branch"].unique()):
    branch_data = df[df["Branch"] == branch_name]
    n_pts = len(branch_data)
    arrow_idx = int(n_pts * 0.4)
    if arrow_idx + 5 < n_pts:
        x0 = branch_data.iloc[arrow_idx]["Real"]
        y0 = branch_data.iloc[arrow_idx]["Imaginary"]
        x1 = branch_data.iloc[arrow_idx + 5]["Real"]
        y1 = branch_data.iloc[arrow_idx + 5]["Imaginary"]
        dx, dy = x1 - x0, y1 - y0
        ax.annotate(
            "",
            xy=(x0 + dx * 0.5, y0 + dy * 0.5),
            xytext=(x0, y0),
            arrowprops={"arrowstyle": "-|>", "color": palette[b_idx], "lw": 2.5, "mutation_scale": 25},
        )

# Open-loop poles via seaborn scatterplot
sns.scatterplot(
    data=df_poles,
    x="Real",
    y="Imaginary",
    hue="Type",
    palette=["#1a1a1a"],
    marker="X",
    s=450,
    edgecolor="white",
    linewidth=1.5,
    zorder=10,
    ax=ax,
    legend=False,
)

# Stability boundary crossings via seaborn scatterplot
sns.scatterplot(
    data=df_crossings,
    x="Real",
    y="Imaginary",
    hue="Type",
    palette=["#DC2626"],
    marker="D",
    s=380,
    edgecolor="white",
    linewidth=1.5,
    zorder=10,
    ax=ax,
    legend=False,
)

# Annotate stability crossings
crossing_y = np.sqrt(3)
ax.annotate(
    f"K = {k_crit:.0f}  |  jω = ±{crossing_y:.2f}",
    xy=(0.0, crossing_y),
    xytext=(2.0, crossing_y + 1.5),
    fontsize=14,
    color="#DC2626",
    fontweight="semibold",
    ha="center",
    bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "#DC2626", "alpha": 0.85, "linewidth": 1},
    arrowprops={"arrowstyle": "->", "color": "#DC2626", "lw": 1.5, "connectionstyle": "arc3,rad=0.15"},
)

# Damping ratio labels (only two, well-spaced)
for zeta in [0.5, 0.9]:
    angle = np.arccos(zeta)
    label_r = 3.8
    lx = -label_r * np.cos(angle)
    ly = label_r * np.sin(angle)
    ax.text(lx - 0.1, ly + 0.2, f"ζ={zeta}", fontsize=11, color="#94a3b8", alpha=0.7, style="italic")

# Axis reference lines
ax.axhline(0, color="#888888", linewidth=0.4, alpha=0.4)
ax.axvline(0, color="#888888", linewidth=0.4, alpha=0.4)

# Style
ax.set_title("root-locus-basic · seaborn · pyplots.ai", fontsize=24, fontweight="medium", color="#2d2d2d", pad=18)
ax.set_xlabel("Real Axis (σ)", fontsize=20, color="#444444")
ax.set_ylabel("Imaginary Axis (jω)", fontsize=20, color="#444444")
ax.tick_params(axis="both", labelsize=16, colors="#555555")
ax.set_xlim(-7, 3.5)
ax.set_ylim(-5.5, 5.5)
ax.set_aspect("equal")
sns.despine(ax=ax)

# Refine legend
legend = ax.get_legend()
legend.set_title("G(s) = 1 / [s(s+1)(s+3)]")
legend.get_title().set_fontsize(14)
legend.get_title().set_fontstyle("italic")
for text in legend.get_texts():
    text.set_fontsize(13)
legend.set_frame_on(True)
legend.get_frame().set_alpha(0.92)
legend.get_frame().set_edgecolor("#dddddd")
legend.get_frame().set_linewidth(0.5)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
