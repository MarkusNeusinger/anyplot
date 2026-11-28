"""anyplot.ai
scatter-complex-plane: Complex Plane Visualization (Argand Diagram)
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 88/100 | Updated: 2026-06-02
"""

import os

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


# Theme-adaptive chrome tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
REAL = "Re(z)"  # role: real
IMAG = "Im(z)"  # role: imaginary
LABEL = "Name"  # role: label
CATEGORY = "Category"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("complex_numbers.csv")
n_roots = 6
angles_roots = 2 * np.pi * np.arange(n_roots) / n_roots
arbitrary_real = np.array([1.5, -0.9, 0.4, -1.7])
arbitrary_imag = np.array([0.6, 1.1, -1.8, -0.8])
df = pd.DataFrame(
    {
        REAL: np.concatenate([np.cos(angles_roots), arbitrary_real, [arbitrary_real[0] + arbitrary_real[1]]]),
        IMAG: np.concatenate([np.sin(angles_roots), arbitrary_imag, [arbitrary_imag[0] + arbitrary_imag[1]]]),
        LABEL: [f"ω{k}" for k in range(n_roots)] + ["z₁", "z₂", "z₃", "z₄"] + ["z₁+z₂"],
        CATEGORY: ["6th Root of Unity (∣z∣ = 1)"] * n_roots + ["Arbitrary Point"] * 4 + ["Sum (z₁+z₂)"],
    }
)

# Plot: reads only df and the constants above
real = df[REAL].to_numpy()
imag = df[IMAG].to_numpy()
categories = df[CATEGORY].unique().tolist()
colors = IMPRINT_PALETTE[: len(categories)]
is_first = (df[CATEGORY] == categories[0]).to_numpy()
is_last = (df[CATEGORY] == categories[-1]).to_numpy()

# Annotation text: point name + rectangular form (a+bi)
df["annotation"] = [
    f"{lbl} = {r:.2f}{'+' if i >= 0 else '−'}{abs(i):.2f}i" for lbl, r, i in zip(df[LABEL], real, imag, strict=True)
]

# Vectors from origin to each point
df_vectors = pd.DataFrame({"x": 0.0, "y": 0.0, "xend": real, "yend": imag, CATEGORY: df[CATEGORY]})

# Unit circle reference
theta = np.linspace(0, 2 * np.pi, 300)
df_circle = pd.DataFrame({"x": np.cos(theta), "y": np.sin(theta)})

# Radial label offsets — spread labels away from vectors to reduce crowding
angles = np.arctan2(imag, real)
label_radius = 0.46
is_left = np.cos(angles) >= 0
df_labels = pd.DataFrame(
    {
        "x": real + label_radius * np.cos(angles),
        "y": imag + label_radius * np.sin(angles),
        "annotation": df["annotation"],
    }
)

# Visual hierarchy via point size (few data points → prominent markers)
df["pt_size"] = np.select([is_first, is_last], [3.5, 5.5], default=4.0)
df["pt_alpha"] = np.select([is_first, is_last], [0.90, 1.0], default=0.95)

# Axis range from the data: whole units outside the farthest point, ticks at integers
limit = np.ceil(np.nanmax(np.abs(np.concatenate([real, imag])))) + 0.5
step = 10 ** np.floor(np.log10(limit))
ticks = np.arange(-np.floor(limit / step), np.floor(limit / step) + 1) * step
unit_label_angle = np.deg2rad(50)

plot = (
    ggplot()
    # Reference axes through origin
    + geom_hline(yintercept=0, color=INK_SOFT, size=0.4, linetype="solid", alpha=0.4)
    + geom_vline(xintercept=0, color=INK_SOFT, size=0.4, linetype="solid", alpha=0.4)
    # Unit circle — dashed reference
    + geom_path(df_circle, aes(x="x", y="y"), color=INK_MUTED, linetype="dashed", size=0.7, alpha=0.65)
    + annotate(
        "text",
        x=np.cos(unit_label_angle),
        y=np.sin(unit_label_angle),
        label="∣z∣ = 1",
        size=5.5,
        color=INK_SOFT,
        fontstyle="italic",
        angle=50,
    )
    # Vectors from origin (no parallelogram construction lines)
    + geom_segment(
        df_vectors,
        aes(x="x", y="y", xend="xend", yend="yend", color=CATEGORY),
        size=0.55,
        alpha=0.50,
        arrow=arrow(length=0.09, type="closed"),
    )
    # Points — main scatter layer with visual hierarchy
    + geom_point(df, aes(x=REAL, y=IMAG, color=CATEGORY, size="pt_size", alpha="pt_alpha"))
    + scale_size_identity()
    + scale_alpha_identity()
    # Halo ring on roots of unity for emphasis
    + geom_point(df[is_first], aes(x=REAL, y=IMAG), size=7.5, color=colors[0], alpha=0.12)
    # Annotation labels — split by horizontal alignment (plotnine limitation)
    + geom_label(
        df_labels[is_left],
        aes(x="x", y="y", label="annotation"),
        size=3.8,
        color=INK,
        fill=ELEVATED_BG,
        alpha=0.88,
        ha="left",
        fontweight="bold",
        label_padding=0.18,
        label_size=0.2,
        boxstyle="round,pad=0.2",
    )
    + geom_label(
        df_labels[~is_left],
        aes(x="x", y="y", label="annotation"),
        size=3.8,
        color=INK,
        fill=ELEVATED_BG,
        alpha=0.88,
        ha="right",
        fontweight="bold",
        label_padding=0.18,
        label_size=0.2,
        boxstyle="round,pad=0.2",
    )
    + labs(x=REAL, y=IMAG, title="scatter-complex-plane · python · plotnine · anyplot.ai", color=CATEGORY)
    + scale_x_continuous(limits=(-limit, limit), breaks=ticks)
    + scale_y_continuous(limits=(-limit, limit), breaks=ticks)
    + coord_fixed(ratio=1)
    + scale_color_manual(values=colors, limits=categories)
    + guides(color=guide_legend(override_aes={"size": 3.5, "alpha": 1.0}))
    + theme_minimal()
    + theme(
        figure_size=(6, 6),
        text=element_text(family="sans-serif", size=7, color=INK),
        plot_title=element_text(size=12, weight="bold", color=INK, margin={"b": 10}),
        axis_title_x=element_text(size=10, color=INK, margin={"t": 8}),
        axis_title_y=element_text(size=10, color=INK, margin={"r": 8}),
        axis_text=element_text(size=8, color=INK_SOFT),
        axis_ticks=element_line(color=INK_SOFT, size=0.3),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_title=element_text(size=9, weight="bold", color=INK),
        legend_position="bottom",
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT, size=0.4),
        legend_key=element_rect(fill="none", color="none"),
        panel_background=element_rect(fill=PAGE_BG, color="none"),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.2, alpha=0.15),
        panel_grid_minor=element_blank(),
        panel_border=element_blank(),
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=6, height=6, units="in", verbose=False)
