"""anyplot.ai
map-projections: World Map with Different Projections
Library: pygal 3.1.3 | Python 3.14.10
Quality: 76/100 | Updated: 2026-11-26
"""

import io
import math
import os
import re
import sys
from itertools import pairwise

import cairosvg
import numpy as np
import pandas as pd


# Remove this script's own directory from sys.path so 'pygal.py' doesn't shadow
# the installed pygal package (a Python gotcha when the file shares a package name)
_here = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != _here]

from pygal.style import Style
from pygal_maps_world.maps import World


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Imprint sequential ramp for colored map regions (fields), (position, hex) stops, low to high
SEQ_FIELDS = (
    [(0.0, "#66E2B2"), (0.368, "#009E73"), (0.582, "#4467A3"), (1.0, "#002850")]
    if THEME == "light"
    else [(0.0, "#00573D"), (0.467, "#009E73"), (1.0, "#CDD9FF")]
)


def ramp_color(stops, t):
    """The hex at t (0 to 1) along (position, hex) stops, blended linearly in sRGB."""
    if not math.isfinite(t):
        return "none"
    t = min(max(t, 0.0), 1.0)
    (p0, c0), (p1, c1) = next((a, b) for a, b in pairwise(stops) if t <= b[0])
    share = (t - p0) / (p1 - p0)
    return "#" + "".join(
        f"{round(int(c0[i : i + 2], 16) * (1 - share) + int(c1[i : i + 2], 16) * share):02X}" for i in (1, 3, 5)
    )


# Constants
ZONE_EDGES = (15, 30, 60)  # latitude (degrees) where one zone gives way to the next
ZONE_RAMP_POSITIONS = (0.1, 0.4, 0.7, 1.0)  # where each zone samples the ramp
GRATICULE_STEP = 30  # degrees between meridians and parallels

# The bundled pygal world map is drawn in the Robinson projection: these are its
# fitted screen parameters (x scale, central x, y scale, equator y) in its 2475 x 1388 viewBox
ROBINSON_PARAMS = (7.65, 1203.0, 707.0, 681.0)
# Robinson's table every 5 degrees of latitude: x factor and y distance from the equator
ROBINSON_LAT = np.arange(0, 95, 5)
ROBINSON_X = [1.0, 0.9986, 0.9954, 0.99, 0.9822, 0.973, 0.96, 0.9427, 0.9216, 0.8962]
ROBINSON_X += [0.8679, 0.835, 0.7986, 0.7597, 0.7186, 0.6732, 0.6213, 0.5722, 0.5322]
ROBINSON_Y = [0, 0.062, 0.124, 0.186, 0.248, 0.31, 0.372, 0.434, 0.4958, 0.5571]
ROBINSON_Y += [0.6176, 0.6769, 0.7346, 0.7903, 0.8435, 0.8936, 0.9394, 0.9761, 1.0]

# Columns: set these to your table's column names
COUNTRY = "Country code"  # role: country
LATITUDE = "Latitude (deg)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("countries.csv")
# Approximate centroid latitude of every country in the bundled world map (ISO 3166 codes)
df = pd.read_csv(
    io.StringIO(
        """ad,42.5
ae,24
af,33.9
al,41.1
am,40.3
ao,-12.3
aq,-80
ar,-35
at,47.6
au,-25.7
az,40.3
ba,44
bd,23.8
be,50.6
bf,12.2
bg,42.7
bh,26
bi,-3.4
bj,9.6
bn,4.5
bo,-16.7
br,-10.8
bt,27.4
bw,-22.2
by,53.5
bz,17.2
ca,61
cd,-2.9
cf,6.6
cg,-0.7
ch,46.8
ci,7.6
cl,-35.7
cm,5.7
cn,35.9
co,4.6
cr,9.9
cu,21.6
cv,16
cy,35
cz,49.8
de,51.1
dj,11.8
dk,56
do,18.9
dz,28.2
ec,-1.4
ee,58.7
eg,26.5
eh,24.5
er,15.4
es,40.2
et,8.6
fi,64.5
fr,46.6
ga,-0.6
gb,54
ge,42.2
gf,4
gh,7.9
gl,72
gm,13.5
gn,10.4
gq,1.7
gr,39.1
gt,15.7
gu,13.4
gw,12
gy,4.8
hk,22.4
hn,14.8
hr,45.1
ht,19
hu,47.2
id,-2.3
ie,53.2
il,31.4
in,22.9
iq,33
ir,32.6
is,65
it,42.8
jm,18.2
jo,31.2
jp,37.6
ke,0.5
kg,41.5
kh,12.7
kp,40.1
kr,36.4
kw,29.3
kz,48.2
la,19.5
lb,33.9
li,47.1
lk,7.6
lr,6.5
ls,-29.6
lt,55.3
lu,49.8
lv,56.9
ly,27
ma,31.8
mc,43.7
md,47.2
me,42.8
mg,-19.4
mk,41.6
ml,17.6
mm,21.1
mn,46.8
mo,22.2
mr,20.3
mt,35.9
mu,-20.3
mv,3.2
mw,-13.2
mx,23.9
my,3.8
mz,-17.3
na,-22.1
ne,17.4
ng,9.6
ni,12.9
nl,52.2
no,64.5
np,28.3
nz,-41.8
om,20.6
pa,8.5
pe,-9.2
pg,-6.5
ph,12.9
pk,29.9
pl,52.1
pr,18.2
ps,31.9
pt,39.6
py,-23.2
re,-21.1
ro,45.9
rs,44
ru,61.5
rw,-2
sa,24.1
sc,-4.7
sd,15.9
se,62.8
sg,1.4
sh,-15.9
si,46.1
sk,48.7
sl,8.5
sm,43.9
sn,14.4
so,5.8
sr,4
st,0.2
sv,13.7
sy,35
sz,-26.5
td,15.4
tg,8.6
th,15.1
tj,38.9
tl,-8.8
tm,39
tn,34
tr,39
tw,23.7
tz,-6.3
ua,49
ug,1.4
us,39.8
uy,-32.8
uz,41.4
va,41.9
ve,7.2
vn,16.2
ye,15.6
yt,-12.8
za,-29
zm,-13.4
zw,-19
"""
    ),
    names=[COUNTRY, LATITUDE],
)

