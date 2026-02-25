""" pyplots.ai
gantt-dependencies: Gantt Chart with Dependencies
Library: highcharts 1.10.3 | Python 3.14
Quality: 86/100 | Updated: 2026-02-25
"""

import tempfile
import time
import urllib.request
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Download Highcharts Gantt JS (includes core + gantt module)
highcharts_gantt_url = "https://cdn.jsdelivr.net/npm/highcharts@11.4.8/highcharts-gantt.js"
with urllib.request.urlopen(highcharts_gantt_url, timeout=30) as response:
    highcharts_gantt_js = response.read().decode("utf-8")

# Chart configuration using Highcharts Gantt with parent/child grouping
# Software Development Project: 4 phases, 12 tasks, finish-to-start dependencies
chart_config = """
Highcharts.ganttChart('container', {
    chart: {
        width: 4800,
        height: 2700,
        backgroundColor: '#ffffff',
        spacingTop: 40,
        spacingBottom: 40,
        spacingLeft: 40,
        spacingRight: 40
    },
    title: {
        text: 'Software Development Project Schedule',
        style: {
            fontSize: '52px',
            fontWeight: 'bold'
        },
        margin: 20
    },
    subtitle: {
        text: 'gantt-dependencies \\u00b7 highcharts \\u00b7 pyplots.ai',
        style: {
            fontSize: '36px',
            color: '#666666'
        }
    },
    xAxis: [{
        min: Date.UTC(2024, 0, 1),
        max: Date.UTC(2024, 3, 1),
        tickInterval: 7 * 24 * 3600 * 1000,
        labels: {
            style: {
                fontSize: '24px'
            },
            format: '{value:%b %e}'
        },
        gridLineWidth: 1,
        gridLineColor: '#e6e6e6'
    }],
    yAxis: {
        labels: {
            style: {
                fontSize: '28px'
            },
            indentation: 30
        },
        gridLineWidth: 1,
        gridLineColor: '#f0f0f0'
    },
    tooltip: {
        style: {
            fontSize: '22px'
        },
        dateTimeLabelFormats: {
            day: '%A, %b %e, %Y'
        }
    },
    navigator: {
        enabled: false
    },
    scrollbar: {
        enabled: false
    },
    rangeSelector: {
        enabled: false
    },
    plotOptions: {
        series: {
            animation: false,
            borderRadius: 6,
            dataLabels: {
                enabled: true,
                align: 'left',
                padding: 10,
                style: {
                    fontSize: '20px',
                    fontWeight: 'bold',
                    textOutline: '3px white'
                },
                format: '{point.name}',
                overflow: 'allow',
                crop: false
            },
            connectors: {
                lineWidth: 4,
                dashStyle: 'Solid',
                lineColor: '#555555',
                radius: 12,
                startMarker: {
                    enabled: false
                },
                endMarker: {
                    enabled: true,
                    width: 14,
                    height: 14
                }
            }
        }
    },
    series: [{
        name: 'Project Schedule',
        data: [
            // Phase 1: Requirements (Jan 1 - Jan 20)
            {
                id: 'requirements',
                name: 'Requirements Phase',
                color: '#306998'
            },
            {
                id: 'req_gather',
                name: 'Gather Requirements',
                parent: 'requirements',
                start: Date.UTC(2024, 0, 1),
                end: Date.UTC(2024, 0, 8),
                color: '#306998'
            },
            {
                id: 'req_analysis',
                name: 'Requirements Analysis',
                parent: 'requirements',
                start: Date.UTC(2024, 0, 9),
                end: Date.UTC(2024, 0, 15),
                dependency: 'req_gather',
                color: '#306998'
            },
            {
                id: 'req_approval',
                name: 'Stakeholder Approval',
                parent: 'requirements',
                start: Date.UTC(2024, 0, 16),
                end: Date.UTC(2024, 0, 20),
                dependency: 'req_analysis',
                color: '#306998'
            },
            // Phase 2: Design (Jan 22 - Feb 9)
            {
                id: 'design',
                name: 'Design Phase',
                color: '#FFD43B'
            },
            {
                id: 'design_arch',
                name: 'Architecture Design',
                parent: 'design',
                start: Date.UTC(2024, 0, 22),
                end: Date.UTC(2024, 0, 31),
                dependency: 'req_approval',
                color: '#FFD43B'
            },
            {
                id: 'design_ui',
                name: 'UI/UX Design',
                parent: 'design',
                start: Date.UTC(2024, 0, 22),
                end: Date.UTC(2024, 1, 5),
                dependency: 'req_approval',
                color: '#FFD43B'
            },
            {
                id: 'design_db',
                name: 'Database Design',
                parent: 'design',
                start: Date.UTC(2024, 1, 1),
                end: Date.UTC(2024, 1, 9),
                dependency: 'design_arch',
                color: '#FFD43B'
            },
            // Phase 3: Development (Feb 12 - Mar 15)
            {
                id: 'development',
                name: 'Development Phase',
                color: '#9467BD'
            },
            {
                id: 'dev_backend',
                name: 'Backend Development',
                parent: 'development',
                start: Date.UTC(2024, 1, 12),
                end: Date.UTC(2024, 2, 4),
                dependency: 'design_db',
                color: '#9467BD'
            },
            {
                id: 'dev_frontend',
                name: 'Frontend Development',
                parent: 'development',
                start: Date.UTC(2024, 1, 7),
                end: Date.UTC(2024, 2, 1),
                dependency: 'design_ui',
                color: '#9467BD'
            },
            {
                id: 'dev_integration',
                name: 'System Integration',
                parent: 'development',
                start: Date.UTC(2024, 2, 5),
                end: Date.UTC(2024, 2, 15),
                dependency: ['dev_backend', 'dev_frontend'],
                color: '#9467BD'
            },
            // Phase 4: Testing (Mar 5 - Mar 29)
            {
                id: 'testing',
                name: 'Testing Phase',
                color: '#17BECF'
            },
            {
                id: 'test_unit',
                name: 'Unit Testing',
                parent: 'testing',
                start: Date.UTC(2024, 2, 5),
                end: Date.UTC(2024, 2, 15),
                dependency: 'dev_backend',
                color: '#17BECF'
            },
            {
                id: 'test_integration',
                name: 'Integration Testing',
                parent: 'testing',
                start: Date.UTC(2024, 2, 16),
                end: Date.UTC(2024, 2, 22),
                dependency: ['dev_integration', 'test_unit'],
                color: '#17BECF'
            },
            {
                id: 'test_uat',
                name: 'User Acceptance Testing',
                parent: 'testing',
                start: Date.UTC(2024, 2, 23),
                end: Date.UTC(2024, 2, 29),
                dependency: 'test_integration',
                color: '#17BECF'
            }
        ]
    }]
});
"""

