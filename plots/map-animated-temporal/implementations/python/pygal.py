""" anyplot.ai
map-animated-temporal: Animated Map over Time
Library: pygal 3.1.0 | Python 3.13.13
Quality: 79/100 | Updated: 2026-05-27
"""

import importlib.util
import json
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
    title_font_size=66,
    label_font_size=44,
    major_label_font_size=36,
    legend_font_size=36,
    value_font_size=28,
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
    font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 64)
    font_legend = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 38)
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

# Interactive HTML: all 6 time steps with tab navigation
html_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=seq_colors,
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
)

# Render all 6 time steps as embeddable SVG strings
svg_frames = []
for time_idx in range(6):
    data = activity_by_time[time_idx]
    binned = {label: {} for label, _, _ in activity_bins}
    for country, value in data.items():
        for label, low, high in activity_bins:
            if low <= value < high:
                binned[label][country] = value
                break
    html_map = World(
        style=html_style,
        width=1600,
        height=900,
        title=f"Seismic Activity · {time_periods[time_idx]} · pygal · anyplot.ai",
        show_legend=True,
        legend_at_bottom=True,
        legend_at_bottom_columns=6,
    )
    for label, _, _ in activity_bins:
        if binned[label]:
            html_map.add(label, binned[label])
    svg_frames.append(html_map.render().decode("utf-8"))

# Build tabbed HTML with JavaScript slider navigation
tab_buttons = ""
svg_divs = ""
for i, (period, svg) in enumerate(zip(time_periods, svg_frames, strict=True)):
    active_btn = " active" if i == 0 else ""
    active_div = "" if i == 0 else ' style="display:none"'
    tab_buttons += f'<button class="tab-btn{active_btn}" onclick="showFrame({i})">{period}</button>\n'
    svg_divs += f'<div class="frame" id="frame-{i}"{active_div}>{svg}</div>\n'

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Seismic Activity · map-animated-temporal · pygal · anyplot.ai</title>
<style>
  body {{ margin: 0; background: {PAGE_BG}; font-family: DejaVu Sans, sans-serif; color: {INK}; }}
  h1 {{ text-align: center; font-size: 1.6em; padding: 0.6em 1em 0.3em; margin: 0; }}
  .tabs {{ display: flex; justify-content: center; gap: 8px; flex-wrap: wrap; padding: 0.4em 1em; }}
  .tab-btn {{
    background: {PAGE_BG}; color: {INK}; border: 2px solid {INK_SOFT};
    border-radius: 6px; padding: 6px 18px; cursor: pointer; font-size: 1em;
    transition: background 0.15s;
  }}
  .tab-btn:hover {{ background: {INK_SOFT}; color: {PAGE_BG}; }}
  .tab-btn.active {{ background: #009E73; color: #FAF8F1; border-color: #009E73; }}
  .frame svg {{ display: block; margin: 0 auto; max-width: 100%; }}
  #progress {{ display: flex; justify-content: center; align-items: center; gap: 12px; padding: 0.3em 1em; }}
  #slider {{ width: 300px; accent-color: #009E73; }}
</style>
</head>
<body>
<h1>Seismic Activity · map-animated-temporal · python · pygal · anyplot.ai</h1>
<div class="tabs">
{tab_buttons}
</div>
<div id="progress">
  <span style="font-size:0.9em;color:{INK_SOFT}">Step:</span>
  <input id="slider" type="range" min="0" max="5" value="0" oninput="showFrame(this.value)">
  <span id="step-label" style="min-width:80px;font-size:0.9em;color:{INK_SOFT}">{time_periods[0]}</span>
</div>
{svg_divs}
<script>
var labels = {json.dumps(time_periods)};
function showFrame(idx) {{
  idx = parseInt(idx);
  document.querySelectorAll('.frame').forEach(function(d, i) {{
    d.style.display = i === idx ? '' : 'none';
  }});
  document.querySelectorAll('.tab-btn').forEach(function(b, i) {{
    b.classList.toggle('active', i === idx);
  }});
  document.getElementById('slider').value = idx;
  document.getElementById('step-label').textContent = labels[idx];
}}
</script>
</body>
</html>"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)
