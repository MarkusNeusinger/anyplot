"""anyplot.ai
map-projections: World Map with Different Projections
Library: seaborn 0.13.2 | Python 3.14.10
Quality: pending | Updated: 2026-11-26
"""

import json
import os
import urllib.request

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Geographic semantic colors (neutral land and sea, theme-adaptive; Imprint chrome tokens)
OCEAN = "#D4E8F7" if THEME == "light" else "#1B2B3C"
LAND = "#C4D5B0" if THEME == "light" else "#4F6B47"
LAND_EDGE = "#4A6A40" if THEME == "light" else "#A9C49E"
GRID = "#8A8A84" if THEME == "light" else "#8E8D86"

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

# Constants
GRATICULE_STEP = 30  # degrees between graticule lines
GLOBE_CENTER = (20.0, 20.0)  # orthographic view center: latitude, longitude

# Columns: set these to your table's column names
COUNTRY_RING = "Country ring"  # role: country
LONGITUDE = "Longitude (°)"  # role: x
LATITUDE = "Latitude (°)"  # role: y

# Data: Natural Earth 110m country boundaries, one row per ring vertex
_NE_URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson"
)
with urllib.request.urlopen(_NE_URL, timeout=20) as _resp:
    _geojson = json.loads(_resp.read())

_rings = []
for _feat in _geojson["features"]:
    _geom = _feat["geometry"]
    _polys = [_geom["coordinates"]] if _geom["type"] == "Polygon" else _geom["coordinates"]
    _rings.extend(np.array(_poly[0]) for _poly in _polys)

df = pd.concat(
    [pd.DataFrame({COUNTRY_RING: i, LONGITUDE: r[:, 0], LATITUDE: r[:, 1]}) for i, r in enumerate(_rings)],
    ignore_index=True,
)

# Plot
# Densify every ring to at most 1° per edge so the polygons follow each projection's curvature
rings = []
for _, ring in df.groupby(COUNTRY_RING, sort=False):
    pts = ring[[LONGITUDE, LATITUDE]].to_numpy()
    steps = np.maximum(np.ceil(np.abs(np.diff(pts, axis=0)).max(axis=1)), 1).astype(int)
    rings.append(
        np.vstack(
            [
                pts[i] + (pts[i + 1] - pts[i]) * np.linspace(0, 1, s, endpoint=False)[:, None]
                for i, s in enumerate(steps)
            ]
            + [pts[-1:]]
        )
    )

p0, l0 = np.radians(GLOBE_CENTER[0]), np.radians(GLOBE_CENTER[1])


def ortho(lon_deg, lat_deg, clip):
    """Orthographic projection; hidden points are NaN, or pushed onto the horizon when clip is set."""
    lr, pr = np.radians(lon_deg), np.radians(lat_deg)
    cos_c = np.sin(p0) * np.sin(pr) + np.cos(p0) * np.cos(pr) * np.cos(lr - l0)
    x = np.cos(pr) * np.sin(lr - l0)
    y = np.cos(p0) * np.sin(pr) - np.sin(p0) * np.cos(pr) * np.cos(lr - l0)
    hidden = cos_c < 0
    if clip:
        r = np.maximum(np.hypot(x, y), 1e-9)
        return np.where(hidden, x / r, x), np.where(hidden, y / r, y)
    return np.where(hidden, np.nan, x), np.where(hidden, np.nan, y)


fig = plt.figure(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
gs = fig.add_gridspec(2, 6, left=0.02, right=0.98, bottom=0.02, top=0.855, wspace=0.12, hspace=0.3)
panels = [
    ("Orthographic", "globe perspective, 20°N 20°E", gs[0, 0:2], None),
    ("Aitoff", "compromise, elliptical", gs[0, 2:6], "aitoff"),
    ("Hammer", "equal-area, elliptical", gs[1, 0:3], "hammer"),
    ("Lambert Cylindrical", "equal-area, squashed poles", gs[1, 3:6], None),
]
lat_line = np.linspace(-90, 90, 181)
lon_line = np.linspace(-180, 180, 361)
meridians = range(-180, 181, GRATICULE_STEP)
parallels = range(-60, 61, GRATICULE_STEP)

for name, note, cell, geo in panels:
    ax = fig.add_subplot(cell, projection=geo) if geo else fig.add_subplot(cell)
    ax.set_facecolor(OCEAN)
    ax.set_title(f"{name}\n{note}", fontsize=10, fontweight="bold", color=INK, pad=4, linespacing=1.3)
    line_style = {"color": GRID, "linewidth": 0.5, "alpha": 0.7, "zorder": 3}

    if geo:  # matplotlib's own Aitoff and Hammer axes
        ax.set_longitude_grid(GRATICULE_STEP)
        ax.set_latitude_grid(GRATICULE_STEP)
        ax.set_longitude_grid_ends(90)
        ax.grid(True, color=GRID, linewidth=0.5, alpha=0.7)
        ax.set_axisbelow(False)
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        for ring in rings:
            ax.fill(
                np.radians(ring[:, 0]),
                np.radians(ring[:, 1]),
                facecolor=LAND,
                edgecolor=LAND_EDGE,
                linewidth=0.4,
                zorder=1,
            )
        ax.spines["geo"].set_edgecolor(INK_SOFT)
        ax.spines["geo"].set_linewidth(0.8)
        continue

    if name == "Orthographic":
        for lon in meridians:
            ax.plot(*ortho(np.full_like(lat_line, lon), lat_line, clip=False), **line_style)
        for lat in parallels:
            ax.plot(*ortho(lon_line, np.full_like(lon_line, lat), clip=False), **line_style)
        for ring in rings:
            ax.fill(
                *ortho(ring[:, 0], ring[:, 1], clip=True), facecolor=LAND, edgecolor=LAND_EDGE, linewidth=0.4, zorder=2
            )
        t = np.linspace(0, 2 * np.pi, 360)
        ax.plot(np.cos(t), np.sin(t), color=INK_SOFT, linewidth=0.8, zorder=5)
        ax.set_xlim(-1.04, 1.04)
        ax.set_ylim(-1.04, 1.04)
    else:  # Lambert cylindrical equal-area: x = longitude, y = sin(latitude)
        for lon in meridians:
            ax.plot([np.radians(lon)] * 2, [-1, 1], **line_style)
        for lat in parallels:
            ax.plot([-np.pi, np.pi], [np.sin(np.radians(lat))] * 2, **line_style)
        for ring in rings:
            ax.fill(
                np.radians(ring[:, 0]),
                np.sin(np.radians(ring[:, 1])),
                facecolor=LAND,
                edgecolor=LAND_EDGE,
                linewidth=0.4,
                zorder=2,
            )
        ax.set_xlim(-np.pi, np.pi)
        ax.set_ylim(-1, 1)

    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_edgecolor(INK_SOFT)
        spine.set_linewidth(0.8)

fig.suptitle("map-projections · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK, y=0.99)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
plt.close()
