""" pyplots.ai
bar-drilldown: Column Chart with Hierarchical Drilling
Library: highcharts unknown | Python 3.13.11
Quality: 92/100 | Created: 2026-01-16
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

# Data: Sales revenue by region (hierarchical)
# Level 1: Regions
# Level 2: Countries within regions
# Level 3: Cities within countries

# Build the complete Highcharts configuration as JavaScript
chart_config = """
Highcharts.chart('container', {
    chart: {
        type: 'column',
        width: 4800,
        height: 2700,
        backgroundColor: '#ffffff',
        marginBottom: 200,
        spacingBottom: 60
    },
    title: {
        text: 'bar-drilldown · highcharts · pyplots.ai',
        style: {
            fontSize: '48px',
            fontWeight: 'bold'
        }
    },
    subtitle: {
        text: 'Sales Revenue by Region — Click columns to drill down',
        style: {
            fontSize: '32px',
            color: '#666666'
        }
    },
    colors: ['#306998', '#FFD43B', '#9467BD', '#17BECF', '#8C564B', '#E377C2', '#7F7F7F', '#2CA02C'],
    xAxis: {
        type: 'category',
        title: {
            text: 'Category',
            style: {
                fontSize: '36px'
            },
            margin: 30
        },
        labels: {
            style: {
                fontSize: '28px'
            }
        }
    },
    yAxis: {
        title: {
            text: 'Revenue ($M)',
            style: {
                fontSize: '36px'
            }
        },
        labels: {
            style: {
                fontSize: '28px'
            },
            formatter: function() {
                return '$' + this.value + 'M';
            }
        },
        gridLineWidth: 1,
        gridLineColor: '#e0e0e0'
    },
    legend: {
        enabled: false
    },
    credits: {
        enabled: false
    },
    tooltip: {
        headerFormat: '<span style="font-size: 28px; font-weight: bold">{series.name}</span><br>',
        pointFormat: '<span style="font-size: 24px">{point.name}</span>: <b style="font-size: 24px">${point.y}M</b>'
    },
    plotOptions: {
        column: {
            borderRadius: 6,
            cursor: 'pointer',
            dataLabels: {
                enabled: true,
                format: '${y}M',
                style: {
                    fontSize: '24px',
                    fontWeight: 'bold',
                    textOutline: '2px white'
                }
            },
            colorByPoint: true
        },
        series: {
            borderWidth: 0
        }
    },
    series: [{
        name: 'Regions',
        data: [
            {
                name: 'North America',
                y: 245,
                drilldown: 'north-america'
            },
            {
                name: 'Europe',
                y: 198,
                drilldown: 'europe'
            },
            {
                name: 'Asia Pacific',
                y: 176,
                drilldown: 'asia-pacific'
            },
            {
                name: 'Latin America',
                y: 87,
                drilldown: 'latin-america'
            },
            {
                name: 'Middle East',
                y: 54,
                drilldown: 'middle-east'
            }
        ]
    }],
    drilldown: {
        breadcrumbs: {
            position: {
                align: 'right',
                y: 5
            },
            style: {
                fontSize: '26px'
            },
            buttonTheme: {
                style: {
                    fontSize: '26px',
                    fontWeight: 'bold'
                },
                states: {
                    hover: {
                        fill: '#f0f0f0'
                    }
                }
            },
            separator: {
                style: {
                    fontSize: '26px'
                }
            },
            showFullPath: true
        },
        activeAxisLabelStyle: {
            textDecoration: 'none',
            fontStyle: 'normal',
            fontSize: '28px'
        },
        activeDataLabelStyle: {
            textDecoration: 'none',
            fontStyle: 'normal',
            fontSize: '24px'
        },
        drillUpButton: {
            relativeTo: 'spacingBox',
            position: {
                y: 0,
                x: 0
            }
        },
        series: [
            {
                id: 'north-america',
                name: 'North America',
                data: [
                    {
                        name: 'United States',
                        y: 185,
                        drilldown: 'usa'
                    },
                    {
                        name: 'Canada',
                        y: 42,
                        drilldown: 'canada'
                    },
                    {
                        name: 'Mexico',
                        y: 18,
                        drilldown: 'mexico'
                    }
                ]
            },
            {
                id: 'europe',
                name: 'Europe',
                data: [
                    {
                        name: 'United Kingdom',
                        y: 52,
                        drilldown: 'uk'
                    },
                    {
                        name: 'Germany',
                        y: 48,
                        drilldown: 'germany'
                    },
                    {
                        name: 'France',
                        y: 41,
                        drilldown: 'france'
                    },
                    {
                        name: 'Italy',
                        y: 32,
                        drilldown: 'italy'
                    },
                    {
                        name: 'Spain',
                        y: 25,
                        drilldown: 'spain'
                    }
                ]
            },
            {
                id: 'asia-pacific',
                name: 'Asia Pacific',
                data: [
                    {
                        name: 'Japan',
                        y: 58,
                        drilldown: 'japan'
                    },
                    {
                        name: 'Australia',
                        y: 45,
                        drilldown: 'australia'
                    },
                    {
                        name: 'South Korea',
                        y: 38,
                        drilldown: 'south-korea'
                    },
                    {
                        name: 'Singapore',
                        y: 35,
                        drilldown: 'singapore'
                    }
                ]
            },
            {
                id: 'latin-america',
                name: 'Latin America',
                data: [
                    {
                        name: 'Brazil',
                        y: 45,
                        drilldown: 'brazil'
                    },
                    {
                        name: 'Argentina',
                        y: 22,
                        drilldown: 'argentina'
                    },
                    {
                        name: 'Chile',
                        y: 20,
                        drilldown: 'chile'
                    }
                ]
            },
            {
                id: 'middle-east',
                name: 'Middle East',
                data: [
                    {
                        name: 'UAE',
                        y: 28,
                        drilldown: 'uae'
                    },
                    {
                        name: 'Saudi Arabia',
                        y: 18,
                        drilldown: 'saudi-arabia'
                    },
                    {
                        name: 'Israel',
                        y: 8,
                        drilldown: 'israel'
                    }
                ]
            },
            // Level 3: Cities within countries
            {
                id: 'usa',
                name: 'United States',
                data: [
                    ['New York', 52],
                    ['Los Angeles', 38],
                    ['Chicago', 28],
                    ['Houston', 24],
                    ['Phoenix', 22],
                    ['Other', 21]
                ]
            },
            {
                id: 'canada',
                name: 'Canada',
                data: [
                    ['Toronto', 18],
                    ['Vancouver', 12],
                    ['Montreal', 8],
                    ['Calgary', 4]
                ]
            },
            {
                id: 'mexico',
                name: 'Mexico',
                data: [
                    ['Mexico City', 10],
                    ['Guadalajara', 5],
                    ['Monterrey', 3]
                ]
            },
            {
                id: 'uk',
                name: 'United Kingdom',
                data: [
                    ['London', 32],
                    ['Manchester', 10],
                    ['Birmingham', 6],
                    ['Edinburgh', 4]
                ]
            },
            {
                id: 'germany',
                name: 'Germany',
                data: [
                    ['Berlin', 15],
                    ['Munich', 14],
                    ['Frankfurt', 12],
                    ['Hamburg', 7]
                ]
            },
            {
                id: 'france',
                name: 'France',
                data: [
                    ['Paris', 25],
                    ['Lyon', 8],
                    ['Marseille', 5],
                    ['Nice', 3]
                ]
            },
            {
                id: 'italy',
                name: 'Italy',
                data: [
                    ['Milan', 15],
                    ['Rome', 10],
                    ['Turin', 4],
                    ['Florence', 3]
                ]
            },
            {
                id: 'spain',
                name: 'Spain',
                data: [
                    ['Madrid', 12],
                    ['Barcelona', 9],
                    ['Valencia', 4]
                ]
            },
            {
                id: 'japan',
                name: 'Japan',
                data: [
                    ['Tokyo', 32],
                    ['Osaka', 14],
                    ['Nagoya', 8],
                    ['Fukuoka', 4]
                ]
            },
            {
                id: 'australia',
                name: 'Australia',
                data: [
                    ['Sydney', 20],
                    ['Melbourne', 15],
                    ['Brisbane', 6],
                    ['Perth', 4]
                ]
            },
            {
                id: 'south-korea',
                name: 'South Korea',
                data: [
                    ['Seoul', 28],
                    ['Busan', 6],
                    ['Incheon', 4]
                ]
            },
            {
                id: 'singapore',
                name: 'Singapore',
                data: [
                    ['Central', 18],
                    ['East', 10],
                    ['West', 7]
                ]
            },
            {
                id: 'brazil',
                name: 'Brazil',
                data: [
                    ['Sao Paulo', 25],
                    ['Rio de Janeiro', 12],
                    ['Brasilia', 5],
                    ['Salvador', 3]
                ]
            },
            {
                id: 'argentina',
                name: 'Argentina',
                data: [
                    ['Buenos Aires', 16],
                    ['Cordoba', 4],
                    ['Rosario', 2]
                ]
            },
            {
                id: 'chile',
                name: 'Chile',
                data: [
                    ['Santiago', 15],
                    ['Valparaiso', 3],
                    ['Concepcion', 2]
                ]
            },
            {
                id: 'uae',
                name: 'UAE',
                data: [
                    ['Dubai', 18],
                    ['Abu Dhabi', 8],
                    ['Sharjah', 2]
                ]
            },
            {
                id: 'saudi-arabia',
                name: 'Saudi Arabia',
                data: [
                    ['Riyadh', 10],
                    ['Jeddah', 6],
                    ['Dammam', 2]
                ]
            },
            {
                id: 'israel',
                name: 'Israel',
                data: [
                    ['Tel Aviv', 5],
                    ['Jerusalem', 2],
                    ['Haifa', 1]
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

# Also save HTML for interactive version (with CDN links for portability)
standalone_html = (
    """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/modules/drilldown.js"></script>
</head>
<body style="margin:0; padding:0; background:#ffffff;">
    <div id="container" style="width: 100%; height: 600px;"></div>
    <script>
    """
    + chart_config
    + """
    </script>
</body>
</html>"""
)

with open("plot.html", "w", encoding="utf-8") as f:
    f.write(standalone_html)

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
