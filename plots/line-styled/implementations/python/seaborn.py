"""anyplot.ai
line-styled: Styled Line Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-05-12
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

# Imprint palette: all eight positions in canonical order, first series is always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants: the four standard dash patterns (on/off lengths in line widths); "" is solid
DASH_PATTERNS = ["", (4, 1.5), (1, 2), (4, 1.5, 1, 1.5)]

# Columns: set these to your table's column names
HOUR = "Hour of day"  # role: x
SERVICE = "Service"  # role: extra
CPU_LOAD = "CPU load (%)"  # role: y_

# Data: replace this block with your own table, for example df = pd.read_csv("cpu_load.csv")
rng = np.random.default_rng(42)
hours = np.arange(0, 24, 0.25)
profiles = {
    "Web API": 40 + 32 * np.exp(-((hours - 13) ** 2) / 18),
    "Database": 28 + 14 * np.exp(-((hours - 20) ** 2) / 8) + 6 * np.exp(-((hours - 9) ** 2) / 6),
    "Cache": 15 + 8 * np.sin(np.pi * (hours - 6) / 12).clip(0),
    "Batch worker": 12 + 55 * np.exp(-(((hours - 2.5 + 12) % 24 - 12) ** 2) / 5),
}
frames = []
for name, base in profiles.items():
    noise = np.convolve(rng.normal(0, 2.2, hours.size + 4), np.ones(5) / 5, mode="valid")
    frames.append(pd.DataFrame({HOUR: hours, SERVICE: name, CPU_LOAD: (base + noise).clip(2, 98)}))
df = pd.concat(frames, ignore_index=True)

# Plot
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
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

services = df[SERVICE].unique()
n_series = len(services)

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
sns.lineplot(
    data=df,
    x=HOUR,
    y=CPU_LOAD,
    hue=SERVICE,
    style=SERVICE,
    palette=IMPRINT_PALETTE[:n_series],
    dashes={name: DASH_PATTERNS[i % len(DASH_PATTERNS)] for i, name in enumerate(services)},
    linewidth=2.2,
    ax=ax,
)

# Style
ax.set_title("line-styled · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel(HOUR, fontsize=10, color=INK)
ax.set_ylabel(CPU_LOAD, fontsize=10, color=INK)
ax.set_xticks(np.arange(0, df[HOUR].max() + 1, 4))
ax.set_xticklabels([f"{int(h):02d}:00" for h in ax.get_xticks()])
ax.set_xlim(df[HOUR].min(), df[HOUR].max())
ax.set_ylim(0, df[CPU_LOAD].max() * 1.12)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)
sns.despine(ax=ax)
ax.legend(title=SERVICE, fontsize=8, title_fontsize=9, loc="upper right", handlelength=4.5, framealpha=0.95)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
