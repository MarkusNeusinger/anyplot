""" pyplots.ai
stereonet-equal-area: Structural Geology Stereonet (Equal-Area Projection)
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 83/100 | Created: 2026-03-15
"""

import matplotlib
import numpy as np
import pandas as pd
from plotnine import (
    aes,
    after_stat,
    coord_fixed,
    element_blank,
    element_text,
    geom_density_2d,
    geom_path,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    guides,
    labs,
    scale_alpha_continuous,
    scale_color_manual,
    scale_shape_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)


matplotlib.use("Agg")

# Data - Geological field measurements (strike/dip for bedding, faults, joints)
np.random.seed(42)

bedding_strike = np.random.normal(45, 12, 40)
bedding_dip = np.clip(np.random.normal(30, 8, 40), 5, 85)

fault_strike = np.random.normal(150, 15, 25)
fault_dip = np.clip(np.random.normal(65, 10, 25), 10, 88)

joint_strike = np.random.normal(280, 20, 35)
joint_dip = np.clip(np.random.normal(75, 8, 35), 15, 89)

strikes = np.concatenate([bedding_strike, fault_strike, joint_strike]) % 360
dips = np.concatenate([bedding_dip, fault_dip, joint_dip])
feature_types = ["Bedding"] * 40 + ["Fault"] * 25 + ["Joint"] * 35

# Primitive circle radius for equal-area projection
r_prim = np.sqrt(2)

# Compute poles (equal-area Schmidt projection)
pole_trend = np.radians((strikes + 90) % 360)
pole_plunge = np.radians(90 - dips)
pole_r = np.sqrt(2) * np.sin((np.pi / 2 - pole_plunge) / 2)
pole_x = pole_r * np.sin(pole_trend)
pole_y = pole_r * np.cos(pole_trend)
poles_df = pd.DataFrame({"x": pole_x, "y": pole_y, "feature_type": feature_types})

# Compute great circles for representative planes
gc_rows = []
gc_indices = {"Bedding": [0, 10, 20, 30], "Fault": [40, 48, 56], "Joint": [65, 75, 85]}
gc_id = 0
for ftype, indices in gc_indices.items():
    for idx in indices:
        if idx >= len(strikes):
            continue
        strike_rad = np.radians(strikes[idx])
        dip_rad = np.radians(dips[idx])
        strike_vec = np.array([np.sin(strike_rad), np.cos(strike_rad), 0.0])
        dip_dir_rad = strike_rad + np.pi / 2
        dip_vec = np.array(
            [np.sin(dip_dir_rad) * np.cos(dip_rad), np.cos(dip_dir_rad) * np.cos(dip_rad), -np.sin(dip_rad)]
        )
        for a in np.linspace(-np.pi / 2, np.pi / 2, 181):
            pt = np.cos(a) * dip_vec + np.sin(a) * strike_vec
            if pt[2] > 0:
                pt = -pt
            horiz = np.sqrt(pt[0] ** 2 + pt[1] ** 2)
            plunge = np.arctan2(-pt[2], horiz)
            trend = np.arctan2(pt[0], pt[1])
            r = np.sqrt(2) * np.sin((np.pi / 2 - plunge) / 2)
            x, y = r * np.sin(trend), r * np.cos(trend)
            if x**2 + y**2 <= r_prim**2 * 1.01:
                gc_rows.append({"x": x, "y": y, "feature_type": ftype, "gc_id": f"{ftype}_{gc_id}"})
        gc_id += 1

gc_df = pd.DataFrame(gc_rows)

# Stereonet grid - primitive circle
circle_angles = np.linspace(0, 2 * np.pi, 361)
prim_df = pd.DataFrame({"x": r_prim * np.cos(circle_angles), "y": r_prim * np.sin(circle_angles), "group": "primitive"})

# Equal-area net grid lines (small circles at 30° dip intervals)
grid_rows = []
for dip_interval in range(30, 90, 30):
    plunge_rad = np.radians(90 - dip_interval)
    r_circle = np.sqrt(2) * np.sin((np.pi / 2 - plunge_rad) / 2)
    for angle in np.linspace(0, 2 * np.pi, 181):
        gx = r_circle * np.cos(angle)
        gy = r_circle * np.sin(angle)
        grid_rows.append({"x": gx, "y": gy, "grid_id": f"dip_{dip_interval}"})

# Radial lines at 30° azimuth intervals
for az in range(0, 360, 30):
    az_rad = np.radians(az)
    for t in np.linspace(0, r_prim, 50):
        grid_rows.append({"x": t * np.sin(az_rad), "y": t * np.cos(az_rad), "grid_id": f"az_{az}"})

grid_df = pd.DataFrame(grid_rows)

