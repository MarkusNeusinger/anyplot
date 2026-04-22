""" pyplots.ai
network-hierarchical: Hierarchical Network Graph with Tree Layout
Library: highcharts unknown | Python 3.13.11
Quality: 92/100 | Created: 2026-01-08
"""

import tempfile
import time
import urllib.request
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data: Organizational hierarchy - CEO -> VPs -> Directors -> Managers
# Structure: list of [from, to] connections for organization chart
connections = [
    # CEO to VPs
    ["CEO", "VP Engineering"],
    ["CEO", "VP Sales"],
    ["CEO", "VP Operations"],
    # VP Engineering to Directors
    ["VP Engineering", "Dir Frontend"],
    ["VP Engineering", "Dir Backend"],
    ["VP Engineering", "Dir DevOps"],
    # VP Sales to Directors
    ["VP Sales", "Dir Americas"],
    ["VP Sales", "Dir EMEA"],
    # VP Operations to Directors
    ["VP Operations", "Dir Logistics"],
    ["VP Operations", "Dir HR"],
    # Directors to Managers
    ["Dir Frontend", "Mgr React"],
    ["Dir Frontend", "Mgr Vue"],
    ["Dir Backend", "Mgr API"],
    ["Dir Backend", "Mgr Database"],
    ["Dir DevOps", "Mgr Cloud"],
    ["Dir Americas", "Mgr NA Sales"],
    ["Dir Americas", "Mgr LATAM"],
    ["Dir EMEA", "Mgr UK Sales"],
    ["Dir EMEA", "Mgr DE Sales"],
    ["Dir Logistics", "Mgr Supply"],
    ["Dir HR", "Mgr Talent"],
]

# Node levels for coloring
node_levels = {
    "CEO": 0,
    "VP Engineering": 1,
    "VP Sales": 1,
    "VP Operations": 1,
    "Dir Frontend": 2,
    "Dir Backend": 2,
    "Dir DevOps": 2,
    "Dir Americas": 2,
    "Dir EMEA": 2,
    "Dir Logistics": 2,
    "Dir HR": 2,
    "Mgr React": 3,
    "Mgr Vue": 3,
    "Mgr API": 3,
    "Mgr Database": 3,
    "Mgr Cloud": 3,
    "Mgr NA Sales": 3,
    "Mgr LATAM": 3,
    "Mgr UK Sales": 3,
    "Mgr DE Sales": 3,
    "Mgr Supply": 3,
    "Mgr Talent": 3,
}

# Level colors (colorblind-safe): Python Blue, Python Yellow, Teal, Pink
level_colors = ["#306998", "#FFD43B", "#17BECF", "#E377C2"]

# Build nodes config with colors based on level
nodes_js = "[\n"
for node_name, level in node_levels.items():
    color = level_colors[level]
    nodes_js += f'    {{id: "{node_name}", color: "{color}"}},\n'
nodes_js += "]"

# Build data connections
data_js = "[\n"
for conn in connections:
    data_js += f'    ["{conn[0]}", "{conn[1]}"],\n'
data_js += "]"

# Download Highcharts JS modules
highcharts_url = "https://code.highcharts.com/highcharts.js"
sankey_url = "https://code.highcharts.com/modules/sankey.js"
organization_url = "https://code.highcharts.com/modules/organization.js"

with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

with urllib.request.urlopen(sankey_url, timeout=30) as response:
    sankey_js = response.read().decode("utf-8")

with urllib.request.urlopen(organization_url, timeout=30) as response:
    organization_js = response.read().decode("utf-8")

# Chart JavaScript using organization chart
chart_js = f"""
Highcharts.chart('container', {{
    chart: {{
        type: 'organization',
        width: 4800,
        height: 2700,
        backgroundColor: '#ffffff',
        inverted: true,
        marginBottom: 100,
        spacingBottom: 50
    }},
    title: {{
        text: 'network-hierarchical · highcharts · pyplots.ai',
        style: {{fontSize: '56px', fontWeight: 'bold'}}
    }},
    subtitle: {{
        text: '<span style="color:#306998; font-size:40px;">●</span> CEO &nbsp;&nbsp;&nbsp; <span style="color:#FFD43B; font-size:40px;">●</span> VPs &nbsp;&nbsp;&nbsp; <span style="color:#17BECF; font-size:40px;">●</span> Directors &nbsp;&nbsp;&nbsp; <span style="color:#E377C2; font-size:40px;">●</span> Managers',
        useHTML: true,
        style: {{fontSize: '32px', color: '#666666'}}
    }},
    accessibility: {{
        enabled: false
    }},
    plotOptions: {{
        organization: {{
            nodeWidth: 120,
            nodePadding: 15,
            borderRadius: 10,
            dataLabels: {{
                enabled: true,
                style: {{
                    fontSize: '22px',
                    fontWeight: 'bold',
                    textOutline: 'none'
                }},
                color: '#333333'
            }},
            colorByPoint: false,
            link: {{
                color: '#888888',
                lineWidth: 3
            }},
            hangingIndentTranslation: 'shrink'
        }}
    }},
    series: [{{
        type: 'organization',
        name: 'Organization',
        keys: ['from', 'to'],
        data: {data_js},
        nodes: {nodes_js},
        levels: [{{
            level: 0,
            color: '#306998',
            dataLabels: {{style: {{color: 'white'}}}}
        }}, {{
            level: 1,
            color: '#FFD43B',
            dataLabels: {{style: {{color: '#333333'}}}}
        }}, {{
            level: 2,
            color: '#17BECF',
            dataLabels: {{style: {{color: '#333333'}}}}
        }}, {{
            level: 3,
            color: '#E377C2',
            dataLabels: {{style: {{color: '#333333'}}}}
        }}]
    }}]
}});
"""

# Generate HTML with inline scripts
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{sankey_js}</script>
    <script>{organization_js}</script>
</head>
<body style="margin:0; padding:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{chart_js}</script>
</body>
</html>"""

# Save HTML file
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Take screenshot with Selenium
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2800")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)  # Wait for chart to render
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
