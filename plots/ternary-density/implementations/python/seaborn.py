"""anyplot.ai
ternary-density: Ternary Density Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-19
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.patches import Polygon
from scipy.ndimage import maximum_filter
from scipy.stats import gaussian_kde


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Imprint sequential colormap for density (single polarity)
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", ["#009E73", "#4467A3"])

sns.set_theme(style="ticks", rc={"figure.facecolor": PAGE_BG, "axes.facecolor": PAGE_BG, "text.color": INK})

# Constants
GRID_STEP = 0.1  # ternary grid every 10 %
N_PEAKS = 3  # density peaks that get a label

# Columns: set these to your table's column names
SAND = "Sand (%)"  # role: component_a
SILT = "Silt (%)"  # role: component_b
CLAY = "Clay (%)"  # role: component_c

# Data: replace this block with your own table, for example df = pd.read_csv("soil.csv")
rng = np.random.default_rng(42)

# Cluster 1: sandy soils
sand1 = rng.beta(5, 2, 200) * 70 + 25
silt1 = rng.beta(2, 3, 200) * (100 - sand1) * 0.6
clay1 = 100 - sand1 - silt1

# Cluster 2: silty soils
silt2 = rng.beta(5, 2, 150) * 60 + 30
sand2 = rng.beta(2, 3, 150) * (100 - silt2) * 0.5
clay2 = 100 - sand2 - silt2

# Cluster 3: clay-rich soils
clay3 = rng.beta(4, 2, 150) * 50 + 30
sand3 = rng.beta(2, 3, 150) * (100 - clay3) * 0.4
silt3 = 100 - clay3 - sand3

df = pd.DataFrame(
    {
        SAND: np.concatenate([sand1, sand2, sand3]),
        SILT: np.concatenate([silt1, silt2, silt3]),
        CLAY: np.concatenate([clay1, clay2, clay3]),
    }
)

# Plot: reads only df and the constants above
H = np.sqrt(3) / 2  # height of the unit equilateral triangle
vertices = np.array([[0, 0], [1, 0], [0.5, H]])

# Ternary to Cartesian: first component bottom-left, second bottom-right, third top
shares = df[[SAND, SILT, CLAY]].dropna().pipe(lambda t: t.div(t.sum(axis=1), axis=0))
x = shares[SILT] + 0.5 * shares[CLAY]
y = H * shares[CLAY]

fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)
ax.set_position([0.02, 0.03, 0.80, 0.86])
triangle_clip = Polygon(vertices, transform=ax.transData)

# Ternary grid under the density: three families parallel to the sides
for frac in np.arange(GRID_STEP, 1 - GRID_STEP / 2, GRID_STEP):
    gkw = {"color": INK_SOFT, "alpha": 0.25, "linewidth": 0.5, "zorder": 1}
    ax.plot([0.5 * frac, 1 - 0.5 * frac], [H * frac, H * frac], **gkw)
    ax.plot([frac, 0.5 * (1 + frac)], [0, H * (1 - frac)], **gkw)
    ax.plot([1 - frac, 0.5 * (1 - frac)], [0, H * (1 - frac)], **gkw)

# KDE density fill, clipped to the triangle
sns.kdeplot(x=x, y=y, fill=True, cmap=imprint_seq, levels=20, alpha=0.85, ax=ax, thresh=0.02, zorder=5)
for collection in ax.collections:
    collection.set_clip_path(triangle_clip)

# Contour lines of the same density surface
n_fill = len(ax.collections)
sns.kdeplot(x=x, y=y, levels=10, color=INK, linewidths=0.9, alpha=0.8, ax=ax, zorder=6)
for collection in ax.collections[n_fill:]:
    collection.set_clip_path(triangle_clip)

# Triangle boundary
ax.add_patch(Polygon(vertices, fill=False, edgecolor=INK, linewidth=1.6, zorder=15))

# Colorbar: relative density
cax = fig.add_axes([0.84, 0.30, 0.022, 0.36])
sm = plt.cm.ScalarMappable(cmap=imprint_seq, norm=Normalize(vmin=0, vmax=1))
sm.set_array([])
cbar = fig.colorbar(sm, cax=cax)
cbar.set_label("Relative Density", fontsize=10, labelpad=6, color=INK)
cbar.ax.yaxis.set_label_position("left")
cbar.set_ticks([0, 0.5, 1.0])
cbar.ax.set_yticklabels(["Low", "Medium", "High"])
cbar.ax.tick_params(colors=INK_SOFT, labelsize=8)
cbar.outline.set_edgecolor(INK_SOFT)
cbar.outline.set_linewidth(0.8)

# Vertex labels from the column names
ax.text(0, -0.07, SAND, ha="center", va="top", fontsize=12, fontweight="bold", color=INK)
ax.text(1, -0.07, SILT, ha="center", va="top", fontsize=12, fontweight="bold", color=INK)
ax.text(0.5, H + 0.05, CLAY, ha="center", va="bottom", fontsize=12, fontweight="bold", color=INK)

# Percentage tick labels along each edge
for frac in np.arange(2 * GRID_STEP, 1 - GRID_STEP / 2, 2 * GRID_STEP):
    label = f"{round(frac * 100)}"
    ax.text(frac, -0.025, label, ha="center", va="top", fontsize=8, color=INK_SOFT)
    ax.text(0.5 * frac - 0.025, H * frac, label, ha="right", va="center", fontsize=8, color=INK_SOFT)
    ax.text(1 - 0.5 * frac + 0.025, H * frac, label, ha="left", va="center", fontsize=8, color=INK_SOFT)

# Label the strongest density peaks, named by their dominant component
gx, gy = np.meshgrid(np.linspace(0, 1, 160), np.linspace(0, H, 140))
density = gaussian_kde(np.vstack([x, y]))(np.vstack([gx.ravel(), gy.ravel()])).reshape(gx.shape)
clay_g = gy / H
inside = (clay_g >= 0) & (gx >= 0.5 * clay_g) & (gx <= 1 - 0.5 * clay_g)
density = np.where(inside, density, 0)
is_peak = (density == maximum_filter(density, size=25)) & (density > 0.1 * density.max())
peak_idx = np.argwhere(is_peak)
peak_idx = peak_idx[np.argsort(-density[tuple(peak_idx.T)])][:N_PEAKS]
names = {SAND: "Sandy soils", SILT: "Silty soils", CLAY: "Clay-rich soils"}
for r, c in peak_idx:
    clay_s = gy[r, c] / H
    silt_s = gx[r, c] - 0.5 * clay_s
    dominant = max({SAND: 1 - silt_s - clay_s, SILT: silt_s, CLAY: clay_s}.items(), key=lambda kv: kv[1])[0]
    ax.text(
        gx[r, c],
        gy[r, c],
        names[dominant].replace(" ", "\n", 1),
        ha="center",
        va="center",
        fontsize=8,
        fontweight="bold",
        color=INK,
        zorder=20,
        bbox={"boxstyle": "round,pad=0.3", "facecolor": PAGE_BG, "edgecolor": INK_SOFT, "alpha": 0.8},
    )

# Style
ax.set_title(
    "Soil Composition · ternary-density · python · seaborn · anyplot.ai",
    fontsize=10.5,
    fontweight="medium",
    color=INK,
    pad=8,
)
ax.set_xlim(-0.12, 1.12)
ax.set_ylim(-0.12, H + 0.1)
ax.set_aspect("equal")
ax.axis("off")

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
