""" anyplot.ai
barcode-ean13: EAN-13 Barcode
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-21
"""

import base64
import os
import sys
import time
from pathlib import Path


# Remove this script's own directory from sys.path so the installed
# bokeh package is found instead of this file (which is also named bokeh.py).
_own_dir = os.path.dirname(os.path.realpath(__file__))
sys.path = [p for p in sys.path if os.path.realpath(p or ".") != _own_dir]

from bokeh.embed import file_html
from bokeh.models import ColumnDataSource, HoverTool, Label
from bokeh.plotting import figure
from bokeh.resources import INLINE
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# EAN-13 encoding patterns
L_CODES = {
    "0": [0, 0, 0, 1, 1, 0, 1],
    "1": [0, 0, 1, 1, 0, 0, 1],
    "2": [0, 0, 1, 0, 0, 1, 1],
    "3": [0, 1, 1, 1, 1, 0, 1],
    "4": [0, 1, 0, 0, 0, 1, 1],
    "5": [0, 1, 1, 0, 0, 0, 1],
    "6": [0, 1, 0, 1, 1, 1, 1],
    "7": [0, 1, 1, 1, 0, 1, 1],
    "8": [0, 1, 1, 0, 1, 1, 1],
    "9": [0, 0, 0, 1, 0, 1, 1],
}

G_CODES = {
    "0": [0, 1, 0, 0, 1, 1, 1],
    "1": [0, 1, 1, 0, 0, 1, 1],
    "2": [0, 0, 1, 1, 0, 1, 1],
    "3": [0, 1, 0, 0, 0, 0, 1],
    "4": [0, 0, 1, 1, 1, 0, 1],
    "5": [0, 1, 1, 1, 0, 0, 1],
    "6": [0, 0, 0, 0, 1, 0, 1],
    "7": [0, 0, 1, 0, 0, 0, 1],
    "8": [0, 0, 0, 1, 0, 0, 1],
    "9": [0, 0, 1, 0, 1, 1, 1],
}

R_CODES = {
    "0": [1, 1, 1, 0, 0, 1, 0],
    "1": [1, 1, 0, 0, 1, 1, 0],
    "2": [1, 1, 0, 1, 1, 0, 0],
    "3": [1, 0, 0, 0, 0, 1, 0],
    "4": [1, 0, 1, 1, 1, 0, 0],
    "5": [1, 0, 0, 1, 1, 1, 0],
    "6": [1, 0, 1, 0, 0, 0, 0],
    "7": [1, 0, 0, 0, 1, 0, 0],
    "8": [1, 0, 0, 1, 0, 0, 0],
    "9": [1, 1, 1, 0, 1, 0, 0],
}

FIRST_DIGIT_PATTERNS = {
    "0": "LLLLLL",
    "1": "LLGLGG",
    "2": "LLGGLG",
    "3": "LLGGGL",
    "4": "LGLLGG",
    "5": "LGGLLG",
    "6": "LGGGLL",
    "7": "LGLGLG",
    "8": "LGLGGL",
    "9": "LGGLGL",
}

START_GUARD = [1, 0, 1]
CENTER_GUARD = [0, 1, 0, 1, 0]
END_GUARD = [1, 0, 1]

# 12-digit German product code — check digit auto-calculated
code = "400638133393"

total = 0
for pos, digit in enumerate(code):
    if pos % 2 == 0:
        total += int(digit)
    else:
        total += int(digit) * 3
check_digit = (10 - (total % 10)) % 10
code = code + str(check_digit)

# Build barcode bit pattern with section labels for HoverTool
barcode_pattern = []
section_labels = []

for bit in START_GUARD:
    barcode_pattern.append(bit)
    section_labels.append("Start Guard")

lg_pattern = FIRST_DIGIT_PATTERNS[code[0]]
for i, digit in enumerate(code[1:7]):
    label = f"Left digit {i + 1}: '{digit}'"
    if lg_pattern[i] == "L":
        bits = L_CODES[digit]
    else:
        bits = G_CODES[digit]
    for bit in bits:
        barcode_pattern.append(bit)
        section_labels.append(label)

for bit in CENTER_GUARD:
    barcode_pattern.append(bit)
    section_labels.append("Center Guard")

for i, digit in enumerate(code[7:13]):
    label = f"Right digit {i + 1}: '{digit}'"
    for bit in R_CODES[digit]:
        barcode_pattern.append(bit)
        section_labels.append(label)

for bit in END_GUARD:
    barcode_pattern.append(bit)
    section_labels.append("End Guard")

