"""anyplot.ai
gantt-dependencies: Gantt Chart with Dependencies
Library: highcharts | Python 3.14
Quality: pending | Updated: 2026-06-02
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette — 4 project phases as categorical series (positions 1–4)
C1 = "#009E73"  # Requirements (brand green)
C2 = "#C475FD"  # Design (lavender)
C3 = "#4467A3"  # Development (blue)
C4 = "#BD8233"  # Testing (ochre)
CRITICAL = "#AE3030"  # matte red — semantic anchor: critical path

# Download Highcharts Gantt JS inline (headless Chrome cannot load CDN from file://)
highcharts_gantt_url = "https://cdn.jsdelivr.net/npm/highcharts@11.4.8/highcharts-gantt.js"
with urllib.request.urlopen(highcharts_gantt_url, timeout=30) as response:
    highcharts_gantt_js = response.read().decode("utf-8")

# JS theme variables — injected before the chart config so JS can reference them
theme_vars_js = f"""
var PAGE_BG = '{PAGE_BG}';
var ELEVATED_BG = '{ELEVATED_BG}';
var INK = '{INK}';
var INK_SOFT = '{INK_SOFT}';
var INK_MUTED = '{INK_MUTED}';
var GRID_COLOR = '{GRID}';
var C1 = '{C1}';
var C2 = '{C2}';
var C3 = '{C3}';
var C4 = '{C4}';
var CRITICAL = '{CRITICAL}';
"""

# PNG chart config (plain string — references JS vars declared above, avoids f-string brace escaping)
chart_config_png = r"""
Highcharts.ganttChart('container', {
    chart: {
        width: 3200,
        height: 1800,
        backgroundColor: PAGE_BG,
        spacingTop: 30,
        spacingBottom: 80,
        spacingLeft: 20,
        spacingRight: 20,
        style: {fontFamily: '"Segoe UI", "Helvetica Neue", Arial, sans-serif'},
        events: {
            load: function() {
                var ren = this.renderer;
                var x = this.plotLeft + this.plotWidth - 480;
                var y = this.plotTop + this.plotHeight + 24;
                ren.path(['M', x, y, 'L', x + 50, y])
                    .attr({'stroke-width': 4, stroke: CRITICAL})
                    .add();
                ren.text('Critical Path', x + 62, y + 6)
                    .css({fontSize: '36px', color: INK_SOFT, fontWeight: '600'})
                    .add();
                ren.path(['M', x + 270, y, 'L', x + 320, y])
                    .attr({'stroke-width': 2, stroke: INK_MUTED, 'stroke-dasharray': '6,4'})
                    .add();
                ren.text('Non-Critical', x + 332, y + 6)
                    .css({fontSize: '36px', color: INK_MUTED, fontWeight: '400'})
                    .add();
            }
        }
    },
    title: {
        text: 'gantt-dependencies · python · highcharts · anyplot.ai',
        style: {fontSize: '66px', fontWeight: '600', color: INK},
        margin: 20
    },
    subtitle: {
        text: 'Software Development Project Schedule — Critical Path & Phase Dependencies',
        style: {fontSize: '44px', color: INK_SOFT}
    },
    xAxis: [{
        min: Date.UTC(2024, 0, 1),
        max: Date.UTC(2024, 2, 31),
        tickInterval: 7 * 24 * 3600 * 1000,
        labels: {style: {fontSize: '44px', color: INK_SOFT}, format: '{value:%b %e}'},
        gridLineWidth: 1,
        gridLineColor: GRID_COLOR,
        lineColor: INK_SOFT,
        tickColor: INK_SOFT,
        currentDateIndicator: false
    }],
    yAxis: {
        labels: {style: {fontSize: '40px', color: INK}, indentation: 20},
        gridLineWidth: 1,
        gridLineColor: GRID_COLOR,
        alternateGridColor: ELEVATED_BG
    },
    tooltip: {
        backgroundColor: ELEVATED_BG,
        borderColor: INK_SOFT,
        style: {fontSize: '36px', color: INK},
        dateTimeLabelFormats: {day: '%A, %b %e, %Y'}
    },
    navigator: {enabled: false},
    scrollbar: {enabled: false},
    rangeSelector: {enabled: false},
    plotOptions: {
        series: {
            animation: false,
            borderRadius: 4,
            groupPadding: 0.05,
            dataLabels: {
                enabled: true,
                align: 'left',
                padding: 8,
                style: {
                    fontSize: '32px',
                    fontWeight: '600',
                    textOutline: '2px ' + PAGE_BG,
                    color: INK
                },
                format: '{point.name}',
                overflow: 'allow',
                crop: false
            },
            connectors: {
                lineWidth: 2,
                dashStyle: 'ShortDash',
                lineColor: INK_MUTED,
                radius: 8,
                startMarker: {enabled: false},
                endMarker: {enabled: true, width: 10, height: 10, color: INK_MUTED}
            }
        }
    },
    series: [{
        name: 'Project Schedule',
        data: [
            {id: 'requirements', name: 'Requirements Phase', color: C1},
            {
                id: 'req_gather', name: 'Gather Requirements', parent: 'requirements',
                start: Date.UTC(2024, 0, 1), end: Date.UTC(2024, 0, 10), color: C1
            },
            {
                id: 'req_analysis', name: 'Requirements Analysis', parent: 'requirements',
                start: Date.UTC(2024, 0, 11), end: Date.UTC(2024, 0, 17),
                dependency: {to: 'req_gather', lineColor: CRITICAL, lineWidth: 4},
                color: C1
            },
            {
                id: 'req_approval', name: 'Stakeholder Approval', parent: 'requirements',
                start: Date.UTC(2024, 0, 18), end: Date.UTC(2024, 0, 22),
                dependency: {to: 'req_analysis', lineColor: CRITICAL, lineWidth: 4},
                color: C1
            },
            {
                id: 'milestone_req', name: 'Requirements Baseline ✓',
                parent: 'requirements', start: Date.UTC(2024, 0, 22), milestone: true,
                dependency: {to: 'req_approval', lineColor: CRITICAL, lineWidth: 4},
                color: INK
            },
            {id: 'design', name: 'Design Phase', color: C2},
            {
                id: 'design_arch', name: 'Architecture Design', parent: 'design',
                start: Date.UTC(2024, 0, 23), end: Date.UTC(2024, 1, 2),
                dependency: {to: 'milestone_req', lineColor: CRITICAL, lineWidth: 4},
                color: C2
            },
            {
                id: 'design_ui', name: 'UI/UX Design', parent: 'design',
                start: Date.UTC(2024, 0, 23), end: Date.UTC(2024, 1, 5),
                dependency: {to: 'milestone_req', lineColor: INK_MUTED, lineWidth: 2, dashStyle: 'ShortDash'},
                color: C2
            },
            {
                id: 'design_db', name: 'Database Design', parent: 'design',
                start: Date.UTC(2024, 1, 3), end: Date.UTC(2024, 1, 9),
                dependency: {to: 'design_arch', lineColor: CRITICAL, lineWidth: 4},
                color: C2
            },
            {id: 'development', name: 'Development Phase', color: C3},
            {
                id: 'dev_backend', name: 'Backend Development', parent: 'development',
                start: Date.UTC(2024, 1, 12), end: Date.UTC(2024, 2, 4),
                dependency: {to: 'design_db', lineColor: CRITICAL, lineWidth: 4},
                color: C3
            },
            {
                id: 'dev_frontend', name: 'Frontend Development', parent: 'development',
                start: Date.UTC(2024, 1, 7), end: Date.UTC(2024, 2, 1),
                dependency: {to: 'design_ui', lineColor: INK_MUTED, lineWidth: 2, dashStyle: 'ShortDash'},
                color: C3
            },
            {
                id: 'dev_integration', name: 'System Integration', parent: 'development',
                start: Date.UTC(2024, 2, 5), end: Date.UTC(2024, 2, 15),
                dependency: [
                    {to: 'dev_backend', lineColor: CRITICAL, lineWidth: 4},
                    {to: 'dev_frontend', lineColor: INK_MUTED, lineWidth: 2, dashStyle: 'ShortDash'}
                ],
                color: C3
            },
            {id: 'testing', name: 'Testing Phase', color: C4},
            {
                id: 'test_unit', name: 'Unit Testing', parent: 'testing',
                start: Date.UTC(2024, 2, 5), end: Date.UTC(2024, 2, 15),
                dependency: {to: 'dev_backend', lineColor: INK_MUTED, lineWidth: 2, dashStyle: 'ShortDash'},
                color: C4
            },
            {
                id: 'test_integration', name: 'Integration Testing', parent: 'testing',
                start: Date.UTC(2024, 2, 16), end: Date.UTC(2024, 2, 22),
                dependency: [
                    {to: 'dev_integration', lineColor: CRITICAL, lineWidth: 4},
                    {to: 'test_unit', lineColor: INK_MUTED, lineWidth: 2, dashStyle: 'ShortDash'}
                ],
                color: C4
            },
            {
                id: 'test_uat', name: 'User Acceptance Testing', parent: 'testing',
                start: Date.UTC(2024, 2, 23), end: Date.UTC(2024, 2, 29),
                dependency: {to: 'test_integration', lineColor: CRITICAL, lineWidth: 4},
                color: C4
            },
            {
                id: 'milestone_release', name: 'Release Ready ★',
                parent: 'testing', start: Date.UTC(2024, 2, 29), milestone: true,
                dependency: {to: 'test_uat', lineColor: CRITICAL, lineWidth: 4},
                color: INK
            }
        ]
    }]
});
"""

# Interactive HTML chart config (CDN-linked, responsive)
chart_config_html = r"""
Highcharts.ganttChart('container', {
    chart: {
        backgroundColor: PAGE_BG,
        style: {fontFamily: '"Segoe UI", "Helvetica Neue", Arial, sans-serif'}
    },
    title: {
        text: 'gantt-dependencies · python · highcharts · anyplot.ai',
        style: {color: INK}
    },
    subtitle: {
        text: 'Software Development Project Schedule — Critical Path & Phase Dependencies',
        style: {color: INK_SOFT}
    },
    xAxis: [{
        min: Date.UTC(2024, 0, 1),
        max: Date.UTC(2024, 2, 31),
        labels: {style: {color: INK_SOFT}},
        gridLineColor: GRID_COLOR,
        lineColor: INK_SOFT,
        tickColor: INK_SOFT,
        currentDateIndicator: false
    }],
    yAxis: {
        labels: {style: {color: INK}, indentation: 20},
        gridLineColor: GRID_COLOR,
        alternateGridColor: ELEVATED_BG
    },
    tooltip: {
        backgroundColor: ELEVATED_BG,
        borderColor: INK_SOFT,
        style: {color: INK}
    },
    navigator: {enabled: false},
    scrollbar: {enabled: false},
    rangeSelector: {enabled: false},
    plotOptions: {
        series: {
            borderRadius: 4,
            connectors: {
                lineWidth: 2,
                lineColor: INK_MUTED,
                radius: 6,
                startMarker: {enabled: false},
                endMarker: {enabled: true, color: INK_MUTED}
            }
        }
    },
    series: [{
        name: 'Project Schedule',
        data: [
            {id: 'requirements', name: 'Requirements Phase', color: C1},
            {id: 'req_gather', name: 'Gather Requirements', parent: 'requirements', start: Date.UTC(2024, 0, 1), end: Date.UTC(2024, 0, 10), color: C1},
            {id: 'req_analysis', name: 'Requirements Analysis', parent: 'requirements', start: Date.UTC(2024, 0, 11), end: Date.UTC(2024, 0, 17), dependency: {to: 'req_gather', lineColor: CRITICAL, lineWidth: 3}, color: C1},
            {id: 'req_approval', name: 'Stakeholder Approval', parent: 'requirements', start: Date.UTC(2024, 0, 18), end: Date.UTC(2024, 0, 22), dependency: {to: 'req_analysis', lineColor: CRITICAL, lineWidth: 3}, color: C1},
            {id: 'milestone_req', name: 'Requirements Baseline ✓', parent: 'requirements', start: Date.UTC(2024, 0, 22), milestone: true, dependency: {to: 'req_approval', lineColor: CRITICAL, lineWidth: 3}, color: INK},
            {id: 'design', name: 'Design Phase', color: C2},
            {id: 'design_arch', name: 'Architecture Design', parent: 'design', start: Date.UTC(2024, 0, 23), end: Date.UTC(2024, 1, 2), dependency: {to: 'milestone_req', lineColor: CRITICAL, lineWidth: 3}, color: C2},
            {id: 'design_ui', name: 'UI/UX Design', parent: 'design', start: Date.UTC(2024, 0, 23), end: Date.UTC(2024, 1, 5), dependency: {to: 'milestone_req', lineColor: INK_MUTED, lineWidth: 2, dashStyle: 'ShortDash'}, color: C2},
            {id: 'design_db', name: 'Database Design', parent: 'design', start: Date.UTC(2024, 1, 3), end: Date.UTC(2024, 1, 9), dependency: {to: 'design_arch', lineColor: CRITICAL, lineWidth: 3}, color: C2},
            {id: 'development', name: 'Development Phase', color: C3},
            {id: 'dev_backend', name: 'Backend Development', parent: 'development', start: Date.UTC(2024, 1, 12), end: Date.UTC(2024, 2, 4), dependency: {to: 'design_db', lineColor: CRITICAL, lineWidth: 3}, color: C3},
            {id: 'dev_frontend', name: 'Frontend Development', parent: 'development', start: Date.UTC(2024, 1, 7), end: Date.UTC(2024, 2, 1), dependency: {to: 'design_ui', lineColor: INK_MUTED, lineWidth: 2, dashStyle: 'ShortDash'}, color: C3},
            {id: 'dev_integration', name: 'System Integration', parent: 'development', start: Date.UTC(2024, 2, 5), end: Date.UTC(2024, 2, 15), dependency: [{to: 'dev_backend', lineColor: CRITICAL, lineWidth: 3}, {to: 'dev_frontend', lineColor: INK_MUTED, lineWidth: 2, dashStyle: 'ShortDash'}], color: C3},
            {id: 'testing', name: 'Testing Phase', color: C4},
            {id: 'test_unit', name: 'Unit Testing', parent: 'testing', start: Date.UTC(2024, 2, 5), end: Date.UTC(2024, 2, 15), dependency: {to: 'dev_backend', lineColor: INK_MUTED, lineWidth: 2, dashStyle: 'ShortDash'}, color: C4},
            {id: 'test_integration', name: 'Integration Testing', parent: 'testing', start: Date.UTC(2024, 2, 16), end: Date.UTC(2024, 2, 22), dependency: [{to: 'dev_integration', lineColor: CRITICAL, lineWidth: 3}, {to: 'test_unit', lineColor: INK_MUTED, lineWidth: 2, dashStyle: 'ShortDash'}], color: C4},
            {id: 'test_uat', name: 'User Acceptance Testing', parent: 'testing', start: Date.UTC(2024, 2, 23), end: Date.UTC(2024, 2, 29), dependency: {to: 'test_integration', lineColor: CRITICAL, lineWidth: 3}, color: C4},
            {id: 'milestone_release', name: 'Release Ready ★', parent: 'testing', start: Date.UTC(2024, 2, 29), milestone: true, dependency: {to: 'test_uat', lineColor: CRITICAL, lineWidth: 3}, color: INK}
        ]
    }]
});
"""

# Save interactive HTML (CDN script, responsive container)
interactive_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>gantt-dependencies · python · highcharts · anyplot.ai</title>
    <script src="https://code.highcharts.com/gantt/highcharts-gantt.js"></script>
</head>
<body style="margin:0; padding:20px; background:{PAGE_BG};">
    <div id="container" style="width:100%; height:800px;"></div>
    <script>
    {theme_vars_js}
    {chart_config_html}
    </script>
</body>
</html>"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(interactive_html)

# Build PNG HTML with inline Highcharts JS (headless Chrome needs inline scripts)
png_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_gantt_js}</script>
</head>
<body style="margin:0; padding:0; background:{PAGE_BG};">
    <div id="container" style="width:3200px; height:1800px;"></div>
    <script>
    {theme_vars_js}
    {chart_config_png}
    </script>
</body>
</html>"""

with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(png_html)
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

# PIL normalization — pins saved PNG to exact 3200×1800 target
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
