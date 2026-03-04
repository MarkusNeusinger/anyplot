"""pyplots.ai
scatter-complex-plane: Complex Plane Visualization (Argand Diagram)
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 86/100 | Created: 2026-03-04
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    arrow,
    coord_fixed,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_hline,
    geom_label,
    geom_path,
    geom_point,
    geom_segment,
    geom_vline,
    ggplot,
    guide_legend,
    guides,
    labs,
    scale_alpha_identity,
    scale_color_manual,
    scale_size_identity,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data — complex numbers: 5th roots of unity + arbitrary points + sum demonstration
n_roots = 5
angles_roots = np.array([2 * np.pi * k / n_roots for k in range(n_roots)])
roots_real = np.cos(angles_roots)
roots_imag = np.sin(angles_roots)
roots_labels = [f"ω{k}" for k in range(n_roots)]

# Arbitrary points — positioned to avoid crowding with roots of unity
arbitrary_real = np.array([1.5, -1.6, 0.4, -0.8, 1.6])
arbitrary_imag = np.array([0.7, -1.4, 1.8, -1.5, -1.2])
arbitrary_labels = ["z₁", "z₂", "z₃", "z₄", "z₅"]

# Complex addition: z₁ + z₂ demonstrates geometric parallelogram rule
sum_real = arbitrary_real[0] + arbitrary_real[1]
sum_imag = arbitrary_imag[0] + arbitrary_imag[1]

real = np.concatenate([roots_real, arbitrary_real, [sum_real]])
imag = np.concatenate([roots_imag, arbitrary_imag, [sum_imag]])
labels = roots_labels + arbitrary_labels + ["z₁+z₂"]
category = ["5th Root of Unity"] * n_roots + ["Arbitrary Point"] * len(arbitrary_real) + ["Sum (z₁ + z₂)"]

# Magnitude for visual hierarchy
magnitude = np.sqrt(real**2 + imag**2)

df_points = pd.DataFrame({"real": real, "imag": imag, "label": labels, "category": category, "magnitude": magnitude})

# Annotation labels: name + rectangular form (a+bi)
annotations = []
for r, i, lbl in zip(real, imag, labels, strict=True):
    sign = "+" if i >= 0 else "−"
    annotations.append(f"{lbl} = {r:.2f}{sign}{abs(i):.2f}i")
df_points["annotation"] = annotations

# Vectors from origin to each point
df_vectors = pd.DataFrame(
    {"x": [0.0] * len(real), "y": [0.0] * len(real), "xend": real, "yend": imag, "category": category}
)

# Parallelogram edges: dashed lines z₁→sum and z₂→sum
df_parallelogram = pd.DataFrame(
    {
        "x": [arbitrary_real[0], arbitrary_real[1]],
        "y": [arbitrary_imag[0], arbitrary_imag[1]],
        "xend": [sum_real, sum_real],
        "yend": [sum_imag, sum_imag],
    }
)

# Unit circle
theta = np.linspace(0, 2 * np.pi, 300)
df_circle = pd.DataFrame({"x": np.cos(theta), "y": np.sin(theta)})

# Smart label positioning — angle-based offset with per-point adjustments
angles = np.arctan2(imag, real)
label_radius = 0.35
x_offsets = label_radius * np.cos(angles)
y_offsets = label_radius * np.sin(angles)
ha_values = ["left" if np.cos(a) >= 0 else "right" for a in angles]

# Manual nudge for the sum point label to avoid vector overlap
sum_idx = len(real) - 1
y_offsets[sum_idx] -= 0.15

df_labels = pd.DataFrame({"x": real + x_offsets, "y": imag + y_offsets, "annotation": annotations, "ha": ha_values})

# Color palette — three-category with green accent for sum
color_roots = "#1B4F72"
color_arb = "#D35400"
color_sum = "#1E8449"
colors = [color_roots, color_arb, color_sum]

# Point sizes by category for visual hierarchy
df_points["pt_size"] = [4.5] * n_roots + [5.5] * len(arbitrary_real) + [7.0]
df_points["pt_alpha"] = [0.90] * n_roots + [0.95] * len(arbitrary_real) + [1.0]

# Build the plot with layered grammar of graphics
plot = (
    ggplot()
    # Reference axes through origin
    + geom_hline(yintercept=0, color="#B0B0B0", size=0.5, linetype="solid")
    + geom_vline(xintercept=0, color="#B0B0B0", size=0.5, linetype="solid")
    # Unit circle — dashed reference
    + geom_path(df_circle, aes(x="x", y="y"), color="#7F8C8D", linetype="dashed", size=0.9, alpha=0.65)
    # Unit circle label
    + annotate("text", x=0.72, y=0.72, label="∣z∣ = 1", size=10, color="#7F8C8D", fontstyle="italic", angle=45)
    # Parallelogram dashed lines for complex addition
    + geom_segment(
        df_parallelogram,
        aes(x="x", y="y", xend="xend", yend="yend"),
        color=color_sum,
        linetype="dotted",
        size=0.8,
        alpha=0.6,
    )
    # Vectors from origin with arrows
    + geom_segment(
        df_vectors,
        aes(x="x", y="y", xend="xend", yend="yend", color="category"),
        size=1.0,
        alpha=0.65,
        arrow=arrow(length=0.12, type="closed"),
    )
    # Points — main scatter layer with mapped size and alpha
    + geom_point(df_points, aes(x="real", y="imag", color="category", size="pt_size", alpha="pt_alpha"))
    + scale_size_identity()
    + scale_alpha_identity()
    # Halo ring on roots of unity for emphasis
    + geom_point(
        df_points[df_points["category"] == "5th Root of Unity"],
        aes(x="real", y="imag"),
        size=10,
        color=color_roots,
        alpha=0.12,
        shape="o",
    )
    # Annotations — split by horizontal alignment for plotnine geom_label
    + geom_label(
        df_labels[df_labels["ha"] == "left"],
        aes(x="x", y="y", label="annotation"),
        size=9,
        color="#2C3E50",
        fill="#FFFFFF",
        alpha=0.80,
        ha="left",
        fontweight="bold",
        label_padding=0.2,
        label_size=0.3,
        boxstyle="round,pad=0.25",
    )
    + geom_label(
        df_labels[df_labels["ha"] == "right"],
        aes(x="x", y="y", label="annotation"),
        size=9,
        color="#2C3E50",
        fill="#FFFFFF",
        alpha=0.80,
        ha="right",
        fontweight="bold",
        label_padding=0.2,
        label_size=0.3,
        boxstyle="round,pad=0.25",
    )
    # Axis labels and title
    + labs(x="Re(z)", y="Im(z)", title="scatter-complex-plane · plotnine · pyplots.ai", color="Category")
    # Axis scales
    + scale_x_continuous(limits=(-2.5, 2.5), breaks=[-2, -1, 0, 1, 2])
    + scale_y_continuous(limits=(-2.5, 2.5), breaks=[-2, -1, 0, 1, 2])
    + coord_fixed(ratio=1)
    # Color scale with descriptive legend labels
    + scale_color_manual(values=colors, labels=["5th Root of Unity (∣z∣ = 1)", "Arbitrary Point", "Sum (z₁ + z₂)"])
    + guides(color=guide_legend(override_aes={"size": 4.5, "alpha": 1}))
    # Theme — refined from theme_minimal
    + theme_minimal()
    + theme(
        figure_size=(12, 12),
        text=element_text(family="sans-serif", size=14, color="#2C3E50"),
        plot_title=element_text(size=24, weight="bold", color="#1A1A2E", margin={"b": 18}),
        axis_title_x=element_text(size=20, color="#34495E", margin={"t": 12}),
        axis_title_y=element_text(size=20, color="#34495E", margin={"r": 12}),
        axis_text=element_text(size=16, color="#7F8C8D"),
        axis_ticks=element_line(color="#CCCCCC", size=0.3),
        axis_ticks_length=5,
        legend_text=element_text(size=15, color="#2C3E50"),
        legend_title=element_text(size=17, weight="bold", color="#1A1A2E"),
        legend_position="bottom",
        legend_background=element_rect(fill="#FFFFFF", color="#D5D8DC", size=0.5),
        legend_key=element_rect(fill="none", color="none"),
        legend_margin=12,
        panel_background=element_rect(fill="#F8F9FA", color="none"),
        plot_background=element_rect(fill="#FFFFFF", color="none"),
        panel_grid_major=element_line(color="#E8E8E8", size=0.25),
        panel_grid_minor=element_blank(),
    )
)

# Save — square format for optimal canvas utilization with equal aspect ratio
plot.save("plot.png", dpi=300, verbose=False)
