""" pyplots.ai
pie-drilldown: Drilldown Pie Chart with Click Navigation
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import tempfile
import time
import urllib.request
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Download Highcharts JS and drilldown module (required for headless Chrome)
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

drilldown_url = "https://code.highcharts.com/modules/drilldown.js"
with urllib.request.urlopen(drilldown_url, timeout=30) as response:
    drilldown_js = response.read().decode("utf-8")

# Data: Company revenue breakdown by department
# Top level: Main departments
# Drilldown: Sub-departments within each

# Build the complete Highcharts configuration as JavaScript
chart_config = """
Highcharts.chart('container', {
    chart: {
        type: 'pie',
        width: 4800,
        height: 2700,
        backgroundColor: '#ffffff'
    },
    title: {
        text: 'pie-drilldown · highcharts · pyplots.ai',
        style: {
            fontSize: '48px',
            fontWeight: 'bold'
        }
    },
    subtitle: {
        text: 'Company Revenue by Department — Click slices to drill down',
        style: {
            fontSize: '32px',
            color: '#666666'
        }
    },
    colors: ['#306998', '#FFD43B', '#9467BD', '#17BECF', '#8C564B', '#E377C2', '#7F7F7F'],
    accessibility: {
        announceNewData: {
            enabled: true
        },
        point: {
            valueSuffix: '%'
        }
    },
    plotOptions: {
        pie: {
            allowPointSelect: true,
            cursor: 'pointer',
            size: '65%',
            dataLabels: {
                enabled: true,
                format: '<b>{point.name}</b>: ${point.y:,.0f} ({point.percentage:.1f}%)',
                style: {
                    fontSize: '26px',
                    fontWeight: 'normal',
                    textOutline: '2px white'
                },
                distance: 50
            },
            showInLegend: true
        },
        series: {
            borderWidth: 3,
            borderColor: '#ffffff',
            dataLabels: {
                enabled: true,
                style: {
                    fontSize: '26px'
                }
            }
        }
    },
    legend: {
        enabled: true,
        align: 'right',
        verticalAlign: 'middle',
        layout: 'vertical',
        itemStyle: {
            fontSize: '28px',
            fontWeight: 'normal'
        },
        itemMarginBottom: 20
    },
    credits: {
        enabled: false
    },
    tooltip: {
        headerFormat: '<span style="font-size: 24px">{series.name}</span><br>',
        pointFormat: '<span style="font-size: 22px; color:{point.color}">{point.name}</span>: <b style="font-size: 22px">${point.y:,.0f}</b> ({point.percentage:.1f}%)<br/>'
    },
    series: [{
        name: 'Departments',
        colorByPoint: true,
        data: [
            {
                name: 'Engineering',
                y: 4500000,
                drilldown: 'engineering'
            },
            {
                name: 'Sales',
                y: 3200000,
                drilldown: 'sales'
            },
            {
                name: 'Marketing',
                y: 1800000,
                drilldown: 'marketing'
            },
            {
                name: 'Operations',
                y: 2100000,
                drilldown: 'operations'
            },
            {
                name: 'Research',
                y: 1400000,
                drilldown: 'research'
            }
        ]
    }],
    drilldown: {
        breadcrumbs: {
            position: {
                align: 'right',
                y: 10
            },
            style: {
                fontSize: '28px'
            },
            buttonTheme: {
                style: {
                    fontSize: '28px'
                }
            }
        },
        activeAxisLabelStyle: {
            textDecoration: 'none',
            fontStyle: 'normal'
        },
        activeDataLabelStyle: {
            textDecoration: 'none',
            fontStyle: 'normal',
            fontSize: '26px'
        },
        series: [
            {
                id: 'engineering',
                name: 'Engineering',
                data: [
                    ['Backend', 1800000],
                    ['Frontend', 1200000],
                    ['DevOps', 800000],
                    ['QA', 700000]
                ]
            },
            {
                id: 'sales',
                name: 'Sales',
                data: [
                    ['Enterprise', 1500000],
                    ['SMB', 900000],
                    ['Inside Sales', 500000],
                    ['Partnerships', 300000]
                ]
            },
            {
                id: 'marketing',
                name: 'Marketing',
                data: [
                    ['Digital', 700000],
                    ['Content', 450000],
                    ['Events', 350000],
                    ['Brand', 300000]
                ]
            },
            {
                id: 'operations',
                name: 'Operations',
                data: [
                    ['IT', 800000],
                    ['HR', 600000],
                    ['Finance', 450000],
                    ['Facilities', 250000]
                ]
            },
            {
                id: 'research',
                name: 'Research',
                data: [
                    ['AI/ML', 600000],
                    ['Product', 450000],
                    ['UX Research', 350000]
                ]
            }
        ]
    }
});
"""

# Build HTML with inline scripts
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{drilldown_js}</script>
</head>
<body style="margin:0; padding:0; background:#ffffff;">
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

# Also save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
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
time.sleep(5)  # Wait for chart to render
driver.save_screenshot("plot.png")
driver.quit()

# Clean up temp file
Path(temp_path).unlink()
