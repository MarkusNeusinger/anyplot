""" anyplot.ai
streamline-basic: Basic Streamline Plot
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-21
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap
from scipy.interpolate import RegularGridInterpolator


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: continuous speed encoding uses the single-polarity Imprint ramp
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", ["#009E73", "#4467A3"])

# Constants
SEEDS_PER_EDGE = 13  # streamlines started along each inflow edge of the domain
STEP = 0.04  # integration step length in data units
MAX_STEPS = 600  # safety cap per streamline
SEGMENT_STRIDE = 3  # integration steps merged into one colored segment

# Columns: set these to your table's column names
X = "X Position (m)"  # role: x
Y = "Y Position (m)"  # role: y
U = "Horizontal velocity u (m/s)"  # role: u
V = "Vertical velocity v (m/s)"  # role: v
SPEED = "Flow Speed (m/s)"  # role: extra
LINE = "Streamline"  # role: extra
SEGMENT = "Segment"  # role: extra

# Data: replace this block with your own grid, for example df = pd.read_csv("field.csv")
# A saddle-point flow, u = x and v = -y, sampled on a regular 41 x 41 grid
grid = np.linspace(-3, 3, 41)
xx, yy = np.meshgrid(grid, grid)
df = pd.DataFrame({X: xx.ravel(), Y: yy.ravel(), U: xx.ravel(), V: -yy.ravel()})

# Plot: reads only df and the constants above
xs = np.sort(df[X].dropna().unique())
ys = np.sort(df[Y].dropna().unique())
u_grid = df.pivot_table(index=Y, columns=X, values=U, sort=True).reindex(index=ys, columns=xs).to_numpy()
v_grid = df.pivot_table(index=Y, columns=X, values=V, sort=True).reindex(index=ys, columns=xs).to_numpy()
interp_u = RegularGridInterpolator((ys, xs), u_grid, bounds_error=False, fill_value=np.nan)
interp_v = RegularGridInterpolator((ys, xs), v_grid, bounds_error=False, fill_value=np.nan)


def velocity(px, py):
    return float(interp_u((py, px))), float(interp_v((py, px)))


# Seeds along the top and bottom edges, spread across the full width
seed_x = np.linspace(xs.min(), xs.max(), SEEDS_PER_EDGE)
seeds = [(sx, ys.max()) for sx in seed_x] + [(sx, ys.min()) for sx in seed_x]

paths = []
for sx, sy in seeds:
    px, py = float(sx), float(sy)
    pts = [(px, py)]
    for _ in range(MAX_STEPS):
        u, v = velocity(px, py)
        mag = np.hypot(u, v)
        if not np.isfinite(mag) or mag < 1e-9:
            break
        # Midpoint step of fixed arc length along the field direction
        mx, my = px + 0.5 * STEP * u / mag, py + 0.5 * STEP * v / mag
        u, v = velocity(mx, my)
        mag = np.hypot(u, v)
        if not np.isfinite(mag) or mag < 1e-9:
            break
        px, py = px + STEP * u / mag, py + STEP * v / mag
        if not (xs.min() <= px <= xs.max() and ys.min() <= py <= ys.max()):
            break
        pts.append((px, py))
    if len(pts) > 2:
        paths.append(np.array(pts))

rows = []
arrows = []
segment_id = 0
for line_id, path in enumerate(paths):
    speeds = np.array([np.hypot(*velocity(px, py)) for px, py in path])
    for k in range(0, len(path) - 1, SEGMENT_STRIDE):
        stop = min(k + SEGMENT_STRIDE, len(path) - 1)
        seg_speed = speeds[k : stop + 1].mean()
        for j in (k, stop):
            rows.append({X: path[j, 0], Y: path[j, 1], SPEED: seg_speed, LINE: line_id, SEGMENT: segment_id})
        segment_id += 1
    # One direction arrow per line, on the inflow part of the path
    a = int(0.3 * (len(path) - 1))
    arrows.append((path[a], path[a + 1], speeds[a]))
lines = pd.DataFrame(rows)

norm = plt.Normalize(lines[SPEED].min(), lines[SPEED].max())

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
        "grid.alpha": 0.15,
    },
)

fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

sns.lineplot(
    data=lines,
    x=X,
    y=Y,
    hue=SPEED,
    hue_norm=norm,
    units=SEGMENT,
    estimator=None,
    sort=False,
    palette=imprint_seq,
    linewidth=1.8,
    solid_capstyle="round",
    legend=False,
    ax=ax,
)

# Direction arrows, colored like the line they sit on
for tail, head, speed in arrows:
    ax.annotate(
        "",
        xy=head,
        xytext=tail,
        arrowprops={"arrowstyle": "-|>", "color": imprint_seq(norm(speed)), "lw": 0, "mutation_scale": 16},
        zorder=10,
    )

# Colorbar naming the encoded scalar
sm = plt.cm.ScalarMappable(cmap=imprint_seq, norm=norm)
sm.set_array([])
cbar = fig.colorbar(sm, ax=ax, shrink=0.8, aspect=20, pad=0.03)
cbar.set_label(SPEED, fontsize=10, color=INK)
cbar.ax.tick_params(labelsize=8, colors=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)

# Style
ax.set_title("streamline-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel(X, fontsize=10, color=INK)
ax.set_ylabel(Y, fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.set_aspect("equal")
ax.set_xlim(xs.min(), xs.max())
ax.set_ylim(ys.min(), ys.max())
ax.yaxis.grid(True, linewidth=0.8)
sns.despine(ax=ax)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
