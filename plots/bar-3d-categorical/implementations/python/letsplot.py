"""anyplot.ai
bar-3d-categorical: 3D Bar Chart for Categorical Comparison
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 83/100 | Updated: 2026-11-21
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID_COLOR = "#C8C7C0" if THEME == "light" else "#3A3A35"

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Cabinet projection: x3 = age-group axis, y3 = depth axis, z3 = height
BW = 0.78  # bar width (x3 units; gap = 1 - BW)
BD = 0.65  # bar depth (y3 units)
DX = 0.52  # x2 shift per unit of y3 depth
DZ = 0.32  # z2 (upward) shift per unit of y3 depth

# Columns
AGE_GROUP = "age_group"  # role: x_category
EDUCATION = "education_level"  # role: y_category
SATISFACTION = "satisfaction_score"  # role: value

# Data
np.random.seed(42)
age_groups = ["18–34", "35–49", "50–64", "65+"]
education_levels = ["High School", "Bachelor's", "Graduate"]  # first = furthest front
base_scores = {
    "High School": [6.1, 5.7, 5.4, 5.8],
    "Bachelor's": [7.0, 7.3, 6.8, 7.1],
    "Graduate": [7.7, 8.0, 7.5, 7.8],
}
df = pd.DataFrame(
    [
        {AGE_GROUP: age, EDUCATION: edu, SATISFACTION: round(base_scores[edu][ai] + np.random.uniform(-0.15, 0.15), 1)}
        for edu in education_levels
        for ai, age in enumerate(age_groups)
    ]
)

# Plot
x_cats = list(dict.fromkeys(df[AGE_GROUP]))
y_cats = list(dict.fromkeys(df[EDUCATION]))
NX, NY = len(x_cats), len(y_cats)
lookup = df.set_index([AGE_GROUP, EDUCATION])[SATISFACTION]
z_max = int(np.ceil(df[SATISFACTION].max() / 2) * 2)
z_ticks = list(range(0, z_max + 1, 2))


def prj(x3, y3, z3):
    return (x3 + y3 * DX, z3 + y3 * DZ)


def shade(col, f):
    """Adjust hex color brightness by factor f."""
    r = min(255, max(0, round(int(col[1:3], 16) * f)))
    g = min(255, max(0, round(int(col[3:5], 16) * f)))
    b = min(255, max(0, round(int(col[5:7], 16) * f)))
    return f"#{r:02X}{g:02X}{b:02X}"


# Base-plane grid
seg_rows = []
for xi in range(NX + 1):
    p0, p1 = prj(xi, 0, 0), prj(xi, NY - 1 + BD, 0)
    seg_rows.append({"x": p0[0], "y": p0[1], "xend": p1[0], "yend": p1[1]})
for yi in [*range(NY), NY - 1 + BD]:
    p0, p1 = prj(0, yi, 0), prj(NX, yi, 0)
    seg_rows.append({"x": p0[0], "y": p0[1], "xend": p1[0], "yend": p1[1]})
df_seg = pd.DataFrame(seg_rows)

# Z-axis with ticks
ax0, ax1 = prj(0, 0, 0), prj(0, 0, z_max)
z_segs = [{"x": ax0[0], "y": ax0[1], "xend": ax1[0], "yend": ax1[1]}]
ztick_rows = []
for zt in z_ticks:
    pt = prj(0, 0, zt)
    z_segs.append({"x": pt[0], "y": pt[1], "xend": pt[0] - 0.18, "yend": pt[1]})
    ztick_rows.append({"x": pt[0] - 0.25, "y": pt[1], "label": str(zt)})
df_zsegs = pd.DataFrame(z_segs)
df_zticks = pd.DataFrame(ztick_rows)

# Category labels and axis titles
x_lbl = [{"x": prj(ai + BW / 2, 0, 0)[0], "y": prj(0, 0, 0)[1] - 0.55, "label": age} for ai, age in enumerate(x_cats)]
df_xlbl = pd.DataFrame(x_lbl)
x_title_pt = prj(NX / 2, 0, 0)
df_xtitle = pd.DataFrame([{"x": x_title_pt[0], "y": x_title_pt[1] - 1.35, "label": "Age Group"}])
z_title_pt = prj(0, 0, z_max / 2)
df_ztitle = pd.DataFrame([{"x": z_title_pt[0] - 1.05, "y": z_title_pt[1], "label": "Satisfaction Score"}])

# Bar polygons (painter's order: back to front)
poly_rows = []
for ei in range(NY - 1, -1, -1):
    c0 = IMPRINT_PALETTE[ei % len(IMPRINT_PALETTE)]
    for ai in range(NX):
        h = lookup[(x_cats[ai], y_cats[ei])]
        x0, x1, y0, y1 = ai, ai + BW, ei, ei + BD
        corner = {
            "bfl": prj(x0, y0, 0),
            "bfr": prj(x1, y0, 0),
            "bbr": prj(x1, y1, 0),
            "tfl": prj(x0, y0, h),
            "tfr": prj(x1, y0, h),
            "tbl": prj(x0, y1, h),
            "tbr": prj(x1, y1, h),
        }
        faces = [
            ([corner["bfl"], corner["bfr"], corner["tfr"], corner["tfl"]], c0),  # front
            ([corner["bfr"], corner["bbr"], corner["tbr"], corner["tfr"]], shade(c0, 0.60)),  # right
            ([corner["tfl"], corner["tfr"], corner["tbr"], corner["tbl"]], shade(c0, 1.32)),  # top
        ]
        for pts, fill_col in faces:
            gid = str(len(poly_rows) // 4)
            poly_rows.extend({"x": px, "y": py, "g": gid, "fill": fill_col} for px, py in pts)
df_poly = pd.DataFrame(poly_rows)
fill_vals = {c: c for c in df_poly["fill"].unique()}

# Value labels (on top of each bar)
val_rows = []
for ei, edu in enumerate(y_cats):
    for ai, age in enumerate(x_cats):
        h = lookup[(age, edu)]
        pt = prj(ai + BW / 2, ei + BD / 2, h)
        val_rows.append({"x": pt[0], "y": pt[1] + 0.3, "label": f"{h:.1f}"})
df_vals = pd.DataFrame(val_rows)

# Manual legend (upper-left, above the bars)
LEG_X, LEG_Y0, LEG_DY = 0.15, z_max + 0.8, 0.9
df_ltitle = pd.DataFrame([{"x": LEG_X, "y": LEG_Y0 + 0.7, "label": "Education Level"}])
df_lrect = pd.DataFrame(
    [
        {
            "xmin": LEG_X,
            "xmax": LEG_X + 0.32,
            "ymin": LEG_Y0 - i * LEG_DY - 0.2,
            "ymax": LEG_Y0 - i * LEG_DY + 0.2,
            "fill": IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)],
        }
        for i in range(NY)
    ]
)
df_ltxt = pd.DataFrame([{"x": LEG_X + 0.45, "y": LEG_Y0 - i * LEG_DY, "label": edu} for i, edu in enumerate(y_cats)])

plot = (
    ggplot()
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend"), data=df_seg, color=GRID_COLOR, size=0.6)
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend"), data=df_zsegs, color=INK_SOFT, size=0.6)
    + geom_polygon(aes(x="x", y="y", group="g", fill="fill"), data=df_poly, color=PAGE_BG, size=0.2)
    + scale_fill_manual(values=fill_vals, guide="none")
    + geom_text(aes(x="x", y="y", label="label"), data=df_zticks, size=7, color=INK_SOFT, hjust=1)
    + geom_text(aes(x="x", y="y", label="label"), data=df_xlbl, size=8, color=INK_SOFT, vjust=1)
    + geom_text(aes(x="x", y="y", label="label"), data=df_xtitle, size=9, color=INK, vjust=1)
    + geom_text(aes(x="x", y="y", label="label"), data=df_ztitle, size=9, color=INK, angle=90)
    + geom_text(aes(x="x", y="y", label="label"), data=df_vals, size=6.5, color=INK)
    + geom_text(aes(x="x", y="y", label="label"), data=df_ltitle, size=9, color=INK, hjust=0, fontface="bold")
    + geom_rect(
        aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="fill"), data=df_lrect, color=INK_SOFT, size=0.2
    )
    + geom_text(aes(x="x", y="y", label="label"), data=df_ltxt, size=8, color=INK_SOFT, hjust=0)
    + labs(title="bar-3d-categorical · python · letsplot · anyplot.ai")
    + scale_y_continuous(limits=[-2.4, z_max + 3.0])
    + theme_void()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_title=element_text(color=INK, size=18, hjust=0.5),
        plot_margin=[20, 50, 20, 20],
    )
    + ggsize(800, 450)
)

ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
