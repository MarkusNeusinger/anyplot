"""anyplot.ai
tree-decision: Decision Tree Visualization with Probabilities
Library: highcharts | Python 3.13
Quality: pending | Created: 2026-06-02
"""

import base64
import json
import os
import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.scatter import ScatterSeries
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens — Imprint palette / theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint categorical palette — 8 hues, hybrid-v3 sort
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
COLOR_DECISION = IMPRINT_PALETTE[0]  # brand green — decision nodes (controllable)
COLOR_CHANCE = IMPRINT_PALETTE[1]  # lavender — chance nodes (uncertain)
COLOR_TERMINAL = IMPRINT_PALETTE[2]  # blue — terminal optimal nodes

# SVG right-pointing triangle markers (base64-encoded for Highcharts symbol URLs)
_tri_opt_svg = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48">'
    f'<polygon points="6,4 44,24 6,44" fill="{COLOR_TERMINAL}"/></svg>'
)
_tri_pruned_svg = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="44" height="44" viewBox="0 0 44 44">'
    f'<polygon points="6,4 40,22 6,40" fill="{INK_MUTED}" opacity="0.55"/></svg>'
)
TRI_OPTIMAL_URL = "url(data:image/svg+xml;base64," + base64.b64encode(_tri_opt_svg.encode()).decode() + ")"
TRI_PRUNED_URL = "url(data:image/svg+xml;base64," + base64.b64encode(_tri_pruned_svg.encode()).decode() + ")"

# Data — Product Launch Decision Tree (R&D investment analysis)
#
# Stage 1 Decision (D1, EMV=$560K):
#   → Launch Product → Chance (C1, EMV=$560K):
#       → High Demand [p=0.6] → $800K payoff (T1) [optimal]
#       → Low Demand  [p=0.4] → Stage 2 Decision (D2, EMV=$200K):
#           → Discount  → $200K payoff (T4) [optimal]
#           → Withdraw  → -$100K payoff (T5) [pruned]
#   → Keep Current  → Chance (C2, EMV=$325K): [pruned branch]
#       → Market Grows  [p=0.5] → $400K payoff (T2) [pruned]
#       → Market Stable [p=0.5] → $250K payoff (T3) [pruned]

# Build chart with highcharts-core
chart = Chart(container="container")
chart.options = HighchartsOptions()

TITLE = "tree-decision · python · highcharts · anyplot.ai"
_n = len(TITLE)
_title_fs = round(66 * 67 / _n) if _n > 67 else 66

# Four-point canvas sync: chart options + HTML div + Selenium --window-size + CDP override
chart.options.chart = {
    "width": 3200,
    "height": 1800,
    "backgroundColor": PAGE_BG,
    "style": {"fontFamily": "system-ui, -apple-system, BlinkMacSystemFont, sans-serif"},
    "spacingTop": 40,
    "spacingBottom": 60,
    "spacingLeft": 60,
    "spacingRight": 60,
}

chart.options.title = {"text": TITLE, "style": {"fontSize": f"{_title_fs}px", "fontWeight": "600", "color": INK}}

chart.options.subtitle = {
    "text": "Product Launch Decision Analysis — Expected Monetary Value (EMV) Rollback",
    "style": {"fontSize": "36px", "fontWeight": "400", "color": INK_SOFT},
}

# Axes are invisible — used only as coordinate frame for node placement
chart.options.x_axis = {"visible": False, "min": 0, "max": 3700, "gridLineWidth": 0}
chart.options.y_axis = {"visible": False, "min": 0, "max": 2100, "reversed": True, "gridLineWidth": 0}

chart.options.tooltip = {
    "useHTML": True,
    "style": {"fontSize": "26px"},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderRadius": 6,
    "headerFormat": "",
    "pointFormat": (
        '<span style="font-size:28px;font-weight:700;color:{point.color}">&#9679; {series.name}</span><br/>'
        '<span style="font-size:24px;font-weight:600">{point.name}</span>'
    ),
}

chart.options.legend = {
    "enabled": True,
    "layout": "vertical",
    "align": "right",
    "verticalAlign": "middle",
    "x": -30,
    "y": 40,
    "itemStyle": {"fontSize": "38px", "fontWeight": "400", "color": INK_SOFT},
    "symbolWidth": 30,
    "symbolHeight": 30,
    "symbolRadius": 4,
    "itemMarginBottom": 28,
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "borderRadius": 6,
    "padding": 28,
}

chart.options.credits = {"enabled": False}

