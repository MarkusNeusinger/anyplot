""" anyplot.ai
heatmap-polar: Polar Heatmap for Cyclic Two-Dimensional Data
Library: highcharts unknown | Python 3.13.13
Quality: 90/100 | Created: 2026-05-13
"""

import json
import os
import tempfile
import time
from pathlib import Path

import numpy as np
import requests
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data: website visits by hour of day (24 angular) × day of week (7 radial)
np.random.seed(42)
days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

hour_labels = []
for h in range(24):
    if h == 0:
        hour_labels.append("12am")
    elif h < 12:
        hour_labels.append(f"{h}am")
    elif h == 12:
        hour_labels.append("12pm")
    else:
        hour_labels.append(f"{h - 12}pm")

# Realistic hourly traffic: ramps through morning, peaks around noon, tapers at night
base_hourly = np.array(
    [5, 3, 2, 2, 2, 4, 8, 14, 28, 48, 60, 67, 70, 62, 56, 64, 68, 58, 47, 36, 25, 17, 11, 7], dtype=float
)
# Weekdays carry full traffic; weekends see ~55% of weekday peak
day_weights = [1.00, 1.00, 1.00, 0.98, 0.95, 0.60, 0.50]

heatmap_data = []
for day_idx, weight in enumerate(day_weights):
    for hour_idx, base in enumerate(base_hourly):
        value = int(round(max(0, base * weight * (1 + np.random.normal(0, 0.08)))))
        heatmap_data.append([hour_idx, day_idx, value])

max_value = max(d[2] for d in heatmap_data)

# Download Highcharts JS inline (headless Chrome cannot load CDN from file://)
hc_base = "https://cdn.jsdelivr.net/npm/highcharts@11.4.6"
highcharts_js = requests.get(f"{hc_base}/highcharts.js", timeout=30).text

# Inject Python data as JS variables; write the rendering logic as a raw JS string
data_js = json.dumps(heatmap_data)
hours_js = json.dumps(hour_labels)
days_js = json.dumps(days)
cfg_js = json.dumps(
    {"pageBg": PAGE_BG, "elevatedBg": ELEVATED_BG, "ink": INK, "inkSoft": INK_SOFT, "maxValue": max_value}
)

