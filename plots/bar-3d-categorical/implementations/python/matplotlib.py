""" anyplot.ai
bar-3d-categorical: 3D Bar Chart for Categorical Comparison
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: 80/100 | Updated: 2026-11-21
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, Normalize
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", ["#009E73", "#4467A3"])

# Columns: set these to your table's column names
FIELD = "Field"  # role: x_category
FERTILIZER = "Fertilizer"  # role: y_category
YIELD = "Wheat yield (t/ha)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("yields.csv")
fields = ["North Field", "River Field", "Hill Field", "Orchard Field"]
fertilizers = ["Control", "Nitrogen", "Phosphate", "Compost"]
yields = [[3.1, 6.4, 4.2, 5.1], [3.6, 5.8, 4.6, 5.7], [2.4, 4.5, 3.3, 4.1], [3.9, 7.2, 5.0, 6.3]]
df = pd.DataFrame(
    {
        FIELD: [f for f in fields for _ in fertilizers],
        FERTILIZER: fertilizers * len(fields),
        YIELD: [v for row in yields for v in row],
    }
)

# Plot: reads only df and the constants above
table = df.pivot_table(index=FIELD, columns=FERTILIZER, values=YIELD, sort=False)
top = np.nanmax(table.to_numpy())
norm = Normalize(vmin=np.nanmin(table.to_numpy()), vmax=top)
bar_size = 0.55

fig = plt.figure(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax = fig.add_subplot(111, projection="3d", computed_zorder=False)
ax.set_facecolor(PAGE_BG)
fig.subplots_adjust(left=0.0, right=0.86, bottom=0.04, top=0.93)

for pane in (ax.xaxis.pane, ax.yaxis.pane, ax.zaxis.pane):
    pane.fill = False
    pane.set_edgecolor(INK_SOFT)
    pane.set_alpha(0.4)
ax.grid(True, alpha=0.15, linewidth=0.4, color=INK)

for i, field in enumerate(table.index):
    for j, fert in enumerate(table.columns):
        value = table.loc[field, fert]
        if np.isnan(value):
            continue
        ax.bar3d(
            i - bar_size / 2,
            j - bar_size / 2,
            0,
            bar_size,
            bar_size,
            value,
            color=imprint_seq(norm(value)),
            alpha=0.92,
            shade=True,
        )
        ax.text(i, j, value + top * 0.03, f"{value:.1f}", ha="center", va="bottom", fontsize=7, color=INK, zorder=10)

ax.view_init(elev=42, azim=-58)
ax.set_zlim(0, top * 1.2)

ax.set_xticks(range(len(table.index)), table.index, fontsize=6.5, color=INK_SOFT)
ax.set_yticks(range(len(table.columns)), table.columns, fontsize=6.5, color=INK_SOFT)
ax.tick_params(axis="z", labelsize=7, colors=INK_SOFT)
ax.tick_params(axis="x", pad=-3)
ax.tick_params(axis="y", pad=-3)
ax.set_xlabel(FIELD, fontsize=9, color=INK, labelpad=6)
ax.set_ylabel(FERTILIZER, fontsize=9, color=INK, labelpad=6)
ax.set_zlabel(YIELD, fontsize=9, color=INK, labelpad=2)

title = "Crop Yield by Field & Fertilizer · bar-3d-categorical · python · matplotlib · anyplot.ai"
ax.set_title(title, fontsize=max(8, round(12 * 67 / len(title))), fontweight="medium", color=INK, pad=4)

# Colorbar in its own axes
cbar_ax = fig.add_axes([0.89, 0.2, 0.02, 0.6])
sm = plt.cm.ScalarMappable(cmap=imprint_seq, norm=norm)
sm.set_array([])
cbar = fig.colorbar(sm, cax=cbar_ax)
cbar.set_label(YIELD, fontsize=9, color=INK)
cbar.ax.tick_params(labelsize=7, colors=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
