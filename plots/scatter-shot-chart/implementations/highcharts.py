"""pyplots.ai
scatter-shot-chart: Basketball Shot Chart
Library: highcharts | Python 3.13
Quality: pending | Created: 2026-03-20
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.scatter import ScatterSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Synthetic basketball shot chart data
np.random.seed(42)

# NBA half-court: basket at (0,0), baseline at y=-5.25, half-court at y=41.75
# Court is 50 ft wide (x: -25 to 25)
# Basket center is 5.25 ft from baseline

# Generate shot data by zone
shots = []

# Paint area 2-pointers (close range)
n_paint = 80
paint_angles = np.random.uniform(0, np.pi, n_paint)
paint_dist = np.random.uniform(0, 8, n_paint)
paint_x = paint_dist * np.cos(paint_angles) * np.array([1 if np.random.random() > 0.5 else -1 for _ in range(n_paint)])
paint_y = paint_dist * np.sin(paint_angles)
paint_made = np.random.random(n_paint) < 0.55
for i in range(n_paint):
    shots.append({"x": float(paint_x[i]), "y": float(paint_y[i]), "made": bool(paint_made[i]), "type": "2-pointer"})

# Mid-range 2-pointers
n_mid = 100
mid_angles = np.random.uniform(0.1, np.pi - 0.1, n_mid)
mid_dist = np.random.uniform(8, 22, n_mid)
mid_x = mid_dist * np.cos(mid_angles) * np.array([1 if np.random.random() > 0.5 else -1 for _ in range(n_mid)])
mid_y = mid_dist * np.sin(mid_angles)
mid_made = np.random.random(n_mid) < 0.40
for i in range(n_mid):
    shots.append({"x": float(mid_x[i]), "y": float(mid_y[i]), "made": bool(mid_made[i]), "type": "2-pointer"})

# Three-pointers (arc)
n_three = 120
three_angles = np.random.uniform(0.05, np.pi - 0.05, n_three)
three_dist = np.random.uniform(23, 27, n_three)
three_x = three_dist * np.cos(three_angles) * np.array([1 if np.random.random() > 0.5 else -1 for _ in range(n_three)])
three_y = three_dist * np.sin(three_angles)
three_made = np.random.random(n_three) < 0.35
for i in range(n_three):
    shots.append({"x": float(three_x[i]), "y": float(three_y[i]), "made": bool(three_made[i]), "type": "3-pointer"})

# Corner threes
n_corner = 40
corner_side = np.array([1 if np.random.random() > 0.5 else -1 for _ in range(n_corner)])
corner_x = corner_side * np.random.uniform(20, 22, n_corner)
corner_y = np.random.uniform(-1, 8, n_corner)
corner_made = np.random.random(n_corner) < 0.38
for i in range(n_corner):
    shots.append({"x": float(corner_x[i]), "y": float(corner_y[i]), "made": bool(corner_made[i]), "type": "3-pointer"})

# Free throws
n_ft = 30
ft_x = np.random.normal(0, 0.3, n_ft)
ft_y = np.full(n_ft, 14.0) + np.random.normal(0, 0.2, n_ft)
ft_made = np.random.random(n_ft) < 0.80
for i in range(n_ft):
    shots.append({"x": float(ft_x[i]), "y": float(ft_y[i]), "made": bool(ft_made[i]), "type": "free-throw"})

# Build series data: made vs missed
made_2pt = [{"x": round(s["x"], 1), "y": round(s["y"], 1)} for s in shots if s["made"] and s["type"] == "2-pointer"]
missed_2pt = [
    {"x": round(s["x"], 1), "y": round(s["y"], 1)} for s in shots if not s["made"] and s["type"] == "2-pointer"
]
made_3pt = [{"x": round(s["x"], 1), "y": round(s["y"], 1)} for s in shots if s["made"] and s["type"] == "3-pointer"]
missed_3pt = [
    {"x": round(s["x"], 1), "y": round(s["y"], 1)} for s in shots if not s["made"] and s["type"] == "3-pointer"
]
made_ft = [{"x": round(s["x"], 1), "y": round(s["y"], 1)} for s in shots if s["made"] and s["type"] == "free-throw"]
missed_ft = [
    {"x": round(s["x"], 1), "y": round(s["y"], 1)} for s in shots if not s["made"] and s["type"] == "free-throw"
]

# Chart setup
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "scatter",
    "width": 3600,
    "height": 3600,
    "backgroundColor": "#1a1a2e",
    "plotBackgroundColor": "#2a2a3e",
    "marginBottom": 120,
    "marginTop": 180,
    "marginLeft": 120,
    "marginRight": 120,
    "style": {"fontFamily": "'Segoe UI', Helvetica, Arial, sans-serif"},
}

chart.options.title = {
    "text": "scatter-shot-chart \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "42px", "fontWeight": "600", "color": "#e8e8e8"},
}

chart.options.subtitle = {
    "text": ('<span style="font-size:28px;color:#aaa;">Season Shot Chart \u2014 370 Attempts</span>'),
    "useHTML": True,
}

chart.options.x_axis = {
    "min": -28,
    "max": 28,
    "title": {"enabled": False},
    "labels": {"enabled": False},
    "gridLineWidth": 0,
    "lineWidth": 0,
    "tickWidth": 0,
}

chart.options.y_axis = {
    "min": -8,
    "max": 32,
    "title": {"enabled": False},
    "labels": {"enabled": False},
    "gridLineWidth": 0,
    "lineWidth": 0,
    "tickWidth": 0,
}

chart.options.legend = {
    "enabled": True,
    "floating": True,
    "verticalAlign": "top",
    "align": "right",
    "x": -30,
    "y": 80,
    "layout": "vertical",
    "itemStyle": {"fontSize": "24px", "fontWeight": "normal", "color": "#ddd"},
    "itemHoverStyle": {"color": "#fff"},
    "symbolRadius": 6,
    "symbolWidth": 22,
    "symbolHeight": 22,
    "itemMarginBottom": 8,
    "backgroundColor": "rgba(26,26,46,0.9)",
    "borderRadius": 10,
    "padding": 18,
}

chart.options.credits = {"enabled": False}

chart.options.tooltip = {
    "headerFormat": "",
    "pointFormat": (
        '<b style="color:{series.color}">{series.name}</b><br/>Position: ({point.x:.1f} ft, {point.y:.1f} ft)'
    ),
    "style": {"fontSize": "20px"},
    "backgroundColor": "rgba(26,26,46,0.92)",
    "borderColor": "#555",
}

chart.options.plot_options = {"scatter": {"shadow": False, "states": {"hover": {"enabled": True}}}}

# Series definitions
series_defs = [
    {"name": "Made 2PT", "data": made_2pt, "color": "#2ecc71", "symbol": "circle", "radius": 10},
    {"name": "Missed 2PT", "data": missed_2pt, "color": "#e74c3c", "symbol": "circle", "radius": 8},
    {"name": "Made 3PT", "data": made_3pt, "color": "#27ae60", "symbol": "diamond", "radius": 11},
    {"name": "Missed 3PT", "data": missed_3pt, "color": "#c0392b", "symbol": "diamond", "radius": 9},
    {"name": "Made FT", "data": made_ft, "color": "#2ecc71", "symbol": "square", "radius": 9},
    {"name": "Missed FT", "data": missed_ft, "color": "#e74c3c", "symbol": "square", "radius": 7},
]

for sdef in series_defs:
    series = ScatterSeries()
    series.name = sdef["name"]
    series.color = sdef["color"]
    series.data = sdef["data"]
    is_made = "Made" in sdef["name"]
    series.marker = {
        "symbol": sdef["symbol"],
        "radius": sdef["radius"],
        "lineColor": "#ffffff" if is_made else sdef["color"],
        "lineWidth": 1 if is_made else 2,
        "fillColor": sdef["color"] if is_made else "rgba(0,0,0,0.15)",
    }
    series.z_index = 6 if is_made else 5
    chart.add_series(series)

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

chart_js = chart.to_js_literal()

# Court drawing via Highcharts renderer API
court_js = """
(function() {
    var origChart = Highcharts.chart;
    Highcharts.chart = function(container, opts) {
        opts.chart = opts.chart || {};
        opts.chart.events = opts.chart.events || {};
        var origLoad = opts.chart.events.load;
        opts.chart.events.load = function() {
            if (origLoad) origLoad.call(this);
            var r = this.renderer;
            var xA = this.xAxis[0];
            var yA = this.yAxis[0];

            function px(v) { return xA.toPixels(v); }
            function py(v) { return yA.toPixels(v); }

            var la = {stroke: "rgba(255,255,255,0.65)", "stroke-width": 3, fill: "none"};

            // Court outline (half court: 50ft wide, baseline to beyond 3pt arc)
            r.rect(px(-25), py(30), px(25)-px(-25), py(-5.25)-py(30)).attr(
                {stroke: "rgba(255,255,255,0.7)", "stroke-width": 4, fill: "none"}
            ).add();

            // Half-court line
            r.path(["M", px(-25), py(30), "L", px(25), py(30)]).attr(
                {stroke: "rgba(255,255,255,0.5)", "stroke-width": 3, dashstyle: "dash"}
            ).add();

            // Paint / key area (16 ft wide, 19 ft from baseline)
            r.rect(px(-8), py(13.75), px(8)-px(-8), py(-5.25)-py(13.75)).attr(la).add();

            // Free-throw circle (6 ft radius at 13.75 ft from baseline)
            var ftPts = [];
            for (var a = 0; a <= 180; a += 3) {
                var rad = a * Math.PI / 180;
                ftPts.push(a === 0 ? "M" : "L");
                ftPts.push(px(6 * Math.cos(rad)));
                ftPts.push(py(13.75 + 6 * Math.sin(rad)));
            }
            r.path(ftPts).attr(la).add();

            // Free-throw circle bottom (dashed)
            var ftBPts = [];
            for (var a = 180; a <= 360; a += 3) {
                var rad = a * Math.PI / 180;
                ftBPts.push(a === 180 ? "M" : "L");
                ftBPts.push(px(6 * Math.cos(rad)));
                ftBPts.push(py(13.75 + 6 * Math.sin(rad)));
            }
            r.path(ftBPts).attr(
                {stroke: "rgba(255,255,255,0.35)", "stroke-width": 2, fill: "none", dashstyle: "dash"}
            ).add();

            // Restricted area arc (4 ft radius)
            var raPts = [];
            for (var a = 0; a <= 180; a += 3) {
                var rad = a * Math.PI / 180;
                raPts.push(a === 0 ? "M" : "L");
                raPts.push(px(4 * Math.cos(rad)));
                raPts.push(py(4 * Math.sin(rad)));
            }
            r.path(raPts).attr(la).add();

            // Three-point line
            // Corner straight sections: from baseline to where arc begins
            // Arc radius 23.75 ft, straight at x = +-22
            var arcStartY = Math.sqrt(23.75*23.75 - 22*22);

            // Left corner straight
            r.path(["M", px(-22), py(-5.25), "L", px(-22), py(arcStartY)]).attr(la).add();
            // Right corner straight
            r.path(["M", px(22), py(-5.25), "L", px(22), py(arcStartY)]).attr(la).add();

            // Three-point arc
            var tpPts = [];
            var startAngle = Math.acos(22/23.75);
            var endAngle = Math.PI - startAngle;
            for (var a = startAngle; a <= endAngle; a += 0.02) {
                tpPts.push(tpPts.length === 0 ? "M" : "L");
                tpPts.push(px(23.75 * Math.cos(a)));
                tpPts.push(py(23.75 * Math.sin(a)));
            }
            r.path(tpPts).attr(la).add();

            // Basket (rim circle, ~0.75 ft radius)
            r.circle(px(0), py(0), 8).attr(
                {stroke: "#ff6b35", "stroke-width": 4, fill: "none"}
            ).add();

            // Backboard (4 ft wide, at y ~ -1.25)
            r.path(["M", px(-3), py(-1.25), "L", px(3), py(-1.25)]).attr(
                {stroke: "rgba(255,255,255,0.8)", "stroke-width": 4}
            ).add();

            // Baseline text
            var zoneStyle = {color: "rgba(255,255,255,0.3)", fontSize: "24px", fontWeight: "bold", fontStyle: "italic"};
            r.text("BASELINE", px(0), py(-6.5)).attr({align: "center"}).css(zoneStyle).add();
        };
        return origChart.call(this, container, opts);
    };
})();
"""

html_content = (
    '<!DOCTYPE html>\n<html>\n<head>\n<meta charset="utf-8">\n'
    "<script>" + highcharts_js + "</script>\n"
    "</head>\n"
    '<body style="margin:0;background:#1a1a2e;">\n'
    '<div id="container" style="width:3600px;height:3600px;"></div>\n'
    "<script>" + court_js + "</script>\n"
    "<script>" + chart_js + "</script>\n"
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
chrome_options.add_argument("--window-size=3600,3600")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
