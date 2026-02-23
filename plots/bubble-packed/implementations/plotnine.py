""" pyplots.ai
bubble-packed: Basic Packed Bubble Chart
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 90/100 | Updated: 2026-02-23
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_rect,
    element_text,
    geom_polygon,
    geom_text,
    ggplot,
    guides,
    labs,
    scale_alpha_manual,
    scale_fill_manual,
    theme,
    theme_void,
)


# Data - department budgets (in millions)
departments = {
    "label": [
        "Engineering",
        "Marketing",
        "Sales",
        "Operations",
        "HR",
        "Finance",
        "R&D",
        "IT Support",
        "Legal",
        "Customer Svc",
        "Design",
        "Logistics",
        "Quality",
        "Training",
        "Admin",
    ],
    "value": [45, 32, 28, 22, 15, 18, 38, 12, 10, 20, 14, 16, 8, 6, 5],
    "group": [
        "Tech",
        "Business",
        "Business",
        "Operations",
        "Support",
        "Business",
        "Tech",
        "Tech",
        "Support",
        "Operations",
        "Tech",
        "Operations",
        "Operations",
        "Support",
        "Support",
    ],
}

df = pd.DataFrame(departments)

# Scale values to radii (area-based scaling for accurate perception)
max_radius = 1.0
min_radius = 0.25
df["radius"] = min_radius + (max_radius - min_radius) * np.sqrt(df["value"] / df["value"].max())

# Circle packing - greedy placement with vectorized collision detection
n = len(df)
radii = df["radius"].values
idx = np.argsort(-radii)
sorted_radii = radii[idx]
gap = 0.03

x = np.zeros(n)
y = np.zeros(n)
angles_sweep = np.linspace(0, 2 * np.pi, 72, endpoint=False)

for i in range(1, n):
    best_dist = float("inf")
    best_x, best_y = 0.0, 0.0
    target_r = sorted_radii[i]

    for ref in range(i):
        place_r = sorted_radii[ref] + target_r + gap
        cx = x[ref] + place_r * np.cos(angles_sweep)
        cy = y[ref] + place_r * np.sin(angles_sweep)

        # Vectorized collision check across all angles simultaneously
        dx_c = cx[:, np.newaxis] - x[:i][np.newaxis, :]
        dy_c = cy[:, np.newaxis] - y[:i][np.newaxis, :]
        dists_c = np.hypot(dx_c, dy_c)
        valid = np.all(dists_c >= target_r + sorted_radii[:i] + gap, axis=1)

        center_dists = cx**2 + cy**2
        valid_dists = np.where(valid, center_dists, float("inf"))
        best_k = np.argmin(valid_dists)
        if valid_dists[best_k] < best_dist:
            best_dist = valid_dists[best_k]
            best_x, best_y = cx[best_k], cy[best_k]

    x[i] = best_x
    y[i] = best_y

# Force simulation to tighten packing (vectorized with numpy)
tri = np.triu(np.ones((n, n), dtype=bool), k=1)
min_dists = sorted_radii[:, np.newaxis] + sorted_radii[np.newaxis, :] + gap

for _ in range(2000):
    x *= 0.997
    y *= 0.997

    dx = x[:, np.newaxis] - x[np.newaxis, :]
    dy = y[:, np.newaxis] - y[np.newaxis, :]
    dists = np.hypot(dx, dy)

    overlap = tri & (dists < min_dists) & (dists > 1e-3)
    if overlap.any():
        safe_dists = np.where(dists > 1e-3, dists, 1.0)
        push = ((min_dists - dists) / (2 * safe_dists)) * overlap
        corr_x = push * dx
        corr_y = push * dy
        x += corr_x.sum(axis=1) - corr_x.sum(axis=0)
        y += corr_y.sum(axis=1) - corr_y.sum(axis=0)

# Restore original order
x_final = np.zeros(n)
y_final = np.zeros(n)
for i, orig_idx in enumerate(idx):
    x_final[orig_idx] = x[i]
    y_final[orig_idx] = y[i]

df["x"] = x_final
df["y"] = y_final

# Build circle polygons for geom_polygon
circle_dfs = []
angles = np.linspace(0, 2 * np.pi, 64)
for i, row in df.iterrows():
    cx = row["x"] + row["radius"] * np.cos(angles)
    cy = row["y"] + row["radius"] * np.sin(angles)
    circle_dfs.append(pd.DataFrame({"x": cx, "y": cy, "label": row["label"], "group": row["group"], "circle_id": i}))
circles_df = pd.concat(circle_dfs, ignore_index=True)
circles_df["group"] = pd.Categorical(circles_df["group"], categories=["Tech", "Business", "Operations", "Support"])

# Labels - conditional sizing: full name for large, abbreviated for small
labels_df = df.copy()
labels_df["display_label"] = labels_df.apply(
    lambda row: (
        row["label"] if row["value"] >= 22 else (row["label"].split()[0] if row["value"] >= 10 else row["label"][:4])
    ),
    axis=1,
)
labels_df["value_label"] = labels_df["value"].apply(lambda v: f"${v}M")

# Alpha by group emphasis — Tech & Business slightly more prominent
alpha_values = {"Tech": 0.90, "Business": 0.85, "Operations": 0.78, "Support": 0.75}

# Color palette - Okabe-Ito colorblind-safe
group_colors = {"Tech": "#0072B2", "Business": "#E69F00", "Operations": "#009E73", "Support": "#CC79A7"}

# Compute group totals for subtitle
group_totals = df.groupby("group")["value"].sum()
subtitle_text = " \u00b7 ".join(f"{g}: \\${group_totals[g]}M" for g in ["Tech", "Business", "Operations", "Support"])

# Tight viewport bounds for optimal canvas utilization
pad = 0.15
x_lo = (df["x"] - df["radius"]).min() - pad
x_hi = (df["x"] + df["radius"]).max() + pad
y_lo = (df["y"] - df["radius"]).min() - pad
y_hi = (df["y"] + df["radius"]).max() + pad
half_span = max(x_hi - x_lo, y_hi - y_lo) / 2
cx_mid, cy_mid = (x_lo + x_hi) / 2, (y_lo + y_hi) / 2

# Plot with layered grammar of graphics composition
plot = (
    ggplot()
    # Layer 1: Circle fills with group-specific alpha
    + geom_polygon(
        data=circles_df,
        mapping=aes(x="x", y="y", fill="group", group="circle_id", alpha="group"),
        color="white",
        size=0.8,
    )
    # Layer 2: Department name labels (bold, white)
    + geom_text(
        data=labels_df[labels_df["value"] >= 10],
        mapping=aes(x="x", y="y", label="display_label"),
        size=12,
        color="white",
        fontweight="bold",
        nudge_y=0.10,
    )
    # Layer 3: Small bubble labels
    + geom_text(
        data=labels_df[labels_df["value"] < 10],
        mapping=aes(x="x", y="y", label="display_label"),
        size=10,
        color="white",
        fontweight="bold",
    )
    # Layer 4: Budget value annotations for large/medium bubbles
    + geom_text(
        data=labels_df[labels_df["value"] >= 12],
        mapping=aes(x="x", y="y", label="value_label"),
        size=10,
        color="white",
        alpha=0.85,
        nudge_y=-0.17,
    )
    # Scales
    + scale_fill_manual(values=group_colors, name="Department Group")
    + scale_alpha_manual(values=alpha_values)
    + guides(alpha=False)
    # Tight viewport with coord_fixed for 1:1 aspect ratio
    + coord_fixed(xlim=(cx_mid - half_span, cx_mid + half_span), ylim=(cy_mid - half_span, cy_mid + half_span))
    + labs(title="bubble-packed \u00b7 plotnine \u00b7 pyplots.ai", subtitle=subtitle_text)
    # Theme — plotnine's distinctive void theme with layered customization
    + theme_void()
    + theme(
        figure_size=(12, 12),
        plot_title=element_text(size=24, ha="center", weight="bold", margin={"b": 5}),
        plot_subtitle=element_text(size=16, ha="center", color="#555555", margin={"t": 5, "b": 10}),
        legend_title=element_text(size=18, weight="bold"),
        legend_text=element_text(size=16),
        legend_position="bottom",
        legend_direction="horizontal",
        legend_key=element_rect(fill="white", color="none"),
        legend_key_size=20,
        plot_background=element_rect(fill="white", color="none"),
        plot_margin=0.02,
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
