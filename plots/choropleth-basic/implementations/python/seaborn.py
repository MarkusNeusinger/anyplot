""" anyplot.ai
choropleth-basic: Choropleth Map with Regional Coloring
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 85/100 | Updated: 2026-11-09
"""

import json
import os
from urllib.request import urlopen

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.collections import PolyCollection
from matplotlib.colors import LinearSegmentedColormap, LogNorm
from matplotlib.path import Path
from matplotlib.ticker import FuncFormatter


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette and the sequential ramp built from its positions 1 and 3
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", [IMPRINT_PALETTE[0], IMPRINT_PALETTE[2]])
REGION_INK = "#FFFDF6"  # labels on the filled regions: the fills are identical in both themes

sns.set_theme(
    style="white",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Constants: US state outlines and an Albers Equal Area composite (Alaska, Hawaii and
# Puerto Rico get their own Albers parameters and are moved next to the lower 48)
GEOJSON_URL = "https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data/geojson/us-states.json"
ALBERS_LOWER48 = {"lon0": -96.0, "lat0": 37.5, "p1": 29.5, "p2": 45.5, "scale": 1.0, "shift": (0.0, 0.0)}
ALBERS_PLACED = {
    "Alaska": {"lon0": -154.0, "lat0": 50.0, "p1": 55.0, "p2": 65.0, "scale": 0.35, "shift": (-0.27, -0.29)},
    "Hawaii": {"lon0": -157.0, "lat0": 3.0, "p1": 8.0, "p2": 18.0, "scale": 1.0, "shift": (-0.12, -0.54)},
    "Puerto Rico": {"lon0": -66.5, "lat0": 18.0, "p1": 8.0, "p2": 18.0, "scale": 1.0, "shift": (0.30, -0.20)},
}
LABEL_MIN_AREA = 0.0017  # smallest projected area that holds a state code

# Columns: set these to your table's column names
STATE = "State"  # role: region_id
STATE_CODE = "State code"  # role: extra
DENSITY = "Population density (people per sq mi)"  # role: value

# Data: 2020 US Census population density of the 50 states and DC (Puerto Rico is not
# part of this table and shows as no data); replace this block with your own table,
# for example df = pd.read_csv("states.csv")
states = [
    ("Alabama", "AL", 99.2),
    ("Alaska", "AK", 1.3),
    ("Arizona", "AZ", 62.9),
    ("Arkansas", "AR", 57.9),
    ("California", "CA", 253.7),
    ("Colorado", "CO", 55.7),
    ("Connecticut", "CT", 744.7),
    ("Delaware", "DE", 508.0),
    ("District of Columbia", "DC", 11280.0),
    ("Florida", "FL", 401.4),
    ("Georgia", "GA", 185.6),
    ("Hawaii", "HI", 226.6),
    ("Idaho", "ID", 22.3),
    ("Illinois", "IL", 231.1),
    ("Indiana", "IN", 189.4),
    ("Iowa", "IA", 57.1),
    ("Kansas", "KS", 35.9),
    ("Kentucky", "KY", 114.1),
    ("Louisiana", "LA", 107.5),
    ("Maine", "ME", 44.2),
    ("Maryland", "MD", 636.1),
    ("Massachusetts", "MA", 901.2),
    ("Michigan", "MI", 177.6),
    ("Minnesota", "MN", 71.7),
    ("Mississippi", "MS", 63.1),
    ("Missouri", "MO", 89.5),
    ("Montana", "MT", 7.4),
    ("Nebraska", "NE", 25.5),
    ("Nevada", "NV", 28.3),
    ("New Hampshire", "NH", 153.8),
    ("New Jersey", "NJ", 1263.0),
    ("New Mexico", "NM", 17.5),
    ("New York", "NY", 428.7),
    ("North Carolina", "NC", 214.7),
    ("North Dakota", "ND", 11.3),
    ("Ohio", "OH", 288.8),
    ("Oklahoma", "OK", 57.7),
    ("Oregon", "OR", 44.1),
    ("Pennsylvania", "PA", 290.5),
    ("Rhode Island", "RI", 1061.4),
    ("South Carolina", "SC", 173.3),
    ("South Dakota", "SD", 11.7),
    ("Tennessee", "TN", 167.6),
    ("Texas", "TX", 111.6),
    ("Utah", "UT", 39.7),
    ("Vermont", "VT", 69.8),
    ("Virginia", "VA", 218.6),
    ("Washington", "WA", 115.9),
    ("West Virginia", "WV", 74.6),
    ("Wisconsin", "WI", 108.8),
    ("Wyoming", "WY", 6.0),
]
df = pd.DataFrame(states, columns=[STATE, STATE_CODE, DENSITY])

# Plot: reads only df and the constants above
with urlopen(GEOJSON_URL, timeout=30) as response:
    features = json.load(response)["features"]


def albers(lon, lat, lon0, lat0, p1, p2, scale, shift):
    """Albers Equal Area conic on the unit sphere, then scaled and moved into place."""
    lon, lat = np.radians(lon), np.radians(lat)
    lon0, lat0, p1, p2 = np.radians([lon0, lat0, p1, p2])
    n = (np.sin(p1) + np.sin(p2)) / 2
    c = np.cos(p1) ** 2 + 2 * n * np.sin(p1)
    rho0 = np.sqrt(c - 2 * n * np.sin(lat0)) / n
    rho = np.sqrt(c - 2 * n * np.sin(lat)) / n
    theta = n * (lon - lon0)
    return np.column_stack([rho * np.sin(theta) * scale + shift[0], (rho0 - rho * np.cos(theta)) * scale + shift[1]])


values = pd.to_numeric(df[DENSITY], errors="coerce")
lookup = dict(zip(df[STATE], values, strict=True))
codes = dict(zip(df[STATE], df[STATE_CODE], strict=True))

shaded, shaded_values, missing, labels = [], [], [], []
for feature in features:
    name = feature["properties"]["name"]
    params = ALBERS_PLACED.get(name, ALBERS_LOWER48)
    geometry = feature["geometry"]
    polygons = [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]
    rings = []
    for polygon in polygons:
        ring = np.asarray(polygon[0], dtype=float)
        lon = np.where(ring[:, 0] > 0, ring[:, 0] - 360, ring[:, 0])  # Aleutians past the antimeridian
        rings.append(albers(lon, ring[:, 1], **params))
    value = lookup.get(name, np.nan)
    if pd.notna(value):
        shaded.extend(rings)
        shaded_values.extend([value] * len(rings))
    else:
        missing.extend(rings)
    # State code at the interior point farthest from the outline of the largest part,
    # where the part is big enough to hold it
    areas = [abs(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y)) / 2 for x, y in (ring.T for ring in rings)]
    ring = rings[int(np.argmax(areas))]
    if name in codes and max(areas) >= LABEL_MIN_AREA:
        gx, gy = np.meshgrid(*(np.linspace(ring[:, i].min(), ring[:, i].max(), 40) for i in range(2)))
        candidates = np.column_stack([gx.ravel(), gy.ravel()])
        candidates = candidates[Path(ring).contains_points(candidates)]
        start, edge = ring[:-1], np.diff(ring, axis=0)
        offset = candidates[:, None, :] - start[None, :, :]
        t = np.clip((offset * edge).sum(-1) / np.maximum((edge**2).sum(-1), 1e-12), 0, 1)
        clearance = np.linalg.norm(offset - t[..., None] * edge, axis=-1).min(axis=1)
        cx, cy = candidates[np.argmax(clearance)]
        labels.append((cx, cy, codes[name]))

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)
norm = LogNorm(vmin=np.nanmin(values), vmax=np.nanmax(values))
regions = PolyCollection(
    shaded, array=np.asarray(shaded_values), cmap=imprint_seq, norm=norm, edgecolor=PAGE_BG, linewidth=0.4
)
ax.add_collection(regions)

