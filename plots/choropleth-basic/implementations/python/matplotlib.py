""" anyplot.ai
choropleth-basic: Choropleth Map with Regional Coloring
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: 85/100 | Updated: 2026-11-08
"""

import json
import os
import sys
import urllib.request


# Prevent matplotlib.py from shadowing the matplotlib package
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != script_dir]

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.collections import PolyCollection  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
NO_DATA = "#D9D6CC" if THEME == "light" else "#3A3A35"

# Imprint palette and the sequential ramp for continuous values
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", [IMPRINT_PALETTE[0], IMPRINT_PALETTE[2]])

# Constants
GEOMETRY_URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson"
)
GEOMETRY_KEY = "ADM0_A3"  # ISO alpha-3 code property in the Natural Earth file
LAT_RANGE = (-58, 84)  # Antarctica is left out of the world view
# Robinson projection table: latitude (deg), parallel length, distance from equator
ROBINSON_LAT = np.arange(0, 95, 5)
ROBINSON_PLEN = np.array([
    1.0000, 0.9986, 0.9954, 0.9900, 0.9822, 0.9730, 0.9600, 0.9427, 0.9216, 0.8962,
    0.8679, 0.8350, 0.7986, 0.7597, 0.7186, 0.6732, 0.6213, 0.5722, 0.5322,
])  # fmt: skip
ROBINSON_PDFE = np.array([
    0.0000, 0.0620, 0.1240, 0.1860, 0.2480, 0.3100, 0.3720, 0.4340, 0.4958, 0.5571,
    0.6176, 0.6769, 0.7346, 0.7903, 0.8435, 0.8936, 0.9394, 0.9761, 1.0000,
])  # fmt: skip

# Columns: set these to your table's column names
COUNTRY = "Country (ISO alpha-3)"  # role: region_id
LIFE_EXPECTANCY = "Life expectancy at birth (years)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("life_expectancy.csv")
life_expectancy = {
    "CAN": 82.0, "USA": 78.0, "MEX": 75.0, "GTM": 74.0, "BLZ": 74.6, "HND": 75.1, "SLV": 73.1, "NIC": 74.9,
    "CRI": 80.3, "PAN": 78.5, "CUB": 79.0, "JAM": 74.5, "HTI": 64.0, "DOM": 74.1, "BHS": 73.9, "TTO": 73.5,
    "COL": 76.0, "VEN": 72.1, "GUY": 69.9, "SUR": 71.6, "ECU": 77.4, "PER": 74.0, "BOL": 71.5, "BRA": 76.0,
    "PRY": 74.3, "URY": 77.9, "ARG": 76.0, "CHL": 80.2,
    "ISL": 83.0, "NOR": 83.2, "SWE": 82.8, "FIN": 81.9, "DNK": 81.4, "GBR": 81.0, "IRL": 82.0, "FRA": 83.0,
    "BEL": 81.9, "NLD": 82.3, "LUX": 82.6, "DEU": 82.0, "CHE": 83.8, "AUT": 81.7, "ITA": 84.0, "ESP": 84.0,
    "PRT": 81.8, "POL": 79.0, "CZE": 79.3, "SVK": 77.8, "HUN": 76.9, "SVN": 81.3, "HRV": 78.6, "BIH": 77.4,
    "SRB": 76.0, "MNE": 76.8, "MKD": 76.2, "ALB": 78.0, "GRC": 81.1, "BGR": 75.1, "ROU": 75.6, "MDA": 72.0,
    "UKR": 73.0, "BLR": 74.8, "LTU": 76.0, "LVA": 75.4, "EST": 78.8, "RUS": 72.0, "CYP": 81.2,
    "MAR": 73.9, "DZA": 77.1, "TUN": 76.7, "LBY": 72.9, "EGY": 72.0, "MRT": 68.4, "MLI": 62.8, "SEN": 68.7,
    "GMB": 65.5, "GNB": 59.7, "GIN": 61.0, "SLE": 60.1, "LBR": 64.1, "CIV": 62.9, "BFA": 62.7, "GHA": 64.1,
    "TGO": 61.6, "BEN": 63.8, "NER": 63.3, "NGA": 54.0, "TCD": 59.6, "CMR": 62.4, "CAF": 53.9, "GNQ": 61.7,
    "GAB": 66.5, "COG": 64.6, "COD": 61.6, "SDN": 65.3, "SDS": 58.6, "ERI": 66.8, "ETH": 67.8, "DJI": 66.6,
    "SOM": 56.5, "KEN": 67.0, "UGA": 64.4, "RWA": 69.6, "BDI": 62.4, "TZA": 66.2, "AGO": 62.0, "ZMB": 64.2,
    "MWI": 65.6, "MOZ": 61.7, "ZWE": 61.5, "NAM": 64.6, "BWA": 69.8, "ZAF": 65.0, "LSO": 54.3, "SWZ": 59.7,
    "MDG": 65.2,
    "TUR": 78.6, "ISR": 82.0, "LBN": 79.0, "SYR": 72.1, "JOR": 74.4, "IRQ": 71.3, "SAU": 76.0, "YEM": 64.6,
    "OMN": 78.1, "ARE": 79.2, "QAT": 80.4, "KWT": 78.7, "IRN": 76.0, "GEO": 73.6, "ARM": 75.2, "AZE": 72.9,
    "KAZ": 71.4, "UZB": 72.1, "TKM": 69.3, "KGZ": 71.9, "TJK": 71.6, "AFG": 63.1, "PAK": 67.0, "IND": 68.0,
    "NPL": 70.9, "BTN": 72.2, "BGD": 73.0, "LKA": 76.4, "MMR": 67.4, "THA": 77.0, "LAO": 68.1, "KHM": 70.7,
    "VNM": 74.0, "MYS": 76.2, "BRN": 74.7, "IDN": 72.0, "PHL": 72.0, "TLS": 69.9, "PNG": 65.4, "CHN": 78.0,
    "MNG": 71.0, "PRK": 73.3, "KOR": 83.0, "JPN": 84.0, "TWN": 80.9,
    "AUS": 83.0, "NZL": 82.0, "FJI": 67.1, "SLB": 70.3, "VUT": 70.4,
}  # fmt: skip
df = pd.DataFrame({COUNTRY: list(life_expectancy), LIFE_EXPECTANCY: list(life_expectancy.values())})

