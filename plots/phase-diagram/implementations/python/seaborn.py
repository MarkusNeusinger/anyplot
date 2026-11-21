"""anyplot.ai
phase-diagram: Phase Diagram (State Space Plot)
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-14
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

# Imprint palette: all eight positions, one per trajectory in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
ARROW_STEPS = (50, 150, 300)  # sample indices along each trajectory that carry a direction arrow

# Columns: set these to your table's column names
POSITION = "Position (x)"  # role: x
VELOCITY = "Velocity (dx/dt)"  # role: dx_dt
TIME = "Time (s)"  # role: t
CONDITION = "Initial condition (x0, v0)"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("trajectories.csv")
# Damped harmonic oscillator: d²x/dt² + 2*zeta*omega*dx/dt + omega²*x = 0
omega = 2 * np.pi
zeta = 0.15
omega_d = omega * np.sqrt(1 - zeta**2)
t = np.linspace(0, 5, 500)
frames = []
for x0, v0 in [(2.0, 0.0), (0.0, 8.0), (-1.5, -5.0), (1.0, 4.0)]:
    # Analytical solution for the underdamped case
    amplitude = np.sqrt(x0**2 + ((zeta * omega * x0 + v0) / omega_d) ** 2)
    phase = np.arctan2(omega_d * x0, zeta * omega * x0 + v0)
    envelope = amplitude * np.exp(-zeta * omega * t)
    frames.append(
        pd.DataFrame(
            {
                POSITION: envelope * np.sin(omega_d * t + phase),
                VELOCITY: envelope
                * (-zeta * omega * np.sin(omega_d * t + phase) + omega_d * np.cos(omega_d * t + phase)),
                TIME: t,
                CONDITION: f"({x0}, {v0})",
            }
        )
    )
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

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)
n_traj = df[CONDITION].nunique()
palette = IMPRINT_PALETTE[:n_traj]

# Trajectories in time order, one smooth curve per initial condition
sns.lineplot(
    data=df,
    x=POSITION,
    y=VELOCITY,
    hue=CONDITION,
    palette=palette,
    units=CONDITION,
    estimator=None,
    sort=False,
    linewidth=1.8,
    alpha=0.85,
    ax=ax,
)

# Starting points: first row of every trajectory
starts = df.groupby(CONDITION, sort=False).head(1)
sns.scatterplot(
    data=starts,
    x=POSITION,
    y=VELOCITY,
    hue=CONDITION,
    palette=palette,
    s=110,
    edgecolor=PAGE_BG,
    linewidth=1.2,
    zorder=5,
    legend=False,
    ax=ax,
)

# Fixed point: the damped system rests at the origin
ax.scatter(0, 0, s=140, color=INK, marker="x", linewidth=2.2, zorder=6, label="Equilibrium")

# Direction arrows, running with time
for i, (_, traj) in enumerate(df.groupby(CONDITION, sort=False)):
    color = IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)]
    xs = traj[POSITION].to_numpy()
    ys = traj[VELOCITY].to_numpy()
    for idx in ARROW_STEPS:
        if idx < len(xs) - 1:
            ax.annotate(
                "",
                xy=(xs[idx] + (xs[idx + 1] - xs[idx]) * 0.5, ys[idx] + (ys[idx + 1] - ys[idx]) * 0.5),
                xytext=(xs[idx], ys[idx]),
                arrowprops={"arrowstyle": "->", "color": color, "lw": 1.3},
            )

# Style
ax.axhline(y=0, color=INK_SOFT, linestyle="--", linewidth=0.9, alpha=0.4)
ax.axvline(x=0, color=INK_SOFT, linestyle="--", linewidth=0.9, alpha=0.4)
ax.set_title("phase-diagram · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel(POSITION, fontsize=10, color=INK)
ax.set_ylabel(VELOCITY, fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
sns.despine(ax=ax)

legend = ax.legend(fontsize=8, loc="upper right", title=CONDITION, title_fontsize=9)
legend.get_frame().set_facecolor(ELEVATED_BG)
legend.get_frame().set_edgecolor(INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
