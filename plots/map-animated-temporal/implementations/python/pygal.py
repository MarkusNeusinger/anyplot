"""anyplot.ai
map-animated-temporal: Animated Map over Time
Library: pygal | Python 3.13
Quality: pending | Created: 2026-05-27
"""

import importlib.util
import os
import sys
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont


# Prevent this file (pygal.py) from shadowing the installed pygal package
_pygal_spec = importlib.util.find_spec("pygal")
if _pygal_spec and _pygal_spec.origin != __file__:
    from pygal.style import Style
else:
    _cwd = os.getcwd()
    sys.path = [p for p in sys.path if os.path.abspath(p) != _cwd]
    try:
        from pygal.style import Style
    finally:
        sys.path.insert(0, _cwd)

from pygal_maps_world.maps import World


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# imprint_seq: #009E73 → #4467A3, 6 stops for 6 intensity bins
n_bins = 6
seq_colors = []
for i in range(n_bins):
    t = i / (n_bins - 1)
    r = int(round(0x00 + (0x44 - 0x00) * t))
    g = int(round(0x9E + (0x67 - 0x9E) * t))
    b = int(round(0x73 + (0xA3 - 0x73) * t))
    seq_colors.append(f"#{r:02X}{g:02X}{b:02X}")
seq_colors = tuple(seq_colors)

# Data: Seismic activity spreading across Pacific Ring of Fire over 6 time steps
time_periods = ["T1: Initial", "T2: +6h", "T3: +12h", "T4: +24h", "T5: +48h", "T6: +72h"]

activity_by_time = {
    0: {"jp": 95, "kr": 15, "ph": 25, "id": 38},
    1: {"jp": 85, "kr": 55, "ph": 40, "id": 22, "nz": 15},
    2: {"jp": 75, "kr": 70, "ph": 65, "id": 50, "tw": 45, "my": 18},
    3: {"jp": 60, "kr": 55, "ph": 75, "id": 80, "tw": 50, "my": 35, "nz": 40, "au": 22},
    4: {"jp": 45, "kr": 40, "ph": 60, "id": 70, "tw": 40, "my": 50, "nz": 65, "au": 35, "cl": 30, "pe": 18},
    5: {
        "jp": 35,
        "kr": 30,
        "ph": 45,
        "id": 55,
        "tw": 30,
        "my": 45,
        "nz": 55,
        "au": 50,
        "cl": 60,
        "pe": 40,
        "mx": 35,
        "ec": 25,
    },
}

activity_bins = [
    ("Minimal (<20)", 0, 20),
    ("Low (20-35)", 20, 35),
    ("Moderate (35-50)", 35, 50),
    ("High (50-65)", 50, 65),
    ("Severe (65-80)", 65, 80),
    ("Extreme (80+)", 80, 101),
]

# Canvas layout: 3200×1800 (landscape)
CANVAS_W = 3200
CANVAS_H = 1800
TITLE_H = 110
LEGEND_H = 130
GRID_H = CANVAS_H - TITLE_H - LEGEND_H  # 1560
GRID_ROWS = 2
GRID_COLS = 3
CELL_W = CANVAS_W // GRID_COLS  # 1066
CELL_H = GRID_H // GRID_ROWS  # 780

# Pygal style for individual map panels (no per-panel legend)
map_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=seq_colors,
    title_font_size=44,
    label_font_size=32,
    major_label_font_size=28,
    legend_font_size=28,
    value_font_size=24,
)

# Render 6 world map panels as PNG bytes
map_images = []
for time_idx in range(6):
    data = activity_by_time[time_idx]

    binned = {label: {} for label, _, _ in activity_bins}
    for country, value in data.items():
        for label, low, high in activity_bins:
            if low <= value < high:
                binned[label][country] = value
                break

    worldmap = World(style=map_style, width=CELL_W, height=CELL_H, title=time_periods[time_idx], show_legend=False)
    for label, _, _ in activity_bins:
        if binned[label]:
            worldmap.add(label, binned[label])

    png_bytes = worldmap.render_to_png()
    map_images.append(Image.open(BytesIO(png_bytes)))

# Compose final 3200×1800 image
combined = Image.new("RGB", (CANVAS_W, CANVAS_H), PAGE_BG)
draw = ImageDraw.Draw(combined)

# Load fonts (fall back to PIL default if DejaVu not available)
try:
    font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 52)
    font_legend = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 34)
except OSError:
    font_title = ImageFont.load_default()
    font_legend = ImageFont.load_default()

# Draw centered title
title_str = "Seismic Activity · map-animated-temporal · python · pygal · anyplot.ai"
tbbox = draw.textbbox((0, 0), title_str, font=font_title)
text_w = tbbox[2] - tbbox[0]
text_h = tbbox[3] - tbbox[1]
title_x = max(20, (CANVAS_W - text_w) // 2)
title_y = (TITLE_H - text_h) // 2
draw.text((title_x, title_y), title_str, fill=INK, font=font_title)

# Paste resized map panels into grid
for idx, img in enumerate(map_images):
    row = idx // GRID_COLS
    col = idx % GRID_COLS
    img_resized = img.resize((CELL_W, CELL_H), Image.Resampling.LANCZOS)
    x = col * CELL_W
    y = TITLE_H + row * CELL_H
    combined.paste(img_resized, (x, y))

# Draw single shared legend at bottom (replaces per-panel legends)
box_sz = 32
gap = 14
padding = 40

total_leg_w = 0
for lbl, _, _ in activity_bins:
    lbbox = draw.textbbox((0, 0), lbl, font=font_legend)
    total_leg_w += box_sz + gap + (lbbox[2] - lbbox[0]) + padding

leg_x = max(20, (CANVAS_W - total_leg_w) // 2)
leg_y_center = TITLE_H + GRID_H + LEGEND_H // 2
leg_y = leg_y_center - box_sz // 2

for (lbl, _, _), color in zip(activity_bins, seq_colors, strict=True):
    draw.rectangle([leg_x, leg_y, leg_x + box_sz, leg_y + box_sz], fill=color, outline=INK_MUTED)
    lbbox = draw.textbbox((0, 0), lbl, font=font_legend)
    lbl_h = lbbox[3] - lbbox[1]
    lbl_w = lbbox[2] - lbbox[0]
    draw.text((leg_x + box_sz + gap, leg_y + (box_sz - lbl_h) // 2), lbl, fill=INK_SOFT, font=font_legend)
    leg_x += box_sz + gap + lbl_w + padding

combined.save(f"plot-{THEME}.png")

# Interactive HTML: final state (T6) choropleth with tooltips and toggleable legend
html_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=seq_colors,
    title_font_size=55,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
)
html_map = World(
    style=html_style,
    width=3200,
    height=1800,
    title="Seismic Activity (T6: +72h) · map-animated-temporal · python · pygal · anyplot.ai",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=6,
)
final_binned = {label: {} for label, _, _ in activity_bins}
for country, value in activity_by_time[5].items():
    for label, low, high in activity_bins:
        if low <= value < high:
            final_binned[label][country] = value
            break
for label, _, _ in activity_bins:
    if final_binned[label]:
        html_map.add(label, final_binned[label])

with open(f"plot-{THEME}.html", "wb") as f:
    f.write(html_map.render())
