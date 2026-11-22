"""anyplot.ai
heatmap-polar: Polar Heatmap for Cyclic Two-Dimensional Data
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-11-22
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Sequential colormap from the Imprint palette (single-sign data)
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", ["#009E73", "#4467A3"])

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
        "grid.alpha": 0.10,
    },
)

# Constants
HOURS_PER_DAY = 24  # the angular axis is a 24-hour clock
LABEL_EVERY = 3  # angular label interval in hours

# Columns: set these to your table's column names
HOUR = "Hour of day"  # role: angular
MONTH = "Month"  # role: radial
DEMAND = "Electricity demand (GW)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("demand.csv")
# Hourly grid electricity demand for each month: winter has heating peaks in the
# morning and evening, summer has one air-conditioning peak in the afternoon.
rng = np.random.default_rng(42)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
hours = np.arange(HOURS_PER_DAY)
rows = []
for m, month in enumerate(months):
    cold = 0.5 + 0.5 * np.cos(2 * np.pi * (m + 0.5) / 12)  # 1 in midwinter, 0 in midsummer
    base = 28 + 6 * np.sin(np.pi * (hours - 5) / 17).clip(0)
    morning = 9 * cold * np.exp(-0.5 * ((hours - 7.5) / 1.6) ** 2)
    evening = 14 * cold * np.exp(-0.5 * ((hours - 18.5) / 2.0) ** 2)
    cooling = 16 * (1 - cold) * np.exp(-0.5 * ((hours - 16) / 3.0) ** 2)
    demand = base + morning + evening + cooling + rng.normal(0, 0.6, HOURS_PER_DAY)
    rows.append(pd.DataFrame({HOUR: hours, MONTH: month, DEMAND: demand}))
df = pd.concat(rows, ignore_index=True)

# Plot: reads only df and the constants above
table = df.pivot_table(index=MONTH, columns=HOUR, values=DEMAND, sort=False)
n_rings, n_hours = table.shape

fig = plt.figure(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax = fig.add_axes([0.11, 0.10, 0.66, 0.66], projection="polar")
ax.set_facecolor(PAGE_BG)

# Cells tile each ring in equal angular widths; the last hour closes onto the first
theta_edges = np.linspace(0, 2 * np.pi, n_hours + 1)
r_edges = np.arange(n_rings + 1, dtype=float)
mesh = ax.pcolormesh(
    theta_edges, r_edges, table.to_numpy(), cmap=imprint_seq, shading="flat", edgecolor=PAGE_BG, linewidth=0.3
)

# Clock orientation: midnight at top, clockwise
ax.set_theta_zero_location("N")
ax.set_theta_direction(-1)

# Hour labels at readable intervals in cyclic order
label_hours = np.arange(0, n_hours, LABEL_EVERY)
ax.set_xticks(2 * np.pi * label_hours / n_hours)
ax.set_xticklabels([f"{h:02d}:00" for h in label_hours], fontsize=9, color=INK_SOFT)
ax.tick_params(axis="x", pad=8)
ax.set_axisbelow(False)

# One label per ring, first category innermost, set on a small panel for legibility
ax.set_ylim(0, n_rings)
ax.set_yticks(np.arange(n_rings) + 0.5)
ax.set_yticklabels(table.index, fontsize=6.5, color=INK, fontweight="medium")
ax.set_rlabel_position(0)
ax.tick_params(axis="y", length=0, pad=0)
for label in ax.get_yticklabels():
    label.set_bbox({"facecolor": PAGE_BG, "edgecolor": "none", "alpha": 0.75, "pad": 0.6})
ax.grid(False)
ax.spines["polar"].set_visible(False)

# Colorbar
cax = fig.add_axes([0.855, 0.24, 0.022, 0.42])
cbar = fig.colorbar(mesh, cax=cax)
cbar.set_label(DEMAND, fontsize=10, color=INK, labelpad=8)
cbar.ax.tick_params(labelsize=9, colors=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)

fig.suptitle("heatmap-polar · python · seaborn · anyplot.ai", fontsize=14, fontweight="medium", color=INK, y=0.96)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
