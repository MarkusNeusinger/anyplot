""" anyplot.ai
genome-track-multi: Genome Track Viewer
Library: highcharts unknown | Python 3.13.13
Quality: 90/100 | Updated: 2026-06-02
"""

import json
import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens (Imprint palette — theme-adaptive chrome)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette — genomic track assignments
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
COL_GENE = IMPRINT_PALETTE[0]  # brand green  — genes (first series)
COL_COVERAGE = IMPRINT_PALETTE[2]  # blue         — coverage
COL_SNP = IMPRINT_PALETTE[1]  # lavender     — SNPs
COL_INDEL = IMPRINT_PALETTE[4]  # matte red    — indels (mutation/error semantic)
COL_ENHANCER = IMPRINT_PALETTE[5]  # cyan         — enhancers
COL_PROMOTER = IMPRINT_PALETTE[3]  # ochre        — promoters

# Title — scale fontsize for length (default 66px @ 67 chars)
TITLE = "TP53 Locus (chr17) · genome-track-multi · python · highcharts · anyplot.ai"
TITLE_FS = max(44, round(66 * 67 / len(TITLE)))  # = 60px

SUBTITLE = "chr17:7,570,000–7,592,000 (GRCh38)"

# Data — TP53 locus on chr17
np.random.seed(42)
region_start = 7570000
region_end = 7592000

# Gene track: TP53 exon structure (simplified GRCh38 coordinates)
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

# Coverage track: simulated read depth — elevated at exons
coverage_positions = np.arange(region_start, region_end, 50)
base_coverage = 30 + np.random.poisson(5, len(coverage_positions))
for exon in exons:
    mask = (coverage_positions >= exon["start"]) & (coverage_positions <= exon["end"])
    base_coverage[mask] = base_coverage[mask] + np.random.poisson(40, mask.sum())
coverage_data = [[int(pos), int(cov)] for pos, cov in zip(coverage_positions, base_coverage, strict=False)]

# Variant track: SNPs and indels with PHRED quality scores
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

# Regulatory track: enhancers and promoters
regulatory = [
    {"start": 7571200, "end": 7571700, "type": "Enhancer"},
    {"start": 7576100, "end": 7576500, "type": "Enhancer"},
    {"start": 7579800, "end": 7580200, "type": "Promoter"},
    {"start": 7589900, "end": 7590700, "type": "Promoter"},
    {"start": 7584000, "end": 7584600, "type": "Enhancer"},
]

# Build arearange arrays (rectangles via 2-point segments separated by nulls)
sorted_exons = sorted(exons, key=lambda e: e["start"])
exon_arearange = []
for i, exon in enumerate(sorted_exons):
    if i > 0:
        exon_arearange.append([sorted_exons[i - 1]["end"] + 1, None, None])
    exon_arearange.append([exon["start"], 0.2, 0.8])
    exon_arearange.append([exon["end"], 0.2, 0.8])

# Intron chevron pattern (mid-point bump = direction indicator)
intron_data = []
for i in range(len(sorted_exons) - 1):
    intron_data.append([sorted_exons[i]["end"], 0.5])
    mid = (sorted_exons[i]["end"] + sorted_exons[i + 1]["start"]) // 2
    intron_data.append([mid, 0.62])
    intron_data.append([sorted_exons[i + 1]["start"], 0.5])

enhancer_arearange = []
for i, r in enumerate([x for x in regulatory if x["type"] == "Enhancer"]):
    if i > 0:
        enhancer_arearange.append([r["start"] - 1, None, None])
    enhancer_arearange.append([r["start"], 0.1, 0.45])
    enhancer_arearange.append([r["end"], 0.1, 0.45])

promoter_arearange = []
for i, r in enumerate([x for x in regulatory if x["type"] == "Promoter"]):
    if i > 0:
        promoter_arearange.append([r["start"] - 1, None, None])
    promoter_arearange.append([r["start"], 0.55, 0.9])
    promoter_arearange.append([r["end"], 0.55, 0.9])

