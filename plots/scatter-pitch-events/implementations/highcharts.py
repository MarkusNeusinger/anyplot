"""pyplots.ai
scatter-pitch-events: Soccer Pitch Event Map
Library: highcharts | Python 3.13
Quality: pending | Created: 2026-03-20
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Synthetic match event data
np.random.seed(42)

pass_x = np.random.uniform(10, 90, 55)
pass_y = np.random.uniform(5, 63, 55)
pass_ex = np.clip(pass_x + np.random.normal(15, 10, 55), 0, 105)
pass_ey = np.clip(pass_y + np.random.normal(0, 12, 55), 0, 68)
pass_ok = np.random.random(55) < 0.78

shot_x = np.random.uniform(65, 100, 18)
shot_y = np.random.uniform(18, 50, 18)
shot_ex = np.full(18, 105.0)
shot_ey = np.clip(34 + np.random.normal(0, 5, 18), 24, 44)
shot_ok = np.random.random(18) < 0.28

tackle_x = np.random.uniform(10, 75, 25)
tackle_y = np.random.uniform(5, 63, 25)
tackle_ok = np.random.random(25) < 0.68

intercept_x = np.random.uniform(25, 80, 22)
intercept_y = np.random.uniform(5, 63, 22)
intercept_ok = np.random.random(22) < 0.72

PASS_CLR = "#42A5F5"
SHOT_CLR = "#EF5350"
TACKLE_CLR = "#FFA726"
INTERCEPT_CLR = "#AB47BC"

# Build series data with per-point marker styling
pass_data = []
for i in range(55):
    fill = PASS_CLR if pass_ok[i] else "rgba(0,0,0,0)"
    lw = 1 if pass_ok[i] else 3
    pass_data.append(
        {
            "x": round(float(pass_x[i]), 1),
            "y": round(float(pass_y[i]), 1),
            "marker": {"fillColor": fill, "lineColor": PASS_CLR, "lineWidth": lw},
        }
    )

shot_data = []
for i in range(18):
    fill = SHOT_CLR if shot_ok[i] else "rgba(0,0,0,0)"
    lw = 1 if shot_ok[i] else 3
    shot_data.append(
        {
            "x": round(float(shot_x[i]), 1),
            "y": round(float(shot_y[i]), 1),
            "marker": {"fillColor": fill, "lineColor": SHOT_CLR, "lineWidth": lw},
        }
    )

tackle_data = []
for i in range(25):
    fill = TACKLE_CLR if tackle_ok[i] else "rgba(0,0,0,0)"
    lw = 1 if tackle_ok[i] else 3
    tackle_data.append(
        {
            "x": round(float(tackle_x[i]), 1),
            "y": round(float(tackle_y[i]), 1),
            "marker": {"fillColor": fill, "lineColor": TACKLE_CLR, "lineWidth": lw},
        }
    )

intercept_data = []
for i in range(22):
    fill = INTERCEPT_CLR if intercept_ok[i] else "rgba(0,0,0,0)"
    lw = 1 if intercept_ok[i] else 3
    intercept_data.append(
        {
            "x": round(float(intercept_x[i]), 1),
            "y": round(float(intercept_y[i]), 1),
            "marker": {"fillColor": fill, "lineColor": INTERCEPT_CLR, "lineWidth": lw},
        }
    )

# Arrow data for passes and shots
arrows = []
for i in range(55):
    arrows.append(
        {
            "x1": round(float(pass_x[i]), 1),
            "y1": round(float(pass_y[i]), 1),
            "x2": round(float(pass_ex[i]), 1),
            "y2": round(float(pass_ey[i]), 1),
            "c": PASS_CLR,
            "ok": bool(pass_ok[i]),
        }
    )
for i in range(18):
    arrows.append(
        {
            "x1": round(float(shot_x[i]), 1),
            "y1": round(float(shot_y[i]), 1),
            "x2": round(float(shot_ex[i]), 1),
            "y2": round(float(shot_ey[i]), 1),
            "c": SHOT_CLR,
            "ok": bool(shot_ok[i]),
        }
    )

# Chart configuration
chart_config = {
    "chart": {
        "type": "scatter",
        "width": 4800,
        "height": 2700,
        "backgroundColor": "#ffffff",
        "plotBackgroundColor": "#2d6a30",
        "marginBottom": 180,
        "marginTop": 140,
        "marginLeft": 100,
        "marginRight": 80,
    },
    "title": {
        "text": "scatter-pitch-events \u00b7 highcharts \u00b7 pyplots.ai",
        "style": {"fontSize": "44px", "fontWeight": "500", "color": "#333"},
    },
    "subtitle": {
        "text": (
            "\u25cf Filled = Successful \u00a0\u00a0\u00a0"
            "\u25cb Hollow = Unsuccessful \u00a0\u00a0\u00a0"
            "\u2192 Arrows show pass/shot direction"
        ),
        "style": {"fontSize": "28px", "color": "#666"},
    },
    "xAxis": {
        "min": -14.5,
        "max": 119.5,
        "title": {"enabled": False},
        "labels": {"enabled": False},
        "gridLineWidth": 0,
        "lineWidth": 0,
        "tickWidth": 0,
    },
    "yAxis": {
        "min": -2,
        "max": 70,
        "title": {"enabled": False},
        "labels": {"enabled": False},
        "gridLineWidth": 0,
        "lineWidth": 0,
        "tickWidth": 0,
    },
    "legend": {
        "enabled": True,
        "floating": True,
        "verticalAlign": "top",
        "align": "left",
        "x": 120,
        "y": 80,
        "layout": "horizontal",
        "itemStyle": {"fontSize": "30px", "fontWeight": "normal", "color": "#333"},
        "symbolRadius": 0,
        "symbolWidth": 28,
        "symbolHeight": 28,
        "itemDistance": 40,
        "backgroundColor": "rgba(255,255,255,0.88)",
        "borderRadius": 8,
        "padding": 16,
    },
    "credits": {"enabled": False},
    "tooltip": {
        "headerFormat": "",
        "pointFormat": "<b>{series.name}</b><br/>Position: ({point.x:.0f}m, {point.y:.0f}m)",
        "style": {"fontSize": "20px"},
    },
    "plotOptions": {"scatter": {"states": {"hover": {"halo": {"size": 0}}}}},
    "series": [
        {
            "type": "scatter",
            "name": "Pass",
            "color": PASS_CLR,
            "marker": {"symbol": "circle", "radius": 14},
            "data": pass_data,
            "zIndex": 5,
        },
        {
            "type": "scatter",
            "name": "Shot",
            "color": SHOT_CLR,
            "marker": {"symbol": "triangle", "radius": 16},
            "data": shot_data,
            "zIndex": 6,
        },
        {
            "type": "scatter",
            "name": "Tackle",
            "color": TACKLE_CLR,
            "marker": {"symbol": "triangle-down", "radius": 15},
            "data": tackle_data,
            "zIndex": 5,
        },
        {
            "type": "scatter",
            "name": "Interception",
            "color": INTERCEPT_CLR,
            "marker": {"symbol": "diamond", "radius": 15},
            "data": intercept_data,
            "zIndex": 5,
        },
    ],
}

# Download Highcharts JS
cdn_urls = ["https://code.highcharts.com/highcharts.js", "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"]
highcharts_js = None
for url in cdn_urls:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            highcharts_js = response.read().decode("utf-8")
        break
    except Exception:
        continue

# Build HTML with inline pitch rendering
chart_json = json.dumps(chart_config)
arrows_json = json.dumps(arrows)

pitch_js = """
document.addEventListener("DOMContentLoaded", function() {
    var chartConfig = CHART_CONFIG;
    var arrowData = ARROWS_DATA;

    chartConfig.chart.events = {
        load: function() {
            var r = this.renderer;
            var xA = this.xAxis[0];
            var yA = this.yAxis[0];

            function px(v) { return xA.toPixels(v); }
            function py(v) { return yA.toPixels(v); }

            var la = {stroke: "rgba(255,255,255,0.85)", "stroke-width": 4, fill: "none"};

            // Pitch outline
            r.rect(px(0), py(68), px(105)-px(0), py(0)-py(68)).attr(la).add();

            // Halfway line
            r.path(["M", px(52.5), py(0), "L", px(52.5), py(68)]).attr(la).add();

            // Center circle (polyline approximation for correct aspect)
            var ccPts = ["M"];
            for (var a = 0; a <= 360; a += 3) {
                var rad = a * Math.PI / 180;
                ccPts.push(a === 0 ? "M" : "L");
                ccPts.push(px(52.5 + 9.15 * Math.cos(rad)));
                ccPts.push(py(34 + 9.15 * Math.sin(rad)));
            }
            r.path(ccPts).attr(la).add();

            // Center spot
            r.circle(px(52.5), py(34), 6).attr({fill: "rgba(255,255,255,0.85)"}).add();

            // Left penalty area (0-16.5 x 13.84-54.16)
            r.rect(px(0), py(54.16), px(16.5)-px(0), py(13.84)-py(54.16)).attr(la).add();

            // Right penalty area (88.5-105 x 13.84-54.16)
            r.rect(px(88.5), py(54.16), px(105)-px(88.5), py(13.84)-py(54.16)).attr(la).add();

            // Left goal area (0-5.5 x 24.84-43.16)
            r.rect(px(0), py(43.16), px(5.5)-px(0), py(24.84)-py(43.16)).attr(la).add();

            // Right goal area (99.5-105 x 24.84-43.16)
            r.rect(px(99.5), py(43.16), px(105)-px(99.5), py(24.84)-py(43.16)).attr(la).add();

            // Penalty spots
            r.circle(px(11), py(34), 6).attr({fill: "rgba(255,255,255,0.85)"}).add();
            r.circle(px(94), py(34), 6).attr({fill: "rgba(255,255,255,0.85)"}).add();

            // Left penalty arc (outside penalty area)
            var laPts = [];
            for (var a = -53; a <= 53; a += 2) {
                var rad = a * Math.PI / 180;
                laPts.push(a === -53 ? "M" : "L");
                laPts.push(px(11 + 9.15 * Math.cos(rad)));
                laPts.push(py(34 + 9.15 * Math.sin(rad)));
            }
            r.path(laPts).attr(la).add();

            // Right penalty arc
            var raPts = [];
            for (var a = 127; a <= 233; a += 2) {
                var rad = a * Math.PI / 180;
                raPts.push(a === 127 ? "M" : "L");
                raPts.push(px(94 + 9.15 * Math.cos(rad)));
                raPts.push(py(34 + 9.15 * Math.sin(rad)));
            }
            r.path(raPts).attr(la).add();

            // Corner arcs (radius 1m)
            var corners = [[0,0,0,90], [105,0,90,180], [105,68,180,270], [0,68,270,360]];
            corners.forEach(function(c) {
                var pts = [];
                for (var a = c[2]; a <= c[3]; a += 5) {
                    var rad = a * Math.PI / 180;
                    pts.push(a === c[2] ? "M" : "L");
                    pts.push(px(c[0] + 1 * Math.cos(rad)));
                    pts.push(py(c[1] + 1 * Math.sin(rad)));
                }
                r.path(pts).attr(la).add();
            });

            // Goal outlines
            var goalLa = {stroke: "rgba(255,255,255,0.6)", "stroke-width": 3, fill: "none"};
            r.rect(px(-2.44), py(37.66), px(0)-px(-2.44), py(30.34)-py(37.66)).attr(goalLa).add();
            r.rect(px(105), py(37.66), px(107.44)-px(105), py(30.34)-py(37.66)).attr(goalLa).add();

            // Directional arrows for passes and shots
            arrowData.forEach(function(a) {
                var x1 = px(a.x1), y1 = py(a.y1);
                var x2 = px(a.x2), y2 = py(a.y2);
                var alpha = a.ok ? 0.4 : 0.18;
                var cr = parseInt(a.c.slice(1,3), 16);
                var cg = parseInt(a.c.slice(3,5), 16);
                var cb = parseInt(a.c.slice(5,7), 16);
                var sc = "rgba(" + cr + "," + cg + "," + cb + "," + alpha + ")";

                r.path(["M", x1, y1, "L", x2, y2])
                    .attr({stroke: sc, "stroke-width": 2}).add();

                var angle = Math.atan2(y2 - y1, x2 - x1);
                var aLen = 16;
                var hx1 = x2 - aLen * Math.cos(angle - 0.4);
                var hy1 = y2 - aLen * Math.sin(angle - 0.4);
                var hx2 = x2 - aLen * Math.cos(angle + 0.4);
                var hy2 = y2 - aLen * Math.sin(angle + 0.4);
                r.path(["M", hx1, hy1, "L", x2, y2, "L", hx2, hy2])
                    .attr({stroke: sc, "stroke-width": 2}).add();
            });
        }
    };

    Highcharts.chart("container", chartConfig);
});
""".replace("CHART_CONFIG", chart_json).replace("ARROWS_DATA", arrows_json)

html_content = (
    '<!DOCTYPE html>\n<html>\n<head>\n<meta charset="utf-8">\n'
    "<script>" + highcharts_js + "</script>\n"
    '</head>\n<body style="margin:0;">\n'
    '<div id="container" style="width:4800px;height:2700px;"></div>\n'
    "<script>" + pitch_js + "</script>\n"
    "</body>\n</html>"
)

# Save interactive HTML
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp file for screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Screenshot with headless Chrome
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