# Generate HTML with inline Highcharts Gantt
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_gantt_js}</script>
</head>
<body style="margin:0; padding:0; background:#ffffff;">
    <div id="container" style="width:4800px; height:2700px;"></div>
    <script>
    {chart_config}
    </script>
</body>
</html>"""

# Write temp HTML and take screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,5000")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)

# Capture the chart container element (may exceed 2700px with treegrid)
container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()

# Save HTML for interactive version
html_output = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>gantt-dependencies - Highcharts - pyplots.ai</title>
    <script src="https://code.highcharts.com/gantt/highcharts-gantt.js"></script>
</head>
<body style="margin:0; padding:20px; background:#ffffff;">
    <div id="container" style="width:100%; height:800px;"></div>
    <script>
    Highcharts.ganttChart('container', {
        title: {
            text: 'Software Development Project Schedule'
        },
        subtitle: {
            text: 'gantt-dependencies \\u00b7 highcharts \\u00b7 pyplots.ai'
        },
        xAxis: [{
            min: Date.UTC(2024, 0, 1),
            max: Date.UTC(2024, 2, 28)
        }],
        yAxis: {
            labels: {
                indentation: 30
            }
        },
        plotOptions: {
            series: {
                connectors: {
                    lineWidth: 2,
                    lineColor: '#555555',
                    radius: 8,
                    endMarker: {
                        enabled: true
                    }
                }
            }
        },
        series: [{
            name: 'Project Schedule',
            data: [
                { id: 'requirements', name: 'Requirements Phase', color: '#306998' },
                { id: 'req_gather', name: 'Gather Requirements', parent: 'requirements', start: Date.UTC(2024, 0, 1), end: Date.UTC(2024, 0, 8), color: '#306998' },
                { id: 'req_analysis', name: 'Requirements Analysis', parent: 'requirements', start: Date.UTC(2024, 0, 9), end: Date.UTC(2024, 0, 15), dependency: 'req_gather', color: '#306998' },
                { id: 'req_approval', name: 'Stakeholder Approval', parent: 'requirements', start: Date.UTC(2024, 0, 16), end: Date.UTC(2024, 0, 20), dependency: 'req_analysis', color: '#306998' },
                { id: 'design', name: 'Design Phase', color: '#FFD43B' },
                { id: 'design_arch', name: 'Architecture Design', parent: 'design', start: Date.UTC(2024, 0, 22), end: Date.UTC(2024, 0, 31), dependency: 'req_approval', color: '#FFD43B' },
                { id: 'design_ui', name: 'UI/UX Design', parent: 'design', start: Date.UTC(2024, 0, 22), end: Date.UTC(2024, 1, 5), dependency: 'req_approval', color: '#FFD43B' },
                { id: 'design_db', name: 'Database Design', parent: 'design', start: Date.UTC(2024, 1, 1), end: Date.UTC(2024, 1, 9), dependency: 'design_arch', color: '#FFD43B' },
                { id: 'development', name: 'Development Phase', color: '#9467BD' },
                { id: 'dev_backend', name: 'Backend Development', parent: 'development', start: Date.UTC(2024, 1, 12), end: Date.UTC(2024, 2, 4), dependency: 'design_db', color: '#9467BD' },
                { id: 'dev_frontend', name: 'Frontend Development', parent: 'development', start: Date.UTC(2024, 1, 7), end: Date.UTC(2024, 2, 1), dependency: 'design_ui', color: '#9467BD' },
                { id: 'dev_integration', name: 'System Integration', parent: 'development', start: Date.UTC(2024, 2, 5), end: Date.UTC(2024, 2, 15), dependency: ['dev_backend', 'dev_frontend'], color: '#9467BD' },
                { id: 'testing', name: 'Testing Phase', color: '#17BECF' },
                { id: 'test_unit', name: 'Unit Testing', parent: 'testing', start: Date.UTC(2024, 2, 5), end: Date.UTC(2024, 2, 15), dependency: 'dev_backend', color: '#17BECF' },
                { id: 'test_integration', name: 'Integration Testing', parent: 'testing', start: Date.UTC(2024, 2, 16), end: Date.UTC(2024, 2, 22), dependency: ['dev_integration', 'test_unit'], color: '#17BECF' },
                { id: 'test_uat', name: 'User Acceptance Testing', parent: 'testing', start: Date.UTC(2024, 2, 23), end: Date.UTC(2024, 2, 29), dependency: 'test_integration', color: '#17BECF' }
            ]
        }]
    });
    </script>
</body>
</html>"""

with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_output)
