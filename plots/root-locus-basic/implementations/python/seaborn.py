""" anyplot.ai
root-locus-basic: Root Locus Plot for Control Systems
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 92/100 | Updated: 2026-06-17
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
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — canonical order, first series always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRANCH_PALETTE = IMPRINT_PALETTE[:3]  # three branches
STABILITY_RED = IMPRINT_PALETTE[4]  # matte red — stability boundary semantic role

# Data — Transfer function G(s) = 1 / [s(s+1)(s+3)]
# Open-loop poles at s = 0, -1, -3; no finite zeros
open_loop_poles = np.array([0.0, -1.0, -3.0])
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

prev_roots = np.sort(open_loop_poles).astype(complex)

for k in gains:
    char_poly = den_coeffs.copy()
    char_poly[-1] += k * num_coeffs[-1]
    roots = np.roots(char_poly)

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

# Imaginary axis crossings — K_critical = 12 by Routh criterion
k_crit = 12.0
char_at_crit = den_coeffs.copy()
char_at_crit[-1] += k_crit * num_coeffs[-1]
crit_roots = np.roots(char_at_crit)
imag_crossings = crit_roots[np.abs(crit_roots.real) < 0.05]

df_poles = pd.DataFrame({"Real": open_loop_poles.real, "Imaginary": np.zeros_like(open_loop_poles)})

crossing_pts = [(c.real, c.imag) for c in imag_crossings if np.abs(c.imag) > 0.01]
df_crossings = pd.DataFrame(crossing_pts, columns=["Real", "Imaginary"])

# Constant damping ratio reference lines
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

# Constant natural frequency semicircles
wn_rows = []
for wn in [2, 4]:
    theta = np.linspace(np.pi / 2, np.pi, 80)
    for t in theta:
        wn_rows.append({"Real": wn * np.cos(t), "Imaginary": wn * np.sin(t), "wn": f"ωn={wn}", "half": "upper"})
        wn_rows.append({"Real": wn * np.cos(t), "Imaginary": -wn * np.sin(t), "wn": f"ωn={wn}", "half": "lower"})
df_wn = pd.DataFrame(wn_rows)

# Plot — square canvas (2400 × 2400 px) suits equal-aspect root locus geometry
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
        "grid.alpha": 0.12,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Reference grid — damping ratio lines
for half in ["upper", "lower"]:
    subset = df_damping[df_damping["half"] == half]
    sns.lineplot(
        data=subset,
        x="Real",
        y="Imaginary",
        hue="zeta",
        palette=[INK_MUTED] * 4,
        linewidth=0.6,
        linestyle="--",
        alpha=0.35,
        sort=False,
        legend=False,
        ax=ax,
    )

# Reference grid — natural frequency semicircles
for half in ["upper", "lower"]:
    subset = df_wn[df_wn["half"] == half]
    sns.lineplot(
        data=subset,
        x="Real",
        y="Imaginary",
        hue="wn",
        palette=[INK_MUTED] * 2,
        linewidth=0.6,
        linestyle=":",
        alpha=0.3,
        sort=False,
        legend=False,
        ax=ax,
    )

# Real-axis locus segments (highlighted as thick semi-transparent bands)
ax.plot([-8, -3], [0, 0], color=BRANCH_PALETTE[0], linewidth=6, alpha=0.18, solid_capstyle="round")
ax.plot([-1, 0], [0, 0], color=BRANCH_PALETTE[0], linewidth=6, alpha=0.18, solid_capstyle="round")

# Main locus branches — seaborn lineplot with hue grouping
sns.lineplot(
    data=df,
    x="Real",
    y="Imaginary",
    hue="Branch",
    palette=BRANCH_PALETTE,
    linewidth=2.5,
    alpha=0.9,
    sort=False,
    legend=True,
    ax=ax,
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
            arrowprops={"arrowstyle": "-|>", "color": BRANCH_PALETTE[b_idx], "lw": 2.5, "mutation_scale": 20},
        )

# Open-loop poles (×) — theme-adaptive ink color
sns.scatterplot(
    data=df_poles,
    x="Real",
    y="Imaginary",
    color=INK,
    marker="X",
    s=350,
    edgecolor=PAGE_BG,
    linewidth=1.5,
    zorder=10,
    legend=False,
    ax=ax,
)

# Stability boundary crossings (◆) — matte red semantic anchor
sns.scatterplot(
    data=df_crossings,
    x="Real",
    y="Imaginary",
    color=STABILITY_RED,
    marker="D",
    s=300,
    edgecolor=PAGE_BG,
    linewidth=1.5,
    zorder=10,
    legend=False,
    ax=ax,
)

# Annotate stability crossing
crossing_y = np.sqrt(3)
ax.annotate(
    f"K = {k_crit:.0f}  |  jω = ±{crossing_y:.2f}",
    xy=(0.0, crossing_y),
    xytext=(2.5, crossing_y + 1.8),
    fontsize=8,
    color=STABILITY_RED,
    fontweight="bold",
    ha="center",
    bbox={
        "boxstyle": "round,pad=0.3",
        "facecolor": ELEVATED_BG,
        "edgecolor": STABILITY_RED,
        "alpha": 0.9,
        "linewidth": 1,
    },
    arrowprops={"arrowstyle": "->", "color": STABILITY_RED, "lw": 1.5, "connectionstyle": "arc3,rad=0.15"},
)

# Damping ratio labels
for zeta in [0.5, 0.9]:
    angle = np.arccos(zeta)
    label_r = 4.2
    lx = -label_r * np.cos(angle)
    ly = label_r * np.sin(angle)
    ax.text(lx - 0.1, ly + 0.2, f"ζ={zeta}", fontsize=8, color=INK_MUTED, alpha=0.85, style="italic")

# Axis reference lines (real and imaginary axes)
ax.axhline(0, color=INK_SOFT, linewidth=0.5, alpha=0.5)
ax.axvline(0, color=INK_SOFT, linewidth=0.5, alpha=0.5)

# Style
title = "root-locus-basic · python · seaborn · anyplot.ai"
n = len(title)
ratio = 67 / n if n > 67 else 1.0
title_fontsize = max(8, round(12 * ratio))

ax.set_title(title, fontsize=title_fontsize, color=INK, pad=12)
ax.set_xlabel("Real Axis (σ)", fontsize=10, color=INK)
ax.set_ylabel("Imaginary Axis (jω)", fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.set_xlim(-7, 3.5)
ax.set_ylim(-5.5, 5.5)
ax.set_aspect("equal")
sns.despine(ax=ax)

# Refine legend with transfer function context
legend = ax.get_legend()
if legend:
    legend.set_title("G(s) = 1 / [s(s+1)(s+3)]")
    legend.get_title().set_fontsize(8)
    legend.get_title().set_fontstyle("italic")
    legend.get_title().set_color(INK)
    for text in legend.get_texts():
        text.set_fontsize(8)
        text.set_color(INK_SOFT)
    legend.set_frame_on(True)
    legend.get_frame().set_facecolor(ELEVATED_BG)
    legend.get_frame().set_edgecolor(INK_SOFT)
    legend.get_frame().set_linewidth(0.5)

# Save
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
plt.close()
