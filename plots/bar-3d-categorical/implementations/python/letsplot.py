""" anyplot.ai
bar-3d-categorical: 3D Bar Chart for Categorical Comparison
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 83/100 | Created: 2026-05-15
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID_COLOR = "#C8C7C0" if THEME == "light" else "#3A3A35"

IMPRINT = ["#009E73", "#C475FD", "#4467A3"]


def shade(col, f):
    """Adjust hex color brightness by factor f."""
    r = min(255, max(0, round(int(col[1:3], 16) * f)))
    g = min(255, max(0, round(int(col[3:5], 16) * f)))
    b = min(255, max(0, round(int(col[5:7], 16) * f)))
    return f"#{r:02X}{g:02X}{b:02X}"


np.random.seed(42)
X_CATS = ["18–34", "35–49", "50–64", "65+"]
Y_CATS = ["High School", "Bachelor's", "Graduate"]  # index 0 = furthest back

BASE = {"High School": [6.1, 5.7, 5.4, 5.8], "Bachelor's": [7.0, 7.3, 6.8, 7.1], "Graduate": [7.7, 8.0, 7.5, 7.8]}

NX = len(X_CATS)
NY = len(Y_CATS)

vals = {
    (ai, ei): round(BASE[edu][ai] + np.random.uniform(-0.15, 0.15), 1)
    for ei, edu in enumerate(Y_CATS)
    for ai in range(NX)
}

# Cabinet projection: x3=age-group axis, y3=depth axis, z3=height
BW = 0.78  # bar width (x3 units; gap = 1 - BW)
BD = 0.65  # bar depth (y3 units)
DX = 0.52  # x2 shift per unit of y3 depth
DZ = 0.32  # z2 (upward) shift per unit of y3 depth


def prj(x3, y3, z3):
    return (x3 + y3 * DX, z3 + y3 * DZ)


# ── Base-plane grid ──────────────────────────────────────────────────
seg_rows = []


def seg(x1, y1, x2, y2):
    seg_rows.append({"x": x1, "y": y1, "xend": x2, "yend": y2})


# Lines along the depth direction (x edges of the grid)
for xi in range(NX + 1):
    p0 = prj(xi, 0, 0)
    p1 = prj(xi, NY - 1 + BD, 0)
    seg(p0[0], p0[1], p1[0], p1[1])

# Lines along the x direction (depth edges of the grid)
for yi_f in [0.0, 1.0, 2.0, NY - 1 + BD]:
    p0 = prj(0, yi_f, 0)
    p1 = prj(NX, yi_f, 0)
    seg(p0[0], p0[1], p1[0], p1[1])

df_seg = pd.DataFrame(seg_rows)

# ── Z-axis (left-front vertical) ────────────────────────────────────
z_segs = []
ztick_rows = []
Z_TICKS = [0, 2, 4, 6, 8, 10]

ax0 = prj(0, 0, 0)
ax1 = prj(0, 0, 10)
z_segs.append({"x": ax0[0], "y": ax0[1], "xend": ax1[0], "yend": ax1[1]})

for zt in Z_TICKS:
    pt = prj(0, 0, zt)
    z_segs.append({"x": pt[0], "y": pt[1], "xend": pt[0] - 0.18, "yend": pt[1]})
    ztick_rows.append({"x": pt[0] - 0.25, "y": pt[1], "label": str(zt)})

df_zsegs = pd.DataFrame(z_segs)
df_zticks = pd.DataFrame(ztick_rows)

# ── Category axis labels ─────────────────────────────────────────────
x_lbl = []
for ai, age in enumerate(X_CATS):
    pt = prj(ai + BW / 2, 0, 0)
    x_lbl.append({"x": pt[0], "y": pt[1] - 0.55, "label": age})
df_xlbl = pd.DataFrame(x_lbl)

# ── Bar polygons (painter's order: back → front) ─────────────────────
poly_rows = []
gc = [0]


def face(pts, fill_col):
    gid = str(gc[0])
    gc[0] += 1
    for px, py in pts:
        poly_rows.append({"x": px, "y": py, "g": gid, "fill": fill_col})


for ei in range(NY - 1, -1, -1):  # draw back→front; ei=0 (High School) drawn last = in front
    c0 = IMPRINT[ei]
    c_front = c0
    c_right = shade(c0, 0.60)
    c_top = shade(c0, 1.32)

    for ai in range(NX):
        h = vals[(ai, ei)]
        x0, x1 = ai, ai + BW
        y0, y1 = ei, ei + BD

        C = {
            k: prj(*v)
            for k, v in {
                "bfl": (x0, y0, 0),
                "bfr": (x1, y0, 0),
                "bbl": (x0, y1, 0),
                "bbr": (x1, y1, 0),
                "tfl": (x0, y0, h),
                "tfr": (x1, y0, h),
                "tbl": (x0, y1, h),
                "tbr": (x1, y1, h),
            }.items()
        }

        face([C["bfl"], C["bfr"], C["tfr"], C["tfl"]], c_front)  # front
        face([C["bfr"], C["bbr"], C["tbr"], C["tfr"]], c_right)  # right
        face([C["tfl"], C["tfr"], C["tbr"], C["tbl"]], c_top)  # top

df_poly = pd.DataFrame(poly_rows)

# ── Value labels (centre-top of each bar) ───────────────────────────
val_rows = []
for ei in range(NY):
    for ai in range(NX):
        h = vals[(ai, ei)]
        pt = prj(ai + BW / 2, ei + BD / 2, h)
        val_rows.append({"x": pt[0], "y": pt[1] + 0.28, "label": f"{h:.1f}"})
df_vals = pd.DataFrame(val_rows)

# ── Manual legend inside chart (upper-left area, above bars) ─────────
LEG_X = 0.15
LEG_Y0 = 10.8
LEG_DY = 0.65
leg_title = [{"x": LEG_X, "y": LEG_Y0 + 0.4, "label": "Education Level"}]
leg_rect = []
leg_text = []
for i, edu in enumerate(Y_CATS):
    lx, ly = LEG_X, LEG_Y0 - i * LEG_DY
    leg_rect.append({"xmin": lx, "xmax": lx + 0.32, "ymin": ly - 0.20, "ymax": ly + 0.20, "fill": IMPRINT[i]})
    leg_text.append({"x": lx + 0.42, "y": ly, "label": edu})

df_ltitle = pd.DataFrame(leg_title)
df_lrect = pd.DataFrame(leg_rect)
df_ltxt = pd.DataFrame(leg_text)

# unique fill → itself (scale_fill_manual with identity mapping)
fill_vals = {c: c for c in df_poly["fill"].unique()}

# ── Assemble plot ─────────────────────────────────────────────────────
plot = (
    ggplot()
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend"), data=df_seg, color=GRID_COLOR, size=0.8)
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend"), data=df_zsegs, color=INK_SOFT, size=0.7)
    + geom_polygon(aes(x="x", y="y", group="g", fill="fill"), data=df_poly, color=PAGE_BG, size=0.3)
    + scale_fill_manual(values=fill_vals, guide="none")
    + geom_text(aes(x="x", y="y", label="label"), data=df_zticks, size=11, color=INK_SOFT, hjust=1)
    + geom_text(aes(x="x", y="y", label="label"), data=df_xlbl, size=12, color=INK_SOFT, vjust=1)
    + geom_text(aes(x="x", y="y", label="label"), data=df_vals, size=10, color=INK)
    + geom_text(aes(x="x", y="y", label="label"), data=df_ltitle, size=14, color=INK, hjust=0, fontface="bold")
    + geom_rect(
        aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="fill"), data=df_lrect, color=INK_SOFT, size=0.3
    )
    + geom_text(aes(x="x", y="y", label="label"), data=df_ltxt, size=13, color=INK_SOFT, hjust=0)
    + labs(title="bar-3d-categorical · letsplot · anyplot.ai")
    + theme_void()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_title=element_text(color=INK, size=24, hjust=0.5),
        plot_margin=[30, 40, 30, 40],
    )
    + ggsize(1600, 900)
)

ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)
ggsave(plot, f"plot-{THEME}.html", path=".")
