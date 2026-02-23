""" pyplots.ai
bubble-packed: Basic Packed Bubble Chart
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 88/100 | Updated: 2026-02-23
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
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

# Circle packing - greedy placement + force simulation
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
        for angle in angles_sweep:
            test_x = x[ref] + place_r * np.cos(angle)
            test_y = y[ref] + place_r * np.sin(angle)

            valid = all(
                np.sqrt((test_x - x[j]) ** 2 + (test_y - y[j]) ** 2) >= target_r + sorted_radii[j] + gap
                for j in range(i)
            )

            if valid:
                center_dist = test_x**2 + test_y**2
                if center_dist < best_dist:
                    best_dist = center_dist
                    best_x, best_y = test_x, test_y

    x[i] = best_x
    y[i] = best_y

# Force simulation to tighten packing
for _ in range(2000):
    x *= 0.997
    y *= 0.997

    for i in range(n):
        for j in range(i + 1, n):
            dx = x[j] - x[i]
            dy = y[j] - y[i]
            dist = np.sqrt(dx * dx + dy * dy)
            min_dist = sorted_radii[i] + sorted_radii[j] + gap

            if dist < min_dist and dist > 0.001:
                overlap = (min_dist - dist) / 2
                nx_d = dx / dist
                ny_d = dy / dist
                x[i] -= overlap * nx_d
                y[i] -= overlap * ny_d
                x[j] += overlap * nx_d
                y[j] += overlap * ny_d

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

# Value annotations below department names (data storytelling layer)
labels_df["value_label"] = labels_df["value"].apply(lambda v: f"${v}M")
# Offset value labels below center, scaled to circle size
labels_df["y_offset"] = labels_df["radius"] * 0.3

# Alpha by group emphasis — Tech & Business slightly more prominent
alpha_values = {"Tech": 0.90, "Business": 0.85, "Operations": 0.78, "Support": 0.75}

# Color palette - Okabe-Ito colorblind-safe
group_colors = {"Tech": "#0072B2", "Business": "#E69F00", "Operations": "#009E73", "Support": "#CC79A7"}

# Compute group totals for subtitle annotation
group_totals = df.groupby("group")["value"].sum()
subtitle_text = " · ".join(f"{g}: ${group_totals[g]}M" for g in ["Tech", "Business", "Operations", "Support"])

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
        nudge_y=0.08,
    )
    # Layer 3: Small bubble labels (smaller text)
    + geom_text(
        data=labels_df[labels_df["value"] < 10],
        mapping=aes(x="x", y="y", label="display_label"),
        size=8,
        color="white",
        fontweight="bold",
    )
    # Layer 4: Budget value annotations for large/medium bubbles
    + geom_text(
        data=labels_df[labels_df["value"] >= 12],
        mapping=aes(x="x", y="y", label="value_label"),
        size=9,
        color="white",
        alpha=0.85,
        nudge_y=-0.15,
    )
    # Scales
    + scale_fill_manual(values=group_colors, name="Department Group")
    + scale_alpha_manual(values=alpha_values)
    + guides(alpha=False)
    + coord_fixed()
    # Annotations
    + annotate("text", x=0, y=-3.6, label=subtitle_text, size=11, color="#555555")
    + labs(title="bubble-packed · plotnine · pyplots.ai")
    # Theme — plotnine's distinctive void theme with layered customization
    + theme_void()
    + theme(
        figure_size=(12, 12),
        plot_title=element_text(size=24, ha="center", weight="bold", margin={"b": 15}),
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
