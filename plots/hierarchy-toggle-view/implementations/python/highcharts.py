""" pyplots.ai
hierarchy-toggle-view: Interactive Treemap-Sunburst Toggle View
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2026-01-11
"""

import base64
import tempfile
import time
import urllib.request
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Hierarchical data: Company organizational structure
# Format: [id, parent, label, value]
hierarchy_data = [
    # Root
    ["company", None, "TechCorp", None],
    # Level 1: Departments
    ["engineering", "company", "Engineering", None],
    ["sales", "company", "Sales", None],
    ["operations", "company", "Operations", None],
    ["hr", "company", "Human Resources", None],
    # Level 2: Engineering teams
    ["frontend", "engineering", "Frontend", None],
    ["backend", "engineering", "Backend", None],
    ["devops", "engineering", "DevOps", None],
    ["qa", "engineering", "QA", None],
    # Level 2: Sales teams
    ["enterprise", "sales", "Enterprise", None],
    ["smb", "sales", "SMB", None],
    ["partners", "sales", "Partners", None],
    # Level 2: Operations teams
    ["support", "operations", "Support", None],
    ["logistics", "operations", "Logistics", None],
    # Level 2: HR teams
    ["recruiting", "hr", "Recruiting", None],
    ["training", "hr", "Training", None],
    # Level 3: Frontend teams (leaf nodes with values)
    ["fe-web", "frontend", "Web Team", 25],
    ["fe-mobile", "frontend", "Mobile Team", 18],
    ["fe-design", "frontend", "Design System", 12],
    # Level 3: Backend teams
    ["be-api", "backend", "API Team", 22],
    ["be-data", "backend", "Data Platform", 28],
    ["be-ml", "backend", "ML/AI Team", 15],
    # Level 3: DevOps teams
    ["devops-infra", "devops", "Infrastructure", 14],
    ["devops-sec", "devops", "Security", 10],
    # Level 3: QA teams
    ["qa-auto", "qa", "Automation", 8],
    ["qa-manual", "qa", "Manual Testing", 6],
    # Level 3: Sales teams
    ["ent-na", "enterprise", "North America", 35],
    ["ent-eu", "enterprise", "Europe", 28],
    ["ent-apac", "enterprise", "Asia Pacific", 20],
    ["smb-direct", "smb", "Direct Sales", 18],
    ["smb-online", "smb", "Online Sales", 22],
    ["partner-tech", "partners", "Tech Partners", 12],
    ["partner-resell", "partners", "Resellers", 15],
    # Level 3: Operations teams
    ["support-t1", "support", "Tier 1 Support", 20],
    ["support-t2", "support", "Tier 2 Support", 12],
    ["support-t3", "support", "Tier 3 Support", 8],
    ["log-warehouse", "logistics", "Warehouse", 10],
    ["log-shipping", "logistics", "Shipping", 8],
    # Level 3: HR teams
    ["rec-tech", "recruiting", "Tech Recruiting", 6],
    ["rec-sales", "recruiting", "Sales Recruiting", 4],
    ["train-onboard", "training", "Onboarding", 5],
    ["train-dev", "training", "Development", 4],
]

# Convert to JavaScript array format
js_data = "[\n"
for item in hierarchy_data:
    id_val, parent_val, label_val, value_val = item
    parent_str = f'"{parent_val}"' if parent_val else "null"
    value_str = str(value_val) if value_val else "null"
    js_data += f'    ["{id_val}", {parent_str}, "{label_val}", {value_str}],\n'
js_data += "]"

# Download Highcharts JS files
highcharts_url = "https://code.highcharts.com/highcharts.js"
treemap_url = "https://code.highcharts.com/modules/treemap.js"
sunburst_url = "https://code.highcharts.com/modules/sunburst.js"

with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

with urllib.request.urlopen(treemap_url, timeout=30) as response:
    treemap_js = response.read().decode("utf-8")

with urllib.request.urlopen(sunburst_url, timeout=30) as response:
    sunburst_js = response.read().decode("utf-8")

# HTML with toggle functionality
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #ffffff;
        }}
        .container {{
            width: 4800px;
            height: 2700px;
            position: relative;
        }}
        .toggle-container {{
            position: absolute;
            top: 40px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 1000;
            display: flex;
            gap: 0;
            background: #e8e8e8;
            border-radius: 30px;
            padding: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        .toggle-btn {{
            padding: 20px 60px;
            font-size: 28px;
            font-weight: 600;
            border: none;
            cursor: pointer;
            border-radius: 24px;
            transition: all 0.3s ease;
            color: #666;
            background: transparent;
        }}
        .toggle-btn.active {{
            background: #306998;
            color: white;
            box-shadow: 0 2px 8px rgba(48, 105, 152, 0.4);
        }}
        .toggle-btn:hover:not(.active) {{
            background: #d0d0d0;
        }}
        #chart-container {{
            width: 100%;
            height: calc(100% - 200px);
            margin-top: 200px;
        }}
        .title {{
            position: absolute;
            top: 140px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 48px;
            font-weight: 700;
            color: #333;
            z-index: 100;
        }}
    </style>
    <script>{highcharts_js}</script>
    <script>{treemap_js}</script>
    <script>{sunburst_js}</script>