# Plot
# Mercator inflates area by sec^2 of the latitude: 1 at the equator, 4 at 60 degrees, unbounded at the poles
exaggeration = 1 / np.cos(np.radians(df[LATITUDE])) ** 2
zone_index = np.digitize(df[LATITUDE].abs(), ZONE_EDGES)
edges_text = ["0", *map(str, ZONE_EDGES)]
scale_at_edge = [1 / math.cos(math.radians(e)) ** 2 for e in (0, *ZONE_EDGES)]
zone_labels = [
    f"{edges_text[i]}°–{edges_text[i + 1]}° · Mercator ×{scale_at_edge[i]:.1f}–{scale_at_edge[i + 1]:.1f}"
    for i in range(len(ZONE_EDGES))
]
zone_labels.append(f"{ZONE_EDGES[-1]}°+ · Mercator ×{scale_at_edge[-1]:.0f} and up")
zone_colors = tuple(ramp_color(SEQ_FIELDS, t) for t in ZONE_RAMP_POSITIONS)

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=zone_colors,
    opacity=1.0,  # legend swatches default to 60 % opacity and would no longer match the map fills
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=2.5,
)

worldmap = World(
    style=custom_style,
    width=3200,
    height=1800,
    title="Robinson · map-projections · python · pygal · anyplot.ai",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    legend_box_size=40,
    print_values=False,
    print_labels=False,
)

# One constant value per zone: pygal washes out a country's fill by its value within the
# series, and every country must show the full color of its zone's legend swatch
for i, label in enumerate(zone_labels):
    codes = df[COUNTRY][zone_index == i]
    worldmap.add(label, dict.fromkeys(codes, i), formatter=lambda _, text=label: text)


def robinson(lon, lat):
    """Screen position of (lon, lat) on the bundled map."""
    x_scale, x_center, y_scale, y_equator = ROBINSON_PARAMS
    x = x_center + x_scale * lon * np.interp(abs(lat), ROBINSON_LAT, ROBINSON_X)
    y = y_equator - np.sign(lat) * y_scale * np.interp(abs(lat), ROBINSON_LAT, ROBINSON_Y)
    return f"{x:.1f},{y:.1f}"


# Graticule: meridians and parallels every GRATICULE_STEP degrees, bent by the same projection
meridians = [[(lon, lat) for lat in range(-90, 91, 3)] for lon in range(-180, 181, GRATICULE_STEP)]
parallels = [[(lon, lat) for lon in range(-180, 181, 3)] for lat in range(-60, 91, GRATICULE_STEP)]
graticule = "".join(
    f'<path d="M{" L".join(robinson(lon, lat) for lon, lat in line)}"/>' for line in meridians + parallels
)
graticule_layer = (
    f'<g fill="none" stroke="{INK_MUTED}" stroke-width="1.6" stroke-opacity="0.55" '
    f'style="pointer-events: none">{graticule}</g>'
)

# The map is a nested <svg>; the graticule goes on top of its countries, inside the same coordinates
svg = worldmap.render().decode()
map_end = re.search(r"</(\w+:)?svg>", svg).group(0)
svg = svg.replace(map_end, graticule_layer + map_end, 1)

cairosvg.svg2png(bytestring=svg.encode(), write_to=f"plot-{THEME}.png", output_width=3200, output_height=1800)
with open(f"plot-{THEME}.html", "w") as f:
    f.write(svg)
