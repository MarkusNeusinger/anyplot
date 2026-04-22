""" pyplots.ai
manhattan-gwas: Manhattan Plot for GWAS
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


# Data - Simulated GWAS data with random p-values and significant peaks
np.random.seed(42)

# Chromosome sizes (approximate human chromosome lengths in Mb)
chr_sizes = {
    1: 249,
    2: 243,
    3: 198,
    4: 191,
    5: 182,
    6: 171,
    7: 159,
    8: 145,
    9: 138,
    10: 134,
    11: 135,
    12: 133,
    13: 115,
    14: 107,
    15: 102,
    16: 90,
    17: 83,
    18: 80,
    19: 59,
    20: 64,
    21: 47,
    22: 51,
}

# Generate SNPs for each chromosome
all_data = []
cumulative_offset = 0
chr_midpoints = {}
chr_boundaries = [0]

for chrom in range(1, 23):
    n_snps = int(chr_sizes[chrom] * 5)  # ~5 SNPs per Mb (~14k points total)

    # Random positions across chromosome
    pos = np.sort(np.random.uniform(0, chr_sizes[chrom], n_snps))

    # Random p-values - mostly non-significant with some significant peaks
    pval = np.random.uniform(0.01, 1.0, n_snps)

    # Add significant peaks on some chromosomes
    if chrom in [2, 6, 11, 17]:
        n_significant = np.random.randint(3, 8)
        sig_indices = np.random.choice(n_snps, n_significant, replace=False)
        pval[sig_indices] = 10 ** (-np.random.uniform(8, 15, n_significant))

    # Add suggestive signals on other chromosomes
    if chrom in [4, 8, 15, 20]:
        n_suggestive = np.random.randint(2, 5)
        sug_indices = np.random.choice(n_snps, n_suggestive, replace=False)
        pval[sug_indices] = 10 ** (-np.random.uniform(5, 7.5, n_suggestive))

    # Transform and store
    neg_log_p = -np.log10(pval)
    cum_pos = pos + cumulative_offset

    for x, y in zip(cum_pos, neg_log_p, strict=False):
        all_data.append({"x": float(x), "y": float(y), "chr": chrom})

    chr_midpoints[chrom] = cumulative_offset + chr_sizes[chrom] / 2
    cumulative_offset += chr_sizes[chrom]
    chr_boundaries.append(cumulative_offset)

# Prepare series by chromosome for alternating colors
series_data = []
for chrom in range(1, 23):
    chrom_points = [[d["x"], d["y"]] for d in all_data if d["chr"] == chrom]
    color = "#306998" if chrom % 2 == 1 else "#7a7a7a"  # Python Blue / Gray
    series_data.append(
        {
            "name": f"Chr {chrom}",
            "data": chrom_points,
            "color": color,
            "showInLegend": False,
            "marker": {"radius": 6, "symbol": "circle"},
            "turboThreshold": 0,
            "animation": False,
        }
    )

# Chromosome tick positions and labels
tick_positions = [chr_midpoints[c] for c in range(1, 23)]
tick_labels = {chr_midpoints[c]: str(c) for c in range(1, 23)}

# Download Highcharts JS
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Build Highcharts configuration
chart_config = {
    "chart": {
        "type": "scatter",
        "width": 4800,
        "height": 2700,
        "backgroundColor": "#ffffff",
        "marginBottom": 180,
        "marginTop": 120,
        "marginLeft": 150,
        "marginRight": 80,
        "style": {"fontFamily": "Arial, sans-serif"},
    },
    "title": {"text": "manhattan-gwas · highcharts · pyplots.ai", "style": {"fontSize": "64px", "fontWeight": "bold"}},
    "subtitle": {
        "text": "Simulated GWAS Results Across Human Chromosomes",
        "style": {"fontSize": "40px", "color": "#666666"},
    },
    "xAxis": {
        "title": {"text": "Chromosome", "style": {"fontSize": "48px", "fontWeight": "bold"}},
        "labels": {"style": {"fontSize": "36px"}, "y": 45},
        "tickPositions": tick_positions,
        "min": 0,
        "max": cumulative_offset,
        "tickLength": 0,
        "lineWidth": 3,
        "lineColor": "#333333",
    },
    "yAxis": {
        "title": {"text": "-log\u2081\u2080(p-value)", "style": {"fontSize": "48px", "fontWeight": "bold"}},
        "labels": {"style": {"fontSize": "36px"}},
        "min": 0,
        "max": 16,
        "gridLineWidth": 1,
        "gridLineColor": "#e0e0e0",
        "lineWidth": 3,
        "lineColor": "#333333",
        "plotLines": [
            {
                "value": 7.3,
                "color": "#DC2626",
                "width": 4,
                "dashStyle": "Dash",
                "zIndex": 5,
                "label": {
                    "text": "Genome-wide significance (p = 5\u00d710\u207b\u2078)",
                    "align": "right",
                    "x": -20,
                    "style": {"fontSize": "32px", "color": "#DC2626", "fontWeight": "bold"},
                },
            },
            {
                "value": 5,
                "color": "#2563EB",
                "width": 3,
                "dashStyle": "Dot",
                "zIndex": 5,
                "label": {
                    "text": "Suggestive (p = 10\u207b\u2075)",
                    "align": "right",
                    "x": -20,
                    "style": {"fontSize": "28px", "color": "#2563EB"},
                },
            },
        ],
    },
    "legend": {"enabled": False},
    "tooltip": {
        "headerFormat": "",
        "pointFormat": "<b>{series.name}</b><br/>-log\u2081\u2080(p): {point.y:.2f}",
        "style": {"fontSize": "24px"},
    },
    "credits": {"enabled": False},
    "series": series_data,
}

# Custom x-axis label formatter
tick_labels_json = json.dumps(tick_labels)

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; padding:0; overflow:hidden;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
        var tickLabels = {tick_labels_json};
        var config = {json.dumps(chart_config)};

        // Custom formatter for chromosome labels
        config.xAxis.labels.formatter = function() {{
            // Find closest tick position
            var pos = this.value;
            var closestKey = null;
            var minDist = Infinity;
            for (var key in tickLabels) {{
                var dist = Math.abs(parseFloat(key) - pos);
                if (dist < minDist) {{
                    minDist = dist;
                    closestKey = key;
                }}
            }}
            if (minDist < 50) {{
                return tickLabels[closestKey];
            }}
            return '';
        }};

        Highcharts.chart('container', config);
    </script>
</body>
</html>"""

# Write temp HTML and take screenshot
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
time.sleep(5)
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()

# Save HTML for interactive viewing
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)
