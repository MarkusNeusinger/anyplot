""" anyplot.ai
barcode-code128: Code 128 Barcode
Library: bokeh 3.10.2 | Python 3.14.10
Quality: 87/100 | Updated: 2026-11-26
"""

import os
import sys
import time
from pathlib import Path


# Remove this script's own directory from sys.path so the installed
# bokeh package is found instead of this file (which is also named bokeh.py).
_own_dir = os.path.dirname(os.path.realpath(__file__))
sys.path = [p for p in sys.path if os.path.realpath(p or ".") != _own_dir]

import base64

from bokeh.embed import file_html
from bokeh.models import ColumnDataSource, HoverTool, Label
from bokeh.plotting import figure
from bokeh.resources import INLINE
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
ACCENT = "#009E73"  # Okabe-Ito green for structural zone annotations

# Constants: the Code 128 symbol table. Entry v holds the six alternating bar/space widths
# of symbol value v (0-102 are the Subset B characters, ord(c) - 32; 104 is Start B).
PATTERNS = [
    *"212222 222122 222221 121223 121322 131222 122213 122312".split(),
    *"132212 221213 221312 231212 112232 122132 122231 113222".split(),
    *"123122 123221 223211 221132 221231 213212 223112 312131".split(),
    *"311222 321122 321221 312212 322112 322211 212123 212321".split(),
    *"232121 111323 131123 131321 112313 132113 132311 211313".split(),
    *"231113 231311 112133 112331 132131 113123 113321 133121".split(),
    *"313121 211331 231131 213113 213311 213131 311123 311321".split(),
    *"331121 312113 312311 332111 314111 221411 431111 111224".split(),
    *"111422 121124 121421 141122 141221 112214 112412 122114".split(),
    *"122411 142112 142211 241211 221114 413111 241112 134111".split(),
    *"111242 121142 121241 114212 124112 124211 411212 421112".split(),
    *"421211 212141 214121 412121 111143 111341 131141 114113".split(),
    *"114311 411113 411311 113141 114131 311141 411131 211412".split(),
    *"211214 211232".split(),
]
START_B_VALUE = 104
STOP = "2331112"  # stop pattern, seven elements
QUIET_ZONE = 10  # standard 10-module quiet zone on each side

# Data: replace CONTENT to encode your own text (Code 128 Subset B, printable ASCII)
CONTENT = "SHIP-2024-ABC123"  # shipping label example

# Plot: reads only CONTENT and the constants above

# Symbol values: Start B, one per character; the check character is their weighted sum mod 103
values = [START_B_VALUE, *[ord(char) - 32 for char in CONTENT]]
checksum = sum(v * max(i, 1) for i, v in enumerate(values)) % 103

# Symbol parts in reading order: (zone label, hover description, width pattern)
parts = [
    ("Start B", "Start Code B", PATTERNS[START_B_VALUE]),
    *[("Data Payload", f"'{char}'  (position {i + 1})", PATTERNS[ord(char) - 32]) for i, char in enumerate(CONTENT)],
    ("Check", f"Check Digit  (value {checksum})", PATTERNS[checksum]),
    ("Stop", "Stop Pattern", STOP),
]

# Walk the patterns: elements alternate bar, space, bar, ... starting with a bar
x_pos = QUIET_ZONE
bar_lefts, bar_rights, bar_descs = [], [], []
zones = []  # (label, x_start, x_end) for the zone bracket annotations
for zone_label, desc, widths in parts:
    zone_start = x_pos
    for k, digit in enumerate(widths):
        w = int(digit)
        if k % 2 == 0:
            bar_lefts.append(x_pos)
            bar_rights.append(x_pos + w)
            bar_descs.append(desc)
        x_pos += w
    if zones and zones[-1][0] == zone_label:
        zones[-1] = (zone_label, zones[-1][1], x_pos)
    else:
        zones.append((zone_label, zone_start, x_pos))

total_modules = x_pos + QUIET_ZONE

# Layout y-coordinates — expanded canvas to accommodate zone annotations above bars
BAR_TOP = 570
BAR_BOTTOM = 80
BRACKET_Y = 608  # horizontal bracket line above bars
ZONE_TEXT_Y = 638  # zone label text above bracket
SUBTITLE_Y = 690  # informational subtitle above zone labels
WHITE_TOP = 735  # top of white barcode background rect
WHITE_BOTTOM = 20

