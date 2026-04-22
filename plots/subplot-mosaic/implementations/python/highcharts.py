""" pyplots.ai
subplot-mosaic: Mosaic Subplot Layout with Varying Sizes
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data
np.random.seed(42)

# Panel A (large left): Time series - monthly sales data
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
sales = [42, 48, 52, 45, 58, 62, 55, 68, 72, 65, 78, 85]

# Panel B (top right): Bar chart - regional performance
regions = ["North", "South", "East", "West"]
regional_sales = [245, 312, 189, 276]

# Panel C (bottom wide): Scatter - product analysis
product_count = 80
product_price = np.random.uniform(10, 100, product_count)
product_revenue = product_price * np.random.uniform(50, 200, product_count) + np.random.normal(0, 500, product_count)
product_data = [[round(float(x), 2), round(float(y), 2)] for x, y in zip(product_price, product_revenue, strict=False)]

# Download Highcharts JS
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Convert data to JSON strings for embedding in JavaScript
months_json = json.dumps(months)
sales_json = json.dumps(sales)
regions_json = json.dumps(regions)
regional_sales_json = json.dumps(regional_sales)
product_data_json = json.dumps(product_data)

# Build HTML with mosaic layout
# Layout: "AAB" / "AAB" / "CCC" - A is large left (2x2), B is small right (1x2), C is wide bottom (3x1)
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <style>
        body {{
            margin: 0;
            padding: 40px;
            background-color: #ffffff;
            font-family: Arial, sans-serif;
        }}
        .main-title {{
            text-align: center;
            font-size: 48px;
            font-weight: bold;
            color: #333333;
            margin-bottom: 30px;
            font-family: Arial, sans-serif;
        }}
        .mosaic-container {{
            display: grid;
            grid-template-columns: 2fr 2fr 1fr;
            grid-template-rows: 1fr 1fr 1fr;
            gap: 30px;
            width: 4680px;
            height: 2450px;
        }}
        #panelA {{
            grid-column: 1 / 3;
            grid-row: 1 / 3;
            background-color: #fafafa;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        #panelB {{
            grid-column: 3 / 4;
            grid-row: 1 / 3;
            background-color: #fafafa;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        #panelC {{
            grid-column: 1 / 4;
            grid-row: 3 / 4;
            background-color: #fafafa;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
    </style>
</head>
<body>
    <div class="main-title">subplot-mosaic · highcharts · pyplots.ai</div>
    <div class="mosaic-container">
        <div id="panelA"></div>
        <div id="panelB"></div>
        <div id="panelC"></div>
    </div>
    <script>
        // Panel A: Time series line chart (large left panel)
        Highcharts.chart('panelA', {{
            chart: {{
                type: 'line',
                backgroundColor: '#fafafa'
            }},
            title: {{
                text: 'Monthly Sales Trend',
                style: {{
                    color: '#333333',
                    fontSize: '36px',
                    fontWeight: 'bold',
                    fontFamily: 'Arial, sans-serif'
                }}
            }},
            xAxis: {{
                categories: {months_json},
                title: {{
                    text: 'Month',
                    style: {{
                        color: '#555555',
                        fontSize: '24px',
                        fontFamily: 'Arial, sans-serif'
                    }}
                }},
                labels: {{
                    style: {{
                        color: '#666666',
                        fontSize: '20px',
                        fontFamily: 'Arial, sans-serif'
                    }}
                }}
            }},
            yAxis: {{
                title: {{
                    text: 'Sales (Units)',
                    style: {{
                        color: '#555555',
                        fontSize: '24px',
                        fontFamily: 'Arial, sans-serif'
                    }}
                }},
                labels: {{
                    style: {{
                        color: '#666666',
                        fontSize: '20px',
                        fontFamily: 'Arial, sans-serif'
                    }}
                }},
                gridLineColor: '#e0e0e0',
                gridLineWidth: 1
            }},
            legend: {{
                enabled: true,
                itemStyle: {{
                    color: '#555555',
                    fontSize: '20px',
                    fontFamily: 'Arial, sans-serif'
                }}
            }},
            plotOptions: {{
                line: {{
                    lineWidth: 4,
                    marker: {{
                        enabled: true,
                        radius: 8,
                        fillColor: '#306998'
                    }},
                    color: '#306998'
                }}
            }},
            series: [{{
                name: 'Sales',
                data: {sales_json}
            }}],
            credits: {{ enabled: false }}
        }});

        // Panel B: Bar chart (small right panel)
        Highcharts.chart('panelB', {{
            chart: {{
                type: 'bar',
                backgroundColor: '#fafafa'
            }},
            title: {{
                text: 'Regional Performance',
                style: {{
                    color: '#333333',
                    fontSize: '36px',
                    fontWeight: 'bold',
                    fontFamily: 'Arial, sans-serif'
                }}
            }},
            xAxis: {{
                categories: {regions_json},
                title: {{
                    text: null
                }},
                labels: {{
                    style: {{
                        color: '#666666',
                        fontSize: '20px',
                        fontFamily: 'Arial, sans-serif'
                    }}
                }}
            }},
            yAxis: {{
                title: {{
                    text: 'Sales (Units)',
                    style: {{
                        color: '#555555',
                        fontSize: '24px',
                        fontFamily: 'Arial, sans-serif'
                    }}
                }},
                labels: {{
                    style: {{
                        color: '#666666',
                        fontSize: '20px',
                        fontFamily: 'Arial, sans-serif'
                    }}
                }},
                gridLineColor: '#e0e0e0',
                gridLineWidth: 1
            }},
            legend: {{
                enabled: false
            }},
            plotOptions: {{
                bar: {{
                    colorByPoint: true,
                    colors: ['#306998', '#FFD43B', '#9467BD', '#17BECF'],
                    borderRadius: 4,
                    dataLabels: {{
                        enabled: true,
                        style: {{
                            fontSize: '18px',
                            fontWeight: 'bold',
                            color: '#333333'
                        }}
                    }}
                }}
            }},
            series: [{{
                name: 'Sales',
                data: {regional_sales_json}
            }}],
            credits: {{ enabled: false }}
        }});

        // Panel C: Scatter chart (wide bottom panel)
        Highcharts.chart('panelC', {{
            chart: {{
                type: 'scatter',
                backgroundColor: '#fafafa'
            }},
            title: {{
                text: 'Product Price vs Revenue Analysis',
                style: {{
                    color: '#333333',
                    fontSize: '36px',
                    fontWeight: 'bold',
                    fontFamily: 'Arial, sans-serif'
                }}
            }},
            xAxis: {{
                title: {{
                    text: 'Product Price ($)',
                    style: {{
                        color: '#555555',
                        fontSize: '24px',
                        fontFamily: 'Arial, sans-serif'
                    }}
                }},
                labels: {{
                    style: {{
                        color: '#666666',
                        fontSize: '20px',
                        fontFamily: 'Arial, sans-serif'
                    }}
                }},
                gridLineColor: '#e0e0e0',
                gridLineWidth: 1
            }},
            yAxis: {{
                title: {{
                    text: 'Revenue ($)',
                    style: {{
                        color: '#555555',
                        fontSize: '24px',
                        fontFamily: 'Arial, sans-serif'
                    }}
                }},
                labels: {{
                    style: {{
                        color: '#666666',
                        fontSize: '20px',
                        fontFamily: 'Arial, sans-serif'
                    }}
                }},
                gridLineColor: '#e0e0e0',
                gridLineWidth: 1
            }},
            legend: {{
                enabled: true,
                itemStyle: {{
                    color: '#555555',
                    fontSize: '20px',
                    fontFamily: 'Arial, sans-serif'
                }}
            }},
            plotOptions: {{
                scatter: {{
                    marker: {{
                        radius: 10,
                        symbol: 'circle',
                        fillColor: 'rgba(48, 105, 152, 0.7)',
                        lineWidth: 2,
                        lineColor: '#306998'
                    }}
                }}
            }},
            series: [{{
                name: 'Products',
                data: {product_data_json}
            }}],
            credits: {{ enabled: false }}
        }});
    </script>
</body>
</html>"""

# Write temp HTML
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Capture screenshot with Selenium
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(8)  # Wait for charts to render
driver.save_screenshot("plot.png")

# Also save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    # Replace inline JS with CDN link for HTML file
    html_for_save = html_content.replace(
        f"<script>{highcharts_js}</script>", '<script src="https://code.highcharts.com/highcharts.js"></script>'
    )
    f.write(html_for_save)

driver.quit()
Path(temp_path).unlink()
