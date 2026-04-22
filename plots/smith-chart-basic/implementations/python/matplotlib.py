""" pyplots.ai
smith-chart-basic: Smith Chart for RF/Impedance
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-15
"""

import matplotlib.pyplot as plt
import numpy as np


# Reference impedance
Z0 = 50  # ohms

# Generate example data: antenna impedance sweep from 1 GHz to 6 GHz
np.random.seed(42)
frequency = np.linspace(1e9, 6e9, 50)  # 50 frequency points

# Simulate realistic antenna impedance variation with frequency
# This creates a spiral-like pattern typical of antenna impedance measurements
z_real = 50 + 30 * np.sin(2 * np.pi * (frequency - 1e9) / 2e9) + 10 * np.cos(4 * np.pi * (frequency - 1e9) / 5e9)
z_imag = 20 * np.cos(2 * np.pi * (frequency - 1e9) / 1.5e9) + 15 * np.sin(3 * np.pi * (frequency - 1e9) / 5e9)

# Normalize impedance
z_norm = (z_real + 1j * z_imag) / Z0

# Convert to reflection coefficient (gamma)
gamma = (z_norm - 1) / (z_norm + 1)

# Create square figure for Smith chart
fig, ax = plt.subplots(figsize=(12, 12))
ax.set_aspect("equal")

# Colors
grid_color = "#888888"
circle_color = "#306998"
data_color = "#FFD43B"

# Draw constant resistance circles
r_values = [0, 0.2, 0.5, 1, 2, 5]
theta = np.linspace(0, 2 * np.pi, 500)

for r in r_values:
    # Center and radius of constant resistance circle
    center = r / (r + 1)
    radius = 1 / (r + 1)
    x_circle = center + radius * np.cos(theta)
    y_circle = radius * np.sin(theta)
    # Clip to unit circle
    mask = x_circle**2 + y_circle**2 <= 1.001
    x_clipped = np.where(mask, x_circle, np.nan)
    y_clipped = np.where(mask, y_circle, np.nan)
    ax.plot(x_clipped, y_clipped, color=grid_color, linewidth=1, alpha=0.6)
    # Label resistance circles
    if r > 0:
        label_x = center + radius
        if label_x <= 1:
            ax.text(label_x + 0.02, 0.02, f"{r}", fontsize=12, color=grid_color, ha="left", va="bottom")

# Draw constant reactance arcs
x_values = [0.2, 0.5, 1, 2, 5]

for x in x_values:
    # Positive reactance (inductive - upper half)
    center_y = 1 / x
    radius = 1 / x
    arc_theta = np.linspace(0, np.pi, 500)
    x_arc = 1 + radius * np.cos(arc_theta + np.pi)
    y_arc = center_y + radius * np.sin(arc_theta + np.pi)
    # Clip to unit circle
    mask = x_arc**2 + y_arc**2 <= 1.001
    x_clipped = np.where(mask, x_arc, np.nan)
    y_clipped = np.where(mask, y_arc, np.nan)
    ax.plot(x_clipped, y_clipped, color=grid_color, linewidth=1, alpha=0.6)

    # Negative reactance (capacitive - lower half)
    y_arc_neg = -center_y + radius * np.sin(arc_theta)
    mask = x_arc**2 + y_arc_neg**2 <= 1.001
    x_clipped = np.where(mask, x_arc, np.nan)
    y_clipped = np.where(mask, y_arc_neg, np.nan)
    ax.plot(x_clipped, y_clipped, color=grid_color, linewidth=1, alpha=0.6)

    # Label reactance arcs
    # Find intersection with unit circle
    if x <= 1:
        angle = 2 * np.arctan(1 / x)
        label_x = np.cos(angle)
        label_y = np.sin(angle)
        ax.text(label_x, label_y + 0.05, f"+j{x}", fontsize=11, color=grid_color, ha="center", va="bottom")
        ax.text(label_x, -label_y - 0.05, f"-j{x}", fontsize=11, color=grid_color, ha="center", va="top")

# Draw horizontal axis (real axis, x=0)
ax.axhline(y=0, color=grid_color, linewidth=1, alpha=0.6)

# Draw unit circle (boundary)
unit_theta = np.linspace(0, 2 * np.pi, 500)
ax.plot(np.cos(unit_theta), np.sin(unit_theta), color=circle_color, linewidth=2.5)

# Draw center point (matched condition)
ax.plot(0, 0, "o", color=circle_color, markersize=10, label="Matched (Z=Z₀)")

# Plot impedance locus
ax.plot(gamma.real, gamma.imag, color=data_color, linewidth=3, label="Impedance Locus", zorder=5)
ax.scatter(gamma.real, gamma.imag, c=data_color, s=60, edgecolors="black", linewidths=0.5, zorder=6)

# Add frequency labels at key points
freq_label_indices = [0, 12, 24, 36, 49]  # Start, middle points, end
for idx in freq_label_indices:
    freq_ghz = frequency[idx] / 1e9
    x_pos = gamma.real[idx]
    y_pos = gamma.imag[idx]
    # Offset labels to avoid overlap with data points
    offset_x = 0.08 if x_pos < 0.5 else -0.08
    offset_y = 0.08 if y_pos >= 0 else -0.08
    ax.annotate(
        f"{freq_ghz:.1f} GHz",
        (x_pos, y_pos),
        xytext=(x_pos + offset_x, y_pos + offset_y),
        fontsize=14,
        fontweight="bold",
        color="black",
        arrowprops={"arrowstyle": "->", "color": "black", "lw": 1.5},
        zorder=10,
    )

# Draw VSWR circles (optional - constant reflection coefficient magnitude)
vswr_values = [1.5, 2, 3]
vswr_angles = [np.pi / 4, np.pi / 3, 5 * np.pi / 12]  # Different angles for each label
for vswr, label_angle in zip(vswr_values, vswr_angles, strict=True):
    gamma_mag = (vswr - 1) / (vswr + 1)
    vswr_theta = np.linspace(0, 2 * np.pi, 200)
    ax.plot(
        gamma_mag * np.cos(vswr_theta),
        gamma_mag * np.sin(vswr_theta),
        "--",
        color="#CC4444",
        linewidth=1.5,
        alpha=0.7,
        label=f"VSWR={vswr}" if vswr == 1.5 else "",
    )
    # Label VSWR circles at different angles to avoid overlap
    label_x = gamma_mag * np.cos(label_angle)
    label_y = gamma_mag * np.sin(label_angle)
    ax.text(label_x, label_y + 0.06, f"VSWR={vswr}", fontsize=11, color="#CC4444", alpha=0.9, ha="center")

# Styling
ax.set_xlim(-1.25, 1.25)
ax.set_ylim(-1.25, 1.25)
ax.set_xlabel("Real(Γ)", fontsize=20)
ax.set_ylabel("Imag(Γ)", fontsize=20)
ax.set_title("smith-chart-basic · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.legend(fontsize=14, loc="upper left")

# Remove axis ticks for cleaner Smith chart appearance
ax.set_xticks([])
ax.set_yticks([])

# Add axis labels on chart edge
ax.text(1.15, 0, "Open\n(Γ=1)", fontsize=12, ha="center", va="center", color=circle_color)
ax.text(-1.15, 0, "Short\n(Γ=-1)", fontsize=12, ha="center", va="center", color=circle_color)
ax.text(0, 1.15, "+jX\n(Inductive)", fontsize=12, ha="center", va="center", color=grid_color)
ax.text(0, -1.15, "-jX\n(Capacitive)", fontsize=12, ha="center", va="center", color=grid_color)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
