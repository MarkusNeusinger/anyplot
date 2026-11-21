"""anyplot.ai
line-styled: Styled Line Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-12
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

# Imprint palette: all eight positions, one per series in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
LINE_STYLES = ["-", "--", ":", "-."]  # solid, dashed, dotted, dash-dot; cycled for more series

# Columns: set these to your table's column names
MONTH = "Month"  # role: x
SERIES = ["Series 1", "Series 2", "Series 3", "Series 4"]  # role: y_

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
# CPU performance benchmarks over twelve months for four processors
np.random.seed(42)
df = pd.DataFrame(
    {
        MONTH: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        SERIES[0]: 100 + np.cumsum(np.random.randn(12) * 3 + 2),
        SERIES[1]: 100 + np.cumsum(np.random.randn(12) * 4 + 1.5),
        SERIES[2]: 100 + np.cumsum(np.random.randn(12) * 2 + 2.5),
        SERIES[3]: 100 + np.cumsum(np.random.randn(12) * 3 + 0.5),
    }
)

# Plot: reads only df and the constants above
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

x = np.arange(len(df))
for i, name in enumerate(SERIES):
    ax.plot(
        x, df[name], linestyle=LINE_STYLES[i % len(LINE_STYLES)], linewidth=2.5, color=IMPRINT_PALETTE[i], label=name
    )

# Style
ax.set_title("line-styled · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xticks(x, df[MONTH])
ax.set_xlabel(MONTH, fontsize=10, color=INK)
ax.set_ylabel("Performance Score", fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)

leg = ax.legend(fontsize=8, loc="upper left", handlelength=4)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

fig.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