# Degree tick marks every 10 degrees
tick_rows = []
for deg in range(0, 360, 10):
    rad = np.radians(deg)
    inner = r_prim * 0.97
    outer = r_prim * 1.0
    tick_rows.append(
        {"x1": inner * np.sin(rad), "y1": inner * np.cos(rad), "x2": outer * np.sin(rad), "y2": outer * np.cos(rad)}
    )
tick_df = pd.DataFrame(tick_rows)

# Cardinal direction labels
dir_labels = []
for deg, label in [(0, "N"), (90, "E"), (180, "S"), (270, "W")]:
    rad = np.radians(deg)
    offset = r_prim * 1.12
    dir_labels.append({"x": offset * np.sin(rad), "y": offset * np.cos(rad), "label": label})
dir_df = pd.DataFrame(dir_labels)

# Degree labels every 30 degrees (excluding cardinal directions)
deg_labels = []
for deg in range(0, 360, 30):
    if deg in (0, 90, 180, 270):
        continue
    rad = np.radians(deg)
    offset = r_prim * 1.08
    deg_labels.append({"x": offset * np.sin(rad), "y": offset * np.cos(rad), "label": f"{deg}°"})
deg_label_df = pd.DataFrame(deg_labels)

# Cluster centroid annotations for data storytelling
annotations = []
for ftype in ["Bedding", "Fault", "Joint"]:
    mask = poles_df["feature_type"] == ftype
    cx, cy = poles_df.loc[mask, "x"].mean(), poles_df.loc[mask, "y"].mean()
    mean_strike = strikes[np.array(feature_types) == ftype].mean()
    mean_dip = dips[np.array(feature_types) == ftype].mean()
    annotations.append({"x": cx, "y": cy - 0.12, "feature_type": ftype, "label": f"{mean_strike:.0f}°/{mean_dip:.0f}°"})
annot_df = pd.DataFrame(annotations)

# Colors (colorblind-safe)
colors = {"Bedding": "#306998", "Fault": "#E5A023", "Joint": "#7B68A0"}
shapes = {"Bedding": "o", "Fault": "D", "Joint": "s"}

# Plot - using plotnine's geom_density_2d (stat_density_2d) for Kamb-style contouring
plot = (
    ggplot()
    # Grid lines (subtle equal-area net)
    + geom_path(aes(x="x", y="y", group="grid_id"), data=grid_df, color="#CCCCCC", size=0.3, alpha=0.5)
    # Primitive circle
    + geom_path(aes(x="x", y="y"), data=prim_df, color="#333333", size=1.2)
    # Tick marks
    + geom_segment(aes(x="x1", y="y1", xend="x2", yend="y2"), data=tick_df, color="#333333", size=0.5)
    # Density contours using plotnine's native stat_density_2d via geom_density_2d
    # after_stat maps computed density level to alpha for visual depth
    + geom_density_2d(
        aes(x="x", y="y", alpha=after_stat("level")), data=poles_df, color="#666666", size=0.6, linetype="dashed"
    )
    + scale_alpha_continuous(range=(0.3, 0.8))
    + guides(alpha=False)
    # Great circles
    + geom_path(aes(x="x", y="y", color="feature_type", group="gc_id"), data=gc_df, size=0.9, alpha=0.7)
    # Poles to planes
    + geom_point(
        aes(x="x", y="y", color="feature_type", shape="feature_type"), data=poles_df, size=3.5, alpha=0.85, stroke=0.5
    )
    # Cardinal directions
    + geom_text(aes(x="x", y="y", label="label"), data=dir_df, size=18, fontweight="bold", color="#222222")
    # Degree labels (increased size for readability)
    + geom_text(aes(x="x", y="y", label="label"), data=deg_label_df, size=13, color="#444444")
    # Cluster orientation annotations
    + geom_text(
        aes(x="x", y="y", label="label", color="feature_type"),
        data=annot_df,
        size=11,
        fontstyle="italic",
        show_legend=False,
    )
    + scale_color_manual(name="Feature Type", values=colors)
    + scale_shape_manual(name="Feature Type", values=shapes)
    + coord_fixed(ratio=1)
    + scale_x_continuous(limits=(-1.85, 1.85))
    + scale_y_continuous(limits=(-1.85, 1.85))
    + labs(title="stereonet-equal-area · plotnine · pyplots.ai")
    + theme(
        figure_size=(12, 12),
        plot_title=element_text(size=24, ha="center"),
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        panel_background=element_blank(),
        plot_background=element_blank(),
        legend_title=element_text(size=16, weight="bold"),
        legend_text=element_text(size=14),
        legend_position="right",
    )
)

# Save
plot.save("plot.png", dpi=300)
