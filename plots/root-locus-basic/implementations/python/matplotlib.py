""" pyplots.ai
root-locus-basic: Root Locus Plot for Control Systems
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 91/100 | Created: 2026-03-20
"""

import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np


# Data — Transfer function G(s) = (s+2) / [s(s+1)(s+3)(s+5)]
# Open-loop poles and zeros
open_loop_poles = np.array([0, -1, -3, -5])
open_loop_zeros = np.array([-2])

# Denominator: s(s+1)(s+3)(s+5) = s^4 + 9s^3 + 23s^2 + 15s
den_coeffs = np.array([1, 9, 23, 15, 0])
# Numerator: (s+2)
num_coeffs = np.array([1, 2])

# Compute root locus by finding roots for varying gain K
gains = np.concatenate(
    [
        np.linspace(0, 1, 200),
        np.linspace(1, 10, 300),
        np.linspace(10, 50, 300),
        np.linspace(50, 200, 300),
        np.linspace(200, 1000, 400),
    ]
)

n_poles = len(den_coeffs) - 1
locus = np.full((len(gains), n_poles), np.nan + 1j * np.nan)

for i, K in enumerate(gains):
    # Characteristic equation: den(s) + K * num(s) = 0
    # Pad numerator to match denominator length
    num_padded = np.zeros(len(den_coeffs))
    num_padded[-len(num_coeffs) :] = num_coeffs
    char_poly = den_coeffs + K * num_padded
    roots = np.roots(char_poly)
    roots = np.sort_complex(roots)
    locus[i, :] = roots

# Sort branches by continuity (greedy nearest-neighbor tracking)
for i in range(1, len(gains)):
    prev = locus[i - 1, :]
    curr = locus[i, :].copy()
    used = np.zeros(n_poles, dtype=bool)
    order = np.zeros(n_poles, dtype=int)
    for j in range(n_poles):
        dists = np.abs(curr - prev[j])
        dists[used] = np.inf
        best = np.argmin(dists)
        order[j] = best
        used[best] = True
    locus[i, :] = curr[order]

# Find imaginary axis crossings (stability boundary)
crossings = []
for branch in range(n_poles):
    real_parts = locus[:, branch].real
    for i in range(1, len(real_parts)):
        if real_parts[i - 1] * real_parts[i] < 0:
            t = abs(real_parts[i - 1]) / (abs(real_parts[i - 1]) + abs(real_parts[i]))
            cross_point = locus[i - 1, branch] + t * (locus[i, branch] - locus[i - 1, branch])
            crossings.append(cross_point)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Subtle background shading: stable (left) vs unstable (right) half-plane
ax.axvspan(-10, 0, color="#2ECC71", alpha=0.04, zorder=0)
ax.axvspan(0, 5, color="#E74C3C", alpha=0.04, zorder=0)
ax.text(
    -6.5,
    -4.5,
    "Stable",
    fontsize=14,
    color="#27AE60",
    alpha=0.6,
    path_effects=[pe.withStroke(linewidth=3, foreground="white")],
)
ax.text(
    0.4,
    -4.5,
    "Unstable",
    fontsize=14,
    color="#C0392B",
    alpha=0.6,
    path_effects=[pe.withStroke(linewidth=3, foreground="white")],
)

# Constant damping ratio lines (light grid)
zeta_values = [0.2, 0.4, 0.6, 0.8]
theta_range = np.linspace(0, np.pi, 200)
max_r = 7
for zeta in zeta_values:
    angle = np.arccos(zeta)
    r = np.linspace(0, max_r, 100)
    line_real = -r * np.cos(np.pi - angle)
    line_imag_pos = r * np.sin(np.pi - angle)
    ax.plot(line_real, line_imag_pos, "--", color="#CCCCCC", linewidth=0.8, alpha=0.6)
    ax.plot(line_real, -line_imag_pos, "--", color="#CCCCCC", linewidth=0.8, alpha=0.6)
    label_r = 3.2 if zeta >= 0.8 else 4.0
    lx = -label_r * np.cos(np.pi - angle) - 0.1
    ly = label_r * np.sin(np.pi - angle) + 0.15
    ax.text(
        lx,
        ly,
        f"ζ={zeta}",
        fontsize=14,
        color="#888888",
        alpha=0.8,
        path_effects=[pe.withStroke(linewidth=3, foreground="white")],
    )