# Plot: reads only df and the constants above
request = urllib.request.Request(GEOMETRY_URL, headers={"User-Agent": "anyplot.ai"})
with urllib.request.urlopen(request, timeout=30) as response:
    countries = json.load(response)["features"]

values = df.set_index(COUNTRY)[LIFE_EXPECTANCY].astype(float)
values = values[~values.index.duplicated()]

# Project every ring to Robinson; regions missing from df keep NaN and render as no-data
rings, ring_values = [], []
for feature in countries:
    geometry = feature["geometry"]
    polygons = geometry["coordinates"] if geometry["type"] == "MultiPolygon" else [geometry["coordinates"]]
    value = values.get(feature["properties"][GEOMETRY_KEY], np.nan)
    for polygon in polygons:
        lon, lat = np.asarray(polygon[0], dtype=float).T
        if lat.max() < LAT_RANGE[0]:
            continue
        lat = np.clip(lat, -90, 90)
        x = 0.8487 * np.interp(np.abs(lat), ROBINSON_LAT, ROBINSON_PLEN) * np.radians(lon)
        y = 1.3523 * np.sign(lat) * np.interp(np.abs(lat), ROBINSON_LAT, ROBINSON_PDFE)
        rings.append(np.column_stack([x, y]))
        ring_values.append(value)

# Map outline: the Robinson frame from the west edge to the east edge
frame_lat = np.linspace(LAT_RANGE[0], LAT_RANGE[1], 120)
frame_x = 0.8487 * np.interp(np.abs(frame_lat), ROBINSON_LAT, ROBINSON_PLEN) * np.pi
frame_y = 1.3523 * np.sign(frame_lat) * np.interp(np.abs(frame_lat), ROBINSON_LAT, ROBINSON_PDFE)
frame = np.column_stack([np.r_[frame_x, -frame_x[::-1]], np.r_[frame_y, frame_y[::-1]]])

fig = plt.figure(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax = fig.add_axes([0.01, 0.05, 0.86, 0.84])
ax.set_facecolor(PAGE_BG)

ax.fill(frame[:, 0], frame[:, 1], color=ELEVATED_BG, edgecolor=INK_SOFT, linewidth=0.6, zorder=0)

regions = PolyCollection(
    rings,
    array=np.ma.masked_invalid(ring_values),
    cmap=imprint_seq.with_extremes(bad=NO_DATA),
    norm=plt.Normalize(np.nanmin(ring_values), np.nanmax(ring_values)),
    edgecolors=PAGE_BG,
    linewidths=0.25,
    zorder=1,
)
ax.add_collection(regions)

ax.set_xlim(frame[:, 0].min() * 1.01, frame[:, 0].max() * 1.01)
ax.set_ylim(frame[:, 1].min() * 1.02, frame[:, 1].max() * 1.02)
ax.set_aspect("equal")
ax.set_axis_off()

# Color legend for the value range, plus a swatch for regions without data
cax = fig.add_axes([0.885, 0.2, 0.018, 0.57])
cbar = fig.colorbar(regions, cax=cax)
cbar.set_label(LIFE_EXPECTANCY, fontsize=9, color=INK)
cbar.ax.tick_params(labelsize=8, colors=INK_SOFT, length=2)
cbar.outline.set_edgecolor(INK_SOFT)
cbar.outline.set_linewidth(0.5)

legend = ax.legend(
    handles=[Patch(facecolor=NO_DATA, edgecolor=INK_SOFT, linewidth=0.4, label="No data")],
    loc="lower left",
    bbox_to_anchor=(0.02, 0.02),
    fontsize=8,
    frameon=False,
)
plt.setp(legend.get_texts(), color=INK_SOFT)

# Title
title = "World Life Expectancy · choropleth-basic · python · matplotlib · anyplot.ai"
title_fontsize = max(8, round(12 * 67 / len(title))) if len(title) > 67 else 12
fig.suptitle(title, x=0.45, y=0.875, fontsize=title_fontsize, color=INK)

plt.savefig(os.path.join(script_dir, f"plot-{THEME}.png"), dpi=400, facecolor=PAGE_BG)
