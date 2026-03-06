""" pyplots.ai
genome-track-multi: Genome Track Viewer
Library: highcharts unknown | Python 3.14.3
Quality: 89/100 | Created: 2026-03-06
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Synthetic genomic data for chr17:7,570,000-7,592,000 (TP53 locus)
np.random.seed(42)

region_start = 7570000
region_end = 7592000

# Gene track - TP53 gene structure (simplified)
exons = [
    {"start": 7571720, "end": 7573008, "label": "Exon 11"},
    {"start": 7573927, "end": 7574033, "label": "Exon 10"},
    {"start": 7576525, "end": 7576657, "label": "Exon 9"},
    {"start": 7576853, "end": 7576926, "label": "Exon 8"},
    {"start": 7577019, "end": 7577155, "label": "Exon 7"},
    {"start": 7577499, "end": 7577608, "label": "Exon 6"},
    {"start": 7578177, "end": 7578289, "label": "Exon 5"},
    {"start": 7578371, "end": 7578554, "label": "Exon 4"},
    {"start": 7579312, "end": 7579590, "label": "Exon 3"},
    {"start": 7579700, "end": 7579721, "label": "Exon 2"},
    {"start": 7590695, "end": 7590863, "label": "Exon 1"},
]

# Coverage track - simulated read depth across the region
coverage_positions = np.arange(region_start, region_end, 50)
base_coverage = 30 + np.random.poisson(5, len(coverage_positions))
for exon in exons:
    mask = (coverage_positions >= exon["start"]) & (coverage_positions <= exon["end"])
    base_coverage[mask] = base_coverage[mask] + np.random.poisson(40, mask.sum())

coverage_data = [[int(pos), int(cov)] for pos, cov in zip(coverage_positions, base_coverage, strict=False)]

# Variant track - SNPs and indels
variants = [
    {"pos": 7572950, "type": "SNP", "id": "rs28934578", "qual": 85},
    {"pos": 7573160, "type": "SNP", "id": "rs1042522", "qual": 99},
    {"pos": 7574003, "type": "SNP", "id": "rs587782144", "qual": 72},
    {"pos": 7576850, "type": "Indel", "id": "rs786201838", "qual": 60},
    {"pos": 7577094, "type": "SNP", "id": "rs28934576", "qual": 91},
    {"pos": 7577539, "type": "SNP", "id": "rs11540652", "qual": 95},
    {"pos": 7578190, "type": "SNP", "id": "rs121912651", "qual": 78},
    {"pos": 7578406, "type": "Indel", "id": "rs587781525", "qual": 55},
    {"pos": 7579472, "type": "SNP", "id": "rs121913343", "qual": 88},
    {"pos": 7590800, "type": "SNP", "id": "rs1800370", "qual": 93},
]

snp_data = [{"x": v["pos"], "y": v["qual"], "name": v["id"]} for v in variants if v["type"] == "SNP"]
indel_data = [{"x": v["pos"], "y": v["qual"], "name": v["id"]} for v in variants if v["type"] == "Indel"]

# Regulatory track - enhancers and promoters
regulatory = [
    {"start": 7571200, "end": 7571700, "type": "Enhancer", "score": 0.75},
    {"start": 7576100, "end": 7576500, "type": "Enhancer", "score": 0.60},
    {"start": 7579800, "end": 7580200, "type": "Promoter", "score": 0.50},
    {"start": 7589900, "end": 7590700, "type": "Promoter", "score": 0.92},
    {"start": 7584000, "end": 7584600, "type": "Enhancer", "score": 0.45},
]

# Build arearange data for exons (rectangles via 2-point segments separated by nulls)
exon_arearange = []
sorted_exons = sorted(exons, key=lambda e: e["start"])
for i, exon in enumerate(sorted_exons):
    if i > 0:
        exon_arearange.append([sorted_exons[i - 1]["end"] + 1, None, None])
    exon_arearange.append([exon["start"], 0.2, 0.8])
    exon_arearange.append([exon["end"], 0.2, 0.8])

# Build intron line data (chevron pattern between exons)
intron_data = []
for i in range(len(sorted_exons) - 1):
    intron_data.append([sorted_exons[i]["end"], 0.5])
    mid = (sorted_exons[i]["end"] + sorted_exons[i + 1]["start"]) // 2
    intron_data.append([mid, 0.62])
    intron_data.append([sorted_exons[i + 1]["start"], 0.5])

# Build arearange data for regulatory elements
enhancer_arearange = []
for i, r in enumerate([reg for reg in regulatory if reg["type"] == "Enhancer"]):
    if i > 0:
        enhancer_arearange.append([r["start"] - 1, None, None])
    enhancer_arearange.append([r["start"], 0.1, 0.45])
    enhancer_arearange.append([r["end"], 0.1, 0.45])

promoter_arearange = []
for i, r in enumerate([reg for reg in regulatory if reg["type"] == "Promoter"]):
    if i > 0:
        promoter_arearange.append([r["start"] - 1, None, None])
    promoter_arearange.append([r["start"], 0.55, 0.9])
    promoter_arearange.append([r["end"], 0.55, 0.9])

# Serialize data to JSON
coverage_json = json.dumps(coverage_data)
snp_json = json.dumps(snp_data)
indel_json = json.dumps(indel_data)
exon_arearange_json = json.dumps(exon_arearange)
intron_json = json.dumps(intron_data)
enhancer_arearange_json = json.dumps(enhancer_arearange)
promoter_arearange_json = json.dumps(promoter_arearange)

# Build exon plot bands for subtle vertical shading across all tracks
exon_plotbands = [{"from": e["start"], "to": e["end"], "color": "rgba(48, 105, 152, 0.04)"} for e in exons]
exon_plotbands_json = json.dumps(exon_plotbands)

chart_js = f"""
Highcharts.chart('container', {{
    chart: {{
        width: 4800,
        height: 2700,
        backgroundColor: '#ffffff',
        spacingTop: 60,
        spacingBottom: 180,
        spacingLeft: 160,
        spacingRight: 60,
        style: {{ fontFamily: 'Arial, sans-serif' }},
        events: {{
            load: function() {{
                var chart = this;
                // Draw track separator lines
                var plotLeft = chart.plotLeft;
                var plotWidth = chart.plotWidth;
                var yAxes = chart.yAxis;
                for (var i = 1; i < yAxes.length; i++) {{
                    var y = yAxes[i].top;
                    chart.renderer.path(['M', plotLeft, y - 8, 'L', plotLeft + plotWidth, y - 8])
                        .attr({{ stroke: '#DDDDDD', 'stroke-width': 2, 'stroke-dasharray': '8,4' }})
                        .add();
                }}
            }}
        }}
    }},

    title: {{
        text: 'TP53 Locus (chr17) \\u00b7 genome-track-multi \\u00b7 highcharts \\u00b7 pyplots.ai',
        style: {{ fontSize: '44px', fontWeight: '500' }}
    }},

    subtitle: {{
        text: 'chr17:7,570,000\\u20137,592,000 (GRCh38)',
        style: {{ fontSize: '28px', color: '#666666' }}
    }},

    credits: {{ enabled: false }},
    legend: {{ enabled: false }},

    xAxis: {{
        min: {region_start},
        max: {region_end},
        title: {{
            text: 'Genomic Position (chr17)',
            style: {{ fontSize: '28px' }}
        }},
        labels: {{
            style: {{ fontSize: '24px' }},
            y: 40,
            formatter: function() {{
                return (this.value / 1000000).toFixed(3) + ' Mb';
            }}
        }},
        lineWidth: 2,
        tickWidth: 0,
        tickInterval: 2000,
        gridLineWidth: 1,
        gridLineColor: 'rgba(0,0,0,0.06)',
        plotBands: {exon_plotbands_json}
    }},

    yAxis: [{{
        title: {{
            text: 'Genes',
            style: {{ fontSize: '26px', fontWeight: 'bold', color: '#306998' }},
            rotation: 0, align: 'high', offset: 0, y: -10, x: -10
        }},
        top: '0%', height: '16%', offset: 0,
        min: -0.1, max: 1.2,
        labels: {{ enabled: false }},
        gridLineWidth: 0, lineWidth: 0
    }}, {{
        title: {{
            text: 'Coverage',
            style: {{ fontSize: '26px', fontWeight: 'bold', color: '#306998' }},
            rotation: 0, align: 'high', offset: 0, y: -10, x: -10
        }},
        top: '22%', height: '28%', offset: 0, min: 0,
        labels: {{ style: {{ fontSize: '20px' }}, format: '{{value}}x' }},
        gridLineWidth: 1, gridLineColor: 'rgba(0,0,0,0.06)', lineWidth: 1
    }}, {{
        title: {{
            text: 'Variants',
            style: {{ fontSize: '26px', fontWeight: 'bold', color: '#306998' }},
            rotation: 0, align: 'high', offset: 0, y: -10, x: -10
        }},
        top: '56%', height: '18%', offset: 0, min: 0, max: 110,
        labels: {{ style: {{ fontSize: '20px' }} }},
        gridLineWidth: 1, gridLineColor: 'rgba(0,0,0,0.06)', lineWidth: 1
    }}, {{
        title: {{
            text: 'Regulatory',
            style: {{ fontSize: '26px', fontWeight: 'bold', color: '#306998' }},
            rotation: 0, align: 'high', offset: 0, y: -10, x: -10
        }},
        top: '80%', height: '14%', offset: 0,
        min: -0.1, max: 1.1,
        labels: {{ enabled: false }},
        gridLineWidth: 0, lineWidth: 0
    }}],

    tooltip: {{
        style: {{ fontSize: '20px' }},
        shared: false,
        useHTML: true
    }},

    plotOptions: {{
        series: {{
            animation: false,
            states: {{ hover: {{ lineWidthPlus: 0 }} }}
        }},
        arearange: {{
            lineWidth: 0,
            marker: {{ enabled: false }}
        }}
    }},

    series: [
        // Gene track - exons as filled rectangles
        {{
            type: 'arearange',
            name: 'Exons',
            yAxis: 0,
            data: {exon_arearange_json},
            color: '#306998',
            fillOpacity: 1.0,
            lineWidth: 1,
            lineColor: '#1E4A6E',
            connectNulls: false,
            tooltip: {{ pointFormat: '<b>Exon</b>' }}
        }},
        // Gene track - intron chevron lines
        {{
            type: 'line',
            name: 'Introns',
            yAxis: 0,
            data: {intron_json},
            color: '#306998',
            lineWidth: 3,
            marker: {{ enabled: false }},
            enableMouseTracking: false
        }},
        // Gene label
        {{
            type: 'scatter',
            name: 'Gene Label',
            yAxis: 0,
            data: [{{ x: {(sorted_exons[0]["start"] + sorted_exons[-1]["end"]) // 2}, y: 1.05,
                dataLabels: {{ enabled: true, format: 'TP53 \\u25c0',
                    style: {{ fontSize: '28px', fontWeight: 'bold', color: '#306998', textOutline: 'none' }} }} }}],
            marker: {{ enabled: false }},
            enableMouseTracking: false
        }},

        // Coverage track
        {{
            type: 'areaspline',
            name: 'Read Depth',
            yAxis: 1,
            data: {coverage_json},
            color: '#306998',
            fillColor: {{
                linearGradient: {{ x1: 0, y1: 0, x2: 0, y2: 1 }},
                stops: [[0, 'rgba(48, 105, 152, 0.5)'], [1, 'rgba(48, 105, 152, 0.05)']]
            }},
            lineWidth: 2,
            marker: {{ enabled: false }},
            tooltip: {{ pointFormat: '<b>Coverage:</b> {{point.y}}x<br/>Position: {{point.x:,.0f}}' }}
        }},

        // Variant track - SNPs
        {{
            type: 'scatter',
            name: 'SNPs',
            yAxis: 2,
            data: {snp_json},
            color: '#E67E22',
            marker: {{ symbol: 'circle', radius: 14, lineWidth: 2, lineColor: '#D35400' }},
            tooltip: {{ pointFormat: '<b>{{point.name}}</b> (SNP)<br/>Quality: {{point.y}}<br/>Position: {{point.x:,.0f}}' }}
        }},
        // Variant track - Indels
        {{
            type: 'scatter',
            name: 'Indels',
            yAxis: 2,
            data: {indel_json},
            color: '#8E44AD',
            marker: {{ symbol: 'diamond', radius: 16, lineWidth: 2, lineColor: '#6C3483' }},
            tooltip: {{ pointFormat: '<b>{{point.name}}</b> (Indel)<br/>Quality: {{point.y}}<br/>Position: {{point.x:,.0f}}' }}
        }},
        // Variant stems (lollipop lines)
        {{
            type: 'columnrange',
            name: 'Stems',
            yAxis: 2,
            data: {json.dumps(snp_data + indel_data)}.map(function(v) {{
                return {{ x: v.x, low: 0, high: v.y }};
            }}),
            pointWidth: 3,
            color: '#BBBBBB',
            borderWidth: 0,
            enableMouseTracking: false
        }},

        // Regulatory track - Enhancers
        {{
            type: 'arearange',
            name: 'Enhancers',
            yAxis: 3,
            data: {enhancer_arearange_json},
            color: '#27AE60',
            fillOpacity: 0.7,
            lineWidth: 1,
            lineColor: '#1E8449',
            connectNulls: false,
            tooltip: {{ pointFormat: '<b>Enhancer</b>' }}
        }},
        // Regulatory track - Promoters
        {{
            type: 'arearange',
            name: 'Promoters',
            yAxis: 3,
            data: {promoter_arearange_json},
            color: '#C0392B',
            fillOpacity: 0.7,
            lineWidth: 1,
            lineColor: '#922B21',
            connectNulls: false,
            tooltip: {{ pointFormat: '<b>Promoter</b>' }}
        }},
        // Regulatory labels
        {{
            type: 'scatter',
            name: 'Legend',
            yAxis: 3,
            data: [
                {{ x: {region_start + 500}, y: 0.28, dataLabels: {{ enabled: true, format: '\\u25a0 Enhancer',
                    style: {{ fontSize: '22px', color: '#27AE60', fontWeight: 'bold', textOutline: 'none' }} }} }},
                {{ x: {region_start + 500}, y: 0.72, dataLabels: {{ enabled: true, format: '\\u25a0 Promoter',
                    style: {{ fontSize: '22px', color: '#C0392B', fontWeight: 'bold', textOutline: 'none' }} }} }}
            ],
            marker: {{ enabled: false }},
            enableMouseTracking: false
        }}
    ]
}});
"""

# Download Highcharts JS and highcharts-more for columnrange
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"
req = urllib.request.Request(highcharts_url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

highcharts_more_url = "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts-more.js"
req2 = urllib.request.Request(highcharts_more_url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req2, timeout=30) as response:
    highcharts_more_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
</head>
<body style="margin:0; padding:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
    {chart_js}
    </script>
</body>
</html>"""

# Write temp HTML file
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Save interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Take screenshot using Selenium
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(8)
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