chart.options.plot_options = {
    "scatter": {
        "states": {"hover": {"marker": {"radiusPlus": 8}}, "inactive": {"opacity": 0.5}},
        "stickyTracking": False,
    }
}

# Decision nodes (squares) — Imprint position 1: brand green
decision_series = ScatterSeries()
decision_series.name = "Decision Node"
decision_series.data = [
    {"x": 300, "y": 960, "id": "D1", "name": "EMV: $560K"},
    {"x": 2450, "y": 590, "id": "D2", "name": "EMV: $200K"},
]
decision_series.marker = {
    "symbol": "square",
    "radius": 44,
    "fillColor": COLOR_DECISION,
    "lineColor": COLOR_DECISION,
    "lineWidth": 0,
}
decision_series.color = COLOR_DECISION
decision_series.data_labels = {
    "enabled": True,
    "format": "{point.name}",
    "y": 74,
    "style": {"fontSize": "32px", "fontWeight": "700", "color": INK, "textOutline": f"2px {PAGE_BG}"},
}
chart.add_series(decision_series)

# Chance nodes (circles) — Imprint position 2: lavender
chance_series = ScatterSeries()
chance_series.name = "Chance Node"
chance_series.data = [
    {"x": 1400, "y": 270, "id": "C1", "name": "EMV: $560K"},
    {"x": 1400, "y": 1650, "id": "C2", "name": "EMV: $325K"},
]
chance_series.marker = {
    "symbol": "circle",
    "radius": 44,
    "fillColor": COLOR_CHANCE,
    "lineColor": COLOR_CHANCE,
    "lineWidth": 0,
}
chance_series.color = COLOR_CHANCE
chance_series.data_labels = {
    "enabled": True,
    "format": "{point.name}",
    "y": 74,
    "style": {"fontSize": "32px", "fontWeight": "700", "color": INK, "textOutline": f"2px {PAGE_BG}"},
}
chart.add_series(chance_series)

# Terminal optimal nodes (right-pointing triangles) — Imprint position 3: blue
optimal_series = ScatterSeries()
optimal_series.name = "Terminal · Optimal"
optimal_series.data = [
    {"x": 2450, "y": 90, "id": "T1", "name": "$800K"},
    {"x": 3350, "y": 410, "id": "T4", "name": "$200K"},
]
optimal_series.marker = {"symbol": TRI_OPTIMAL_URL, "width": 48, "height": 48}
optimal_series.color = COLOR_TERMINAL
optimal_series.data_labels = {
    "enabled": True,
    "format": "{point.name}",
    "align": "left",
    "x": 58,
    "y": 6,
    "style": {"fontSize": "34px", "fontWeight": "700", "color": INK, "textOutline": f"2px {PAGE_BG}"},
}
chart.add_series(optimal_series)

# Terminal pruned nodes (muted triangles) — branches eliminated by rollback
pruned_series = ScatterSeries()
pruned_series.name = "Terminal · Pruned"
pruned_series.data = [
    {"x": 3350, "y": 790, "id": "T5", "name": "−$100K"},
    {"x": 2450, "y": 1300, "id": "T2", "name": "$400K"},
    {"x": 2450, "y": 2000, "id": "T3", "name": "$250K"},
]
pruned_series.marker = {"symbol": TRI_PRUNED_URL, "width": 44, "height": 44}
pruned_series.color = INK_MUTED
pruned_series.data_labels = {
    "enabled": True,
    "format": "{point.name}",
    "align": "left",
    "x": 52,
    "y": 6,
    "style": {"fontSize": "30px", "fontWeight": "400", "color": INK_MUTED, "textOutline": "none"},
}
chart.add_series(pruned_series)

chart_js = chart.to_js_literal()

# Edge data for custom Highcharts renderer (bezier curves + branch labels)
edges_data = [
    {"fx": 300, "fy": 960, "tx": 1400, "ty": 270, "label": "Launch Product", "p": False},
    {"fx": 300, "fy": 960, "tx": 1400, "ty": 1650, "label": "Keep Current", "p": True},
    {"fx": 1400, "fy": 270, "tx": 2450, "ty": 90, "label": "High Demand (0.6)", "p": False},
    {"fx": 1400, "fy": 270, "tx": 2450, "ty": 590, "label": "Low Demand (0.4)", "p": False},
    {"fx": 2450, "fy": 590, "tx": 3350, "ty": 410, "label": "Discount", "p": False},
    {"fx": 2450, "fy": 590, "tx": 3350, "ty": 790, "label": "Withdraw", "p": True},
    {"fx": 1400, "fy": 1650, "tx": 2450, "ty": 1300, "label": "Market Grows (0.5)", "p": True},
    {"fx": 1400, "fy": 1650, "tx": 2450, "ty": 2000, "label": "Market Stable (0.5)", "p": True},
]
edges_json = json.dumps(edges_data)

