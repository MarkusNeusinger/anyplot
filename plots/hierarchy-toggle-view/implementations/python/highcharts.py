""" anyplot.ai
hierarchy-toggle-view: Interactive Treemap-Sunburst Toggle View
Library: highcharts unknown | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-19
"""

import base64
import os
import subprocess
import tempfile
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette for departments (positions 1-4)
DEPT_COLORS = {"engineering": "#009E73", "sales": "#C475FD", "operations": "#4467A3", "hr": "#BD8233"}

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
    # Level 3: Enterprise sales teams
    ["ent-na", "enterprise", "North America", 35],
    ["ent-eu", "enterprise", "Europe", 28],
    ["ent-apac", "enterprise", "Asia Pacific", 20],
    # Level 3: SMB sales teams
    ["smb-direct", "smb", "Direct Sales", 18],
    ["smb-online", "smb", "Online Sales", 22],
    # Level 3: Partner sales teams
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

# Convert to JavaScript array literal
js_data = "[\n"
for item in hierarchy_data:
    id_val, parent_val, label_val, value_val = item
    parent_str = f'"{parent_val}"' if parent_val else "null"
    value_str = str(value_val) if value_val is not None else "null"
    js_data += f'    ["{id_val}", {parent_str}, "{label_val}", {value_str}],\n'
js_data += "]"

# Build JavaScript color map object literal
js_color_map = "{\n"
for dept, color in DEPT_COLORS.items():
    js_color_map += f"    '{dept}': '{color}',\n"
js_color_map += "}"

# Install Highcharts via npm and read local files (CDN blocked in CI)
hc_prefix = "/tmp/hc-anyplot"
subprocess.run(["npm", "install", "highcharts", "--prefix", hc_prefix], check=True, capture_output=True)
hc_dir = Path(hc_prefix) / "node_modules" / "highcharts"
highcharts_js = (hc_dir / "highcharts.js").read_text(encoding="utf-8")
treemap_js = (hc_dir / "modules" / "treemap.js").read_text(encoding="utf-8")
sunburst_js = (hc_dir / "modules" / "sunburst.js").read_text(encoding="utf-8")

# HTML with toggle functionality and theme-adaptive chrome
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: {PAGE_BG};
            color: {INK};
        }}
        .outer {{
            width: 4800px;
            height: 2700px;
            position: relative;
            background: {PAGE_BG};
            box-sizing: border-box;
        }}
        .toggle-container {{
            position: absolute;
            top: 50px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 1000;
            display: flex;
            gap: 0;
            background: {ELEVATED_BG};
            border-radius: 32px;
            padding: 10px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.18);
        }}
        .toggle-btn {{
            padding: 22px 70px;
            font-size: 30px;
            font-weight: 600;
            border: none;
            cursor: pointer;
            border-radius: 26px;
            transition: all 0.3s ease;
            color: {INK_SOFT};
            background: transparent;
        }}
        .toggle-btn.active {{
            background: #009E73;
            color: #FAF8F1;
            box-shadow: 0 2px 10px rgba(0,158,115,0.45);
        }}
        #chart-container {{
            position: absolute;
            top: 160px;
            left: 0;
            right: 0;
            bottom: 60px;
        }}
        .spec-label {{
            position: absolute;
            bottom: 14px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 26px;
            color: {INK_SOFT};
            z-index: 100;
            white-space: nowrap;
            letter-spacing: 0.02em;
        }}
    </style>
    <script>{highcharts_js}</script>
    <script>{treemap_js}</script>
    <script>{sunburst_js}</script>