# Constant natural frequency circles (light grid)
wn_values = [1, 2, 3, 4, 5, 6]
for wn in wn_values:
    circle_theta = np.linspace(np.pi / 2, 3 * np.pi / 2, 200)
    ax.plot(wn * np.cos(circle_theta), wn * np.sin(circle_theta), "--", color="#CCCCCC", linewidth=0.8, alpha=0.6)

# Branch colors
branch_colors = ["#306998", "#E8553A", "#17BECF", "#9467BD"]

# Draw locus branches
for branch in range(n_poles):
    real = locus[:, branch].real
    imag = locus[:, branch].imag
    ax.plot(real, imag, color=branch_colors[branch % len(branch_colors)], linewidth=2.5, alpha=0.85, zorder=3)

# Add arrows indicating direction of increasing gain using FancyArrowPatch
for branch in range(n_poles):
    n_pts = len(gains)
    idx = n_pts // 3
    if idx + 5 < n_pts:
        p1 = locus[idx, branch]
        p2 = locus[idx + 5, branch]
        dx = p2.real - p1.real
        dy = p2.imag - p1.imag
        length = np.sqrt(dx**2 + dy**2)
        if length > 0.005:
            arrow = mpatches.FancyArrowPatch(
                (p1.real, p1.imag),
                (p2.real, p2.imag),
                arrowstyle="-|>",
                color=branch_colors[branch % len(branch_colors)],
                linewidth=2,
                mutation_scale=20,
                zorder=4,
                path_effects=[pe.withStroke(linewidth=4, foreground="white", alpha=0.5)],
            )
            ax.add_patch(arrow)

# Mark open-loop poles (x markers)
ax.scatter(
    open_loop_poles.real,
    np.zeros_like(open_loop_poles),
    marker="x",
    s=250,
    color="#333333",
    linewidths=3,
    zorder=5,
    label="Open-loop poles",
)

# Mark open-loop zeros (o markers)
ax.scatter(
    open_loop_zeros.real,
    np.zeros_like(open_loop_zeros),
    marker="o",
    s=200,
    facecolors="none",
    edgecolors="#333333",
    linewidths=3,
    zorder=5,
    label="Open-loop zeros",
)

# Mark imaginary axis crossings with labels
for cp in crossings:
    ax.scatter(cp.real, cp.imag, marker="D", s=200, color="#D4A017", edgecolors="white", linewidths=1.5, zorder=6)
    ax.annotate(
        f"jω≈{cp.imag:+.1f}",
        xy=(cp.real, cp.imag),
        xytext=(12, 8),
        textcoords="offset points",
        fontsize=13,
        color="#B8860B",
        fontweight="bold",
        path_effects=[pe.withStroke(linewidth=3, foreground="white")],
        zorder=7,
    )

# Real axis segments (to the left of odd number of real poles+zeros)
real_points = np.sort(np.concatenate([open_loop_poles.real, open_loop_zeros.real]))
x_range = np.linspace(-8, 1, 5000)
on_locus = np.zeros_like(x_range, dtype=bool)
for i, x in enumerate(x_range):
    count = np.sum(real_points >= x)
    on_locus[i] = count % 2 == 1

segments = []
in_segment = False
for i, val in enumerate(on_locus):
    if val and not in_segment:
        start = x_range[i]
        in_segment = True
    elif not val and in_segment:
        segments.append((start, x_range[i - 1]))
        in_segment = False
if in_segment:
    segments.append((start, x_range[-1]))

for seg_start, seg_end in segments:
    ax.plot([seg_start, seg_end], [0, 0], color="#306998", linewidth=4, alpha=0.3, zorder=2)

# Axes through origin
ax.axhline(y=0, color="#666666", linewidth=0.8, zorder=1)
ax.axvline(x=0, color="#666666", linewidth=0.8, zorder=1)

# Style
ax.set_xlabel("Real Axis (σ)", fontsize=20)
ax.set_ylabel("Imaginary Axis (jω)", fontsize=20)
ax.set_title("root-locus-basic · matplotlib · pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)
ax.legend(fontsize=16, loc="upper left", framealpha=0.9)
ax.set_aspect("equal")
ax.set_xlim(-7, 2.5)
ax.set_ylim(-5, 5)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
