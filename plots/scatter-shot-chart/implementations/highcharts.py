"""pyplots.ai
scatter-shot-chart: Basketball Shot Chart
Library: highcharts unknown | Python 3.14.3
Quality: repair-2 | Created: 2026-03-20
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

# Generate shot data by zone using a compact zone definition table
shots = []
# Zone definitions: (n, angle_range, dist_range, make_pct, shot_type, use_polar)
zones = [
    (80, (0, np.pi), (0, 8), 0.55, "2-pointer", True),  # Paint area
    (100, (0.1, np.pi - 0.1), (8, 22), 0.40, "2-pointer", True),  # Mid-range
    (120, (0.05, np.pi - 0.05), (23, 27), 0.35, "3-pointer", True),  # Arc threes
]
for n, (a_lo, a_hi), (d_lo, d_hi), pct, stype, _ in zones:
    angles = np.random.uniform(a_lo, a_hi, n)
    dists = np.random.uniform(d_lo, d_hi, n)
    signs = np.where(np.random.random(n) > 0.5, 1, -1)
    xs, ys = dists * np.cos(angles) * signs, dists * np.sin(angles)
    made = np.random.random(n) < pct
    for i in range(n):
        shots.append({"x": float(xs[i]), "y": float(ys[i]), "made": bool(made[i]), "type": stype})

# Corner threes (rectangular distribution)
n_corner = 40
corner_signs = np.where(np.random.random(n_corner) > 0.5, 1, -1)
corner_x = corner_signs * np.random.uniform(20, 22, n_corner)
corner_y = np.random.uniform(-1, 8, n_corner)
corner_made = np.random.random(n_corner) < 0.38
for i in range(n_corner):
    shots.append({"x": float(corner_x[i]), "y": float(corner_y[i]), "made": bool(corner_made[i]), "type": "3-pointer"})

# Free throws (clustered at FT line)
n_ft = 30
ft_x = np.random.normal(0, 0.3, n_ft)
ft_y = 14.0 + np.random.normal(0, 0.2, n_ft)
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
    "marginTop": 160,
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
    "max": 30,
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
    "itemStyle": {"fontSize": "28px", "fontWeight": "normal", "color": "#ddd"},
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
# Colorblind-safe palette: blue (#4A90D9) for made, orange (#E8833A) for missed
MADE_COLOR = "#4A90D9"
MISSED_COLOR = "#E8833A"
series_defs = [
    {"name": "Made 2PT", "data": made_2pt, "color": MADE_COLOR, "symbol": "circle", "radius": 10},
    {"name": "Missed 2PT", "data": missed_2pt, "color": MISSED_COLOR, "symbol": "circle", "radius": 8},
    {"name": "Made 3PT", "data": made_3pt, "color": MADE_COLOR, "symbol": "diamond", "radius": 11},
    {"name": "Missed 3PT", "data": missed_3pt, "color": MISSED_COLOR, "symbol": "diamond", "radius": 9},
    {"name": "Made FT", "data": made_ft, "color": MADE_COLOR, "symbol": "square", "radius": 9},
    {"name": "Missed FT", "data": missed_ft, "color": MISSED_COLOR, "symbol": "square", "radius": 7},
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
        "lineColor": "#ffffff",
        "lineWidth": 1 if is_made else 2,
        "fillColor": sdef["color"] if is_made else "rgba(232,131,58,0.45)",
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

            var la = {stroke: "rgba(255,255,255,0.55)", "stroke-width": 2.5, fill: "none"};
            var laPrimary = {stroke: "rgba(255,255,255,0.75)", "stroke-width": 4, fill: "none"};

            // Court outline (half court: 50ft wide, baseline to beyond 3pt arc)
            r.rect(px(-25), py(30), px(25)-px(-25), py(-5.25)-py(30)).attr(
                {stroke: "rgba(255,255,255,0.8)", "stroke-width": 5, fill: "none"}
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
            r.path(["M", px(-22), py(-5.25), "L", px(-22), py(arcStartY)]).attr(laPrimary).add();
            // Right corner straight
            r.path(["M", px(22), py(-5.25), "L", px(22), py(arcStartY)]).attr(laPrimary).add();

            // Three-point arc
            var tpPts = [];
            var startAngle = Math.acos(22/23.75);
            var endAngle = Math.PI - startAngle;
            for (var a = startAngle; a <= endAngle; a += 0.02) {
                tpPts.push(tpPts.length === 0 ? "M" : "L");
                tpPts.push(px(23.75 * Math.cos(a)));
                tpPts.push(py(23.75 * Math.sin(a)));
            }
            r.path(tpPts).attr(laPrimary).add();

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
