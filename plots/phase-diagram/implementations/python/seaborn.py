""" anyplot.ai
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

# Okabe-Ito palette (first series always #009E73)
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data: Damped harmonic oscillator phase trajectories
np.random.seed(42)

# System parameters for damped oscillator: d²x/dt² + 2*zeta*omega*dx/dt + omega²*x = 0
omega = 2 * np.pi
zeta = 0.15

# Generate multiple trajectories from different initial conditions
t = np.linspace(0, 5, 500)
trajectories = []
initial_conditions = [(2.0, 0.0), (0.0, 8.0), (-1.5, -5.0), (1.0, 4.0)]

for x0, v0 in initial_conditions:
    # Analytical solution for underdamped oscillator
    omega_d = omega * np.sqrt(1 - zeta**2)
    A = np.sqrt(x0**2 + ((zeta * omega * x0 + v0) / omega_d) ** 2)
    phi = np.arctan2(omega_d * x0, zeta * omega * x0 + v0)

    # Position and velocity (derivative)
    x = A * np.exp(-zeta * omega * t) * np.sin(omega_d * t + phi)
    dx_dt = (
        A
        * np.exp(-zeta * omega * t)
        * (-zeta * omega * np.sin(omega_d * t + phi) + omega_d * np.cos(omega_d * t + phi))
    )

    trajectories.append((x, dx_dt, f"({x0}, {v0})"))

# Create DataFrame for seaborn
data = []
for x, dx_dt, label in trajectories:
    for i in range(len(x)):
        data.append({"Position (x)": x[i], "Velocity (dx/dt)": dx_dt[i], "Initial Condition": label, "Time": t[i]})
df = pd.DataFrame(data)

# Configure seaborn theme
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

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Plot trajectories with gradient alpha to reduce density
sns.lineplot(
    data=df,
    x="Position (x)",
    y="Velocity (dx/dt)",
    hue="Initial Condition",
    palette=IMPRINT,
    linewidth=3,
    alpha=0.8,
    legend=True,
    ax=ax,
    sort=False,
)

# Add starting points as larger markers
for i, (x, dx_dt, _label) in enumerate(trajectories):
    ax.scatter(x[0], dx_dt[0], s=300, color=IMPRINT[i], zorder=5, edgecolor=PAGE_BG, linewidth=2)

# Add fixed point (equilibrium at origin)
ax.scatter(0, 0, s=400, color=INK, marker="x", linewidth=3.5, zorder=6, label="Equilibrium")

# Add direction arrows on trajectories
for i, (x, dx_dt, _label) in enumerate(trajectories):
    arrow_indices = [50, 150, 300]
    for idx in arrow_indices:
        if idx < len(x) - 1:
            dx = x[idx + 1] - x[idx]
            dy = dx_dt[idx + 1] - dx_dt[idx]
            ax.annotate(
                "",
                xy=(x[idx] + dx * 0.5, dx_dt[idx] + dy * 0.5),
                xytext=(x[idx], dx_dt[idx]),
                arrowprops={"arrowstyle": "->", "color": IMPRINT[i], "lw": 2},
            )

# Styling
ax.set_xlabel("Position (x)", fontsize=20, color=INK)
ax.set_ylabel("Velocity (dx/dt)", fontsize=20, color=INK)
ax.set_title("phase-diagram · seaborn · anyplot.ai", fontsize=24, color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Remove top and right spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

# Add zero lines for reference
ax.axhline(y=0, color=INK_SOFT, linestyle="--", linewidth=1.5, alpha=0.4)
ax.axvline(x=0, color=INK_SOFT, linestyle="--", linewidth=1.5, alpha=0.4)

# Adjust legend
legend = ax.legend(fontsize=14, loc="upper right", title="Initial Condition", title_fontsize=16)
legend.get_frame().set_facecolor(ELEVATED_BG)
legend.get_frame().set_edgecolor(INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
