"""anyplot.ai
windbarb-basic: Wind Barb Plot for Meteorological Data
Library: pygal 3.1.0 | Python 3.13.13
Quality: 81/100 | Updated: 2026-11-22
"""

import math
import os
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: a single series here, so the first position only
BRAND = "#009E73"
IMPRINT_PALETTE = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Constants
CALM_KT = 2.5  # winds below this speed are drawn as an open circle without a staff
STAFF, BSPC, BFULL, BHALF = 50, 11, 30, 15  # barb geometry in canvas pixels

# Columns: set these to your table's column names
LONGITUDE = "Longitude"  # role: x
LATITUDE = "Latitude"  # role: y
U_WIND = "Zonal wind u (kt)"  # role: u
V_WIND = "Meridional wind v (kt)"  # role: v

# Data: replace this block with your own table, for example df = pd.read_csv("winds.csv")
# Synthetic surface winds on a 12 x 7 station grid circling a low-pressure centre
np.random.seed(42)
lon_g, lat_g = np.meshgrid(np.linspace(-125, -70, 12), np.linspace(25, 55, 7))
slons, slats = lon_g.ravel(), lat_g.ravel()
dist = np.hypot(slons + 100.0, slats - 40.0) + 0.5
from_dir = (
    np.degrees(np.arctan2(slons + 100.0, slats - 40.0) + math.pi / 2) + np.random.normal(0, 12, slons.size)
) % 360
speed = np.clip(22 + 180 / dist + np.random.normal(0, 4, slons.size), 3, 70)
speed[[10, 45]] = 1.5  # two calm stations
df = pd.DataFrame(
    {
        LONGITUDE: slons,
        LATITUDE: slats,
        U_WIND: -speed * np.sin(np.radians(from_dir)),
        V_WIND: -speed * np.cos(np.radians(from_dir)),
    }
)


# Plot: reads only df and the constants above
def barb_elems(cx, cy, spd, dirn):
    """Return SVG element strings for one wind barb: staff points toward the direction the wind comes from."""
    if spd < CALM_KT:
        return [f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="10" fill="none" stroke="{BRAND}" stroke-width="3"/>']
    out = [f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="4" fill="{BRAND}"/>']
    dr = math.radians(dirn)
    sdx, sdy = math.sin(dr), -math.cos(dr)
    xt, yt = cx + sdx * STAFF, cy + sdy * STAFF
    out.append(
        f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{xt:.1f}" y2="{yt:.1f}" '
        f'stroke="{BRAND}" stroke-width="3" stroke-linecap="round"/>'
    )
    bpx, bpy = -sdy, sdx  # feathers on the left of the staff (Northern Hemisphere)
    n50, rest = divmod(round(spd / 5) * 5, 50)
    n10, rest = divmod(rest, 10)
    n5 = rest // 5
    pos = 0.0
    for _ in range(n50):
        bx, by = xt - sdx * pos, yt - sdy * pos
        tx, ty = bx + bpx * BFULL, by + bpy * BFULL
        nx, ny = bx - sdx * BSPC, by - sdy * BSPC
        out.append(f'<polygon points="{bx:.1f},{by:.1f} {tx:.1f},{ty:.1f} {nx:.1f},{ny:.1f}" fill="{BRAND}"/>')
        pos += BSPC
    for count, length in ((n10, BFULL), (n5, BHALF)):
        for _ in range(count):
            bx, by = xt - sdx * pos, yt - sdy * pos
            out.append(
                f'<line x1="{bx:.1f}" y1="{by:.1f}" x2="{bx + bpx * length:.1f}" y2="{by + bpy * length:.1f}" '
                f'stroke="{BRAND}" stroke-width="3" stroke-linecap="round"/>'
            )
            pos += BSPC
    return out


class WindBarbXY(pygal.XY):
    """pygal.XY that overlays wind barbs, positioned with pygal's own data-to-pixel view."""

    def __init__(self, winds, **kw):
        self._winds = winds
        super().__init__(**kw)

    def _draw(self):
        super()._draw()
        layer = self.svg.node(self.nodes["plot"], tag="g", id="wind-barbs")
        for lon, lat, spd, dirn in self._winds:
            for s in barb_elems(self.view.x(lon), self.view.y(lat), spd, dirn):
                layer.append(ET.fromstring(s))
        self._draw_key()

    def _draw_key(self):
        """Key below the plot area: sample barbs for 5, 10, 20 and 50 kt plus the calm circle."""
        samples = [(5, "5 kt"), (10, "10 kt"), (20, "20 kt"), (50, "50 kt"), (0, f"Calm (<{CALM_KT} kt)")]
        left = self.margin_box.left
        step = (self.width - self.margin_box.left - self.margin_box.right) / len(samples)
        y = self.height - 60
        key = self.svg.node(self.nodes["graph"], tag="g", id="wind-key")
        for j, (spd, label) in enumerate(samples):
            x = left + j * step
            for s in barb_elems(x, y, spd if spd else 0.0, 0):
                key.append(ET.fromstring(s))
            txt = ET.SubElement(key, "text")
            txt.set("x", f"{x + 70:.1f}")
            txt.set("y", f"{y + 12:.1f}")
            txt.set("fill", INK_MUTED)
            txt.set("font-size", str(self.style.legend_font_size))
            txt.set("font-family", "sans-serif")
            txt.text = label


speed_kt = np.hypot(df[U_WIND], df[V_WIND])
from_deg = np.degrees(np.arctan2(-df[U_WIND], -df[V_WIND])) % 360
winds = [w for w in zip(df[LONGITUDE], df[LATITUDE], speed_kt, from_deg, strict=True) if not np.isnan(w).any()]

lons = sorted(df[LONGITUDE].dropna().unique())
lats = sorted(df[LATITUDE].dropna().unique())

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    guide_stroke_color=INK_MUTED,
    major_guide_stroke_color=INK_MUTED,
    colors=IMPRINT_PALETTE,
    title_font_size=66,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=40,
    value_font_size=36,
    stroke_width=2.5,
)

chart = WindBarbXY(
    winds=winds,
    style=custom_style,
    width=3200,
    height=1800,
    title="windbarb-basic · python · pygal · anyplot.ai",
    x_title=LONGITUDE,
    y_title=LATITUDE,
    show_dots=False,
    stroke=False,
    show_legend=False,
    show_x_guides=True,
    show_y_guides=True,
    margin_bottom=170,
    xrange=(min(lons) - 4, max(lons) + 4),
    range=(min(lats) - 3, max(lats) + 3),
    x_value_formatter=lambda lon: f"{abs(lon):.0f}°{'W' if lon < 0 else 'E'}",
    value_formatter=lambda lat: f"{abs(lat):.0f}°{'N' if lat >= 0 else 'S'}",
)
# Two corner points set the axis range; their dots are hidden
chart.add("range", [(min(lons), min(lats)), (max(lons), max(lats))])
chart.x_labels = [float(lon) for lon in lons]
chart.y_labels = [float(lat) for lat in lats]

chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