# JS to draw bezier edges + branch labels using the Highcharts renderer API.
# Python color tokens are injected via string concatenation to support both themes.
edge_js = (
    "(function() {"
    "  var chart = Highcharts.charts[Highcharts.charts.length - 1];"
    "  if (!chart) return;"
    "  var ren = chart.renderer;"
    "  var xAxis = chart.xAxis[0];"
    "  var yAxis = chart.yAxis[0];"
    "  var INK = '" + INK + "';"
    "  var INK_MUTED = '" + INK_MUTED + "';"
    "  var OPTIMAL_COLOR = '" + COLOR_DECISION + "';"
    "  var PRUNE_MARK_COLOR = '#AE3030';"
    "  var edges = " + edges_json + ";"
    "  edges.forEach(function(e) {"
    "    var x1 = xAxis.toPixels(e.fx);"
    "    var y1 = yAxis.toPixels(e.fy);"
    "    var x2 = xAxis.toPixels(e.tx);"
    "    var y2 = yAxis.toPixels(e.ty);"
    "    var midX = (x1 + x2) / 2;"
    "    var edgeColor = e.p ? INK_MUTED : OPTIMAL_COLOR;"
    "    var edgeWidth = e.p ? 3 : 6;"
    "    ren.path(['M', x1, y1, 'C', midX, y1, midX, y2, x2, y2]).attr({"
    "      'stroke': edgeColor,"
    "      'stroke-width': edgeWidth,"
    "      'fill': 'none',"
    "      'stroke-dasharray': e.p ? '16,10' : 'none',"
    "      'opacity': e.p ? 0.4 : 1.0,"
    "      zIndex: 1"
    "    }).add();"
    "    if (e.p) {"
    "      var px = x1 + (x2 - x1) * 0.35;"
    "      var py = y1 + (y2 - y1) * 0.25;"
    "      ren.path(["
    "        'M', px-14, py-20, 'L', px+14, py+20,"
    "        'M', px+2,  py-20, 'L', px+30, py+20"
    "      ]).attr({"
    "        'stroke': PRUNE_MARK_COLOR,"
    "        'stroke-width': 5,"
    "        'opacity': 0.65,"
    "        zIndex: 5"
    "      }).add();"
    "    }"
    "    var lx = x1 + (x2 - x1) * 0.44;"
    "    var ly = y1 + (y2 - y1) * 0.38 - 28;"
    "    var lcolor = e.p ? INK_MUTED : INK;"
    "    ren.label(e.label, lx, ly, null, null, null, false, false).attr({"
    "      align: 'center', zIndex: 6, padding: 6, r: 3"
    "    }).css({"
    "      fontSize: '30px',"
    "      fontWeight: e.p ? '400' : '600',"
    "      color: lcolor,"
    "      fontFamily: 'system-ui, -apple-system, sans-serif'"
    "    }).add();"
    "  });"
    "})();"
)

# Download Highcharts JS (try local node_modules first, then CDN)
highcharts_paths = [
    Path(__file__).resolve().parents[3] / "node_modules" / "highcharts" / "highcharts.js",
    Path("node_modules/highcharts/highcharts.js"),
]
highcharts_js = None
for _p in highcharts_paths:
    if _p.exists():
        highcharts_js = _p.read_text(encoding="utf-8")
        break
if highcharts_js is None:
    _req = urllib.request.Request(
        "https://cdn.jsdelivr.net/npm/highcharts/highcharts.js", headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(_req, timeout=30) as _resp:
        highcharts_js = _resp.read().decode("utf-8")

html_content = (
    "<!DOCTYPE html><html><head><meta charset='utf-8'>"
    "<script>" + highcharts_js + "</script>"
    "</head>"
    "<body style='margin:0; background:" + PAGE_BG + ";'>"
    "<div id='container' style='width:3200px; height:1800px;'></div>"
    "<script>" + chart_js + "</script>"
    "<script>setTimeout(function() {" + edge_js + "}, 400);</script>"
    "</body></html>"
)

# Save HTML artifact (theme-suffixed)
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot via Selenium — CDP override is the authoritative canvas size setter
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

# PIL safety net — pin output to exact 3200×1800
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