# Raw JavaScript (no Python f-string escaping needed for braces)
js_logic = r"""
var heatmapData = __DATA__;
var hourLabels = __HOURS__;
var days = __DAYS__;
var cfg = __CFG__;

// Viridis color interpolation
var viridisPalette = [
    [0.00, [68,  1,  84]],
    [0.25, [59, 82, 139]],
    [0.50, [33,144,140]],
    [0.75, [93,200, 99]],
    [1.00, [253,231, 37]]
];

function valueToColor(value) {
    var t = cfg.maxValue > 0 ? Math.min(1, Math.max(0, value / cfg.maxValue)) : 0;
    for (var i = 0; i < viridisPalette.length - 1; i++) {
        if (t >= viridisPalette[i][0] && t <= viridisPalette[i + 1][0]) {
            var f = (t - viridisPalette[i][0]) / (viridisPalette[i + 1][0] - viridisPalette[i][0]);
            var r = Math.round(viridisPalette[i][1][0] + f * (viridisPalette[i + 1][1][0] - viridisPalette[i][1][0]));
            var g = Math.round(viridisPalette[i][1][1] + f * (viridisPalette[i + 1][1][1] - viridisPalette[i][1][1]));
            var b = Math.round(viridisPalette[i][1][2] + f * (viridisPalette[i + 1][1][2] - viridisPalette[i][1][2]));
            return 'rgb(' + r + ',' + g + ',' + b + ')';
        }
    }
    return 'rgb(253,231,37)';
}

// Annular sector path (0° = north, clockwise)
function arcPath(cx, cy, r1, r2, a1, a2) {
    var x1 = cx + r1 * Math.sin(a1), y1 = cy - r1 * Math.cos(a1);
    var x2 = cx + r2 * Math.sin(a1), y2 = cy - r2 * Math.cos(a1);
    var x3 = cx + r2 * Math.sin(a2), y3 = cy - r2 * Math.cos(a2);
    var x4 = cx + r1 * Math.sin(a2), y4 = cy - r1 * Math.cos(a2);
    var lg = (a2 - a1 > Math.PI) ? 1 : 0;
    return ['M', x1, y1, 'L', x2, y2, 'A', r2, r2, 0, lg, 1, x3, y3, 'L', x4, y4, 'A', r1, r1, 0, lg, 0, x1, y1, 'Z'];
}

Highcharts.chart('container', {
    chart: {
        backgroundColor: cfg.pageBg,
        width: 3600,
        height: 3600,
        margin: [180, 440, 120, 120],
        animation: false,
        style: { fontFamily: 'Arial, sans-serif' },
        events: {
            render: function () {
                var chart = this;
                if (chart._drawn) { return; }
                chart._drawn = true;

                var cx  = chart.plotLeft + chart.plotWidth  / 2;
                var cy  = chart.plotTop  + chart.plotHeight / 2;
                var rMax = Math.min(chart.plotWidth, chart.plotHeight) / 2 * 0.95;
                var rMin = rMax * 0.10;
                var N_ANG = 24, N_RAD = 7;

                // ── Heatmap cells ──────────────────────────────────────────
                heatmapData.forEach(function (pt) {
                    var hour = pt[0], day = pt[1], val = pt[2];
                    var r1 = rMin + (day / N_RAD) * (rMax - rMin);
                    var r2 = rMin + ((day + 1) / N_RAD) * (rMax - rMin);
                    var a1 = (hour / N_ANG) * 2 * Math.PI;
                    var a2 = ((hour + 1) / N_ANG) * 2 * Math.PI;
                    chart.renderer.path(arcPath(cx, cy, r1, r2, a1, a2))
                        .attr({ fill: valueToColor(val), stroke: cfg.pageBg, 'stroke-width': 1.5 })
                        .add();
                });

                // ── Hour labels around the perimeter ─────────────────────
                for (var h = 0; h < N_ANG; h++) {
                    var ang = ((h + 0.5) / N_ANG) * 2 * Math.PI;
                    var lr  = rMax * 1.07;
                    var lx  = cx + lr * Math.sin(ang);
                    var ly  = cy - lr * Math.cos(ang);
                    chart.renderer.text(hourLabels[h], lx, ly + 9)
                        .attr({ align: 'center', zIndex: 12 })
                        .css({ color: cfg.inkSoft, fontSize: '22px', fontFamily: 'Arial, sans-serif' })
                        .add();
                }

                // ── Day labels (radial axis): between 12am and 1am, at each ring mid-radius
                var labelAng = (0.5 / N_ANG) * 2 * Math.PI;   // midpoint of 12am cell ≈ 7.5°
                for (var d = 0; d < N_RAD; d++) {
                    var rMid = rMin + ((d + 0.5) / N_RAD) * (rMax - rMin);
                    var dlx  = cx + rMid * Math.sin(labelAng);
                    var dly  = cy - rMid * Math.cos(labelAng);
                    chart.renderer.text(days[d], dlx, dly + 9)
                        .attr({ align: 'left', zIndex: 12 })
                        .css({ color: '#FFFFFF', fontSize: '26px', fontWeight: '700',
                               fontFamily: 'Arial, sans-serif',
                               textShadow: '0 0 6px rgba(0,0,0,0.9)' })
                        .add();
                }

                // ── Colorbar ───────────────────────────────────────────────
                var barX  = chart.plotLeft + chart.plotWidth + 60;
                var barY  = chart.plotTop  + chart.plotHeight * 0.15;
                var barH  = chart.plotHeight * 0.68;
                var barW  = 52;
                var nBand = 200;

                for (var i = 0; i < nBand; i++) {
                    var t     = 1 - i / nBand;
                    var bY    = barY + (i / nBand) * barH;
                    var bH    = barH / nBand + 0.5;
                    var color = valueToColor(t * cfg.maxValue);
                    chart.renderer.rect(barX, bY, barW, bH)
                        .attr({ fill: color, 'stroke-width': 0 })
                        .add();
                }
                chart.renderer.rect(barX, barY, barW, barH)
                    .attr({ fill: 'none', stroke: cfg.inkSoft, 'stroke-width': 2 })
                    .add();

                [0, 0.25, 0.5, 0.75, 1.0].forEach(function (frac) {
                    var ty    = barY + (1 - frac) * barH;
                    var label = Math.round(frac * cfg.maxValue).toString();
                    chart.renderer.rect(barX + barW, ty - 1, 14, 2)
                        .attr({ fill: cfg.inkSoft }).add();
                    chart.renderer.text(label, barX + barW + 22, ty + 9)
                        .css({ color: cfg.inkSoft, fontSize: '22px', fontFamily: 'Arial, sans-serif' })
                        .add();
                });

                chart.renderer.text('Visits / hr', barX + barW / 2, barY - 32)
                    .attr({ align: 'center', zIndex: 12 })
                    .css({ color: cfg.ink, fontSize: '26px', fontWeight: '500',
                           fontFamily: 'Arial, sans-serif' })
                    .add();
            }
        }
    },
    title: {
        text: 'heatmap-polar · highcharts · anyplot.ai',
        style: { fontSize: '44px', color: '__INK__', fontWeight: '600',
                 fontFamily: 'Arial, sans-serif' },
        y: 70
    },
    subtitle: {
        text: 'Hourly website visits by day of week',
        style: { fontSize: '28px', color: '__INK_SOFT__', fontFamily: 'Arial, sans-serif' },
        y: 128
    },
    xAxis:   { visible: false },
    yAxis:   { visible: false },
    legend:  { enabled: false },
    series:  [],
    credits: { enabled: false },
    tooltip: { enabled: false }
});
"""

# Substitute Python values into the JS string
js_logic = (
    js_logic.replace("__DATA__", data_js)
    .replace("__HOURS__", hours_js)
    .replace("__DAYS__", days_js)
    .replace("__CFG__", cfg_js)
    .replace("__INK__", INK)
    .replace("__INK_SOFT__", INK_SOFT)
)

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width:3600px; height:3600px;"></div>
    <script>
{js_logic}
    </script>
</body>
</html>"""

# Save HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot via Selenium headless Chrome
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=3700,3700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot("plot_raw.png")
driver.quit()

# Crop to exact 3600×3600
img = Image.open("plot_raw.png")
img_cropped = img.crop((0, 0, 3600, 3600))
img_cropped.save(f"plot-{THEME}.png")
Path("plot_raw.png").unlink()

Path(temp_path).unlink()
