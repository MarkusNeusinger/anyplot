"""anyplot.ai
scatter-complex-plane: Complex Plane Visualization (Argand Diagram)
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 89/100 | Updated: 2026-06-02
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — first series always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

sns.set_theme(
    style="white",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK,
        "grid.alpha": 0.15,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Constants
MARKER_CYCLE = ["D", "X", "o", "s", "^", "v", "P", "*"]  # one marker per category, in order
UNIT_TOLERANCE = 0.01  # a point within this of modulus 1 counts as lying on the unit circle

# Columns: set these to your table's column names
REAL = "Re(z)"  # role: real
IMAGINARY = "Im(z)"  # role: imaginary
LABEL = "Label"  # role: label
CATEGORY = "Category"  # role: extra
MAGNITUDE = "Magnitude |z|"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("complex_numbers.csv")
roots_of_unity = [np.exp(2j * np.pi * k / 3) for k in range(3)]
root_sum = sum(roots_of_unity)
arbitrary_points = [2.5 + 1.5j, -1.8 + 2.2j, 1.0 - 2.0j, -2.5 - 1.0j, 0.5 + 2.8j, -1.2 - 2.5j, 3.0 + 0.0j]
all_points = roots_of_unity + [root_sum] + arbitrary_points

df = pd.DataFrame(
    {
        REAL: [z.real for z in all_points],
        IMAGINARY: [z.imag for z in all_points],
        LABEL: (
            [f"$\\omega_{k}$" for k in range(3)]
            + ["$\\Sigma\\omega_k$"]
            + [f"$z_{{{i + 1}}}$" for i in range(len(arbitrary_points))]
        ),
        CATEGORY: ["Roots of Unity"] * 3 + ["Sum of Roots"] + ["Arbitrary Points"] * len(arbitrary_points),
        MAGNITUDE: [abs(z) for z in all_points],
    }
)

# Plot: reads only df and the constants above
categories = list(df[CATEGORY].unique())
colors = [IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] for i in range(len(categories))]  # repeats past eight categories
cat_colors = dict(zip(categories, colors, strict=True))

# JointGrid — square canvas (2400×2400 px) suits the equal-aspect complex plane
g = sns.JointGrid(data=df, x=REAL, y=IMAGINARY, height=6, ratio=6, space=0.15)
g.figure.set_dpi(400)
g.figure.patch.set_facecolor(PAGE_BG)
ax = g.ax_joint
ax.set_facecolor(PAGE_BG)

# Main scatter with hue, style, and size encoding
sns.scatterplot(
    data=df,
    x=REAL,
    y=IMAGINARY,
    hue=CATEGORY,
    style=CATEGORY,
    size=MAGNITUDE,
    sizes=(150, 450),
    markers=[MARKER_CYCLE[i % len(MARKER_CYCLE)] for i in range(len(categories))],
    palette=colors,
    edgecolor=PAGE_BG,
    linewidth=1.5,
    zorder=5,
    ax=ax,
    legend="full",
)

# Marginal KDE plots — distinctively seaborn, adds statistical context
for cat, color in cat_colors.items():
    subset = df[df[CATEGORY] == cat]
    sns.kdeplot(
        data=subset, x=REAL, color=color, fill=True, alpha=0.3, linewidth=1.5, ax=g.ax_marg_x, warn_singular=False
    )
    sns.kdeplot(
        data=subset, y=IMAGINARY, color=color, fill=True, alpha=0.3, linewidth=1.5, ax=g.ax_marg_y, warn_singular=False
    )

# Marginal axes styling
g.ax_marg_x.set_xlabel("")
g.ax_marg_x.set_ylabel("")
g.ax_marg_y.set_xlabel("")
g.ax_marg_y.set_ylabel("")
g.ax_marg_x.tick_params(left=False, labelleft=False)
g.ax_marg_y.tick_params(bottom=False, labelbottom=False)
g.ax_marg_x.set_facecolor(PAGE_BG)
g.ax_marg_y.set_facecolor(PAGE_BG)

# Vectors from origin to each point
for _, row in df.iterrows():
    ax.annotate(
        "",
        xy=(row[REAL], row[IMAGINARY]),
        xytext=(0, 0),
        arrowprops={"arrowstyle": "->", "color": cat_colors[row[CATEGORY]], "lw": 1.8, "alpha": 0.5},
    )

# Annotations with rectangular form — each box sits beyond its arrow tip, along the vector's direction
for _, row in df.iterrows():
    re_part, im_part = row[REAL], row[IMAGINARY]
    sign = "-" if im_part < 0 else "+"
    rect_form = f"{re_part:.1f}{sign}{abs(im_part):.1f}i".replace("-0.0", "0.0").replace("+-", "-")
    modulus = np.hypot(re_part, im_part)
    ux, uy = (re_part / modulus, im_part / modulus) if modulus > UNIT_TOLERANCE else (0.7, -0.7)
    if (
        abs(modulus - 1) < UNIT_TOLERANCE
    ):  # unit-circle points: turn the label 45° off the ray, clear of the outer points
        ux, uy = (ux - uy) / np.sqrt(2), (ux + uy) / np.sqrt(2)
    ax.annotate(
        f"{row[LABEL]}\n{rect_form}",
        xy=(re_part, im_part),
        xytext=(20 * ux, 20 * uy),
        textcoords="offset points",
        multialignment="center",
        ha="left" if ux > 0.3 else "right" if ux < -0.3 else "center",
        va="bottom" if uy > 0.3 else "top" if uy < -0.3 else "center",
        fontsize=9,
        color=INK,
        fontweight="medium",
        bbox={
            "boxstyle": "round,pad=0.3",
            "facecolor": ELEVATED_BG,
            "edgecolor": INK_SOFT,
            "alpha": 0.9,
            "linewidth": 0.5,
        },
        zorder=6,
    )

# Polygon through the points of unit modulus, ordered by angle
on_circle = df[(df[MAGNITUDE] - 1).abs() < UNIT_TOLERANCE]
if len(on_circle) >= 3:
    order = np.argsort(np.arctan2(on_circle[IMAGINARY], on_circle[REAL]))
    ring = on_circle.iloc[np.append(order, order[0])]
    ax.plot(ring[REAL], ring[IMAGINARY], ls="-", color=IMPRINT_PALETTE[0], lw=2.0, alpha=0.4, zorder=3)

# Unit circle — dashed reference at r=1
theta = np.linspace(0, 2 * np.pi, 200)
ax.plot(np.cos(theta), np.sin(theta), ls="--", color=INK_MUTED, lw=1.8, alpha=0.8, label="Unit Circle")

# Style
ax.set_aspect("equal")

title = "scatter-complex-plane · python · seaborn · anyplot.ai"
n = len(title)
title_fontsize = max(8, round(12 * (67 / n if n > 67 else 1.0)))
# Reserve top margin so suptitle sits above the top marginal without clipping
g.figure.subplots_adjust(top=0.90)
g.figure.suptitle(title, fontsize=title_fontsize, fontweight="medium", color=INK, y=0.97)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)

ax.axhline(0, color=INK_SOFT, lw=1.0, zorder=0)
ax.axvline(0, color=INK_SOFT, lw=1.0, zorder=0)

sns.despine(ax=ax, left=True, bottom=True)
sns.despine(ax=g.ax_marg_x, left=True, bottom=True)
sns.despine(ax=g.ax_marg_y, left=True, bottom=True)

ax.xaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)

limit = max(df[REAL].abs().max(), df[IMAGINARY].abs().max(), 1.0) * 1.6
ax.set_xlim(-limit, limit)
ax.set_ylim(-limit, limit)

ax.set_xlabel(REAL, fontsize=10, labelpad=8, color=INK)
ax.set_ylabel(IMAGINARY, fontsize=10, labelpad=8, color=INK)

# Legend — keep category + unit circle entries, drop the magnitude size entries
handles, leg_labels = ax.get_legend_handles_labels()
wanted = set(categories) | {"Unit Circle"}
keep = [(h, lbl) for h, lbl in zip(handles, leg_labels, strict=False) if lbl in wanted]
ax.legend(
    [h for h, _ in keep],
    [lbl for _, lbl in keep],
    fontsize=8,
    loc="upper right",
    framealpha=0.95,
    edgecolor=INK_SOFT,
    fancybox=True,
    labelcolor=INK,
)

# Save — bbox_inches must stay default (None) to preserve exact 2400×2400 canvas
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
