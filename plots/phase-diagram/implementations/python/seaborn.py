""" pyplots.ai
phase-diagram: Phase Diagram (State Space Plot)
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data: Damped harmonic oscillator phase trajectories
np.random.seed(42)

# System parameters for damped oscillator: d²x/dt² + 2*zeta*omega*dx/dt + omega²*x = 0
omega = 2 * np.pi  # Natural frequency
zeta = 0.15  # Damping ratio (underdamped)

# Generate multiple trajectories from different initial conditions
t = np.linspace(0, 5, 500)
trajectories = []
initial_conditions = [
    (2.0, 0.0),  # Large displacement, zero velocity
    (0.0, 8.0),  # Zero displacement, positive velocity
    (-1.5, -5.0),  # Negative displacement, negative velocity
    (1.0, 4.0),  # Mixed positive
]

for x0, v0 in initial_conditions:
    # Analytical solution for underdamped oscillator
    omega_d = omega * np.sqrt(1 - zeta**2)  # Damped frequency
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

# Plot
sns.set_style("whitegrid")
fig, ax = plt.subplots(figsize=(16, 9))

# Use seaborn lineplot for trajectories with color gradient by hue
palette = ["#306998", "#FFD43B", "#E24A33", "#348ABD"]
sns.lineplot(
    data=df,
    x="Position (x)",
    y="Velocity (dx/dt)",
    hue="Initial Condition",
    palette=palette,
    linewidth=2.5,
    alpha=0.9,
    legend=True,
    ax=ax,
    sort=False,
)

# Add starting points as larger markers
for i, (x, dx_dt, _label) in enumerate(trajectories):
    ax.scatter(x[0], dx_dt[0], s=250, color=palette[i], zorder=5, edgecolor="white", linewidth=2)

# Add fixed point (equilibrium at origin)
ax.scatter(0, 0, s=300, color="black", marker="x", linewidth=4, zorder=6, label="Equilibrium")

# Add direction arrows on trajectories
for i, (x, dx_dt, _label) in enumerate(trajectories):
    # Add arrows at several points along trajectory
    arrow_indices = [50, 150, 300]
    for idx in arrow_indices:
        if idx < len(x) - 1:
            dx = x[idx + 1] - x[idx]
            dy = dx_dt[idx + 1] - dx_dt[idx]
            ax.annotate(
                "",
                xy=(x[idx] + dx * 0.5, dx_dt[idx] + dy * 0.5),
                xytext=(x[idx], dx_dt[idx]),
                arrowprops={"arrowstyle": "->", "color": palette[i], "lw": 2},
            )

# Styling
ax.set_xlabel("Position (x)", fontsize=20)
ax.set_ylabel("Velocity (dx/dt)", fontsize=20)
ax.set_title("phase-diagram · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)

# Adjust legend
ax.legend(fontsize=14, loc="upper right", title="Initial Condition", title_fontsize=16)

# Add zero lines for reference
ax.axhline(y=0, color="gray", linestyle="--", linewidth=1.5, alpha=0.5)
ax.axvline(x=0, color="gray", linestyle="--", linewidth=1.5, alpha=0.5)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
