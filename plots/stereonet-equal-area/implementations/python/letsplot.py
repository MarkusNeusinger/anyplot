"""anyplot.ai
stereonet-equal-area: Structural Geology Stereonet (Equal-Area Projection)
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-26
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_blank,
    element_rect,
    element_text,
    geom_contour,
    geom_path,
    geom_point,
    geom_polygon,
    geom_segment,
    geom_text,
    gggrid,
    ggplot,
    ggsize,
    labs,
    layer_tooltips,
    scale_color_manual,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme-adaptive chrome (Imprint design tokens)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
RULE = "#D8D4C8" if THEME == "light" else "#33332E"

# Imprint palette: all eight positions, one per feature class in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
STRIKE = "Strike (°)"  # role: strike
DIP = "Dip (°)"  # role: dip
DIP_DIRECTION = "Dip direction (°)"  # role: dip_direction
FEATURE_TYPE = "Feature Type"  # role: feature_type

# Data: replace this block with your own table, for example df = pd.read_csv("measurements.csv")
# Field measurements from a structural geology mapping campaign
np.random.seed(42)

# Bedding planes (NE strike ~045, moderate dip ~35° SE)
n_bedding = 25
bedding_strike = np.random.normal(45, 12, n_bedding) % 360
bedding_dip = np.clip(np.random.normal(35, 8, n_bedding), 5, 85)

# Joint set (N-S striking ~000, steep dip ~78° W)
n_joints = 20
joints_strike = np.random.normal(355, 10, n_joints) % 360
joints_dip = np.clip(np.random.normal(78, 7, n_joints), 10, 89)

# Faults (NW-SE striking ~150, moderate-steep dip ~60°)
n_faults = 13
faults_strike = np.random.uniform(130, 170, n_faults)
faults_dip = np.clip(np.random.normal(60, 12, n_faults), 10, 89)

# Foliation (E-W strike ~270, gentle dip ~25° N)
n_foliation = 12
foliation_strike = np.random.normal(270, 8, n_foliation) % 360
foliation_dip = np.clip(np.random.normal(25, 6, n_foliation), 5, 60)

strike_values = np.concatenate([bedding_strike, joints_strike, faults_strike, foliation_strike])
df = pd.DataFrame(
    {
        STRIKE: strike_values,
        DIP: np.concatenate([bedding_dip, joints_dip, faults_dip, foliation_dip]),
        DIP_DIRECTION: (strike_values + 90) % 360,
        FEATURE_TYPE: ["Bedding"] * n_bedding
        + ["Joint"] * n_joints
        + ["Fault"] * n_faults
        + ["Foliation"] * n_foliation,
    }
)

# Plot: reads only df and the constants above
# Derived columns used by the layers below
X, Y, XEND, YEND, GROUP, LABEL = "x", "y", "xend", "yend", "group", "label"

feature_types = list(dict.fromkeys(df[FEATURE_TYPE]))
strike_rad = np.radians(df[STRIKE].to_numpy())
dip_rad = np.radians(df[DIP].to_numpy())
dip_dir_rad = np.radians(df[DIP_DIRECTION].to_numpy())

# Equal-area (Schmidt net) lower-hemisphere projection of each pole
# The pole trends opposite the dip direction (azimuth dip_direction + 180) and plunges 90 - dip
pole_x_3d = -np.sin(dip_rad) * np.sin(dip_dir_rad)
pole_y_3d = -np.sin(dip_rad) * np.cos(dip_dir_rad)
pole_z_3d = -np.cos(dip_rad)
pole_scale = 1.0 / np.sqrt(1.0 - pole_z_3d)
poles_df = pd.DataFrame(
    {
        X: pole_x_3d * pole_scale,
        Y: pole_y_3d * pole_scale,
        FEATURE_TYPE: df[FEATURE_TYPE],
        "strike": [f"{s:.0f}°" for s in df[STRIKE]],
        "dip": [f"{d:.0f}°" for d in df[DIP]],
    }
)
pole_x = poles_df[X].to_numpy()
pole_y = poles_df[Y].to_numpy()

# Great circle path for each plane, clipped to the primitive circle
gc_frames = []
alphas = np.linspace(0, np.pi, 60)
for i in range(len(df)):
    sv_x, sv_y = np.sin(strike_rad[i]), np.cos(strike_rad[i])
    dv_x = np.cos(dip_rad[i]) * np.sin(dip_dir_rad[i])
    dv_y = np.cos(dip_rad[i]) * np.cos(dip_dir_rad[i])
    dv_z = -np.sin(dip_rad[i])
    px = np.cos(alphas) * sv_x + np.sin(alphas) * dv_x
    py = np.cos(alphas) * sv_y + np.sin(alphas) * dv_y
    pz = np.sin(alphas) * dv_z
    sc = 1.0 / np.sqrt(1.0 - pz)
    gx, gy = px * sc, py * sc
    inside = gx**2 + gy**2 <= 1.0
    gc_frames.append(pd.DataFrame({X: gx[inside], Y: gy[inside], GROUP: i, FEATURE_TYPE: df[FEATURE_TYPE].iloc[i]}))
gc_df = pd.concat(gc_frames, ignore_index=True)

# Primitive circle (outer boundary)
theta = np.linspace(0, 2 * np.pi, 200)
circle_df = pd.DataFrame({X: np.cos(theta), Y: np.sin(theta)})

# Kamb density with exponential smoothing (weight exp(k (|cos| - 1)) per pole, axial data), expressed in
# standard deviations above the count expected from a uniform distribution
n_poles = len(poles_df)
pole_vec = np.column_stack([pole_x_3d, pole_y_3d, pole_z_3d])
kamb_k = 2.0 * (1.0 + n_poles / 9.0)
mean_w = (1.0 - np.exp(-kamb_k)) / kamb_k
mean_w2 = (1.0 - np.exp(-2.0 * kamb_k)) / (2.0 * kamb_k)
expected = n_poles * mean_w
sigma = np.sqrt(n_poles * (mean_w2 - mean_w**2))
grid = np.linspace(-1.0, 1.0, 241)
gx_grid, gy_grid = np.meshgrid(grid, grid)
r2 = gx_grid**2 + gy_grid**2
inside_net = r2 <= 1.0
# Inverse Lambert projection back to the lower hemisphere (outside the net the cell stays empty)
k = np.sqrt(np.clip(2.0 - r2, 0.0, None))
cell_vec = np.stack([gx_grid * k, gy_grid * k, -(1.0 - r2)], axis=-1)
cos_angle = np.abs(cell_vec @ pole_vec.T)
counts = np.exp(kamb_k * (cos_angle - 1.0)).sum(axis=-1)
# Floor at 1.5 sigma so only the contours from 2 sigma upward are drawn, and none outside the net
kamb_sigma = np.where(inside_net, np.maximum((counts - expected) / sigma, 1.5), 1.5)
kamb_df = pd.DataFrame({X: gx_grid.ravel(), Y: gy_grid.ravel(), "kamb": kamb_sigma.ravel()})

# Tick marks every 10° (longer every 30°)
tick_degrees = np.arange(0, 360, 10)
tick_rad = np.radians(tick_degrees)
tick_inner = np.where(tick_degrees % 30 != 0, 0.95, 0.92)
tick_df = pd.DataFrame(
    {X: np.sin(tick_rad) * tick_inner, Y: np.cos(tick_rad) * tick_inner, XEND: np.sin(tick_rad), YEND: np.cos(tick_rad)}
)

# Reference cross lines (N-S, E-W)
ref_df = pd.DataFrame({X: [0, -1], Y: [-1, 0], XEND: [0, 1], YEND: [1, 0]})

# Cardinal direction labels
cardinal_df = pd.DataFrame({X: [0, 1.1, 0, -1.1], Y: [1.1, 0, -1.1, 0], LABEL: ["N", "E", "S", "W"]})

# Mean pole annotations and confidence ellipses per feature type
mean_rows = []
ellipse_frames = []
t = np.linspace(0, 2 * np.pi, 40)
for idx, ft in enumerate(feature_types):
    sel = (df[FEATURE_TYPE] == ft).to_numpy()
    mx, my = pole_x[sel].mean(), pole_y[sel].mean()
    # Circular mean for strike (handles wraparound at 0/360°)
    s_rad = strike_rad[sel]
    mean_strike = np.degrees(np.arctan2(np.sin(s_rad).mean(), np.cos(s_rad).mean())) % 360
    mean_dip = df[DIP].to_numpy()[sel].mean()
    # Place the label where it stays furthest from every pole, other labels and the cardinal letters
    best_score, nudge_x, nudge_y = -1.0, 0.0, -0.25
    obstacles = np.vstack(
        [
            np.column_stack([pole_x, pole_y]),
            cardinal_df[[X, Y]].to_numpy(),
            np.array([[r[X], r[Y]] for r in mean_rows]).reshape(-1, 2),
        ]
    )
    for ang in np.radians(np.arange(0, 360, 20)):
        for reach in (0.25, 0.35):
            cx, cy = mx + reach * np.cos(ang), my + reach * np.sin(ang)
            if np.hypot(cx, cy) > 1.0 - 0.12:
                continue
            score = np.hypot(obstacles[:, 0] - cx, obstacles[:, 1] - cy).min()
            if score > best_score:
                best_score, nudge_x, nudge_y = score, cx - mx, cy - my
    mean_rows.append(
        {X: mx, Y: my, LABEL: f"{ft}\n{mean_strike:.0f}/{mean_dip:.0f}", "nudge_x": nudge_x, "nudge_y": nudge_y}
    )
    # 1-sigma confidence ellipse around the cluster
    eigvals, eigvecs = np.linalg.eigh(np.cov(pole_x[sel], pole_y[sel]))
    angle = np.arctan2(eigvecs[1, 1], eigvecs[0, 1])
    ex = np.sqrt(eigvals[1]) * np.cos(t)
    ey = np.sqrt(eigvals[0]) * np.sin(t)
    ellipse_frames.append(
        pd.DataFrame(
            {
                X: mx + ex * np.cos(angle) - ey * np.sin(angle),
                Y: my + ex * np.sin(angle) + ey * np.cos(angle),
                GROUP: idx,
                FEATURE_TYPE: ft,
            }
        )
    )
ellipse_df = pd.concat(ellipse_frames, ignore_index=True)
mean_df = pd.DataFrame(mean_rows)

# Tooltips for poles showing strike/dip
pole_tooltips = layer_tooltips().line(f"@{{{FEATURE_TYPE}}}").line("Strike: @strike").line("Dip: @dip")

plot = (
    ggplot()
    # Reference cross lines
    + geom_segment(aes(x=X, y=Y, xend=XEND, yend=YEND), data=ref_df, color=RULE, size=0.5, linetype="dashed")
    # Kamb density contours, one line per standard deviation above the expected count
    + geom_contour(
        aes(x=X, y=Y, z="kamb"), data=kamb_df, color=INK_MUTED, alpha=0.7, size=0.6, binwidth=1, show_legend=False
    )
    # Great circles
    + geom_path(aes(x=X, y=Y, group=GROUP, color=FEATURE_TYPE), data=gc_df, size=0.5, alpha=0.35, show_legend=False)
    # Confidence ellipses around each cluster
    + geom_polygon(
        aes(x=X, y=Y, group=GROUP, fill=FEATURE_TYPE), data=ellipse_df, alpha=0.12, size=0, show_legend=False
    )
    # Poles to planes with tooltips
    + geom_point(aes(x=X, y=Y, color=FEATURE_TYPE), data=poles_df, size=4.5, alpha=0.88, tooltips=pole_tooltips)
    # Mean pole markers (diamond shape)
    + geom_point(aes(x=X, y=Y), data=mean_df, size=9, shape=18, color=INK, alpha=0.95, show_legend=False)
)

# Mean annotations, one layer per label because each carries its own nudge
for _, row in mean_df.iterrows():
    plot += geom_text(
        aes(x=X, y=Y, label=LABEL),
        data=pd.DataFrame([{X: row[X], Y: row[Y], LABEL: row[LABEL]}]),
        size=7,
        color=INK,
        nudge_x=row["nudge_x"],
        nudge_y=row["nudge_y"],
        fontface="italic",
        show_legend=False,
    )

plot = (
    plot
    # Primitive circle and ticks
    + geom_path(aes(x=X, y=Y), data=circle_df, color=INK, size=1.4)
    + geom_segment(aes(x=X, y=Y, xend=XEND, yend=YEND), data=tick_df, color=INK, size=0.9)
    # Cardinal labels
    + geom_text(aes(x=X, y=Y, label=LABEL), data=cardinal_df, size=9, color=INK, fontface="bold")
    + scale_color_manual(values=IMPRINT_PALETTE, name=FEATURE_TYPE)
    + scale_fill_manual(values=IMPRINT_PALETTE)
    + coord_fixed()
    + scale_x_continuous(limits=[-1.18, 1.18])
    + scale_y_continuous(limits=[-1.18, 1.18])
    + labs(title="stereonet-equal-area · python · letsplot · anyplot.ai")
    + theme(
        plot_title=element_text(size=18, hjust=0.5, face="bold", color=INK, margin=[0, 0, 12, 0]),
        legend_title=element_text(size=14, face="bold", color=INK),
        legend_text=element_text(size=12, color=INK_SOFT),
        legend_position=[0.9, 0.1],
        legend_justification=[0.5, 0.5],
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT, size=0.5),
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_grid=element_blank(),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    )
)

# The fixed aspect leaves the canvas edges transparent: a one-panel grid paints the page color
plot = gggrid([plot]) + ggsize(600, 600) + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))

ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
