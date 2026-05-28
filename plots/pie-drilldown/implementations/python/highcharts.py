""" anyplot.ai
pie-drilldown: Drilldown Pie Chart with Click Navigation
Library: highcharts unknown | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-15
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette (position 1 is brand green #009E73, then follow canonical order)
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]


# Download Highcharts JS and drilldown module (required for headless Chrome)
def fetch_url(url, max_retries=3):
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url)
            req.add_header("User-Agent", "Mozilla/5.0 (X11; Linux x86_64)")
            with urllib.request.urlopen(req, timeout=30) as response:
                return response.read().decode("utf-8")
        except urllib.error.HTTPError:
            if attempt < max_retries - 1:
                time.sleep(2**attempt)
                continue
            raise


highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@11.0.0/highcharts.js"
highcharts_js = fetch_url(highcharts_url)

drilldown_url = "https://cdn.jsdelivr.net/npm/highcharts@11.0.0/modules/drilldown.js"
drilldown_js = fetch_url(drilldown_url)

# Data: Company revenue breakdown by department
# Top level: Main departments
# Drilldown: Sub-departments within each

# Build the complete Highcharts configuration as JavaScript
chart_config = f"""
Highcharts.chart('container', {{
    chart: {{
        type: 'pie',
        width: 4800,
        height: 2700,
        backgroundColor: '{PAGE_BG}'
    }},
    title: {{
        text: 'pie-drilldown · highcharts · anyplot.ai',
        style: {{
            fontSize: '32px',
            fontWeight: 'bold',
            color: '{INK}'
        }}
    }},
    subtitle: {{
        text: 'Company Revenue by Department — Click slices to drill down',
        style: {{
            fontSize: '24px',
            color: '{INK_SOFT}'
        }}
    }},
    colors: {IMPRINT},
    accessibility: {{
        announceNewData: {{
            enabled: true
        }},
        point: {{
            valueSuffix: '%'
        }}
    }},
    plotOptions: {{
        pie: {{
            allowPointSelect: true,
            cursor: 'pointer',
            size: '65%',
            dataLabels: {{
                enabled: true,
                format: '<b>{{point.name}}</b>: ${{point.y:,.0f}} ({{point.percentage:.1f}}%)',
                style: {{
                    fontSize: '24px',
                    fontWeight: 'normal',
                    color: '{INK}',
                    textOutline: '2px {PAGE_BG}'
                }},
                distance: 50
            }},
            showInLegend: true
        }},
        series: {{
            borderWidth: 3,
            borderColor: '{PAGE_BG}',
            dataLabels: {{
                enabled: true,
                style: {{
                    fontSize: '24px',
                    color: '{INK}'
                }}
            }}
        }}
    }},
    legend: {{
        enabled: true,
        align: 'bottom',
        verticalAlign: 'bottom',
        layout: 'horizontal',
        itemStyle: {{
            fontSize: '20px',
            color: '{INK_SOFT}'
        }},
        itemMarginRight: 30,
        backgroundColor: '{ELEVATED_BG}',
        borderColor: '{INK_SOFT}',
        borderWidth: 1,
        padding: 20
    }},
    credits: {{
        enabled: false
    }},
    tooltip: {{
        headerFormat: '<span style="font-size: 22px; color: {{point.color}}"{{series.name}}</span><br>',
        pointFormat: '<span style="font-size: 20px; color:{INK}">{{point.name}}</span>: <b style="font-size: 20px">${{point.y:,.0f}}</b> ({{point.percentage:.1f}}%)<br/>'
    }},
    series: [{{
        name: 'Departments',
        colorByPoint: true,
        data: [
            {{
                name: 'Engineering',
                y: 4500000,
                drilldown: 'engineering'
            }},
            {{
                name: 'Sales',
                y: 3200000,
                drilldown: 'sales'
            }},
            {{
                name: 'Marketing',
                y: 1800000,
                drilldown: 'marketing'
            }},
            {{
                name: 'Operations',
                y: 2100000,
                drilldown: 'operations'
            }},
            {{
                name: 'Research',
                y: 1400000,
                drilldown: 'research'
            }}
        ]
    }}],
    drilldown: {{
        breadcrumbs: {{
            position: {{
                align: 'center',
                y: 50
            }},
            style: {{
                fontSize: '20px',
                color: '{INK_SOFT}'
            }},
            buttonTheme: {{
                style: {{
                    fontSize: '18px',
                    color: '{INK_SOFT}'
                }},
                fill: '{ELEVATED_BG}',
                stroke: '{INK_SOFT}',
                'stroke-width': 1,
                r: 4
            }}
        }},
        activeAxisLabelStyle: {{
            textDecoration: 'none',
            fontStyle: 'normal'
        }},
        activeDataLabelStyle: {{
            textDecoration: 'none',
            fontStyle: 'normal',
            fontSize: '24px'
        }},
        series: [
            {{
                id: 'engineering',
                name: 'Engineering',
                data: [
                    ['Backend', 1800000],
                    ['Frontend', 1200000],
                    ['DevOps', 800000],
                    ['QA', 700000]
                ]
            }},
            {{
                id: 'sales',
                name: 'Sales',
                data: [
                    ['Enterprise', 1500000],
                    ['SMB', 900000],
                    ['Inside Sales', 500000],
                    ['Partnerships', 300000]
                ]
            }},
            {{
                id: 'marketing',
                name: 'Marketing',
                data: [
                    ['Digital', 700000],
                    ['Content', 450000],
                    ['Events', 350000],
                    ['Brand', 300000]
                ]
            }},
            {{
                id: 'operations',
                name: 'Operations',
                data: [
                    ['IT', 800000],
                    ['HR', 600000],
                    ['Finance', 450000],
                    ['Facilities', 250000]
                ]
            }},
            {{
                id: 'research',
                name: 'Research',
                data: [
                    ['AI/ML', 600000],
                    ['Product', 450000],
                    ['UX Research', 350000]
                ]
            }}
        ]
    }}
}});
"""

# Build HTML with inline scripts
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{drilldown_js}</script>
</head>
<body style="margin:0; padding:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
    {chart_config}
    </script>
</body>
</html>"""

# Write temp HTML and take screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Save HTML for interactive version
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Set up Chrome for screenshot
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

# Clean up temp file
Path(temp_path).unlink()
