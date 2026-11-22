"""anyplot.ai
windrose-basic: Wind Rose Chart
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-05-07
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

# Imprint palette, in canonical order: one color per speed bin
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

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
        "grid.color": INK_SOFT,
        "grid.alpha": 0.25,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Constants
SPEED_EDGES = [0, 3, 6, 10, 15, np.inf]
SPEED_LABELS = ["0-3 m/s", "3-6 m/s", "6-10 m/s", "10-15 m/s", "15+ m/s"]
COMPASS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]

# Columns
DIRECTION = "direction"  # role: direction
SPEED_BIN = "speed_bin"  # role: speed
FREQUENCY = "frequency"  # role: frequency

# Data
rng = np.random.default_rng(42)
n_obs = 8760

# Prevailing winds from the SW, with weaker NE and W components
direction_weights = np.zeros(360)
direction_weights[200:240] = 3.0
direction_weights[30:60] = 1.5
direction_weights[260:290] = 1.0
direction_weights += 0.2
direction_weights /= direction_weights.sum()

wind_dir = (rng.choice(360, size=n_obs, p=direction_weights) + rng.uniform(-10, 10, n_obs)) % 360

# Stronger winds from the prevailing sectors (Weibull-distributed speeds)
sw = (wind_dir >= 200) & (wind_dir <= 240)
ne = (wind_dir >= 30) & (wind_dir <= 60)
shape = np.where(sw, 2.2, np.where(ne, 2.0, 1.8))
scale = np.where(sw, 8.0, np.where(ne, 6.0, 4.0))
offset = np.where(sw, 2.0, np.where(ne, 1.0, 0.5))
wind_speed = np.clip(rng.weibull(shape) * scale + offset, 0, 25)

# Frequency of observations per direction sector (centered on its compass point) and speed bin, in percent
sector_width = 360 / len(COMPASS)
sector = (((wind_dir + sector_width / 2) % 360) // sector_width).astype(int)
speed_bin = pd.cut(wind_speed, bins=SPEED_EDGES, labels=SPEED_LABELS, right=False)
freq = pd.crosstab(sector, speed_bin, normalize=True) * 100
freq = freq.reindex(index=range(len(COMPASS)), columns=SPEED_LABELS, fill_value=0)
df = freq.rename_axis(index=DIRECTION, columns=SPEED_BIN).stack().rename(FREQUENCY).reset_index()
df[DIRECTION] = df[DIRECTION] * sector_width

# Plot
table = df.pivot(index=DIRECTION, columns=SPEED_BIN, values=FREQUENCY).sort_index().fillna(0)
speed_order = list(df[SPEED_BIN].drop_duplicates())
angles = table.index.to_numpy(dtype=float)
n_sectors = len(table)
sector_deg = np.diff(angles).min() if n_sectors > 1 else 360.0

fig = plt.figure(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax = fig.add_subplot(111, projection="polar")
ax.set_facecolor(PAGE_BG)
ax.set_theta_zero_location("N")
ax.set_theta_direction(-1)

theta = np.deg2rad(angles)
colors = IMPRINT_PALETTE[: len(speed_order)]

bottom = np.zeros(n_sectors)
for label, color in zip(speed_order, colors, strict=False):
    ax.bar(
        theta,
        table[label].to_numpy(),
        width=np.deg2rad(sector_deg) * 0.92,
        bottom=bottom,
        color=color,
        edgecolor=PAGE_BG,
        linewidth=0.4,
        label=label,
    )
    bottom += table[label].to_numpy()

# Axes: frequency rings from zero, compass labels around the rim
total_max = float(np.nanmax(bottom)) if n_sectors else 1.0
magnitude = 10 ** np.floor(np.log10(total_max / 9))
ring_step = next(m * magnitude for m in (1, 2, 5, 10) if m * magnitude >= total_max / 9)
max_freq = np.ceil(total_max / ring_step) * ring_step
rings = np.arange(ring_step, max_freq + ring_step / 2, ring_step)
ax.set_ylim(0, max_freq)
ax.set_yticks(rings)
ax.set_yticklabels([f"{r:g}%" for r in rings], fontsize=8, color=INK_SOFT)
ax.set_rlabel_position(112.5)
ax.set_xticks(np.deg2rad(angles))
compass = {i * 45.0: name for i, name in enumerate(COMPASS)}
ax.set_xticklabels([compass.get(a, f"{a:g}°") for a in angles], fontsize=11, fontweight="medium", color=INK)
ax.tick_params(axis="x", pad=6)
ax.grid(True, linewidth=0.6, color=INK_SOFT, alpha=0.25)
ax.spines["polar"].set_color(INK_SOFT)
ax.spines["polar"].set_linewidth(0.8)

ax.set_title("windrose-basic · python · seaborn · anyplot.ai", fontsize=12, pad=18, fontweight="medium", color=INK)

legend = ax.legend(
    title="Wind speed", loc="lower right", bbox_to_anchor=(1.18, -0.02), fontsize=8, title_fontsize=9, framealpha=0.95
)
legend.get_title().set_color(INK)
for text in legend.get_texts():
    text.set_color(INK)

fig.subplots_adjust(left=0.08, right=0.84, top=0.88, bottom=0.08)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
