"""pyplots.ai
scatter-pitch-events: Soccer Pitch Event Map
Library: highcharts unknown | Python 3.14.3
Quality: 83/100 | Created: 2026-03-20
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

events = {
    "Pass": {
        "n": 55,
        "color": "#2196F3",
        "symbol": "circle",
        "radius": 13,
        "z": 4,
        "success_rate": 0.78,
        "x_range": (10, 90),
        "y_range": (5, 63),
        "has_arrow": True,
    },
    "Shot": {
        "n": 18,
        "color": "#E53935",
        "symbol": "triangle",
        "radius": 18,
        "z": 8,
        "success_rate": 0.28,
        "x_range": (65, 100),
        "y_range": (18, 50),
        "has_arrow": True,
    },
    "Tackle": {
        "n": 25,
        "color": "#FF9800",
        "symbol": "triangle-down",
        "radius": 14,
        "z": 5,
        "success_rate": 0.68,
        "x_range": (10, 75),
        "y_range": (5, 63),
        "has_arrow": False,
    },
    "Interception": {
        "n": 22,
        "color": "#00897B",
        "symbol": "diamond",
        "radius": 14,
        "z": 5,
        "success_rate": 0.72,
        "x_range": (25, 80),
        "y_range": (5, 63),
        "has_arrow": False,
    },
}

arrows = []
series_list = []

for name, cfg in events.items():
    n = cfg["n"]
    x = np.random.uniform(*cfg["x_range"], n)
    y = np.random.uniform(*cfg["y_range"], n)
    ok = np.random.random(n) < cfg["success_rate"]

    # Unsuccessful: white fill with colored border for contrast on green pitch
    data = [
        {
            "x": round(float(x[i]), 1),
            "y": round(float(y[i]), 1),
            "marker": {
                "fillColor": cfg["color"] if ok[i] else "rgba(255,255,255,0.75)",
                "lineColor": cfg["color"],
                "lineWidth": 2 if ok[i] else 3,
            },
        }
        for i in range(n)
    ]

    series_list.append(
        {
            "type": "scatter",
            "name": name,
            "color": cfg["color"],
            "marker": {"symbol": cfg["symbol"], "radius": cfg["radius"], "lineColor": cfg["color"], "lineWidth": 2},
            "data": data,
            "zIndex": cfg["z"],
        }
    )

    if cfg["has_arrow"]:
        if name == "Shot":
            ex = np.full(n, 105.0)
            ey = np.clip(34 + np.random.normal(0, 5, n), 24, 44)
        else:
            ex = np.clip(x + np.random.normal(15, 10, n), 0, 105)
            ey = np.clip(y + np.random.normal(0, 12, n), 0, 68)
        for i in range(n):
            arrows.append(
                {
                    "x1": round(float(x[i]), 1),
                    "y1": round(float(y[i]), 1),
                    "x2": round(float(ex[i]), 1),
                    "y2": round(float(ey[i]), 1),
                    "c": cfg["color"],
                    "ok": bool(ok[i]),
                }
            )

# Chart configuration
chart_config = {
    "chart": {
        "type": "scatter",
        "width": 4800,
        "height": 2700,
        "backgroundColor": "#1a1a2e",
        "plotBackgroundColor": {
            "linearGradient": {"x1": 0, "y1": 0, "x2": 0, "y2": 1},
            "stops": [[0, "#2d7a32"], [0.5, "#256b28"], [1, "#1e5c20"]],
        },
        "marginBottom": 180,
        "marginTop": 160,
        "marginLeft": 100,
        "marginRight": 80,
        "style": {"fontFamily": "'Segoe UI', Helvetica, Arial, sans-serif"},
    },
    "title": {
        "text": "scatter-pitch-events \u00b7 highcharts \u00b7 pyplots.ai",
        "style": {"fontSize": "46px", "fontWeight": "600", "color": "#e8e8e8", "letterSpacing": "0.5px"},
    },
    "subtitle": {
        "text": (
            '<span style="font-size:30px;color:#aaa;">'
            "\u25cf Filled = Successful \u00a0\u00a0"
            "\u25cb White = Unsuccessful \u00a0\u00a0"
            "\u2192 Arrows show pass/shot trajectory \u00a0\u00a0"
            "| Shots enlarged for tactical emphasis"
            "</span>"
        ),
        "useHTML": True,
        "style": {"fontSize": "30px"},
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
        "itemStyle": {"fontSize": "30px", "fontWeight": "normal", "color": "#ddd"},
        "itemHoverStyle": {"color": "#fff"},
        "symbolRadius": 0,
        "symbolWidth": 28,
        "symbolHeight": 28,
        "itemDistance": 40,
        "backgroundColor": "rgba(26,26,46,0.85)",
        "borderRadius": 10,
        "padding": 18,
        "shadow": True,
    },
    "credits": {"enabled": False},
    "tooltip": {
        "headerFormat": "",
        "pointFormat": (
            '<b style="color:{series.color}">{series.name}</b><br/>Position: ({point.x:.0f}m, {point.y:.0f}m)'
        ),
        "style": {"fontSize": "20px"},
        "backgroundColor": "rgba(26,26,46,0.92)",
        "borderColor": "#555",
        "shadow": True,
    },
    "plotOptions": {
        "scatter": {
            "states": {"hover": {"halo": {"size": 12, "attributes": {"opacity": 0.25}}}},
            "shadow": {"color": "rgba(0,0,0,0.3)", "offsetX": 0, "offsetY": 2, "width": 6},
        }
    },
    "series": series_list,
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

            var la = {stroke: "rgba(255,255,255,0.82)", "stroke-width": 4, fill: "none"};

            // Pitch outline
            r.rect(px(0), py(68), px(105)-px(0), py(0)-py(68)).attr(la).add();

            // Halfway line
            r.path(["M", px(52.5), py(0), "L", px(52.5), py(68)]).attr(la).add();

            // Center circle
            var ccPts = [];
            for (var a = 0; a <= 360; a += 3) {
                var rad = a * Math.PI / 180;
                ccPts.push(a === 0 ? "M" : "L");
                ccPts.push(px(52.5 + 9.15 * Math.cos(rad)));
                ccPts.push(py(34 + 9.15 * Math.sin(rad)));
            }
            r.path(ccPts).attr(la).add();

            // Center spot
            r.circle(px(52.5), py(34), 7).attr({fill: "rgba(255,255,255,0.82)"}).add();

            // Penalty areas
            r.rect(px(0), py(54.16), px(16.5)-px(0), py(13.84)-py(54.16)).attr(la).add();
            r.rect(px(88.5), py(54.16), px(105)-px(88.5), py(13.84)-py(54.16)).attr(la).add();

            // Goal areas
            r.rect(px(0), py(43.16), px(5.5)-px(0), py(24.84)-py(43.16)).attr(la).add();
            r.rect(px(99.5), py(43.16), px(105)-px(99.5), py(24.84)-py(43.16)).attr(la).add();

            // Penalty spots
            r.circle(px(11), py(34), 7).attr({fill: "rgba(255,255,255,0.82)"}).add();
            r.circle(px(94), py(34), 7).attr({fill: "rgba(255,255,255,0.82)"}).add();

            // Left penalty arc
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

            // Corner arcs
            [[0,0,0,90],[105,0,90,180],[105,68,180,270],[0,68,270,360]].forEach(function(c) {
                var pts = [];
                for (var a = c[2]; a <= c[3]; a += 5) {
                    var rad = a * Math.PI / 180;
                    pts.push(a === c[2] ? "M" : "L");
                    pts.push(px(c[0] + Math.cos(rad)));
                    pts.push(py(c[1] + Math.sin(rad)));
                }
                r.path(pts).attr(la).add();
            });

            // Goal outlines
            var goalLa = {stroke: "rgba(255,255,255,0.55)", "stroke-width": 3, fill: "none"};
            r.rect(px(-2.44), py(37.66), px(0)-px(-2.44), py(30.34)-py(37.66)).attr(goalLa).add();
            r.rect(px(105), py(37.66), px(107.44)-px(105), py(30.34)-py(37.66)).attr(goalLa).add();

            // Directional arrows with glow effect for successful
            arrowData.forEach(function(a) {
                var x1 = px(a.x1), y1 = py(a.y1);
                var x2 = px(a.x2), y2 = py(a.y2);
                var alpha = a.ok ? 0.45 : 0.15;
                var cr = parseInt(a.c.slice(1,3), 16);
                var cg = parseInt(a.c.slice(3,5), 16);
                var cb = parseInt(a.c.slice(5,7), 16);
                var sc = "rgba(" + cr + "," + cg + "," + cb + "," + alpha + ")";
                var sw = a.ok ? 2.5 : 1.5;

                r.path(["M", x1, y1, "L", x2, y2])
                    .attr({stroke: sc, "stroke-width": sw}).add();

                var angle = Math.atan2(y2 - y1, x2 - x1);
                var aLen = a.ok ? 18 : 12;
                var hx1 = x2 - aLen * Math.cos(angle - 0.4);
                var hy1 = y2 - aLen * Math.sin(angle - 0.4);
                var hx2 = x2 - aLen * Math.cos(angle + 0.4);
                var hy2 = y2 - aLen * Math.sin(angle + 0.4);
                r.path(["M", hx1, hy1, "L", x2, y2, "L", hx2, hy2])
                    .attr({stroke: sc, "stroke-width": sw}).add();
            });

            // Zone labels - subtle pitch thirds
            var zoneStyle = {color: "rgba(255,255,255,0.12)", fontSize: "28px", fontWeight: "bold"};
            r.text("DEFENSIVE THIRD", px(17.5), py(-0.5)).attr({align: "center"}).css(zoneStyle).add();
            r.text("MIDDLE THIRD", px(52.5), py(-0.5)).attr({align: "center"}).css(zoneStyle).add();
            r.text("ATTACKING THIRD", px(87.5), py(-0.5)).attr({align: "center"}).css(zoneStyle).add();
        }
    };

    Highcharts.chart("container", chartConfig);
});
""".replace("CHART_CONFIG", chart_json).replace("ARROWS_DATA", arrows_json)

html_content = (
    '<!DOCTYPE html>\n<html>\n<head>\n<meta charset="utf-8">\n'
    "<script>" + highcharts_js + "</script>\n"
    '</head>\n<body style="margin:0;background:#1a1a2e;">\n'
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
