"""anyplot.ai
map-drilldown-geographic: Drillable Geographic Map
Library: highcharts | Python 3.13
Quality: 90/100 | Created: 2026-01-20
"""

import os
import tempfile
import time
from pathlib import Path

import requests
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Download required JavaScript files (inline for headless Chrome)
highmaps_js = requests.get("https://cdn.jsdelivr.net/npm/highcharts/highmaps.js", timeout=60).text

drilldown_js = requests.get("https://cdn.jsdelivr.net/npm/highcharts/modules/drilldown.js", timeout=60).text

us_topo = requests.get(
    "https://cdn.jsdelivr.net/npm/@highcharts/map-collection/countries/us/us-all.topo.json", timeout=60
).text

# 3-level hierarchy: US Regions (L1) → States per region (L2) → Cities per state (L3)
# L1 map colors states by region using anyplot categorical palette (positions 1-4)
chart_config = f"""
(function() {{
    var regionNames = {{
        'west': 'West', 'south': 'South', 'midwest': 'Midwest', 'northeast': 'Northeast'
    }};

    var REGION_COLORS = {{
        'west': '#009E73',
        'south': '#9418DB',
        'midwest': '#B71D27',
        'northeast': '#16B8F3'
    }};

    var stateRegions = {{
        'us-ca': 'west', 'us-wa': 'west', 'us-or': 'west', 'us-nv': 'west',
        'us-az': 'west', 'us-ut': 'west', 'us-co': 'west', 'us-nm': 'west',
        'us-id': 'west', 'us-mt': 'west', 'us-wy': 'west', 'us-ak': 'west', 'us-hi': 'west',
        'us-tx': 'south', 'us-fl': 'south', 'us-ga': 'south', 'us-nc': 'south',
        'us-va': 'south', 'us-tn': 'south', 'us-la': 'south', 'us-ky': 'south',
        'us-sc': 'south', 'us-al': 'south', 'us-ms': 'south', 'us-ar': 'south',
        'us-ok': 'south', 'us-wv': 'south', 'us-md': 'south', 'us-de': 'south',
        'us-il': 'midwest', 'us-oh': 'midwest', 'us-mi': 'midwest', 'us-in': 'midwest',
        'us-wi': 'midwest', 'us-mn': 'midwest', 'us-mo': 'midwest', 'us-ia': 'midwest',
        'us-ks': 'midwest', 'us-ne': 'midwest', 'us-sd': 'midwest', 'us-nd': 'midwest',
        'us-ny': 'northeast', 'us-pa': 'northeast', 'us-nj': 'northeast', 'us-ma': 'northeast',
        'us-ct': 'northeast', 'us-nh': 'northeast', 'us-me': 'northeast',
        'us-ri': 'northeast', 'us-vt': 'northeast'
    }};

    var regionSales = {{
        'west': 595, 'south': 754, 'midwest': 453, 'northeast': 479
    }};

    var regionStateList = {{
        'west': ['us-ca', 'us-wa', 'us-or', 'us-nv', 'us-az', 'us-ut', 'us-co', 'us-nm', 'us-id', 'us-mt', 'us-wy', 'us-ak', 'us-hi'],
        'south': ['us-tx', 'us-fl', 'us-ga', 'us-nc', 'us-va', 'us-tn', 'us-la', 'us-ky', 'us-sc', 'us-al', 'us-ms', 'us-ar', 'us-ok', 'us-wv', 'us-md', 'us-de'],
        'midwest': ['us-il', 'us-oh', 'us-mi', 'us-in', 'us-wi', 'us-mn', 'us-mo', 'us-ia', 'us-ks', 'us-ne', 'us-sd', 'us-nd'],
        'northeast': ['us-ny', 'us-pa', 'us-nj', 'us-ma', 'us-ct', 'us-nh', 'us-me', 'us-ri', 'us-vt']
    }};

    var allStateData = {{
        'us-ca': {{ name: 'California', value: 245 }},
        'us-tx': {{ name: 'Texas', value: 198 }},
        'us-fl': {{ name: 'Florida', value: 156 }},
        'us-ny': {{ name: 'New York', value: 215 }},
        'us-il': {{ name: 'Illinois', value: 98 }},
        'us-pa': {{ name: 'Pennsylvania', value: 87 }},
        'us-oh': {{ name: 'Ohio', value: 76 }},
        'us-ga': {{ name: 'Georgia', value: 89 }},
        'us-nc': {{ name: 'North Carolina', value: 72 }},
        'us-mi': {{ name: 'Michigan', value: 68 }},
        'us-nj': {{ name: 'New Jersey', value: 94 }},
        'us-va': {{ name: 'Virginia', value: 65 }},
        'us-wa': {{ name: 'Washington', value: 112 }},
        'us-az': {{ name: 'Arizona', value: 58 }},
        'us-ma': {{ name: 'Massachusetts', value: 78 }},
        'us-tn': {{ name: 'Tennessee', value: 52 }},
        'us-in': {{ name: 'Indiana', value: 45 }},
        'us-mo': {{ name: 'Missouri', value: 42 }},
        'us-md': {{ name: 'Maryland', value: 56 }},
        'us-wi': {{ name: 'Wisconsin', value: 48 }},
        'us-co': {{ name: 'Colorado', value: 67 }},
        'us-mn': {{ name: 'Minnesota', value: 55 }},
        'us-sc': {{ name: 'South Carolina', value: 38 }},
        'us-al': {{ name: 'Alabama', value: 35 }},
        'us-la': {{ name: 'Louisiana', value: 42 }},
        'us-ky': {{ name: 'Kentucky', value: 34 }},
        'us-or': {{ name: 'Oregon', value: 52 }},
        'us-ok': {{ name: 'Oklahoma', value: 32 }},
        'us-ct': {{ name: 'Connecticut', value: 45 }},
        'us-ut': {{ name: 'Utah', value: 38 }},
        'us-ia': {{ name: 'Iowa', value: 28 }},
        'us-nv': {{ name: 'Nevada', value: 42 }},
        'us-ar': {{ name: 'Arkansas', value: 24 }},
        'us-ms': {{ name: 'Mississippi', value: 22 }},
        'us-ks': {{ name: 'Kansas', value: 26 }},
        'us-nm': {{ name: 'New Mexico', value: 18 }},
        'us-ne': {{ name: 'Nebraska', value: 16 }},
        'us-id': {{ name: 'Idaho', value: 14 }},
        'us-wv': {{ name: 'West Virginia', value: 12 }},
        'us-hi': {{ name: 'Hawaii', value: 28 }},
        'us-nh': {{ name: 'New Hampshire', value: 15 }},
        'us-me': {{ name: 'Maine', value: 12 }},
        'us-mt': {{ name: 'Montana', value: 10 }},
        'us-ri': {{ name: 'Rhode Island', value: 14 }},
        'us-de': {{ name: 'Delaware', value: 12 }},
        'us-sd': {{ name: 'South Dakota', value: 8 }},
        'us-nd': {{ name: 'North Dakota', value: 7 }},
        'us-ak': {{ name: 'Alaska', value: 18 }},
        'us-vt': {{ name: 'Vermont', value: 8 }},
        'us-wy': {{ name: 'Wyoming', value: 6 }}
    }};

    var cityDrilldowns = {{
        'us-ca': {{ name: 'California', data: [['Los Angeles', 85], ['San Francisco', 62], ['San Diego', 38], ['San Jose', 32], ['Sacramento', 18], ['Other', 10]] }},
        'us-tx': {{ name: 'Texas', data: [['Houston', 68], ['Dallas', 52], ['Austin', 42], ['San Antonio', 24], ['Fort Worth', 12]] }},
        'us-fl': {{ name: 'Florida', data: [['Miami', 58], ['Orlando', 35], ['Tampa', 28], ['Jacksonville', 22], ['Other', 13]] }},
        'us-ny': {{ name: 'New York', data: [['New York City', 165], ['Buffalo', 18], ['Rochester', 15], ['Albany', 12], ['Other', 5]] }},
        'us-il': {{ name: 'Illinois', data: [['Chicago', 72], ['Aurora', 8], ['Naperville', 7], ['Springfield', 6], ['Other', 5]] }},
        'us-pa': {{ name: 'Pennsylvania', data: [['Philadelphia', 52], ['Pittsburgh', 22], ['Allentown', 8], ['Other', 5]] }},
        'us-wa': {{ name: 'Washington', data: [['Seattle', 78], ['Spokane', 15], ['Tacoma', 12], ['Other', 7]] }},
        'us-ma': {{ name: 'Massachusetts', data: [['Boston', 58], ['Worcester', 10], ['Cambridge', 7], ['Other', 3]] }},
        'us-ga': {{ name: 'Georgia', data: [['Atlanta', 65], ['Augusta', 12], ['Savannah', 8], ['Other', 4]] }},
        'us-co': {{ name: 'Colorado', data: [['Denver', 45], ['Colorado Springs', 12], ['Boulder', 7], ['Other', 3]] }},
        'us-oh': {{ name: 'Ohio', data: [['Columbus', 28], ['Cleveland', 22], ['Cincinnati', 18], ['Other', 8]] }},
        'us-mi': {{ name: 'Michigan', data: [['Detroit', 32], ['Grand Rapids', 18], ['Ann Arbor', 12], ['Other', 6]] }},
        'us-nc': {{ name: 'North Carolina', data: [['Charlotte', 32], ['Raleigh', 22], ['Durham', 12], ['Other', 6]] }},
        'us-nj': {{ name: 'New Jersey', data: [['Newark', 35], ['Jersey City', 28], ['Trenton', 18], ['Other', 13]] }},
        'us-va': {{ name: 'Virginia', data: [['Virginia Beach', 22], ['Richmond', 20], ['Norfolk', 15], ['Other', 8]] }},
        'us-az': {{ name: 'Arizona', data: [['Phoenix', 32], ['Tucson', 15], ['Scottsdale', 8], ['Other', 3]] }}
    }};

    // Level 1: all 50 states colored by their region (4-color categorical choropleth)
    var level1Data = Object.keys(stateRegions).map(function(key) {{
        var region = stateRegions[key];
        return {{
            'hc-key': key,
            color: REGION_COLORS[region],
            value: regionSales[region],
            drilldown: region,
            regionName: regionNames[region]
        }};
    }});

    var chart = Highcharts.mapChart('container', {{
        chart: {{
            width: 3200,
            height: 1800,
            backgroundColor: '{PAGE_BG}',
            spacing: [80, 60, 80, 60],
            events: {{
                drilldown: function(e) {{
                    if (!e.seriesOptions && e.point && e.point.drilldown) {{
                        var drilldownId = e.point.drilldown;
                        var regionKeys = ['west', 'south', 'midwest', 'northeast'];
                        var isRegion = regionKeys.indexOf(drilldownId) !== -1;

                        if (isRegion) {{
                            // Level 2: Region → States bar chart
                            var states = regionStateList[drilldownId];
                            var stateChartData = states
                                .filter(function(key) {{ return !!allStateData[key]; }})
                                .map(function(key) {{
                                    var state = allStateData[key];
                                    return {{
                                        name: state.name,
                                        y: state.value,
                                        drilldown: cityDrilldowns[key] ? key : null
                                    }};
                                }})
                                .sort(function(a, b) {{ return b.y - a.y; }});

                            chart.addSeriesAsDrilldown(e.point, {{
                                type: 'column',
                                name: regionNames[drilldownId] + ' Region',
                                data: stateChartData,
                                colorByPoint: false,
                                color: REGION_COLORS[drilldownId],
                                dataLabels: {{
                                    enabled: true,
                                    format: '${{point.y}}M',
                                    style: {{
                                        fontSize: '26px',
                                        color: '{INK}',
                                        textOutline: 'none',
                                        fontWeight: 'bold'
                                    }}
                                }}
                            }});
                        }} else {{
                            // Level 3: State → Cities bar chart
                            var cityData = cityDrilldowns[drilldownId];
                            if (cityData) {{
                                chart.addSeriesAsDrilldown(e.point, {{
                                    type: 'column',
                                    name: cityData.name + ' Cities',
                                    data: cityData.data.map(function(item) {{
                                        return {{ name: item[0], y: item[1] }};
                                    }}),
                                    colorByPoint: false,
                                    color: '#009E73',
                                    dataLabels: {{
                                        enabled: true,
                                        format: '${{point.y}}M',
                                        style: {{
                                            fontSize: '26px',
                                            color: '{INK}',
                                            textOutline: 'none',
                                            fontWeight: 'bold'
                                        }}
                                    }}
                                }});
                            }}
                        }}
                    }}
                }}
            }}
        }},
        title: {{
            text: 'map-drilldown-geographic · python · highcharts · anyplot.ai',
            style: {{
                fontSize: '56px',
                fontWeight: 'bold',
                color: '{INK}'
            }},
            y: 50
        }},
        subtitle: {{
            text: 'US Regional Sales ($M) — Click a region to drill into states, then cities',
            style: {{
                fontSize: '36px',
                color: '{INK_SOFT}'
            }},
            y: 110
        }},
        mapNavigation: {{
            enabled: false
        }},
        legend: {{
            enabled: true,
            layout: 'horizontal',
            align: 'center',
            verticalAlign: 'bottom',
            floating: false,
            backgroundColor: '{ELEVATED_BG}',
            borderWidth: 1,
            borderColor: '{INK_SOFT}',
            padding: 24,
            itemStyle: {{
                fontSize: '36px',
                color: '{INK_SOFT}',
                fontWeight: 'normal'
            }},
            symbolRadius: 4
        }},
        tooltip: {{
            backgroundColor: '{ELEVATED_BG}',
            style: {{
                fontSize: '32px',
                color: '{INK}'
            }},
            headerFormat: '',
            pointFormat: '<b>{{point.regionName}} Region</b><br/>Total Sales: ${{point.value}}M<br/><i style="color:{INK_SOFT}">Click to explore states</i>'
        }},
        credits: {{
            enabled: false
        }},
        plotOptions: {{
            map: {{
                cursor: 'pointer',
                states: {{
                    hover: {{
                        brightness: 0.1
                    }}
                }},
                dataLabels: {{
                    enabled: false
                }},
                borderColor: '{PAGE_BG}',
                borderWidth: 1.5,
                nullColor: '{INK_SOFT}'
            }},
            column: {{
                borderRadius: 4,
                cursor: 'pointer',
                groupPadding: 0.08,
                pointPadding: 0.04
            }}
        }},
        xAxis: {{
            lineColor: '{INK_SOFT}',
            tickColor: '{INK_SOFT}',
            labels: {{
                style: {{
                    fontSize: '30px',
                    color: '{INK_SOFT}'
                }},
                rotation: -40
            }},
            title: {{
                style: {{
                    fontSize: '40px',
                    color: '{INK}'
                }}
            }}
        }},
        yAxis: {{
            title: {{
                text: 'Sales ($M)',
                style: {{
                    fontSize: '40px',
                    color: '{INK}'
                }}
            }},
            labels: {{
                style: {{
                    fontSize: '30px',
                    color: '{INK_SOFT}'
                }},
                formatter: function() {{
                    return '$' + this.value + 'M';
                }}
            }},
            gridLineColor: 'rgba(128,128,128,0.10)'
        }},
        drilldown: {{
            breadcrumbs: {{
                position: {{
                    align: 'left',
                    x: 60,
                    y: 20
                }},
                style: {{
                    fontSize: '28px',
                    color: '{INK_SOFT}'
                }},
                buttonTheme: {{
                    style: {{
                        fontSize: '28px',
                        color: '{INK}',
                        fontWeight: 'bold'
                    }},
                    states: {{
                        hover: {{
                            fill: '{ELEVATED_BG}'
                        }}
                    }}
                }},
                showFullPath: true
            }},
            activeAxisLabelStyle: {{
                textDecoration: 'none',
                fontStyle: 'normal',
                fontSize: '26px',
                color: '{INK}'
            }},
            activeDataLabelStyle: {{
                textDecoration: 'none',
                fontStyle: 'normal',
                fontSize: '26px',
                color: '{INK}'
            }}
        }},
        series: [{{
            type: 'map',
            mapData: topology,
            name: 'US Regions',
            data: level1Data,
            joinBy: 'hc-key',
            allowPointSelect: true
        }}]
    }});
}})();
"""

# Inline HTML for headless Chrome screenshot
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highmaps_js}</script>
    <script>{drilldown_js}</script>
</head>
<body style="margin:0; padding:0; background:{PAGE_BG};">
    <div id="container" style="width: 3200px; height: 1800px;"></div>
    <script>
        var topology = {us_topo};
        {chart_config}
    </script>
</body>
</html>"""

# Standalone HTML with CDN links for interactive use
standalone_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://cdn.jsdelivr.net/npm/highcharts/highmaps.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/highcharts/modules/drilldown.js"></script>
</head>
<body style="margin:0; padding:0; background:{PAGE_BG};">
    <div id="container" style="width: 100%; height: 100vh; min-height: 600px;"></div>
    <script>
        fetch('https://cdn.jsdelivr.net/npm/@highcharts/map-collection/countries/us/us-all.topo.json')
            .then(function(r) {{ return r.json(); }})
            .then(function(topology) {{
                {chart_config}
            }});
    </script>
</body>
</html>"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(standalone_html)

# Take screenshot via headless Chrome
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
time.sleep(8)  # Maps need extra time to render topology
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# Pin to exact canvas dims so post-render gate passes
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
