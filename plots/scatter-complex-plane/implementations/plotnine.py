""" pyplots.ai
scatter-complex-plane: Complex Plane Visualization (Argand Diagram)
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 78/100 | Created: 2026-03-04
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    arrow,
    coord_fixed,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_hline,
    geom_path,
    geom_point,
    geom_segment,
    geom_text,
    geom_vline,
    ggplot,
    labs,
    scale_color_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data — complex numbers: 5th roots of unity + arbitrary points
n_roots = 5
angles_roots = np.array([2 * np.pi * k / n_roots for k in range(n_roots)])
roots_real = np.cos(angles_roots)
roots_imag = np.sin(angles_roots)
roots_labels = [f"ω{k}" for k in range(n_roots)]

arbitrary_real = np.array([1.2, -1.2, 0.5, -0.7, 0.8])
arbitrary_imag = np.array([1.4, -0.3, 1.7, -1.4, -0.6])
arbitrary_labels = ["z₁", "z₂", "z₃", "z₄", "z₅"]

real = np.concatenate([roots_real, arbitrary_real])
imag = np.concatenate([roots_imag, arbitrary_imag])
labels = roots_labels + arbitrary_labels
category = ["5th Root of Unity"] * n_roots + ["Arbitrary Point"] * len(arbitrary_real)

df_points = pd.DataFrame({"real": real, "imag": imag, "label": labels, "category": category})

# Annotation labels: name + rectangular form (a+bi)
annotations = []
for r, i, lbl in zip(real, imag, labels, strict=True):
    sign = "+" if i >= 0 else "−"
    annotations.append(f"{lbl} ({r:.1f}{sign}{abs(i):.1f}i)")
df_points["annotation"] = annotations

# Vectors from origin to each point
df_vectors = pd.DataFrame(
    {"x": [0.0] * len(real), "y": [0.0] * len(real), "xend": real, "yend": imag, "category": category}
)

# Unit circle
theta = np.linspace(0, 2 * np.pi, 200)
df_circle = pd.DataFrame({"x": np.cos(theta), "y": np.sin(theta)})

# Label offset positions — shift labels away from origin
ha_values = ["left" if r >= 0 else "right" for r in real]
x_offsets = np.where(np.array(real) >= 0, 0.18, -0.18)
df_labels = pd.DataFrame({"x": real + x_offsets, "y": imag + 0.13, "annotation": annotations, "ha": ha_values})

# Colors
colors = ["#306998", "#E67E22"]

# Plot
plot = (
    ggplot()
    # Axes through origin
    + geom_hline(yintercept=0, color="#888888", size=0.5, alpha=0.6)
    + geom_vline(xintercept=0, color="#888888", size=0.5, alpha=0.6)
    # Unit circle
    + geom_path(df_circle, aes(x="x", y="y"), color="#999999", linetype="dashed", size=0.8, alpha=0.6)
    # Vectors from origin
    + geom_segment(
        df_vectors,
        aes(x="x", y="y", xend="xend", yend="yend", color="category"),
        size=1.0,
        alpha=0.7,
        arrow=arrow(length=0.12, type="closed"),
    )
    # Points
    + geom_point(df_points, aes(x="real", y="imag", color="category"), size=5, alpha=0.9)
    # Annotations — left-aligned for right-side points, right-aligned for left-side
    + geom_text(
        df_labels[df_labels["ha"] == "left"], aes(x="x", y="y", label="annotation"), size=7, color="#333333", ha="left"
    )
    + geom_text(
        df_labels[df_labels["ha"] == "right"],
        aes(x="x", y="y", label="annotation"),
        size=7,
        color="#333333",
        ha="right",
    )
    # Labels and title
    + labs(x="Real Axis", y="Imaginary Axis", title="scatter-complex-plane · plotnine · pyplots.ai", color="Category")
    # Equal aspect ratio with padding for labels
    + scale_x_continuous(limits=(-2.0, 2.0))
    + scale_y_continuous(limits=(-2.0, 2.0))
    + coord_fixed(ratio=1)
    # Theme
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24, weight="bold"),
        legend_text=element_text(size=14),
        legend_title=element_text(size=16),
        legend_position="bottom",
        legend_background=element_rect(fill="white", alpha=0.8),
        panel_grid_major=element_line(color="#e0e0e0", size=0.3, alpha=0.3),
        panel_grid_minor=element_blank(),
    )
    + scale_color_manual(values=colors)
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
