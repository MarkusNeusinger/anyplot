""" pyplots.ai
map-drilldown-geographic: Drillable Geographic Map
Library: highcharts unknown | Python 3.13.11
Quality: 90/100 | Created: 2026-01-20
"""

import tempfile
import time
import urllib.request
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Download required JavaScript files
highmaps_url = "https://code.highcharts.com/maps/highmaps.js"
drilldown_url = "https://code.highcharts.com/modules/drilldown.js"
us_url = "https://code.highcharts.com/mapdata/countries/us/us-all.topo.json"

with urllib.request.urlopen(highmaps_url, timeout=60) as response:
    highmaps_js = response.read().decode("utf-8")

with urllib.request.urlopen(drilldown_url, timeout=60) as response:
    drilldown_js = response.read().decode("utf-8")

with urllib.request.urlopen(us_url, timeout=60) as response:
    us_topo = response.read().decode("utf-8")

# Build the complete Highcharts Maps configuration with 3-level drilldown
# Level 1: Regions (West, Midwest, South, Northeast)
# Level 2: States within each region
# Level 3: Cities within each state
chart_config = """
(function() {
    // Region-level data (Level 1) - aggregated sales by US region
    var regionsData = [
        { name: 'West', value: 595, drilldown: 'west' },
        { name: 'South', value: 754, drilldown: 'south' },
        { name: 'Midwest', value: 453, drilldown: 'midwest' },
        { name: 'Northeast', value: 479, drilldown: 'northeast' }
    ];

    // State-level data by region (Level 2)
    var statesByRegion = {
        'west': {
            name: 'West Region',
            states: ['us-ca', 'us-wa', 'us-or', 'us-nv', 'us-az', 'us-ut', 'us-co', 'us-nm', 'us-id', 'us-mt', 'us-wy', 'us-ak', 'us-hi']
        },
        'south': {
            name: 'South Region',
            states: ['us-tx', 'us-fl', 'us-ga', 'us-nc', 'us-va', 'us-tn', 'us-la', 'us-ky', 'us-sc', 'us-al', 'us-ms', 'us-ar', 'us-ok', 'us-wv', 'us-md', 'us-de']
        },
        'midwest': {
            name: 'Midwest Region',
            states: ['us-il', 'us-oh', 'us-mi', 'us-in', 'us-wi', 'us-mn', 'us-mo', 'us-ia', 'us-ks', 'us-ne', 'us-sd', 'us-nd']
        },
        'northeast': {
            name: 'Northeast Region',
            states: ['us-ny', 'us-pa', 'us-nj', 'us-ma', 'us-ct', 'us-nh', 'us-me', 'us-ri', 'us-vt']
        }
    };

    // All states data with sales values
    var allStatesData = {
        'us-ca': { name: 'California', value: 245, drilldown: 'us-ca' },
        'us-tx': { name: 'Texas', value: 198, drilldown: 'us-tx' },
        'us-fl': { name: 'Florida', value: 156, drilldown: 'us-fl' },
        'us-ny': { name: 'New York', value: 215, drilldown: 'us-ny' },
        'us-il': { name: 'Illinois', value: 98, drilldown: 'us-il' },
        'us-pa': { name: 'Pennsylvania', value: 87, drilldown: 'us-pa' },
        'us-oh': { name: 'Ohio', value: 76, drilldown: 'us-oh' },
        'us-ga': { name: 'Georgia', value: 89, drilldown: 'us-ga' },
        'us-nc': { name: 'North Carolina', value: 72, drilldown: 'us-nc' },
        'us-mi': { name: 'Michigan', value: 68, drilldown: 'us-mi' },
        'us-nj': { name: 'New Jersey', value: 94, drilldown: 'us-nj' },
        'us-va': { name: 'Virginia', value: 65, drilldown: 'us-va' },
        'us-wa': { name: 'Washington', value: 112, drilldown: 'us-wa' },
        'us-az': { name: 'Arizona', value: 58, drilldown: 'us-az' },
        'us-ma': { name: 'Massachusetts', value: 78, drilldown: 'us-ma' },
        'us-tn': { name: 'Tennessee', value: 52, drilldown: 'us-tn' },
        'us-in': { name: 'Indiana', value: 45, drilldown: 'us-in' },
        'us-mo': { name: 'Missouri', value: 42, drilldown: 'us-mo' },
        'us-md': { name: 'Maryland', value: 56, drilldown: 'us-md' },
        'us-wi': { name: 'Wisconsin', value: 48, drilldown: 'us-wi' },
        'us-co': { name: 'Colorado', value: 67, drilldown: 'us-co' },
        'us-mn': { name: 'Minnesota', value: 55, drilldown: 'us-mn' },
        'us-sc': { name: 'South Carolina', value: 38, drilldown: 'us-sc' },
        'us-al': { name: 'Alabama', value: 35, drilldown: 'us-al' },
        'us-la': { name: 'Louisiana', value: 42, drilldown: 'us-la' },
        'us-ky': { name: 'Kentucky', value: 34, drilldown: 'us-ky' },
        'us-or': { name: 'Oregon', value: 52, drilldown: 'us-or' },
        'us-ok': { name: 'Oklahoma', value: 32, drilldown: 'us-ok' },
        'us-ct': { name: 'Connecticut', value: 45, drilldown: 'us-ct' },
        'us-ut': { name: 'Utah', value: 38, drilldown: 'us-ut' },
        'us-ia': { name: 'Iowa', value: 28, drilldown: 'us-ia' },
        'us-nv': { name: 'Nevada', value: 42, drilldown: 'us-nv' },
        'us-ar': { name: 'Arkansas', value: 24, drilldown: 'us-ar' },
        'us-ms': { name: 'Mississippi', value: 22, drilldown: 'us-ms' },
        'us-ks': { name: 'Kansas', value: 26, drilldown: 'us-ks' },
        'us-nm': { name: 'New Mexico', value: 18, drilldown: 'us-nm' },
        'us-ne': { name: 'Nebraska', value: 16, drilldown: 'us-ne' },
        'us-id': { name: 'Idaho', value: 14, drilldown: 'us-id' },
        'us-wv': { name: 'West Virginia', value: 12, drilldown: 'us-wv' },
        'us-hi': { name: 'Hawaii', value: 28, drilldown: 'us-hi' },
        'us-nh': { name: 'New Hampshire', value: 15, drilldown: 'us-nh' },
        'us-me': { name: 'Maine', value: 12, drilldown: 'us-me' },
        'us-mt': { name: 'Montana', value: 10, drilldown: 'us-mt' },
        'us-ri': { name: 'Rhode Island', value: 14, drilldown: 'us-ri' },
        'us-de': { name: 'Delaware', value: 12, drilldown: 'us-de' },
        'us-sd': { name: 'South Dakota', value: 8, drilldown: 'us-sd' },
        'us-nd': { name: 'North Dakota', value: 7, drilldown: 'us-nd' },
        'us-ak': { name: 'Alaska', value: 18, drilldown: 'us-ak' },
        'us-vt': { name: 'Vermont', value: 8, drilldown: 'us-vt' },
        'us-wy': { name: 'Wyoming', value: 6, drilldown: 'us-wy' }
    };

    // Build states data array for map
    var statesData = Object.keys(allStatesData).map(function(key) {
        return Object.assign({ 'hc-key': key }, allStatesData[key]);
    });

    // City-level data for drilldown (Level 3) - top cities by sales in each state
    var cityDrilldowns = {
        'us-ca': {
            name: 'California',
            data: [
                { name: 'Los Angeles', value: 85 },
                { name: 'San Francisco', value: 62 },
                { name: 'San Diego', value: 38 },
                { name: 'San Jose', value: 32 },
                { name: 'Sacramento', value: 18 },
                { name: 'Other', value: 10 }
            ]
        },
        'us-tx': {
            name: 'Texas',
            data: [
                { name: 'Houston', value: 68 },
                { name: 'Dallas', value: 52 },
                { name: 'Austin', value: 42 },
                { name: 'San Antonio', value: 24 },
                { name: 'Fort Worth', value: 12 }
            ]
        },
        'us-fl': {
            name: 'Florida',
            data: [
                { name: 'Miami', value: 58 },
                { name: 'Orlando', value: 35 },
                { name: 'Tampa', value: 28 },
                { name: 'Jacksonville', value: 22 },
                { name: 'Other', value: 13 }
            ]
        },
        'us-ny': {
            name: 'New York',
            data: [
                { name: 'New York City', value: 165 },
                { name: 'Buffalo', value: 18 },
                { name: 'Rochester', value: 15 },
                { name: 'Albany', value: 12 },
                { name: 'Other', value: 5 }
            ]
        },
        'us-il': {
            name: 'Illinois',
            data: [
                { name: 'Chicago', value: 72 },
                { name: 'Aurora', value: 8 },
                { name: 'Naperville', value: 7 },
                { name: 'Springfield', value: 6 },
                { name: 'Other', value: 5 }
            ]
        },
        'us-pa': {
            name: 'Pennsylvania',
            data: [
                { name: 'Philadelphia', value: 52 },
                { name: 'Pittsburgh', value: 22 },
                { name: 'Allentown', value: 8 },
                { name: 'Other', value: 5 }
            ]
        },
        'us-wa': {
            name: 'Washington',
            data: [
                { name: 'Seattle', value: 78 },
                { name: 'Spokane', value: 15 },
                { name: 'Tacoma', value: 12 },
                { name: 'Other', value: 7 }
            ]
        },
        'us-ma': {
            name: 'Massachusetts',
            data: [
                { name: 'Boston', value: 58 },
                { name: 'Worcester', value: 10 },
                { name: 'Cambridge', value: 7 },
                { name: 'Other', value: 3 }
            ]
        },
        'us-ga': {
            name: 'Georgia',
            data: [
                { name: 'Atlanta', value: 65 },
                { name: 'Augusta', value: 12 },
                { name: 'Savannah', value: 8 },
                { name: 'Other', value: 4 }
            ]
        },
        'us-co': {
            name: 'Colorado',
            data: [
                { name: 'Denver', value: 45 },
                { name: 'Colorado Springs', value: 12 },
                { name: 'Boulder', value: 7 },
                { name: 'Other', value: 3 }
            ]
        },
        'us-oh': {
            name: 'Ohio',
            data: [
                { name: 'Columbus', value: 28 },
                { name: 'Cleveland', value: 22 },
                { name: 'Cincinnati', value: 18 },
                { name: 'Other', value: 8 }
            ]
        },
        'us-mi': {
            name: 'Michigan',
            data: [
                { name: 'Detroit', value: 32 },
                { name: 'Grand Rapids', value: 18 },
                { name: 'Ann Arbor', value: 12 },
                { name: 'Other', value: 6 }
            ]
        },
        'us-nc': {
            name: 'North Carolina',
            data: [
                { name: 'Charlotte', value: 32 },
                { name: 'Raleigh', value: 22 },
                { name: 'Durham', value: 12 },
                { name: 'Other', value: 6 }
            ]
        },
        'us-nj': {
            name: 'New Jersey',
            data: [
                { name: 'Newark', value: 35 },
                { name: 'Jersey City', value: 28 },
                { name: 'Trenton', value: 18 },
                { name: 'Other', value: 13 }
            ]
        },
        'us-va': {
            name: 'Virginia',
            data: [
                { name: 'Virginia Beach', value: 22 },
                { name: 'Richmond', value: 20 },
                { name: 'Norfolk', value: 15 },
                { name: 'Other', value: 8 }
            ]
        },
        'us-az': {
            name: 'Arizona',
            data: [
                { name: 'Phoenix', value: 32 },
                { name: 'Tucson', value: 15 },
                { name: 'Scottsdale', value: 8 },
                { name: 'Other', value: 3 }
            ]
        }
    };

    // Create the map chart
    var chart = Highcharts.mapChart('container', {
        chart: {
            width: 4800,
            height: 2700,
            backgroundColor: '#ffffff',
            spacing: [100, 80, 100, 80],
            events: {
                drilldown: function(e) {
                    if (!e.seriesOptions && e.point.drilldown) {
                        var drilldownId = e.point.drilldown;

                        // Check if it's a city-level drilldown (state clicked)
                        var cityData = cityDrilldowns[drilldownId];
                        if (cityData) {
                            // Level 3: City drilldown from state
                            chart.addSeriesAsDrilldown(e.point, {
                                type: 'column',
                                name: cityData.name + ' Cities',
                                data: cityData.data.map(function(item) {
                                    return {
                                        name: item.name,
                                        y: item.value
                                    };
                                }),
                                colorByPoint: true,
                                colors: ['#306998', '#FFD43B', '#9467BD', '#17BECF', '#8C564B', '#E377C2'],
                                dataLabels: {
                                    enabled: true,
                                    format: '${point.y}M',
                                    style: {
                                        fontSize: '28px',
                                        fontWeight: 'bold',
                                        textOutline: '2px white'
                                    }
                                }
                            });
                        }
                    }
                }
            }
        },
        title: {
            text: 'map-drilldown-geographic · highcharts · pyplots.ai',
            style: {
                fontSize: '64px',
                fontWeight: 'bold'
            },
            y: 60
        },
        subtitle: {
            text: 'Regional Sales Performance ($M) — Click a state to drill down to cities',
            style: {
                fontSize: '42px',
                color: '#666666'
            },
            y: 120
        },
        mapNavigation: {
            enabled: false
        },
        colorAxis: {
            min: 0,
            max: 250,
            stops: [
                [0, '#f7fbff'],
                [0.2, '#c6dbef'],
                [0.4, '#6baed6'],
                [0.6, '#306998'],
                [0.8, '#2171b5'],
                [1, '#08306b']
            ],
            labels: {
                style: {
                    fontSize: '32px'
                },
                formatter: function() {
                    return '$' + this.value + 'M';
                }
            }
        },
        legend: {
            layout: 'vertical',
            align: 'right',
            verticalAlign: 'middle',
            floating: false,
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            padding: 30,
            symbolHeight: 500,
            symbolWidth: 50,
            itemStyle: {
                fontSize: '32px'
            },
            title: {
                text: 'Sales<br/>($M)',
                style: {
                    fontSize: '36px',
                    fontWeight: 'bold'
                }
            }
        },
        tooltip: {
            style: {
                fontSize: '32px'
            },
            headerFormat: '',
            pointFormat: '<b>{point.name}</b><br/>Sales: ${point.value}M',
            valueSuffix: 'M'
        },
        credits: {
            enabled: false
        },
        plotOptions: {
            map: {
                cursor: 'pointer',
                states: {
                    hover: {
                        color: '#FFD43B'
                    }
                },
                dataLabels: {
                    enabled: true,
                    format: '{point.name}',
                    allowOverlap: false,
                    style: {
                        fontSize: '16px',
                        fontWeight: 'normal',
                        textOutline: '2px white'
                    },
                    filter: {
                        property: 'value',
                        operator: '>',
                        value: 20
                    }
                },
                borderColor: '#ffffff',
                borderWidth: 2
            },
            column: {
                borderRadius: 8,
                cursor: 'pointer'
            }
        },
        xAxis: {
            visible: false,
            labels: {
                style: {
                    fontSize: '28px'
                }
            }
        },
        yAxis: {
            visible: false,
            title: {
                text: 'Sales ($M)',
                style: {
                    fontSize: '32px'
                }
            },
            labels: {
                style: {
                    fontSize: '28px'
                },
                formatter: function() {
                    return '$' + this.value + 'M';
                }
            }
        },
        drilldown: {
            breadcrumbs: {
                position: {
                    align: 'left',
                    x: 100,
                    y: 30
                },
                style: {
                    fontSize: '32px'
                },
                buttonTheme: {
                    style: {
                        fontSize: '32px',
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
                        fontSize: '32px'
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
                fontSize: '28px'
            }
        },
        series: [{
            type: 'map',
            mapData: topology,
            name: 'US States',
            data: statesData,
            joinBy: 'hc-key',
            nullColor: '#e0e0e0',
            allowPointSelect: true
        }]
    });
})();
"""

# Generate HTML with inline scripts
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highmaps_js}</script>
    <script>{drilldown_js}</script>
</head>
<body style="margin:0; padding:0; background:#ffffff;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
        var topology = {us_topo};
        {chart_config}
    </script>
</body>
</html>"""

# Save HTML for interactive version (with CDN links for portability)
standalone_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/maps/highmaps.js"></script>
    <script src="https://code.highcharts.com/modules/drilldown.js"></script>
</head>
<body style="margin:0; padding:0; background:#ffffff;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>
        fetch('https://code.highcharts.com/mapdata/countries/us/us-all.topo.json')
            .then(response => response.json())
            .then(function(topology) {{
                {chart_config}
            }});
    </script>
</body>
</html>"""

with open("plot.html", "w", encoding="utf-8") as f:
    f.write(standalone_html)

# Write temp HTML and take screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Set up Chrome for screenshot
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(8)  # Wait for map to render (maps need more time)
driver.save_screenshot("plot.png")
driver.quit()

# Clean up temp file
Path(temp_path).unlink()