# Create figure — 3200×1800 canonical landscape canvas
W, H = 3200, 1800
p = figure(
    width=W,
    height=H,
    title="barcode-code128 · python · bokeh · anyplot.ai",
    x_range=(0, total_modules),
    y_range=(0, 760),
    toolbar_location=None,
    min_border_bottom=80,
    min_border_left=60,
    min_border_top=110,
    min_border_right=60,
)

# Typography
p.title.text_font_size = "50pt"
p.title.align = "center"
p.title.text_color = INK

# Theme-adaptive canvas background
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

# No axes or grid — barcode is a self-contained graphic
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False

# White label background — spec requires high-contrast black bars on white
p.quad(left=0, right=total_modules, top=WHITE_TOP, bottom=WHITE_BOTTOM, fill_color="#FFFFFF", line_color=None)

# Barcode bars — ColumnDataSource enables HoverTool interactivity
source = ColumnDataSource(
    data={
        "left": bar_lefts,
        "right": bar_rights,
        "top": [BAR_TOP] * len(bar_lefts),
        "bottom": [BAR_BOTTOM] * len(bar_lefts),
        "desc": bar_descs,
    }
)
bars = p.quad(
    left="left", right="right", top="top", bottom="bottom", fill_color="#000000", line_color=None, source=source
)

# HoverTool — Bokeh's distinctive interactive feature: reveals encoded element on hover
hover = HoverTool(renderers=[bars], tooltips=[("Element", "@desc")])
p.add_tools(hover)

# Zone bracket annotations — educates the viewer about barcode structure
BRACKET_LW = 4
for zone_label, zx_start, zx_end in zones:
    zmid = (zx_start + zx_end) / 2
    # Horizontal bracket line spanning the zone
    p.segment(x0=[zx_start], y0=[BRACKET_Y], x1=[zx_end], y1=[BRACKET_Y], line_color=ACCENT, line_width=BRACKET_LW)
    # Vertical ticks down from bracket to bar top
    p.segment(
        x0=[zx_start, zx_end],
        y0=[BAR_TOP, BAR_TOP],
        x1=[zx_start, zx_end],
        y1=[BRACKET_Y, BRACKET_Y],
        line_color=ACCENT,
        line_width=BRACKET_LW,
    )
    # Zone label text centered above bracket
    p.add_layout(
        Label(
            x=zmid,
            y=ZONE_TEXT_Y,
            text=zone_label,
            text_align="center",
            text_baseline="bottom",
            text_font_size="34pt",
            text_color=ACCENT,
        )
    )

# Informational subtitle — context for the viewer (DE-01)
p.add_layout(
    Label(
        x=total_modules / 2,
        y=SUBTITLE_Y,
        text=f"Code 128 Subset B  ·  {len(CONTENT)} characters  ·  checksum: mod 103  ·  quiet zones: {QUIET_ZONE} modules",
        text_align="center",
        text_baseline="bottom",
        text_font_size="34pt",
        text_color="#4A4A44",  # sits on the white label tile in both themes
    )
)

# Human-readable text below barcode
p.add_layout(
    Label(
        x=total_modules / 2,
        y=48,
        text=CONTENT,
        text_font_size="34pt",
        text_align="center",
        text_baseline="middle",
        text_color="#000000",
        text_font="monospace",
    )
)

# Save interactive HTML with inline resources (no CDN dependency for offline rendering)
html_path = Path(f"plot-{THEME}.html").resolve()
html_path.write_text(file_html(p, INLINE))

# Screenshot with headless Chrome via Selenium + CDP for exact dimensions
opts = Options()
for arg in (
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    f"--window-size={W},{H}",
    "--hide-scrollbars",
):
    opts.add_argument(arg)
driver = webdriver.Chrome(options=opts)
driver.set_window_size(W, H)
driver.get(f"file://{html_path}")
time.sleep(3)

# CDP captureScreenshot handles browser-chrome offset and captures at exact W×H
result = driver.execute_cdp_cmd(
    "Page.captureScreenshot",
    {"format": "png", "captureBeyondViewport": True, "clip": {"x": 0, "y": 0, "width": W, "height": H, "scale": 1.0}},
)
Path(f"plot-{THEME}.png").write_bytes(base64.b64decode(result["data"]))
driver.quit()
