"""anyplot.ai
piano-roll-midi: MIDI Piano Roll Visualization
Library: highcharts unknown | Python 3.13.13
Quality: 87/100 | Updated: 2026-06-03
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

np.random.seed(42)

# MIDI helpers
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
BLACK_KEY_INDICES = {1, 3, 6, 8, 10}

# Data: C–Am–F–G chord progression, 8 measures of 4/4
# (start_beat, duration_beats, midi_pitch, velocity, role)
notes = [
    # Measure 1-2: C major chord + melody
    (0.0, 4.0, 48, 90, "bass"),
    (0.0, 2.0, 52, 75, "harmony"),
    (0.0, 2.0, 55, 75, "harmony"),
    (2.0, 2.0, 52, 70, "harmony"),
    (2.0, 2.0, 55, 70, "harmony"),
    (0.0, 1.0, 64, 100, "melody"),
    (1.0, 1.0, 67, 105, "melody"),
    (2.0, 1.5, 72, 110, "melody"),
    (3.5, 0.5, 71, 80, "melody"),
    (4.0, 4.0, 48, 85, "bass"),
    (4.0, 2.0, 52, 72, "harmony"),
    (4.0, 2.0, 55, 72, "harmony"),
    (6.0, 2.0, 52, 68, "harmony"),
    (6.0, 2.0, 55, 68, "harmony"),
    (4.0, 1.0, 72, 108, "melody"),
    (5.0, 0.5, 71, 85, "melody"),
    (5.5, 0.5, 69, 82, "melody"),
    (6.0, 2.0, 67, 95, "melody"),
    # Measure 3-4: A minor chord + melody
    (8.0, 4.0, 57, 88, "bass"),
    (8.0, 2.0, 48, 72, "harmony"),
    (8.0, 2.0, 52, 72, "harmony"),
    (10.0, 2.0, 48, 68, "harmony"),
    (10.0, 2.0, 52, 68, "harmony"),
    (8.0, 1.0, 69, 102, "melody"),
    (9.0, 1.0, 67, 95, "melody"),
    (10.0, 1.5, 64, 100, "melody"),
    (11.5, 0.5, 62, 78, "melody"),
    (12.0, 4.0, 57, 85, "bass"),
    (12.0, 2.0, 48, 70, "harmony"),
    (12.0, 2.0, 52, 70, "harmony"),
    (14.0, 2.0, 48, 65, "harmony"),
    (14.0, 2.0, 52, 65, "harmony"),
    (12.0, 1.0, 60, 98, "melody"),
    (13.0, 1.0, 62, 90, "melody"),
    (14.0, 2.0, 64, 105, "melody"),
    # Measure 5-6: F major chord + melody
    (16.0, 4.0, 53, 92, "bass"),
    (16.0, 2.0, 57, 74, "harmony"),
    (16.0, 2.0, 60, 74, "harmony"),
    (18.0, 2.0, 57, 70, "harmony"),
    (18.0, 2.0, 60, 70, "harmony"),
    (16.0, 1.0, 65, 100, "melody"),
    (17.0, 1.0, 67, 106, "melody"),
    (18.0, 1.5, 69, 112, "melody"),
    (19.5, 0.5, 67, 82, "melody"),
    (20.0, 4.0, 53, 88, "bass"),
    (20.0, 2.0, 57, 72, "harmony"),
    (20.0, 2.0, 60, 72, "harmony"),
    (22.0, 2.0, 57, 66, "harmony"),
    (22.0, 2.0, 60, 66, "harmony"),
    (20.0, 1.0, 69, 108, "melody"),
    (21.0, 0.5, 67, 84, "melody"),
    (21.5, 0.5, 65, 80, "melody"),
    (22.0, 2.0, 64, 96, "melody"),
    # Measure 7-8: G major chord + melody
    (24.0, 4.0, 55, 95, "bass"),
    (24.0, 2.0, 59, 76, "harmony"),
    (24.0, 2.0, 62, 76, "harmony"),
    (26.0, 2.0, 59, 72, "harmony"),
    (26.0, 2.0, 62, 72, "harmony"),
    (24.0, 1.0, 67, 105, "melody"),
    (25.0, 1.0, 69, 110, "melody"),
    (26.0, 1.5, 71, 118, "melody"),
    (27.5, 0.5, 69, 85, "melody"),
    (28.0, 4.0, 55, 90, "bass"),
    (28.0, 2.0, 59, 74, "harmony"),
    (28.0, 2.0, 62, 74, "harmony"),
    (30.0, 2.0, 59, 70, "harmony"),
    (30.0, 2.0, 62, 70, "harmony"),
    (28.0, 1.0, 71, 115, "melody"),
    (29.0, 1.0, 72, 120, "melody"),
    (30.0, 2.0, 72, 125, "melody"),
]

# Pitch range — auto-fit to data
used_pitches = sorted({n[2] for n in notes})
min_pitch = min(used_pitches)
max_pitch = max(used_pitches)
all_midi_range = list(range(min_pitch, max_pitch + 1))
categories = []
for midi in all_midi_range:
    octave = midi // 12 - 1
    name = NOTE_NAMES[midi % 12]
    categories.append(f"{name}{octave}")
pitch_to_index = {midi: i for i, midi in enumerate(all_midi_range)}

# Velocity → color: imprint_div reversed — blue (soft/piano) → theme midpoint → red (loud/forte)
vel_min, vel_max = 60, 127
_s0 = (68, 103, 163)  # #4467A3 blue at vel=60
_s1 = (250, 248, 241) if THEME == "light" else (26, 26, 23)  # #FAF8F1 / #1A1A17 midpoint
_s2 = (174, 48, 48)  # #AE3030 red at vel=127

# Role config: distinct pointWidth + opacity + border for colorblind safety
role_config = {
    "melody": {"borderWidth": 2, "borderColor": "rgba(255,255,255,0.85)", "pointWidth": 44, "opacity": 1.0},
    "harmony": {"borderWidth": 1, "borderColor": "rgba(0,0,0,0.06)", "pointWidth": 30, "opacity": 0.60},
    "bass": {"borderWidth": 2, "borderColor": "rgba(0,0,0,0.22)", "pointWidth": 52, "opacity": 0.90},
}

# Build series data — inline velocity interpolation
series_data = {"melody": [], "harmony": [], "bass": []}
for start, dur, pitch, vel, role in notes:
    t = float(np.clip((vel - vel_min) / (vel_max - vel_min), 0.0, 1.0))
    if t < 0.5:
        s = t / 0.5
        rv = int(_s0[0] * (1 - s) + _s1[0] * s)
        gv = int(_s0[1] * (1 - s) + _s1[1] * s)
        bv = int(_s0[2] * (1 - s) + _s1[2] * s)
    else:
        s = (t - 0.5) / 0.5
        rv = int(_s1[0] * (1 - s) + _s2[0] * s)
        gv = int(_s1[1] * (1 - s) + _s2[1] * s)
        bv = int(_s1[2] * (1 - s) + _s2[2] * s)
    alpha = role_config[role]["opacity"]
    series_data[role].append(
        {
            "x": start,
            "x2": start + dur,
            "y": pitch_to_index[pitch],
            "color": f"rgba({rv},{gv},{bv},{alpha})",
            "custom": {"pitch": pitch, "velocity": vel, "noteName": categories[pitch_to_index[pitch]], "role": role},
        }
    )

# Colorbar gradient (80 segments, top=loud/crimson, bottom=soft/teal)
colorbar_colors = []
for i in range(80):
    t = 1 - i / 79
    if t < 0.5:
        s = t / 0.5
        rv = int(_s0[0] * (1 - s) + _s1[0] * s)
        gv = int(_s0[1] * (1 - s) + _s1[1] * s)
        bv = int(_s0[2] * (1 - s) + _s1[2] * s)
    else:
        s = (t - 0.5) / 0.5
        rv = int(_s1[0] * (1 - s) + _s2[0] * s)
        gv = int(_s1[1] * (1 - s) + _s2[1] * s)
        bv = int(_s1[2] * (1 - s) + _s2[2] * s)
    colorbar_colors.append(f"rgb({rv},{gv},{bv})")

# Black key row shading — theme-adaptive
band_color = "rgba(0,0,0,0.07)" if THEME == "light" else "rgba(255,255,255,0.07)"
plot_bands = []
for midi in all_midi_range:
    if (midi % 12) in BLACK_KEY_INDICES:
        idx = pitch_to_index[midi]
        plot_bands.append({"from": idx - 0.5, "to": idx + 0.5, "color": band_color})

# Beat grid lines — stronger at measure boundaries
beat_lines = []
for beat in range(33):
    is_measure = beat % 4 == 0
    beat_lines.append(
        {"value": beat, "color": INK_SOFT if is_measure else GRID, "width": 2 if is_measure else 1, "zIndex": 3}
    )

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

title_text = "piano-roll-midi · python · highcharts · anyplot.ai"
n_title = len(title_text)
title_fs = round(66 * 67 / n_title) if n_title > 67 else 66

chart.options.chart = {
    "type": "xrange",
    "width": 3200,
    "height": 1800,
    "backgroundColor": PAGE_BG,
    "marginLeft": 175,
    "marginTop": 160,
    "marginBottom": 155,
    "marginRight": 245,
    "style": {"fontFamily": "'Segoe UI', 'Helvetica Neue', Arial, sans-serif", "color": INK},
}

chart.options.title = {
    "text": title_text,
    "style": {"fontSize": f"{title_fs}px", "fontWeight": "600", "color": INK},
    "y": 78,
}

chart.options.subtitle = {
    "text": "C – Am – F – G · 8 measures of 4/4 · velocity-colored dynamics",
    "style": {"fontSize": "38px", "color": INK_SOFT, "fontWeight": "400"},
    "y": 126,
}

chart.options.x_axis = {
    "title": {"text": "Beats (quarter notes)", "style": {"fontSize": "56px", "color": INK}},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}, "step": 1},
    "min": 0,
    "max": 32,
    "tickInterval": 4,
    "gridLineWidth": 0,
    "plotLines": beat_lines,
    "lineWidth": 0,
    "tickLength": 0,
}

chart.options.y_axis = {
    "type": "category",
    "categories": categories,
    "title": {"text": "Pitch", "style": {"fontSize": "56px", "color": INK}},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "plotBands": plot_bands,
    "reversed": False,
    "lineWidth": 0,
    "tickLength": 0,
}

chart.options.legend = {
    "enabled": True,
    "align": "center",
    "verticalAlign": "bottom",
    "itemStyle": {"fontSize": "44px", "fontWeight": "500", "color": INK_SOFT},
    "itemDistance": 56,
    "symbolWidth": 40,
    "symbolHeight": 22,
    "symbolRadius": 4,
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "borderRadius": 4,
    "padding": 14,
    "margin": 18,
}

chart.options.tooltip = {
    "headerFormat": "",
    "pointFormat": (
        '<span style="font-size:36px"><b>{point.custom.noteName}</b> (MIDI {point.custom.pitch})<br/>'
        "Beat {point.x} – {point.x2}<br/>"
        "Velocity: {point.custom.velocity}<br/>"
        "Role: {point.custom.role}</span>"
    ),
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderRadius": 8,
    "style": {"color": INK},
}

series_configs = [("Melody", "melody", "#009E73"), ("Bass", "bass", "#C475FD"), ("Harmony", "harmony", "#4467A3")]
series_list = []
for label, role, legend_color in series_configs:
    cfg = role_config[role]
    series_list.append(
        {
            "type": "xrange",
            "name": label,
            "data": series_data[role],
            "color": legend_color,
            "pointWidth": cfg["pointWidth"],
            "borderRadius": 4,
            "borderWidth": cfg["borderWidth"],
            "borderColor": cfg["borderColor"],
            "dataLabels": {"enabled": False},
        }
    )
chart.options.series = series_list
chart.options.credits = {"enabled": False}

# Download Highcharts JS modules (with /tmp cache)
cache_dir = Path("/tmp")
cdn_urls = {
    "highcharts": ("https://cdn.jsdelivr.net/npm/highcharts@11.4.8/highcharts.js", cache_dir / "highcharts.js"),
    "xrange": ("https://cdn.jsdelivr.net/npm/highcharts@11.4.8/modules/xrange.js", cache_dir / "hc_xrange.js"),
}
js_scripts = {}
for name, (url, cache_path) in cdn_urls.items():
    if cache_path.exists() and cache_path.stat().st_size > 1000:
        js_scripts[name] = cache_path.read_text(encoding="utf-8")
    else:
        with urllib.request.urlopen(url, timeout=30) as resp:
            content = resp.read().decode("utf-8")
        cache_path.write_text(content, encoding="utf-8")
        js_scripts[name] = content
highcharts_js = js_scripts["highcharts"]
xrange_js = js_scripts["xrange"]

html_str = chart.to_js_literal()

# Chord labels rendered above the plot area via Highcharts renderer
chord_labels = [("C", 2), ("C", 6), ("Am", 10), ("Am", 14), ("F", 18), ("F", 22), ("G", 26), ("G", 30)]
chord_labels_js = ""
for text, beat in chord_labels:
    chord_labels_js += f"""
    r.text('{text}', chart.xAxis[0].toPixels({beat}), 168)
      .attr({{'text-anchor': 'middle'}})
      .css({{fontSize: '32px', color: '{INK_SOFT}', fontWeight: '600', fontStyle: 'italic'}}).add();"""

# Velocity colorbar via Highcharts renderer
colors_js_array = "[" + ",".join(f"'{c}'" for c in colorbar_colors) + "]"

colorbar_js = f"""
<script>
(function() {{
  var checkChart = setInterval(function() {{
    var chart = Highcharts.charts[0];
    if (!chart) return;
    clearInterval(checkChart);
    var r = chart.renderer;
    var cx = 2958, cy = 162, cw = 26, totalH = 1410;
    var colors = {colors_js_array};
    var nSegs = colors.length;
    var segH = totalH / nSegs;
    for (var i = 0; i < nSegs; i++) {{
      r.rect(cx, cy + i * segH, cw, segH + 1, 0).attr({{fill: colors[i], 'stroke-width': 0}}).add();
    }}
    r.rect(cx, cy, cw, totalH, 5).attr({{fill: 'none', stroke: '{INK_SOFT}', 'stroke-width': 1}}).add();
    r.text('Velocity', cx + cw / 2, cy - 18)
      .attr({{'text-anchor': 'middle'}})
      .css({{fontSize: '38px', color: '{INK}', fontWeight: '600'}}).add();
    r.text('forte', cx + cw + 14, cy + 20).css({{fontSize: '30px', color: '{INK_SOFT}'}}).add();
    r.text('127', cx + cw + 14, cy + 50).css({{fontSize: '28px', color: '{INK_SOFT}'}}).add();
    r.text('mezzo', cx + cw + 14, cy + totalH / 2 + 6).css({{fontSize: '30px', color: '{INK_SOFT}'}}).add();
    r.text('93', cx + cw + 14, cy + totalH / 2 + 36).css({{fontSize: '28px', color: '{INK_SOFT}'}}).add();
    r.text('piano', cx + cw + 14, cy + totalH - 14).css({{fontSize: '30px', color: '{INK_SOFT}'}}).add();
    r.text('60', cx + cw + 14, cy + totalH + 16).css({{fontSize: '28px', color: '{INK_SOFT}'}}).add();
    {chord_labels_js}
  }}, 100);
}})();
</script>
"""

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{xrange_js}</script>
</head>
<body style="margin:0; padding:0; background: {PAGE_BG};">
    <div id="container" style="width: 3200px; height: 1800px;"></div>
    <script>{html_str}</script>
    {colorbar_js}
</body>
</html>"""

# Save HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot via Selenium + CDP viewport override
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--hide-scrollbars")
chrome_options.add_argument("--window-size=3200,1800")

driver = webdriver.Chrome(options=chrome_options)
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 3200, "height": 1800, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# Pin to exact canvas dimensions
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
