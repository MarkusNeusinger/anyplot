"""anyplot.ai
line-parametric: Parametric Curve Plot
Library: matplotlib | Python
"""

import os as _os
import sys as _sys


# Prevent this file (matplotlib.py) from shadowing the installed matplotlib package
_here = _os.path.dirname(_os.path.abspath(__file__))
_sys.path = [p for p in _sys.path if _os.path.abspath(p) != _here]
del _sys, _here

import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.colors import LinearSegmentedColormap


# Theme-adaptive chrome tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint sequential colormap — used for continuous parametric parameter t
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", ["#009E73", "#4467A3"])

# Semantic marker colors: green=start (go), red=end (stop) — Imprint positions 1 and 5
COLOR_START = "#009E73"  # Imprint position 1 — brand green
COLOR_END = "#AE3030"  # Imprint position 5 — matte red

# --- Data ---
t_lissajous = np.linspace(0, 2 * np.pi, 1000)
x_lissajous = np.sin(3 * t_lissajous)
y_lissajous = np.sin(2 * t_lissajous)

t_spiral = np.linspace(0, 4 * np.pi, 1000)
x_spiral = t_spiral * np.cos(t_spiral)
y_spiral = t_spiral * np.sin(t_spiral)

# --- Canvas: 3200 × 1800 px (landscape 16:9, hard rule — no deviation) ---
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
for ax in (ax1, ax2):
    ax.set_facecolor(PAGE_BG)

# --- Lissajous panel ---
points_l = np.array([x_lissajous, y_lissajous]).T.reshape(-1, 1, 2)
segments_l = np.concatenate([points_l[:-1], points_l[1:]], axis=1)
lc1 = LineCollection(segments_l, cmap=imprint_seq, linewidth=2.5, capstyle="round")
lc1.set_array(t_lissajous[:-1])
ax1.add_collection(lc1)
ax1.set_xlim(x_lissajous.min() - 0.15, x_lissajous.max() + 0.15)
ax1.set_ylim(y_lissajous.min() - 0.15, y_lissajous.max() + 0.15)
ax1.plot(
    x_lissajous[0],
    y_lissajous[0],
    "o",
    color=COLOR_START,
    markersize=7,
    zorder=5,
    label="Start (t = 0)",
    markeredgecolor=PAGE_BG,
    markeredgewidth=1.0,
)
ax1.plot(
    x_lissajous[-1],
    y_lissajous[-1],
    "s",
    color=COLOR_END,
    markersize=7,
    zorder=5,
    label="End (t = 2π)",
    markeredgecolor=PAGE_BG,
    markeredgewidth=1.0,
)
cb1 = fig.colorbar(lc1, ax=ax1, pad=0.03, aspect=30, shrink=0.85)
cb1.set_label("Parameter t (rad)", fontsize=8, labelpad=6, color=INK_SOFT)
cb1.ax.tick_params(labelsize=7, colors=INK_SOFT)
cb1.outline.set_visible(False)
ax1.annotate(
    "Self-intersection\nat origin (3:2 ratio)",
    xy=(0, 0),
    xytext=(0.45, -0.72),
    fontsize=7,
    color=INK_MUTED,
    fontstyle="italic",
    arrowprops={"arrowstyle": "->", "color": INK_MUTED, "lw": 0.8},
    ha="center",
)

# --- Archimedean Spiral panel ---
points_s = np.array([x_spiral, y_spiral]).T.reshape(-1, 1, 2)
segments_s = np.concatenate([points_s[:-1], points_s[1:]], axis=1)
lc2 = LineCollection(segments_s, cmap=imprint_seq, linewidth=2.5, capstyle="round")
lc2.set_array(t_spiral[:-1])
ax2.add_collection(lc2)
margin = t_spiral.max() * 0.1
ax2.set_xlim(x_spiral.min() - margin, x_spiral.max() + margin)
ax2.set_ylim(y_spiral.min() - margin, y_spiral.max() + margin)
ax2.plot(
    x_spiral[0],
    y_spiral[0],
    "o",
    color=COLOR_START,
    markersize=7,
    zorder=5,
    label="Start (t = 0)",
    markeredgecolor=PAGE_BG,
    markeredgewidth=1.0,
)
ax2.plot(
    x_spiral[-1],
    y_spiral[-1],
    "s",
    color=COLOR_END,
    markersize=7,
    zorder=5,
    label="End (t = 4π)",
    markeredgecolor=PAGE_BG,
    markeredgewidth=1.0,
)
cb2 = fig.colorbar(lc2, ax=ax2, pad=0.03, aspect=30, shrink=0.85)
cb2.set_label("Parameter t (rad)", fontsize=8, labelpad=6, color=INK_SOFT)
cb2.ax.tick_params(labelsize=7, colors=INK_SOFT)
cb2.outline.set_visible(False)
ax2.annotate(
    "Radius grows\nlinearly with t",
    xy=(x_spiral[750], y_spiral[750]),
    xytext=(6, 8),
    fontsize=7,
    color=INK_MUTED,
    fontstyle="italic",
    arrowprops={"arrowstyle": "->", "color": INK_MUTED, "lw": 0.8},
    ha="center",
)

# --- Per-panel styling: equal aspect, spines, labels, legend, grid ---
panel_info = [
    (ax1, "Lissajous Figure", "x(t) = sin(3t)", "y(t) = sin(2t)"),
    (ax2, "Archimedean Spiral", "x(t) = t · cos(t)", "y(t) = t · sin(t)"),
]
for ax, title_text, xlabel, ylabel in panel_info:
    ax.set_aspect("equal")
    ax.set_xlabel(xlabel, fontsize=10, color=INK)
    ax.set_ylabel(ylabel, fontsize=10, color=INK)
    ax.set_title(title_text, fontsize=12, fontweight="medium", pad=8, color=INK)
    ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
    for spine in ax.spines.values():
        spine.set_visible(False)
    leg = ax.legend(fontsize=8, loc="lower right", frameon=True, fancybox=False, framealpha=0.9)
    if leg:
        leg.get_frame().set_facecolor(ELEVATED_BG)
        leg.get_frame().set_edgecolor(INK_SOFT)
        plt.setp(leg.get_texts(), color=INK_SOFT)
    ax.grid(True, alpha=0.15, linewidth=0.6, color=INK)

# --- Figure title ---
title = "line-parametric · python · matplotlib · anyplot.ai"
fig.suptitle(title, fontsize=12, fontweight="medium", y=0.98, color=INK)

plt.tight_layout(rect=[0, 0, 1, 0.94])
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