</head>
<body>
    <div class="outer">
        <div class="toggle-container">
            <button class="toggle-btn active" id="treemap-btn" onclick="showTreemap()">Treemap</button>
            <button class="toggle-btn" id="sunburst-btn" onclick="showSunburst()">Sunburst</button>
        </div>
        <div id="chart-container"></div>
        <div class="spec-label">hierarchy-toggle-view · python · highcharts · anyplot.ai</div>
    </div>
    <script>
        var rawData = {js_data};

        var colorMap = {js_color_map};

        function getDeptColor(id, parent) {{
            if (colorMap[id]) return colorMap[id];
            for (var i = 0; i < rawData.length; i++) {{
                if (rawData[i][0] === parent) {{
                    if (colorMap[rawData[i][0]]) return colorMap[rawData[i][0]];
                    return getDeptColor(rawData[i][0], rawData[i][1]);
                }}
            }}
            return '#888888';
        }}

        var processedData = rawData.map(function(item) {{
            return {{
                id: item[0],
                parent: item[1] || undefined,
                name: item[2],
                value: item[3],
                color: getDeptColor(item[0], item[1])
            }};
        }});

        var currentChart = null;
        var currentType = 'treemap';

        var chartBg = '{PAGE_BG}';
        var elevatedBg = '{ELEVATED_BG}';
        var inkColor = '{INK}';
        var inkSoft = '{INK_SOFT}';

        function createTreemap() {{
            return Highcharts.chart('chart-container', {{
                chart: {{
                    backgroundColor: chartBg,
                    animation: {{ duration: 800 }}
                }},
                title: {{
                    text: 'TechCorp Organizational Structure · Employee Headcount',
                    style: {{ fontSize: '42px', fontWeight: '600', color: inkColor }},
                    y: 28
                }},
                series: [{{
                    type: 'treemap',
                    layoutAlgorithm: 'squarified',
                    allowDrillToNode: true,
                    animationLimit: 1000,
                    dataLabels: {{
                        enabled: true,
                        style: {{
                            fontSize: '26px',
                            fontWeight: 'bold',
                            textOutline: '3px contrast'
                        }}
                    }},
                    levels: [{{
                        level: 1,
                        dataLabels: {{
                            enabled: true,
                            style: {{ fontSize: '40px' }}
                        }},
                        borderWidth: 5,
                        borderColor: chartBg
                    }}, {{
                        level: 2,
                        dataLabels: {{
                            enabled: true,
                            style: {{ fontSize: '32px' }}
                        }},
                        borderWidth: 3,
                        borderColor: chartBg
                    }}, {{
                        level: 3,
                        dataLabels: {{
                            enabled: true,
                            style: {{ fontSize: '26px' }}
                        }},
                        borderWidth: 2,
                        borderColor: chartBg
                    }}],
                    data: processedData
                }}],
                tooltip: {{
                    style: {{ fontSize: '22px' }},
                    backgroundColor: elevatedBg,
                    borderColor: inkSoft,
                    pointFormat: '<b>{{point.name}}</b>: {{point.value}} employees'
                }},
                credits: {{ enabled: false }}
            }});
        }}

        function createSunburst() {{
            return Highcharts.chart('chart-container', {{
                chart: {{
                    backgroundColor: chartBg,
                    animation: {{ duration: 800 }}
                }},
                title: {{
                    text: 'TechCorp Organizational Structure · Employee Headcount',
                    style: {{ fontSize: '42px', fontWeight: '600', color: inkColor }},
                    y: 28
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
                            fontSize: '24px',
                            fontWeight: 'bold',
                            textOutline: '2px contrast',
                            color: inkColor
                        }},
                        rotationMode: 'circular'
                    }},
                    levels: [{{
                        level: 1,
                        dataLabels: {{
                            style: {{ fontSize: '32px' }}
                        }}
                    }}, {{
                        level: 2,
                        colorByPoint: false,
                        dataLabels: {{
                            style: {{ fontSize: '28px' }}
                        }}
                    }}, {{
                        level: 3,
                        dataLabels: {{
                            style: {{ fontSize: '24px' }}
                        }}
                    }}, {{
                        level: 4,
                        dataLabels: {{
                            enabled: true,
                            style: {{ fontSize: '22px' }}
                        }}
                    }}]
                }}],
                tooltip: {{
                    style: {{ fontSize: '22px' }},
                    backgroundColor: elevatedBg,
                    borderColor: inkSoft,
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

        currentChart = createTreemap();
    </script>
</body>
</html>"""

# Save HTML artifact (theme-suffixed)
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Create PNG screenshot via Selenium
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

driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 4800, "height": 2700, "deviceScaleFactor": 1, "mobile": False}
)
time.sleep(1)

screenshot_data = driver.execute_cdp_cmd("Page.captureScreenshot", {"format": "png"})

with open(f"plot-{THEME}.png", "wb") as f:
    f.write(base64.b64decode(screenshot_data["data"]))

driver.quit()
Path(temp_path).unlink()
