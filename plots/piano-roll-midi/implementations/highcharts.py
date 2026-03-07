"""pyplots.ai
piano-roll-midi: MIDI Piano Roll Visualization
Library: highcharts unknown | Python 3.14.3
Quality: 85/100 | Created: 2026-03-07
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


np.random.seed(42)

# MIDI helpers
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
BLACK_KEY_INDICES = {1, 3, 6, 8, 10}

# Data - A chord progression with melody (C-Am-F-G, 8 measures of 4/4)
# Each note: (start_beat, duration_beats, midi_pitch, velocity, role)
# role: "bass", "harmony", "melody"
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
    # Measure 7-8: G major chord + melody (building to end)
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

# Determine pitch range - only include pitches that have notes (no empty rows)
used_pitches = sorted({n[2] for n in notes})
min_pitch = min(used_pitches)
max_pitch = max(used_pitches)

# Build category list for only the used range
all_midi_range = list(range(min_pitch, max_pitch + 1))
categories = []
for midi in all_midi_range:
    octave = midi // 12 - 1
    name = NOTE_NAMES[midi % 12]
    categories.append(f"{name}{octave}")

pitch_to_index = {midi: i for i, midi in enumerate(all_midi_range)}

# Velocity color mapping: teal (soft) -> amber (medium) -> crimson (loud)
# Using brighter amber midpoint for crisper transitions
vel_min, vel_max = 60, 127
color_stops_rgb = [
    (20, 130, 150),  # #14829696 deep teal (soft/piano)
    (255, 165, 0),  # #ffa500 bright amber (medium/mezzo) - crisper than olive-gold
    (185, 25, 40),  # #b91928 crimson (loud/forte)
]

# Role-specific styling
role_config = {
    "melody": {"borderWidth": 2, "borderColor": "rgba(255, 255, 255, 0.7)", "pointWidth": 56, "opacity": 1.0},
    "harmony": {"borderWidth": 1, "borderColor": "rgba(0, 0, 0, 0.08)", "pointWidth": 48, "opacity": 0.72},
    "bass": {"borderWidth": 1, "borderColor": "rgba(0, 0, 0, 0.12)", "pointWidth": 64, "opacity": 0.85},
}

# Build xrange data points grouped by role
series_data = {"melody": [], "harmony": [], "bass": []}
for start, dur, pitch, vel, role in notes:
    t = float(np.clip((vel - vel_min) / (vel_max - vel_min), 0.0, 1.0))
    if t < 0.5:
        s = t / 0.5
        r = int(color_stops_rgb[0][0] * (1 - s) + color_stops_rgb[1][0] * s)
        g = int(color_stops_rgb[0][1] * (1 - s) + color_stops_rgb[1][1] * s)
        b = int(color_stops_rgb[0][2] * (1 - s) + color_stops_rgb[1][2] * s)
    else:
        s = (t - 0.5) / 0.5
        r = int(color_stops_rgb[1][0] * (1 - s) + color_stops_rgb[2][0] * s)
        g = int(color_stops_rgb[1][1] * (1 - s) + color_stops_rgb[2][1] * s)
        b = int(color_stops_rgb[1][2] * (1 - s) + color_stops_rgb[2][2] * s)
    alpha = role_config[role]["opacity"]
    color = f"rgba({r},{g},{b},{alpha})"
    series_data[role].append(
        {
            "x": start,
            "x2": start + dur,
            "y": pitch_to_index[pitch],
            "color": color,
            "custom": {"pitch": pitch, "velocity": vel, "noteName": categories[pitch_to_index[pitch]], "role": role},
        }
    )

# Plot bands for black keys (subtle darker background rows)
plot_bands = []
for midi in all_midi_range:
    if (midi % 12) in BLACK_KEY_INDICES:
        idx = pitch_to_index[midi]
        plot_bands.append({"from": idx - 0.5, "to": idx + 0.5, "color": "rgba(0, 0, 0, 0.06)"})

# Beat grid lines for x-axis (stronger at measure boundaries)
total_beats = 32
beat_lines = []
for beat in range(total_beats + 1):
    is_measure = beat % 4 == 0
    beat_lines.append(
        {"value": beat, "color": "#999999" if is_measure else "#dddddd", "width": 2 if is_measure else 1, "zIndex": 3}
    )

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "xrange",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#fafafa",
    "marginLeft": 200,
    "marginTop": 180,
    "marginBottom": 200,
    "marginRight": 380,
    "style": {"fontFamily": "'Segoe UI', 'Helvetica Neue', Arial, sans-serif"},
}

chart.options.title = {
    "text": "piano-roll-midi \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "44px", "fontWeight": "600", "color": "#2c2c2c"},
    "y": 55,
}

chart.options.subtitle = {
    "text": "C \u2013 Am \u2013 F \u2013 G chord progression \u00b7 8 measures \u00b7 velocity-colored dynamics",
    "style": {"fontSize": "26px", "color": "#666666", "fontWeight": "400"},
    "y": 100,
}

chart.options.x_axis = {
    "title": {"text": "Beats", "style": {"fontSize": "28px", "color": "#444444"}},
    "labels": {"style": {"fontSize": "22px", "color": "#555555"}, "step": 1},
    "min": 0,
    "max": 32,
    "tickInterval": 4,
    "gridLineWidth": 0,
    "plotLines": beat_lines,
    "lineWidth": 0,
}

chart.options.y_axis = {
    "type": "category",
    "categories": categories,
    "title": {"text": "Pitch", "style": {"fontSize": "28px", "color": "#444444"}},
    "labels": {"style": {"fontSize": "20px", "color": "#555555"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.04)",
    "plotBands": plot_bands,
    "reversed": False,
    "lineWidth": 0,
}

chart.options.legend = {
    "enabled": True,
    "align": "left",
    "verticalAlign": "top",
    "x": 220,
    "y": 110,
    "floating": True,
    "itemStyle": {"fontSize": "22px", "fontWeight": "500", "color": "#444"},
    "itemDistance": 40,
    "symbolWidth": 28,
    "symbolHeight": 16,
    "symbolRadius": 4,
    "backgroundColor": "rgba(255,255,255,0.8)",
    "borderWidth": 0,
}

chart.options.tooltip = {
    "headerFormat": "",
    "pointFormat": '<span style="font-size:22px"><b>{point.custom.noteName}</b> (MIDI {point.custom.pitch})<br/>'
    "Beat {point.x} \u2013 {point.x2}<br/>"
    "Velocity: {point.custom.velocity}<br/>"
    "Role: {point.custom.role}</span>",
    "backgroundColor": "rgba(255,255,255,0.95)",
    "borderColor": "#cccccc",
    "borderRadius": 8,
    "shadow": {"color": "rgba(0,0,0,0.15)", "offsetX": 2, "offsetY": 2, "width": 4},
}

# Three series for visual hierarchy: melody (prominent), bass (solid), harmony (subtle)
series_configs = [("Melody", "melody", "#d94040"), ("Bass", "bass", "#2a7a8a"), ("Harmony", "harmony", "#c0a030")]

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
            "borderRadius": 5,
            "borderWidth": cfg["borderWidth"],
            "borderColor": cfg["borderColor"],
            "dataLabels": {"enabled": False},
        }
    )
chart.options.series = series_list

chart.options.credits = {"enabled": False}

# Download Highcharts JS modules
cache_dir = Path("/tmp")
cdn_urls = {
    "highcharts": ("https://cdn.jsdelivr.net/npm/highcharts@11.4.8/highcharts.js", cache_dir / "highcharts.js"),
    "xrange": ("https://cdn.jsdelivr.net/npm/highcharts@11.4.8/modules/xrange.js", cache_dir / "hc_xrange.js"),
    "annotations": (
        "https://cdn.jsdelivr.net/npm/highcharts@11.4.8/modules/annotations.js",
        cache_dir / "hc_annotations.js",
    ),
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
annotations_js = js_scripts["annotations"]

# Generate HTML with inline scripts and velocity colorbar via Highcharts renderer callback
html_str = chart.to_js_literal()

# Chord labels positioned above the chart area
chord_labels = [
    {"text": "C", "beat": 2},
    {"text": "C", "beat": 6},
    {"text": "Am", "beat": 10},
    {"text": "Am", "beat": 14},
    {"text": "F", "beat": 18},
    {"text": "F", "beat": 22},
    {"text": "G", "beat": 26},
    {"text": "G", "beat": 30},
]

# JavaScript for chord labels and velocity colorbar
chord_labels_js = ""
for cl in chord_labels:
    chord_labels_js += f"""
    r.text('{cl["text"]}', chart.xAxis[0].toPixels({cl["beat"]}), 155)
      .attr({{'text-anchor':'middle'}})
      .css({{fontSize:'26px', color:'#888', fontWeight:'600', fontStyle:'italic'}}).add();"""

colorbar_js = f"""
<script>
(function() {{
  var checkChart = setInterval(function() {{
    var chart = Highcharts.charts[0];
    if (!chart) return;
    clearInterval(checkChart);
    var r = chart.renderer;
    var x = 4470, y = 220, w = 36, totalH = 2200;
    var stops = [[20,130,150],[255,165,0],[185,25,40]];
    var nSegs = 80;
    var segH = totalH / nSegs;
    for (var i = 0; i < nSegs; i++) {{
      var t = 1 - i / (nSegs - 1);
      var c0, c1, s;
      if (t < 0.5) {{ s = t / 0.5; c0 = stops[0]; c1 = stops[1]; }}
      else {{ s = (t - 0.5) / 0.5; c0 = stops[1]; c1 = stops[2]; }}
      var cr = Math.round(c0[0]*(1-s)+c1[0]*s);
      var cg = Math.round(c0[1]*(1-s)+c1[1]*s);
      var cb = Math.round(c0[2]*(1-s)+c1[2]*s);
      r.rect(x, y + i*segH, w, segH+1, 0).attr({{fill:'rgb('+cr+','+cg+','+cb+')', 'stroke-width':0}}).add();
    }}
    r.rect(x, y, w, totalH, 6).attr({{fill:'none', stroke:'#bbb', 'stroke-width':1}}).add();
    r.text('Velocity', x + w/2, y - 15).attr({{'text-anchor':'middle'}}).css({{fontSize:'24px', color:'#444', fontWeight:'600'}}).add();
    r.text('127 (forte)', x + w + 14, y + 18).css({{fontSize:'20px', color:'#666'}}).add();
    r.text('93 (mezzo)', x + w + 14, y + totalH/2 + 6).css({{fontSize:'20px', color:'#666'}}).add();
    r.text('60 (piano)', x + w + 14, y + totalH - 4).css({{fontSize:'20px', color:'#666'}}).add();
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
    <script>{annotations_js}</script>
</head>
<body style="margin:0; padding:0; background: #fafafa;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
    {colorbar_js}
</body>
</html>"""

# Save HTML
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot with Selenium
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=5000,3000")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)

container = driver.find_element("id", "container")
container.screenshot("plot.png")

driver.quit()
Path(temp_path).unlink()
