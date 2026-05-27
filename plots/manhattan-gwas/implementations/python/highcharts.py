""" anyplot.ai
manhattan-gwas: Manhattan Plot for GWAS
Library: highcharts unknown | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-15
"""

import json
import os
import subprocess
import tempfile
import time
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette for alternating chromosomes
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]

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

# Prepare series by chromosome with Okabe-Ito alternating colors
series_data = []
for chrom in range(1, 23):
    chrom_points = [[d["x"], d["y"]] for d in all_data if d["chr"] == chrom]
    # Use alternating Okabe-Ito colors
    color_idx = (chrom - 1) % len(IMPRINT)
    color = IMPRINT[color_idx]
    series_data.append(
        {
            "name": f"Chr {chrom}",
            "data": chrom_points,
            "color": color,
            "showInLegend": False,
            "marker": {"radius": 8, "symbol": "circle"},
            "turboThreshold": 0,
            "animation": False,
        }
    )

# Chromosome tick positions and labels
tick_positions = [chr_midpoints[c] for c in range(1, 23)]
tick_labels = {chr_midpoints[c]: str(c) for c in range(1, 23)}

# Download Highcharts JS
highcharts_url = "https://code.highcharts.com/highcharts.js"
result = subprocess.run(
    [
        "curl",
        "-s",
        "-A",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "-H",
        "Accept: */*",
        "-H",
        "Referer: https://www.highcharts.com/",
        highcharts_url,
    ],
    capture_output=True,
    text=True,
    timeout=30,
)
highcharts_js = result.stdout

# Build Highcharts configuration
chart_config = {
    "chart": {
        "type": "scatter",
        "width": 4800,
        "height": 2700,
        "backgroundColor": PAGE_BG,
        "marginBottom": 180,
        "marginTop": 120,
        "marginLeft": 150,
        "marginRight": 80,
        "style": {"fontFamily": "Arial, sans-serif", "color": INK},
    },
    "title": {
        "text": "manhattan-gwas · highcharts · anyplot.ai",
        "style": {"fontSize": "28px", "fontWeight": "bold", "color": INK},
    },
    "subtitle": {
        "text": "Simulated GWAS Results Across Human Chromosomes",
        "style": {"fontSize": "22px", "color": INK_SOFT},
    },
    "xAxis": {
        "title": {"text": "Chromosome", "style": {"fontSize": "22px", "fontWeight": "bold", "color": INK}},
        "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}, "y": 45},
        "tickPositions": tick_positions,
        "min": 0,
        "max": cumulative_offset,
        "tickLength": 0,
        "lineWidth": 2,
        "lineColor": INK_SOFT,
    },
    "yAxis": {
        "title": {"text": "-log₁₀(p-value)", "style": {"fontSize": "22px", "fontWeight": "bold", "color": INK}},
        "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
        "min": 0,
        "max": 16,
        "gridLineWidth": 1,
        "gridLineColor": GRID,
        "lineWidth": 2,
        "lineColor": INK_SOFT,
        "plotLines": [
            {
                "value": 7.3,
                "color": "#009E73",
                "width": 4,
                "dashStyle": "Dash",
                "zIndex": 5,
                "label": {
                    "text": "Genome-wide significance (p = 5×10⁻⁸)",
                    "align": "right",
                    "x": -20,
                    "style": {"fontSize": "18px", "color": "#009E73", "fontWeight": "bold"},
                },
            },
            {
                "value": 5,
                "color": INK_SOFT,
                "width": 3,
                "dashStyle": "Dot",
                "zIndex": 5,
                "label": {
                    "text": "Suggestive (p = 10⁻⁵)",
                    "align": "right",
                    "x": -20,
                    "style": {"fontSize": "16px", "color": INK_SOFT},
                },
            },
        ],
    },
    "legend": {"enabled": False},
    "tooltip": {
        "headerFormat": "",
        "pointFormat": "<b>{series.name}</b><br/>-log₁₀(p): {point.y:.2f}",
        "style": {"fontSize": "16px"},
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
<body style="margin:0; padding:0; overflow:hidden; background:{PAGE_BG};">
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

# Save HTML artifact for the site
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

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
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