# No-data regions: muted gray with hatching, never a color of the scale
ax.add_collection(
    PolyCollection(missing, facecolor=INK_MUTED, edgecolor=PAGE_BG, linewidth=0.4, hatch="////", alpha=0.55)
)

for cx, cy, code in labels:
    ax.text(cx, cy, code, ha="center", va="center", fontsize=6.5, fontweight="bold", color=REGION_INK)

# Colorbar
cbar = fig.colorbar(regions, ax=ax, shrink=0.72, aspect=22, pad=0.01)
cbar.set_label(DENSITY, fontsize=9, color=INK, labelpad=6)
cbar.ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
cbar.ax.tick_params(labelsize=8, colors=INK_SOFT, length=0, which="both")
cbar.outline.set_visible(False)

# Style
title = "choropleth-basic · python · seaborn · anyplot.ai"
ax.set_title(title, fontsize=round(12 * min(1.0, 67 / len(title))), fontweight="medium", color=INK, pad=6)
ax.set_aspect("equal")
ax.autoscale_view()
ax.set_axis_off()

if missing:
    no_data = mpatches.Patch(facecolor=INK_MUTED, edgecolor=PAGE_BG, hatch="////", alpha=0.55, label="No data")
    ax.legend(handles=[no_data], loc="lower right", fontsize=8, frameon=True, labelcolor=INK)

fig.subplots_adjust(left=0.01, right=0.99, top=0.94, bottom=0.02)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
