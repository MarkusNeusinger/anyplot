""" pyplots.ai
scatter-complex-plane: Complex Plane Visualization (Argand Diagram)
Library: letsplot 4.8.2 | Python 3.14.3
Quality: 86/100 | Created: 2026-03-04
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Data - Complex numbers: 5th roots of unity + arbitrary points
np.random.seed(42)

n_roots = 5
roots_angles = np.array([2 * np.pi * k / n_roots for k in range(n_roots)])
roots_real = np.cos(roots_angles)
roots_imag = np.sin(roots_angles)
roots_labels = [f"\u03c9{k}" for k in range(n_roots)]

arbitrary_real = np.array([1.8, -2.0, 0.5, -0.4, 2.3, -1.6])
arbitrary_imag = np.array([1.3, -1.4, 2.1, -1.9, -0.5, 0.7])
arbitrary_labels = [f"z{i + 1}" for i in range(len(arbitrary_real))]

sum_real = np.array([roots_real[1] + roots_real[2]])
sum_imag = np.array([roots_imag[1] + roots_imag[2]])
sum_labels = ["\u03c91+\u03c92"]

all_real = np.concatenate([roots_real, arbitrary_real, sum_real])
all_imag = np.concatenate([roots_imag, arbitrary_imag, sum_imag])
all_labels = roots_labels + arbitrary_labels + sum_labels
all_category = ["5th Root of Unity"] * n_roots + ["Arbitrary"] * len(arbitrary_real) + ["Sum"]

# Compute magnitude and angle for each point
all_mag = np.sqrt(all_real**2 + all_imag**2)
all_angle_deg = np.degrees(np.arctan2(all_imag, all_real))

# Rectangular form annotations
rect_labels = []
for r, i in zip(all_real, all_imag, strict=True):
    sign = "+" if i >= 0 else "\u2212"
    rect_labels.append(f"{r:.2f}{sign}{abs(i):.2f}i")

# Polar form annotations (visible in static PNG)
polar_labels = []
for mag, ang in zip(all_mag, all_angle_deg, strict=True):
    polar_labels.append(f"r={mag:.2f}, \u03b8={ang:.0f}\u00b0")

df = pd.DataFrame(
    {
        "real": all_real,
        "imaginary": all_imag,
        "label": all_labels,
        "category": all_category,
        "rect_form": rect_labels,
        "polar_form": polar_labels,
        "magnitude": all_mag,
        "angle_deg": all_angle_deg,
    }
)

# Smart label placement: offset radially outward
angles = np.arctan2(all_imag, all_real)
base_offset = 0.45
label_x = all_real + base_offset * np.cos(angles)
label_y = all_imag + base_offset * np.sin(angles) + 0.18

# Resolve crowded labels with simple repulsion
min_sep_x = 1.2
min_sep_y = 0.6
for _ in range(12):
    for i in range(len(label_x)):
        for j in range(i + 1, len(label_x)):
            dx = label_x[i] - label_x[j]
            dy = label_y[i] - label_y[j]
            norm_dist = np.sqrt((dx / min_sep_x) ** 2 + (dy / min_sep_y) ** 2)
            if norm_dist < 1.0:
                push = 0.2 * (1.0 - norm_dist) / max(norm_dist, 0.01)
                label_x[i] += dx * push
                label_y[i] += dy * push
                label_x[j] -= dx * push
                label_y[j] -= dy * push

df["label_x"] = label_x
df["label_y"] = label_y

# Arrow data (vectors from origin to each point)
arrows_df = pd.DataFrame(
    {
        "x_start": np.zeros(len(all_real)),
        "y_start": np.zeros(len(all_real)),
        "x_end": all_real,
        "y_end": all_imag,
        "category": all_category,
    }
)

# Unit circle
theta = np.linspace(0, 2 * np.pi, 200)
circle_df = pd.DataFrame({"x": np.cos(theta), "y": np.sin(theta)})

# Colors: blue for roots, orange for arbitrary, magenta for sum
colors = ["#306998", "#E3882D", "#AA3377"]

# Tooltips: distinctive lets-plot feature for HTML interactivity
point_tooltips = (
    layer_tooltips()  # noqa: F405
    .title("@label")
    .line("Category|@category")
    .line("Rectangular|@rect_form")
    .line("Polar|@polar_form")
    .format("magnitude", ".3f")
    .format("angle_deg", ".1f")
)

# Plot
plot = (
    ggplot()  # noqa: F405
    # Unit circle filled region (subtle)
    + geom_polygon(  # noqa: F405
        data=circle_df,
        mapping=aes(x="x", y="y"),  # noqa: F405
        fill="#EAF0FA",
        alpha=0.45,
        color="rgba(0,0,0,0)",
    )
    # Unit circle (dashed reference)
    + geom_path(  # noqa: F405
        data=circle_df,
        mapping=aes(x="x", y="y"),  # noqa: F405
        color="#8893A8",
        size=1.1,
        linetype="dashed",
    )
    # Axes through origin
    + geom_hline(yintercept=0, color="#AAAAAA", size=0.5)  # noqa: F405
    + geom_vline(xintercept=0, color="#AAAAAA", size=0.5)  # noqa: F405
    # Vectors from origin
    + geom_segment(  # noqa: F405
        data=arrows_df,
        mapping=aes(  # noqa: F405
            x="x_start", y="y_start", xend="x_end", yend="y_end", color="category"
        ),
        size=1.3,
        alpha=0.7,
        arrow=arrow(length=13, type="open"),  # noqa: F405
    )
    # Points with interactive tooltips
    + geom_point(  # noqa: F405
        data=df,
        mapping=aes(x="real", y="imaginary", color="category"),  # noqa: F405
        size=8,
        alpha=0.95,
        shape=21,
        fill="#FFFFFF",
        stroke=2.8,
        tooltips=point_tooltips,
    )
    # Point labels (name) - positioned radially outward
    + geom_text(  # noqa: F405
        data=df,
        mapping=aes(  # noqa: F405
            x="label_x", y="label_y", label="label", color="category"
        ),
        size=14,
        fontface="bold",
    )
    # Coordinate annotations (a+bi form) positioned below labels
    + geom_text(  # noqa: F405
        data=df,
        mapping=aes(x="label_x", y="label_y", label="rect_form"),  # noqa: F405
        size=10,
        color="#555555",
        nudge_y=-0.24,
    )
    # Polar form annotations (r, theta) below rectangular form
    + geom_text(  # noqa: F405
        data=df,
        mapping=aes(x="label_x", y="label_y", label="polar_form"),  # noqa: F405
        size=9,
        color="#777777",
        fontface="italic",
        nudge_y=-0.46,
    )
    # Scales
    + scale_color_manual(values=colors)  # noqa: F405
    + coord_fixed()  # noqa: F405
    + labs(  # noqa: F405
        x="Real Part",
        y="Imaginary Part",
        title="scatter-complex-plane \u00b7 letsplot \u00b7 pyplots.ai",
        subtitle="5th roots of unity, arbitrary points, and complex addition on the Argand diagram",
        color="Category",
    )
    + scale_x_continuous(  # noqa: F405
        breaks=[-3, -2, -1, 0, 1, 2, 3], expand=[0.12, 0.12]
    )
    + scale_y_continuous(  # noqa: F405
        breaks=[-3, -2, -1, 0, 1, 2, 3], expand=[0.12, 0.12]
    )
    + flavor_high_contrast_light()  # noqa: F405
    + theme(  # noqa: F405
        plot_title=element_text(  # noqa: F405
            size=26, color="#1a1a1a", face="bold"
        ),
        plot_subtitle=element_text(  # noqa: F405
            size=17, color="#555555", face="italic"
        ),
        axis_title=element_text(size=21, color="#333333"),  # noqa: F405
        axis_text=element_text(size=17, color="#555555"),  # noqa: F405
        legend_title=element_text(size=19),  # noqa: F405
        legend_text=element_text(size=17),  # noqa: F405
        panel_grid_major=element_line(color="#E0E0E0", size=0.25),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
        plot_margin=[35, 55, 25, 25],
    )
    + ggsize(1600, 900)  # noqa: F405
)

# Save
export_ggsave(plot, filename="plot.png", path=".", scale=3)
export_ggsave(plot, filename="plot.html", path=".")