# Canvas dimensions (canonical Bokeh landscape)
W, H = 3200, 1800

# Scale barcode to ~70% of canvas width
quiet_zone_modules = 11
total_modules = quiet_zone_modules + len(barcode_pattern) + quiet_zone_modules
module_width = int(W * 0.70 / total_modules)
quiet_zone = quiet_zone_modules * module_width

# Bar heights in data coordinates
bar_height = 1200
guard_height = 1400
text_y_pos = 80

# Guard bar module index ranges
start_guard_end = 2
center_guard_start = 3 + 6 * 7
center_guard_end = center_guard_start + 4
end_guard_start = center_guard_end + 1 + 6 * 7

bar_lefts = []
bar_widths_px = []
bar_tops = []
bar_bottoms = []
bar_sections = []

x_pos = quiet_zone
module_idx = 0
i = 0

while i < len(barcode_pattern):
    if barcode_pattern[i] == 1:
        bar_start = x_pos
        bar_w = 0
        start_module = module_idx
        sec = section_labels[i]

        while i < len(barcode_pattern) and barcode_pattern[i] == 1:
            bar_w += module_width
            x_pos += module_width
            module_idx += 1
            i += 1

        is_guard = (
            start_module <= start_guard_end
            or center_guard_start <= start_module <= center_guard_end
            or start_module >= end_guard_start
        )

        bar_lefts.append(bar_start)
        bar_widths_px.append(bar_w)
        bar_sections.append(sec)
        if is_guard:
            bar_tops.append(guard_height + 150)
            bar_bottoms.append(150)
        else:
            bar_tops.append(bar_height + 150)
            bar_bottoms.append(280)
    else:
        x_pos += module_width
        module_idx += 1
        i += 1

total_barcode_width = x_pos + quiet_zone
x_offset = (W - total_barcode_width) / 2
bar_lefts = [left + x_offset for left in bar_lefts]
bar_rights = [left + w for left, w in zip(bar_lefts, bar_widths_px, strict=True)]

# Figure
p = figure(
    width=W,
    height=H,
    title="barcode-ean13 · python · bokeh · anyplot.ai",
    x_range=(0, W),
    y_range=(0, guard_height + 450),
    toolbar_location=None,
    min_border_top=110,
    min_border_bottom=80,
    min_border_left=80,
    min_border_right=50,
)

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

p.title.text_font_size = "50pt"
p.title.align = "center"
p.title.text_color = INK
p.title.text_font_style = "normal"

p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False

source = ColumnDataSource(
    data={"left": bar_lefts, "right": bar_rights, "top": bar_tops, "bottom": bar_bottoms, "section": bar_sections}
)

bars = p.quad(left="left", right="right", top="top", bottom="bottom", color=INK, source=source)

# HoverTool reveals which digit or guard section each bar encodes
hover = HoverTool(renderers=[bars], tooltips=[("Encodes", "@section")])
p.add_tools(hover)

# Human-readable digits: first digit outside left guard
first_digit_x = x_offset + quiet_zone - module_width * 5
p.add_layout(
    Label(
        x=first_digit_x,
        y=text_y_pos,
        text=code[0],
        text_font_size="48pt",
        text_align="center",
        text_baseline="bottom",
        text_color=INK,
        text_font="monospace",
    )
)

left_start = x_offset + quiet_zone + 3 * module_width
left_span = 6 * 7 * module_width
p.add_layout(
    Label(
        x=left_start + left_span / 2,
        y=text_y_pos,
        text=code[1:7],
        text_font_size="48pt",
        text_align="center",
        text_baseline="bottom",
        text_color=INK,
        text_font="monospace",
    )
)

right_start = left_start + left_span + 5 * module_width
right_span = 6 * 7 * module_width
p.add_layout(
    Label(
        x=right_start + right_span / 2,
        y=text_y_pos,
        text=code[7:13],
        text_font_size="48pt",
        text_align="center",
        text_baseline="bottom",
        text_color=INK,
        text_font="monospace",
    )
)

# Save interactive HTML with inline resources (no CDN dependency)
html_path = Path(f"plot-{THEME}.html").resolve()
html_path.write_text(file_html(p, INLINE))

# Screenshot with headless Chrome via Selenium + CDP for exact W×H dimensions
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
result = driver.execute_cdp_cmd(
    "Page.captureScreenshot",
    {"format": "png", "captureBeyondViewport": True, "clip": {"x": 0, "y": 0, "width": W, "height": H, "scale": 1.0}},
)
Path(f"plot-{THEME}.png").write_bytes(base64.b64decode(result["data"]))
driver.quit()