</head>
<body>
    <div class="container">
        <div class="toggle-container">
            <button class="toggle-btn active" id="treemap-btn" onclick="showTreemap()">Treemap</button>
            <button class="toggle-btn" id="sunburst-btn" onclick="showSunburst()">Sunburst</button>
        </div>
        <div class="title">hierarchy-toggle-view · highcharts · pyplots.ai</div>
        <div id="chart-container"></div>
    </div>
    <script>
        var rawData = {js_data};

        // Color palette - consistent across both views
        var colorMap = {{
            'engineering': '#306998',
            'sales': '#FFD43B',
            'operations': '#9467BD',
            'hr': '#17BECF'
        }};

        // Get department color for any node
        function getDeptColor(id, parent) {{
            if (colorMap[id]) return colorMap[id];
            // Find parent department
            for (var i = 0; i < rawData.length; i++) {{
                if (rawData[i][0] === parent) {{
                    if (colorMap[rawData[i][0]]) return colorMap[rawData[i][0]];
                    return getDeptColor(rawData[i][0], rawData[i][1]);
                }}
            }}
            return '#666666';
        }}

        // Process data for both chart types
        var processedData = rawData.map(function(item) {{
            var color = getDeptColor(item[0], item[1]);
            return {{
                id: item[0],
                parent: item[1] || undefined,
                name: item[2],
                value: item[3],
                color: color
            }};
        }});

        var currentChart = null;
        var currentType = 'treemap';

        function createTreemap() {{
            return Highcharts.chart('chart-container', {{
                chart: {{
                    backgroundColor: '#ffffff',
                    animation: {{ duration: 800 }}
                }},
                title: {{
                    text: 'TechCorp Organizational Structure · Employee Headcount',
                    style: {{ fontSize: '36px', fontWeight: '600', color: '#333' }},
                    y: 30
                }},
                subtitle: {{
                    text: null
                }},
                series: [{{
                    type: 'treemap',
                    layoutAlgorithm: 'squarified',
                    allowDrillToNode: true,
                    animationLimit: 1000,
                    dataLabels: {{
                        enabled: true,
                        style: {{
                            fontSize: '24px',
                            fontWeight: 'bold',
                            textOutline: '3px contrast'
                        }}
                    }},
                    levels: [{{
                        level: 1,
                        dataLabels: {{
                            enabled: true,
                            style: {{ fontSize: '36px' }}
                        }},
                        borderWidth: 4,
                        borderColor: '#ffffff'
                    }}, {{
                        level: 2,
                        dataLabels: {{
                            enabled: true,
                            style: {{ fontSize: '28px' }}
                        }},
                        borderWidth: 3,
                        borderColor: '#ffffff'
                    }}, {{
                        level: 3,
                        dataLabels: {{
                            enabled: true,
                            style: {{ fontSize: '22px' }}
                        }},
                        borderWidth: 2,
                        borderColor: '#ffffff'
                    }}],
                    data: processedData
                }}],
                tooltip: {{
                    style: {{ fontSize: '22px' }},
                    pointFormat: '<b>{{point.name}}</b>: {{point.value}} employees'
                }},
                credits: {{ enabled: false }}
            }});
        }}

        function createSunburst() {{
            return Highcharts.chart('chart-container', {{
                chart: {{
                    backgroundColor: '#ffffff',
                    animation: {{ duration: 800 }}
                }},
                title: {{
                    text: 'TechCorp Organizational Structure · Employee Headcount',
                    style: {{ fontSize: '36px', fontWeight: '600', color: '#333' }},
                    y: 30
                }},
                subtitle: {{
                    text: null
                }},
                series: [{{
                    type: 'sunburst',
                    data: processedData,
                    allowDrillToNode: true,
                    cursor: 'pointer',
                    dataLabels: {{
                        enabled: true,
                        format: '{{point.name}}',
                        style: {{
                            fontSize: '20px',
                            fontWeight: 'bold',
                            textOutline: '2px contrast'
                        }},
                        rotationMode: 'circular'
                    }},
                    levels: [{{
                        level: 1,
                        dataLabels: {{
                            style: {{ fontSize: '28px' }}
                        }}
                    }}, {{
                        level: 2,
                        colorByPoint: false,
                        dataLabels: {{
                            style: {{ fontSize: '24px' }}
                        }}
                    }}, {{
                        level: 3,
                        dataLabels: {{
                            style: {{ fontSize: '18px' }}
                        }}
                    }}, {{
                        level: 4,
                        dataLabels: {{
                            enabled: true,
                            style: {{ fontSize: '16px' }}
                        }}
                    }}]
                }}],
                tooltip: {{
                    style: {{ fontSize: '22px' }},
                    pointFormat: '<b>{{point.name}}</b>: {{point.value}} employees'
                }},
                credits: {{ enabled: false }}
            }});
        }}

        function showTreemap() {{
            if (currentType === 'treemap') return;
            currentType = 'treemap';
            document.getElementById('treemap-btn').classList.add('active');
            document.getElementById('sunburst-btn').classList.remove('active');
            if (currentChart) currentChart.destroy();
            currentChart = createTreemap();
        }}

        function showSunburst() {{
            if (currentType === 'sunburst') return;
            currentType = 'sunburst';
            document.getElementById('sunburst-btn').classList.add('active');
            document.getElementById('treemap-btn').classList.remove('active');
            if (currentChart) currentChart.destroy();
            currentChart = createSunburst();
        }}

        // Initialize with treemap
        currentChart = createTreemap();
    </script>
</body>
</html>"""

# Write HTML file for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Create PNG screenshot using Selenium
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")
chrome_options.add_argument("--hide-scrollbars")
chrome_options.add_argument("--force-device-scale-factor=1")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)

# Use CDP to capture screenshot at exact dimensions
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 4800, "height": 2700, "deviceScaleFactor": 1, "mobile": False}
)
time.sleep(1)

# Take full screenshot
screenshot_data = driver.execute_cdp_cmd("Page.captureScreenshot", {"format": "png"})

with open("plot.png", "wb") as f:
    f.write(base64.b64decode(screenshot_data["data"]))

driver.quit()

Path(temp_path).unlink()
