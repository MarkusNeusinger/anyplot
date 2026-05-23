""" anyplot.ai
map-projections: World Map with Different Projections
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 76/100 | Updated: 2026-05-23
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Geographic semantic colors (theme-adaptive)
OCEAN = "#D4E8F7" if THEME == "light" else "#192837"
LAND = "#C4D5B0" if THEME == "light" else "#2A3D26"
LAND_EDGE = "#4A6A40" if THEME == "light" else "#3A5534"
GRID = "#9A9A9A" if THEME == "light" else "#4A4A4A"

sns.set_theme(
    style="white",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": OCEAN,
        "axes.edgecolor": INK_SOFT,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
    },
)

# Major continent outlines (simplified polygons, lon/lat degrees)
coastlines = [
    # North America
    [
        (-168, 66),
        (-141, 70),
        (-130, 70),
        (-120, 60),
        (-125, 50),
        (-125, 40),
        (-117, 33),
        (-105, 25),
        (-97, 26),
        (-82, 25),
        (-81, 30),
        (-75, 35),
        (-70, 42),
        (-67, 45),
        (-60, 47),
        (-55, 52),
        (-60, 60),
        (-65, 68),
        (-80, 70),
        (-100, 73),
        (-120, 75),
        (-145, 72),
        (-168, 66),
    ],
    # South America
    [
        (-82, 10),
        (-77, 0),
        (-80, -5),
        (-70, -15),
        (-60, -5),
        (-50, 0),
        (-35, -5),
        (-40, -23),
        (-55, -35),
        (-68, -55),
        (-75, -50),
        (-75, -40),
        (-70, -20),
        (-80, -5),
        (-82, 10),
    ],
    # Europe
    [
        (-10, 36),
        (-10, 45),
        (-5, 48),
        (0, 52),
        (5, 55),
        (10, 58),
        (20, 60),
        (28, 70),
        (35, 70),
        (30, 60),
        (25, 55),
        (20, 50),
        (15, 45),
        (20, 40),
        (25, 35),
        (35, 35),
        (28, 42),
        (20, 38),
        (10, 38),
        (-10, 36),
    ],
    # Africa
    [
        (-17, 15),
        (-17, 28),
        (-5, 36),
        (10, 38),
        (20, 33),
        (35, 30),
        (45, 12),
        (52, 12),
        (45, 0),
        (42, -10),
        (35, -25),
        (25, -34),
        (18, -35),
        (12, -20),
        (15, -5),
        (5, 5),
        (-10, 5),
        (-17, 15),
    ],
    # Asia
    [
        (35, 30),
        (45, 42),
        (52, 45),
        (70, 42),
        (80, 30),
        (75, 15),
        (90, 22),
        (100, 15),
        (105, 22),
        (110, 5),
        (120, 25),
        (130, 35),
        (140, 45),
        (145, 55),
        (135, 70),
        (100, 78),
        (70, 75),
        (50, 70),
        (30, 70),
        (35, 50),
        (45, 45),
        (35, 30),
    ],
    # Australia
    [
        (113, -22),
        (120, -18),
        (135, -12),
        (145, -15),
        (152, -25),
        (150, -38),
        (140, -38),
        (130, -33),
        (115, -35),
        (113, -22),
    ],
]

# Major city reference points for seaborn scatterplot layer
cities = pd.DataFrame(
    {
        "name": ["London", "São Paulo", "Mumbai", "Cairo", "Beijing", "Sydney"],
        "lon": [0.1, -46.6, 72.8, 31.2, 116.4, 151.2],
        "lat": [51.5, -23.5, 19.1, 30.1, 39.9, -33.9],
    }
)


def project(lons, lats, proj):
    lons = np.asarray(lons, dtype=float)
    lats = np.asarray(lats, dtype=float)
    lr = np.radians(lons)
    pr = np.radians(lats)

    if proj == "orthographic":
        # Perspective from space, centered 20°N 20°E (Europe/Africa/Asia view)
        p0, l0 = np.radians(20.0), np.radians(20.0)
        cos_c = np.sin(p0) * np.sin(pr) + np.cos(p0) * np.cos(pr) * np.cos(lr - l0)
        x = np.cos(pr) * np.sin(lr - l0)
        y = np.cos(p0) * np.sin(pr) - np.sin(p0) * np.cos(pr) * np.cos(lr - l0)
        x = np.where(cos_c >= 0, x, np.nan)
        y = np.where(cos_c >= 0, y, np.nan)

    elif proj == "aitoff":
        # Compromise elliptical — full globe, balanced distortion
        alpha = np.arccos(np.clip(np.cos(pr) * np.cos(lr / 2), -1.0, 1.0))
        sin_a = np.sin(alpha)
        k = np.where(sin_a < 1e-10, 1.0, alpha / sin_a)
        x = 2 * k * np.cos(pr) * np.sin(lr / 2)
        y = k * np.sin(pr)

    elif proj == "hammer":
        # Equal-area elliptical (Hammer–Aitoff)
        z = np.sqrt(1 + np.cos(pr) * np.cos(lr / 2))
        x = 2 * np.sqrt(2) * np.cos(pr) * np.sin(lr / 2) / z
        y = np.sqrt(2) * np.sin(pr) / z

    else:  # lambert_cylindrical — equal-area, strongly squashed poles
        x = lr
        y = np.sin(pr)

    return x, y


# Projection configurations
proj_configs = [
    ("orthographic", "Orthographic\n(Globe Perspective, 20°N 20°E)", (-1.15, 1.15), (-1.15, 1.15)),
    ("aitoff", "Aitoff\n(Compromise Elliptical)", (-3.5, 3.5), (-1.9, 1.9)),
    ("hammer", "Hammer\n(Equal-Area Elliptical)", (-3.1, 3.1), (-1.6, 1.6)),
    ("lambert_cylindrical", "Lambert Cylindrical\n(Equal-Area, Squashed)", (-3.5, 3.5), (-1.1, 1.1)),
]

fig, axes = plt.subplots(2, 2, figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
axes = axes.flatten()

for idx, (proj_key, title, xlim, ylim) in enumerate(proj_configs):
    ax = axes[idx]
    ax.set_facecolor(OCEAN)

    # Graticule: meridians every 30°
    for lon in range(-180, 181, 30):
        lts = np.linspace(-85, 85, 120)
        xs, ys = project(np.full_like(lts, float(lon)), lts, proj_key)
        ax.plot(xs, ys, color=GRID, linewidth=0.5, alpha=0.6)

    # Graticule: parallels every 30°
    for lat in range(-60, 61, 30):
        lns = np.linspace(-180, 180, 300)
        xs, ys = project(lns, np.full_like(lns, float(lat)), proj_key)
        ax.plot(xs, ys, color=GRID, linewidth=0.5, alpha=0.6)

    # Coastline fills
    for coast in coastlines:
        lons_c = np.array([p[0] for p in coast])
        lats_c = np.array([p[1] for p in coast])
        xs, ys = project(lons_c, lats_c, proj_key)
        if (~np.isnan(xs)).sum() >= 3:
            ax.fill(xs, ys, color=LAND, edgecolor=LAND_EDGE, linewidth=0.8, alpha=0.9, zorder=2)

    # Horizon circle for orthographic
    if proj_key == "orthographic":
        t = np.linspace(0, 2 * np.pi, 360)
        ax.plot(np.cos(t), np.sin(t), color=INK_SOFT, linewidth=0.8, zorder=5)

    # City reference dots — seaborn scatterplot layer
    cx, cy = project(cities["lon"].values, cities["lat"].values, proj_key)
    city_df = pd.DataFrame({"x": cx, "y": cy})
    visible = ~np.isnan(cx)
    if visible.any():
        sns.scatterplot(
            data=city_df[visible],
            x="x",
            y="y",
            color="#009E73",
            s=20,
            marker="o",
            edgecolor=PAGE_BG,
            linewidth=0.5,
            legend=False,
            zorder=6,
            ax=ax,
        )

    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.set_title(title, fontsize=8, fontweight="bold", color=INK, pad=4)
    for spine in ax.spines.values():
        spine.set_edgecolor(INK_SOFT)
        spine.set_linewidth(0.8)

fig.suptitle("map-projections · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK, y=0.995)

plt.tight_layout(rect=[0, 0, 1, 0.955])
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
plt.close()
