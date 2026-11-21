""" anyplot.ai
histogram-stacked: Stacked Histogram
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: 83/100 | Updated: 2026-11-21
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
BINS = 20  # number of shared bins for all groups

# Columns: set these to your table's column names
RESPONSE_TIME = "Response Time (ms)"  # role: values
REGION = "Server region"  # role: group
COUNT_LABEL = "Number of Requests"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("requests.csv")
rng = np.random.RandomState(42)
us_east = np.clip(rng.normal(loc=45, scale=12, size=200), 10, 120)
europe = np.clip(rng.normal(loc=65, scale=15, size=180), 15, 140)
asia = np.clip(rng.normal(loc=80, scale=20, size=150), 20, 160)
df = pd.DataFrame(
    {
        RESPONSE_TIME: np.concatenate([us_east, europe, asia]),
        REGION: ["US-East"] * len(us_east) + ["Europe"] * len(europe) + ["Asia-Pacific"] * len(asia),
    }
)

# Plot: reads only df and the constants above
groups = [(name, rows[RESPONSE_TIME].dropna().to_numpy()) for name, rows in df.groupby(REGION, sort=False)]
edges = np.histogram_bin_edges(df[RESPONSE_TIME].dropna(), bins=BINS)

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

ax.hist(
    [values for _, values in groups],
    bins=edges,
    stacked=True,
    color=[IMPRINT_PALETTE[i] for i in range(len(groups))],
    label=[name for name, _ in groups],
    edgecolor=PAGE_BG,
    linewidth=0.4,
)

# Style
ax.set_xlabel(RESPONSE_TIME, fontsize=10, color=INK)
ax.set_ylabel(COUNT_LABEL, fontsize=10, color=INK)
ax.set_title("histogram-stacked · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)

for s in ("top", "right"):
    ax.spines[s].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

ax.set_axisbelow(True)
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)

leg = ax.legend(title=REGION, fontsize=8, title_fontsize=8, loc="upper right", frameon=True)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
leg.get_frame().set_linewidth(0.8)
plt.setp(leg.get_texts(), color=INK_SOFT)
leg.get_title().set_color(INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
