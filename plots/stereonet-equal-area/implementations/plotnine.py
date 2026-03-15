"""pyplots.ai
stereonet-equal-area: Structural Geology Stereonet (Equal-Area Projection)
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 82/100 | Created: 2026-03-15
"""

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_blank,
    element_text,
    geom_path,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    labs,
    scale_color_manual,
    scale_shape_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)
from scipy.ndimage import gaussian_filter


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

# Compute great circles (sample representative planes per type)
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
        angles = np.linspace(-np.pi / 2, np.pi / 2, 181)
        for a in angles:
            pt = np.cos(a) * dip_vec + np.sin(a) * strike_vec
            if pt[2] > 0:
                pt = -pt
            horiz = np.sqrt(pt[0] ** 2 + pt[1] ** 2)
            plunge = np.arctan2(-pt[2], horiz)
            trend = np.arctan2(pt[0], pt[1])
            r = np.sqrt(2) * np.sin((np.pi / 2 - plunge) / 2)
            x = r * np.sin(trend)
            y = r * np.cos(trend)
            if x**2 + y**2 <= r_prim**2 * 1.01:
                gc_rows.append({"x": x, "y": y, "feature_type": ftype, "gc_id": f"{ftype}_{gc_id}"})
        gc_id += 1

gc_df = pd.DataFrame(gc_rows)

# Stereonet grid - primitive circle
circle_angles = np.linspace(0, 2 * np.pi, 361)
prim_df = pd.DataFrame({"x": r_prim * np.cos(circle_angles), "y": r_prim * np.sin(circle_angles), "group": "primitive"})

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
    offset = r_prim * 1.07
    deg_labels.append({"x": offset * np.sin(rad), "y": offset * np.cos(rad), "label": f"{deg}°"})
deg_label_df = pd.DataFrame(deg_labels)

# Density contours (Kamb-style kernel density on projected pole coordinates)
grid_res = 200
gx_lin = np.linspace(-r_prim, r_prim, grid_res)
gy_lin = np.linspace(-r_prim, r_prim, grid_res)
gx_grid, gy_grid = np.meshgrid(gx_lin, gy_lin)
density = np.zeros_like(gx_grid)

sigma = 0.15
for i in range(len(pole_x)):
    dist_sq = (gx_grid - pole_x[i]) ** 2 + (gy_grid - pole_y[i]) ** 2
    density += np.exp(-dist_sq / (2 * sigma**2))

density = gaussian_filter(density, sigma=3)
circle_mask = gx_grid**2 + gy_grid**2 > r_prim**2
density[circle_mask] = np.nan

# Extract contour coordinates (using matplotlib for numerical contour extraction only)
fig_tmp, ax_tmp = plt.subplots()
valid_density = density[~np.isnan(density)]
levels = np.linspace(valid_density.max() * 0.2, valid_density.max() * 0.8, 5)
cs = ax_tmp.contour(gx_lin, gy_lin, density, levels=levels)
plt.close(fig_tmp)

contour_rows = []
contour_id = 0
for level_segs in cs.allsegs:
    for seg in level_segs:
        if len(seg) > 0:
            for xi, yi in seg:
                if xi**2 + yi**2 <= r_prim**2 * 1.01:
                    contour_rows.append({"x": xi, "y": yi, "contour_id": contour_id})
            contour_id += 1

contour_df = pd.DataFrame(contour_rows) if contour_rows else pd.DataFrame({"x": [], "y": [], "contour_id": []})

# Colors (colorblind-safe: blue, orange, purple)
colors = {"Bedding": "#306998", "Fault": "#E5A023", "Joint": "#7B68A0"}
shapes = {"Bedding": "o", "Fault": "D", "Joint": "s"}

# Plot
plot = (
    ggplot()
    + geom_path(aes(x="x", y="y"), data=prim_df, color="#333333", size=1.2)
    + geom_segment(aes(x="x1", y="y1", xend="x2", yend="y2"), data=tick_df, color="#333333", size=0.5)
    + geom_path(
        aes(x="x", y="y", group="contour_id"), data=contour_df, color="#777777", size=0.7, alpha=0.7, linetype="dashed"
    )
    + geom_path(aes(x="x", y="y", color="feature_type", group="gc_id"), data=gc_df, size=0.9, alpha=0.7)
    + geom_point(
        aes(x="x", y="y", color="feature_type", shape="feature_type"), data=poles_df, size=3.5, alpha=0.85, stroke=0.5
    )
    + geom_text(aes(x="x", y="y", label="label"), data=dir_df, size=18, fontweight="bold", color="#222222")
    + geom_text(aes(x="x", y="y", label="label"), data=deg_label_df, size=10, color="#555555")
    + scale_color_manual(name="Feature Type", values=colors)
    + scale_shape_manual(name="Feature Type", values=shapes)
    + coord_fixed(ratio=1)
    + scale_x_continuous(limits=(-1.8, 1.8))
    + scale_y_continuous(limits=(-1.8, 1.8))
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