# Exon plot bands — subtle cross-track shading aligned to gene positions
plotband_color = "rgba(0,158,115,0.06)" if THEME == "light" else "rgba(0,158,115,0.10)"
exon_plotbands = [{"from": e["start"], "to": e["end"], "color": plotband_color} for e in exons]

# Pre-compute inline label positions
gene_label_x = (sorted_exons[0]["start"] + sorted_exons[-1]["end"]) // 2
legend_snp_x = region_start + 600
legend_indel_x = region_start + 3200
legend_reg_x = region_start + 400

# Coverage gradient stops (#4467A3 = rgb(68,103,163))
cov_hi = "rgba(68,103,163,0.55)"
cov_lo = "rgba(68,103,163,0.04)"

# Serialize data for JS injection
coverage_json = json.dumps(coverage_data)
snp_json = json.dumps(snp_data)
indel_json = json.dumps(indel_data)
all_variants_json = json.dumps(snp_data + indel_data)
exon_arearange_json = json.dumps(exon_arearange)
intron_json = json.dumps(intron_data)
enhancer_arearange_json = json.dumps(enhancer_arearange)
promoter_arearange_json = json.dumps(promoter_arearange)
exon_plotbands_json = json.dumps(exon_plotbands)

# Chart JavaScript — raw JS for multi-yAxis complexity
chart_js = f"""
Highcharts.chart('container', {{
    chart: {{
        width: 3200,
        height: 1800,
        backgroundColor: '{PAGE_BG}',
        spacingTop: 50,
        spacingBottom: 80,
        spacingLeft: 120,
        spacingRight: 50,
        style: {{ fontFamily: 'Arial, sans-serif', color: '{INK}' }},
        events: {{
            load: function() {{
                var chart = this;
                var plotLeft  = chart.plotLeft;
                var plotWidth = chart.plotWidth;
                var yAxes     = chart.yAxis;
                for (var i = 1; i < yAxes.length; i++) {{
                    var y = yAxes[i].top;
                    chart.renderer.path(['M', plotLeft, y - 6, 'L', plotLeft + plotWidth, y - 6])
                        .attr({{ stroke: '{INK_SOFT}', 'stroke-width': 1.5, 'stroke-dasharray': '6,4' }})
                        .add();
                }}
            }}
        }}
    }},

    title: {{
        text: '{TITLE}',
        style: {{ fontSize: '{TITLE_FS}px', fontWeight: '500', color: '{INK}' }}
    }},

    subtitle: {{
        text: '{SUBTITLE}',
        style: {{ fontSize: '36px', color: '{INK_SOFT}' }}
    }},

    credits: {{ enabled: false }},
    legend:  {{ enabled: false }},

    xAxis: {{
        min: {region_start},
        max: {region_end},
        title: {{
            text: 'Genomic Position (chr17)',
            style: {{ fontSize: '44px', color: '{INK}' }}
        }},
        labels: {{
            style: {{ fontSize: '34px', color: '{INK_SOFT}' }},
            y: 36,
            formatter: function() {{
                return (this.value / 1000000).toFixed(3) + ' Mb';
            }}
        }},
        lineWidth: 1, lineColor: '{INK_SOFT}',
        tickWidth: 1, tickColor: '{INK_SOFT}',
        tickInterval: 2000,
        gridLineWidth: 1, gridLineColor: '{GRID}',
        plotBands: {exon_plotbands_json}
    }},

    yAxis: [{{
        title: {{
            text: 'Genes',
            style: {{ fontSize: '40px', fontWeight: 'bold', color: '{COL_GENE}' }},
            rotation: 0, align: 'high', offset: 0, y: -8, x: -8
        }},
        top: '0%', height: '16%', offset: 0,
        min: -0.1, max: 1.2,
        labels: {{ enabled: false }},
        gridLineWidth: 0, lineWidth: 0
    }}, {{
        title: {{
            text: 'Coverage',
            style: {{ fontSize: '40px', fontWeight: 'bold', color: '{COL_COVERAGE}' }},
            rotation: 0, align: 'high', offset: 0, y: -8, x: -8
        }},
        top: '22%', height: '28%', offset: 0, min: 0,
        labels: {{
            style: {{ fontSize: '32px', color: '{INK_SOFT}' }},
            format: '{{value}}x'
        }},
        gridLineWidth: 1, gridLineColor: '{GRID}',
        lineWidth: 1, lineColor: '{INK_SOFT}'
    }}, {{
        title: {{
            text: 'Variants',
            style: {{ fontSize: '40px', fontWeight: 'bold', color: '{INK}' }},
            rotation: 0, align: 'high', offset: 0, y: -8, x: -8
        }},
        top: '56%', height: '18%', offset: 0, min: 0, max: 110,
        labels: {{
            style: {{ fontSize: '32px', color: '{INK_SOFT}' }}
        }},
        gridLineWidth: 1, gridLineColor: '{GRID}',
        lineWidth: 1, lineColor: '{INK_SOFT}'
    }}, {{
        title: {{
            text: 'Regulatory',
            style: {{ fontSize: '40px', fontWeight: 'bold', color: '{INK}' }},
            rotation: 0, align: 'high', offset: 0, y: -8, x: -8
        }},
        top: '80%', height: '14%', offset: 0,
        min: -0.1, max: 1.1,
        labels: {{ enabled: false }},
        gridLineWidth: 0, lineWidth: 0
    }}],

    tooltip: {{
        style: {{ fontSize: '28px', color: '{INK}' }},
        backgroundColor: '{ELEVATED_BG}',
        borderColor: '{INK_SOFT}',
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
        // Gene track — exon rectangles
        {{
            type: 'arearange',
            name: 'Exons',
            yAxis: 0,
            data: {exon_arearange_json},
            color: '{COL_GENE}',
            fillOpacity: 1.0,
            lineWidth: 1,
            lineColor: '{COL_GENE}',
            connectNulls: false,
            tooltip: {{ pointFormat: '<b>Exon</b>' }}
        }},
        // Gene track — intron chevron lines (minus-strand direction)
        {{
            type: 'line',
            name: 'Introns',
            yAxis: 0,
            data: {intron_json},
            color: '{COL_GENE}',
            lineWidth: 3,
            marker: {{ enabled: false }},
            enableMouseTracking: false
        }},
        // Gene label with strand arrow
        {{
            type: 'scatter',
            name: 'Gene Label',
            yAxis: 0,
            data: [{{ x: {gene_label_x}, y: 1.05,
                dataLabels: {{ enabled: true, format: 'TP53 ◀',
                    style: {{ fontSize: '36px', fontWeight: 'bold',
                              color: '{COL_GENE}', textOutline: 'none' }} }} }}],
            marker: {{ enabled: false }},
            enableMouseTracking: false
        }},

        // Coverage track — areaspline with gradient fill
        {{
            type: 'areaspline',
            name: 'Read Depth',
            yAxis: 1,
            data: {coverage_json},
            color: '{COL_COVERAGE}',
            fillColor: {{
                linearGradient: {{ x1: 0, y1: 0, x2: 0, y2: 1 }},
                stops: [[0, '{cov_hi}'], [1, '{cov_lo}']]
            }},
            lineWidth: 2,
            marker: {{ enabled: false }},
            tooltip: {{ pointFormat: '<b>Coverage:</b> {{point.y}}x<br/>Position: {{point.x:,.0f}}' }}
        }},

        // Variant track — SNP lollipop markers
        {{
            type: 'scatter',
            name: 'SNPs',
            yAxis: 2,
            data: {snp_json},
            color: '{COL_SNP}',
            marker: {{ symbol: 'circle', radius: 12, lineWidth: 1.5, lineColor: '{INK}' }},
            tooltip: {{ pointFormat: '<b>{{point.name}}</b> (SNP)<br/>PHRED: {{point.y}}<br/>Pos: {{point.x:,.0f}}' }}
        }},
        // Variant track — Indel lollipop markers
        {{
            type: 'scatter',
            name: 'Indels',
            yAxis: 2,
            data: {indel_json},
            color: '{COL_INDEL}',
            marker: {{ symbol: 'diamond', radius: 14, lineWidth: 1.5, lineColor: '{INK}' }},
            tooltip: {{ pointFormat: '<b>{{point.name}}</b> (Indel)<br/>PHRED: {{point.y}}<br/>Pos: {{point.x:,.0f}}' }}
        }},
        // Variant lollipop stems
        {{
            type: 'columnrange',
            name: 'Stems',
            yAxis: 2,
            data: {all_variants_json}.map(function(v) {{
                return {{ x: v.x, low: 0, high: v.y }};
            }}),
            pointWidth: 2,
            color: '{INK_SOFT}',
            borderWidth: 0,
            enableMouseTracking: false
        }},
        // Variant inline legend
        {{
            type: 'scatter',
            name: 'Variant Legend',
            yAxis: 2,
            data: [
                {{ x: {legend_snp_x},   y: 105,
                    dataLabels: {{ enabled: true, format: '● SNP',
                        align: 'left', x: 5,
                        style: {{ fontSize: '28px', color: '{COL_SNP}',
                                  fontWeight: 'bold', textOutline: 'none' }} }} }},
                {{ x: {legend_indel_x}, y: 105,
                    dataLabels: {{ enabled: true, format: '◆ Indel',
                        align: 'left', x: 5,
                        style: {{ fontSize: '28px', color: '{COL_INDEL}',
                                  fontWeight: 'bold', textOutline: 'none' }} }} }}
            ],
            marker: {{ enabled: false }},
            enableMouseTracking: false
        }},

        // Regulatory track — Enhancer rectangles
        {{
            type: 'arearange',
            name: 'Enhancers',
            yAxis: 3,
            data: {enhancer_arearange_json},
            color: '{COL_ENHANCER}',
            fillOpacity: 0.75,
            lineWidth: 1,
            lineColor: '{COL_ENHANCER}',
            connectNulls: false,
            tooltip: {{ pointFormat: '<b>Enhancer</b>' }}
        }},
        // Regulatory track — Promoter rectangles
        {{
            type: 'arearange',
            name: 'Promoters',
            yAxis: 3,
            data: {promoter_arearange_json},
            color: '{COL_PROMOTER}',
            fillOpacity: 0.75,
            lineWidth: 1,
            lineColor: '{COL_PROMOTER}',
            connectNulls: false,
            tooltip: {{ pointFormat: '<b>Promoter</b>' }}
        }},
        // Regulatory inline legend
        {{
            type: 'scatter',
            name: 'Regulatory Legend',
            yAxis: 3,
            data: [
                {{ x: {legend_reg_x}, y: 0.28,
                    dataLabels: {{ enabled: true, format: '■ Enhancer',
                        style: {{ fontSize: '28px', color: '{COL_ENHANCER}',
                                  fontWeight: 'bold', textOutline: 'none' }} }} }},
                {{ x: {legend_reg_x}, y: 0.72,
                    dataLabels: {{ enabled: true, format: '■ Promoter',
                        style: {{ fontSize: '28px', color: '{COL_PROMOTER}',
                                  fontWeight: 'bold', textOutline: 'none' }} }} }}
            ],
            marker: {{ enabled: false }},
            enableMouseTracking: false
        }}
    ]
}});
"""

# Download Highcharts JS inline (headless Chrome cannot load external CDN scripts)
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"
req = urllib.request.Request(highcharts_url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

highcharts_more_url = "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts-more.js"
req2 = urllib.request.Request(highcharts_more_url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req2, timeout=30) as response:
    highcharts_more_js = response.read().decode("utf-8")

# Build HTML with inline scripts (no external CDN references)
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
</head>
<body style="margin:0; padding:0; background:{PAGE_BG};">
    <div id="container" style="width: 3200px; height: 1800px;"></div>
    <script>
    {chart_js}
    </script>
</body>
</html>"""

# Save interactive HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML and take screenshot via Selenium
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
# CDP override makes the viewport authoritative — --window-size alone is eaten
# by Chrome chrome (toolbar/scrollbar leftovers) in headless mode
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 3200, "height": 1800, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# PIL safety net: pin to exact 3200×1800 in case of ±1-2px rounding drift
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _canvas = Image.new("RGB", (3200, 1800), PAGE_BG)
    _canvas.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _canvas.save(f"plot-{THEME}.png")
