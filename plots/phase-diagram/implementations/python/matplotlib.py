"""anyplot.ai
phase-diagram: Phase Diagram (State Space Plot)
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-14
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

# Imprint palette: all eight positions, one per trajectory in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
EQUILIBRIUM = 0.0  # the damped system comes to rest at x = 0, dx/dt = 0
ARROWS_PER_TRAJECTORY = 4  # direction arrows spread along each curve

# Columns: set these to your table's column names
TRAJECTORY = "Trajectory"  # role: extra
TIME = "Time (s)"  # role: t
POSITION = "Position x (arbitrary units)"  # role: x
VELOCITY = "Velocity dx/dt (arbitrary units)"  # role: dx_dt

# Data: replace this block with your own table, for example df = pd.read_csv("trajectories.csv")
# Damped harmonic oscillator x'' + 2*gamma*x' + omega0^2*x = 0 (underdamped), four initial conditions
gamma = 0.15
omega0 = 1.0
omega_d = np.sqrt(omega0**2 - gamma**2)
t = np.linspace(0, 50, 2000)
starts = [(3.0, 0.0), (3.0, 0.5), (2.5, 2.5), (2.0, 4.0)]  # amplitude and phase
frames = []
for amplitude, phase in starts:
    envelope = amplitude * np.exp(-gamma * t)
    angle = omega_d * t + phase
    frames.append(
        pd.DataFrame(
            {
                TRAJECTORY: f"Trajectory {len(frames) + 1} (A={amplitude:.1f})",
                TIME: t,
                POSITION: envelope * np.cos(angle),
                VELOCITY: envelope * (-gamma * np.cos(angle) - omega_d * np.sin(angle)),
            }
        )
    )
df = pd.concat(frames, ignore_index=True)

# Plot: reads only df and the constants above
fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

for i, (name, rows) in enumerate(df.groupby(TRAJECTORY, sort=False)):
    x = rows[POSITION].to_numpy()
    v = rows[VELOCITY].to_numpy()
    color = IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)]
    ax.plot(x, v, color=color, linewidth=2.2, alpha=0.85, label=name)
    ax.scatter(x[0], v[0], s=110, color=color, edgecolor=PAGE_BG, linewidth=1.2, zorder=5)

    # Arrows run with time: rightward above dx/dt = 0, leftward below it
    for idx in np.linspace(len(x) // 20, len(x) - len(x) // 10, ARROWS_PER_TRAJECTORY, dtype=int):
        ax.annotate(
            "",
            xy=(x[idx + 10], v[idx + 10]),
            xytext=(x[idx], v[idx]),
            arrowprops={"arrowstyle": "->", "color": color, "lw": 1.8, "mutation_scale": 14},
        )

ax.scatter(
    EQUILIBRIUM,
    EQUILIBRIUM,
    s=160,
    color=INK,
    marker="X",
    edgecolor=PAGE_BG,
    linewidth=1.0,
    zorder=10,
    label="Equilibrium (stable)",
)
ax.axhline(EQUILIBRIUM, color=INK_SOFT, linewidth=1.0, linestyle="--", alpha=0.4)
ax.axvline(EQUILIBRIUM, color=INK_SOFT, linewidth=1.0, linestyle="--", alpha=0.4)

# Style
title = "Damped Oscillator · phase-diagram · python · matplotlib · anyplot.ai"
ax.set_title(title, fontsize=10, fontweight="medium", color=INK)
ax.set_xlabel(POSITION, fontsize=10, color=INK)
ax.set_ylabel(VELOCITY, fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(True, alpha=0.15, linewidth=0.8, color=INK)

limit = np.ceil(max(df[POSITION].abs().max(), df[VELOCITY].abs().max()) * 1.15)
ax.set_xlim(-limit, limit)
ax.set_ylim(-limit, limit)
ax.set_aspect("equal", adjustable="box")

leg = ax.legend(fontsize=8, loc="upper right", framealpha=0.95)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

fig.subplots_adjust(left=0.13, right=0.97, top=0.93, bottom=0.10)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
