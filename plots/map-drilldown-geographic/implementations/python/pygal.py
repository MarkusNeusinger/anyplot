""" pyplots.ai
map-drilldown-geographic: Drillable Geographic Map
Library: pygal 3.1.0 | Python 3.13.11
Quality: 82/100 | Created: 2026-01-20
"""

import json

import pygal
from pygal.style import Style
from pygal_maps_world.maps import World


# Hierarchical sales data: World -> Country -> State -> City
# Values represent regional sales in millions USD
hierarchy = {
    "world": {"name": "World", "parent": None, "children": ["us", "de", "jp", "br", "au"], "value": None},
    "us": {"name": "United States", "parent": "world", "value": 2100, "children": ["us_ca", "us_tx", "us_ny", "us_fl"]},
    "de": {"name": "Germany", "parent": "world", "value": 580, "children": ["de_by", "de_nw", "de_he"]},
    "jp": {"name": "Japan", "parent": "world", "value": 850, "children": ["jp_13", "jp_27", "jp_23"]},
    "br": {"name": "Brazil", "parent": "world", "value": 520, "children": ["br_sp", "br_rj", "br_mg"]},
    "au": {"name": "Australia", "parent": "world", "value": 380, "children": ["au_nsw", "au_vic", "au_qld"]},
    "us_ca": {"name": "California", "parent": "us", "value": 680, "children": ["us_ca_la", "us_ca_sf", "us_ca_sd"]},
    "us_tx": {"name": "Texas", "parent": "us", "value": 520, "children": ["us_tx_hou", "us_tx_dal", "us_tx_aus"]},
    "us_ny": {"name": "New York", "parent": "us", "value": 580, "children": ["us_ny_nyc", "us_ny_buf", "us_ny_alb"]},
    "us_fl": {"name": "Florida", "parent": "us", "value": 320, "children": ["us_fl_mia", "us_fl_orl", "us_fl_tam"]},
    "de_by": {"name": "Bavaria", "parent": "de", "value": 210, "children": ["de_by_muc", "de_by_nur"]},
    "de_nw": {"name": "North Rhine-Westphalia", "parent": "de", "value": 240, "children": ["de_nw_col", "de_nw_dus"]},
    "de_he": {"name": "Hesse", "parent": "de", "value": 130, "children": ["de_he_fra", "de_he_wie"]},
    "jp_13": {"name": "Tokyo", "parent": "jp", "value": 420, "children": ["jp_13_shi", "jp_13_min"]},
    "jp_27": {"name": "Osaka", "parent": "jp", "value": 280, "children": ["jp_27_osa", "jp_27_sak"]},
    "jp_23": {"name": "Aichi", "parent": "jp", "value": 150, "children": ["jp_23_nag", "jp_23_toy"]},
    "br_sp": {"name": "Sao Paulo", "parent": "br", "value": 280, "children": ["br_sp_sao", "br_sp_cam"]},
    "br_rj": {"name": "Rio de Janeiro", "parent": "br", "value": 160, "children": ["br_rj_rio", "br_rj_nit"]},
    "br_mg": {"name": "Minas Gerais", "parent": "br", "value": 80, "children": ["br_mg_bho", "br_mg_ube"]},
    "au_nsw": {"name": "New South Wales", "parent": "au", "value": 180, "children": ["au_nsw_syd", "au_nsw_new"]},
    "au_vic": {"name": "Victoria", "parent": "au", "value": 140, "children": ["au_vic_mel", "au_vic_gee"]},
    "au_qld": {"name": "Queensland", "parent": "au", "value": 60, "children": ["au_qld_bri", "au_qld_gol"]},
    "us_ca_la": {"name": "Los Angeles", "parent": "us_ca", "value": 320, "children": []},
    "us_ca_sf": {"name": "San Francisco", "parent": "us_ca", "value": 240, "children": []},
    "us_ca_sd": {"name": "San Diego", "parent": "us_ca", "value": 120, "children": []},
    "us_tx_hou": {"name": "Houston", "parent": "us_tx", "value": 220, "children": []},
    "us_tx_dal": {"name": "Dallas", "parent": "us_tx", "value": 180, "children": []},
    "us_tx_aus": {"name": "Austin", "parent": "us_tx", "value": 120, "children": []},
    "us_ny_nyc": {"name": "New York City", "parent": "us_ny", "value": 420, "children": []},
    "us_ny_buf": {"name": "Buffalo", "parent": "us_ny", "value": 90, "children": []},
    "us_ny_alb": {"name": "Albany", "parent": "us_ny", "value": 70, "children": []},
    "us_fl_mia": {"name": "Miami", "parent": "us_fl", "value": 140, "children": []},
    "us_fl_orl": {"name": "Orlando", "parent": "us_fl", "value": 100, "children": []},
    "us_fl_tam": {"name": "Tampa", "parent": "us_fl", "value": 80, "children": []},
    "de_by_muc": {"name": "Munich", "parent": "de_by", "value": 150, "children": []},
    "de_by_nur": {"name": "Nuremberg", "parent": "de_by", "value": 60, "children": []},
    "de_nw_col": {"name": "Cologne", "parent": "de_nw", "value": 130, "children": []},
    "de_nw_dus": {"name": "Dusseldorf", "parent": "de_nw", "value": 110, "children": []},
    "de_he_fra": {"name": "Frankfurt", "parent": "de_he", "value": 90, "children": []},
    "de_he_wie": {"name": "Wiesbaden", "parent": "de_he", "value": 40, "children": []},
    "jp_13_shi": {"name": "Shibuya", "parent": "jp_13", "value": 280, "children": []},
    "jp_13_min": {"name": "Minato", "parent": "jp_13", "value": 140, "children": []},
    "jp_27_osa": {"name": "Osaka City", "parent": "jp_27", "value": 200, "children": []},
    "jp_27_sak": {"name": "Sakai", "parent": "jp_27", "value": 80, "children": []},
    "jp_23_nag": {"name": "Nagoya", "parent": "jp_23", "value": 100, "children": []},
    "jp_23_toy": {"name": "Toyota", "parent": "jp_23", "value": 50, "children": []},
    "br_sp_sao": {"name": "Sao Paulo City", "parent": "br_sp", "value": 220, "children": []},
    "br_sp_cam": {"name": "Campinas", "parent": "br_sp", "value": 60, "children": []},
    "br_rj_rio": {"name": "Rio City", "parent": "br_rj", "value": 120, "children": []},
    "br_rj_nit": {"name": "Niteroi", "parent": "br_rj", "value": 40, "children": []},
    "br_mg_bho": {"name": "Belo Horizonte", "parent": "br_mg", "value": 60, "children": []},
    "br_mg_ube": {"name": "Uberlandia", "parent": "br_mg", "value": 20, "children": []},
    "au_nsw_syd": {"name": "Sydney", "parent": "au_nsw", "value": 140, "children": []},
    "au_nsw_new": {"name": "Newcastle", "parent": "au_nsw", "value": 40, "children": []},
    "au_vic_mel": {"name": "Melbourne", "parent": "au_vic", "value": 110, "children": []},
    "au_vic_gee": {"name": "Geelong", "parent": "au_vic", "value": 30, "children": []},
    "au_qld_bri": {"name": "Brisbane", "parent": "au_qld", "value": 45, "children": []},
    "au_qld_gol": {"name": "Gold Coast", "parent": "au_qld", "value": 15, "children": []},
}

# Colorblind-friendly palette
COLORS = ("#1B4F72", "#E67E22", "#148F77", "#6C3483", "#922B21", "#1E8449")

# Custom style for large canvas with larger legend
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#111111",
    foreground_subtle="#666666",
    colors=COLORS,
    title_font_size=72,
    label_font_size=48,
    legend_font_size=48,
    major_label_font_size=44,
    value_font_size=40,
    tooltip_font_size=40,
    no_data_font_size=36,
)

# PNG map - world level view showing sales tiers by region
png_map = World(
    style=custom_style,
    width=4800,
    height=2700,
    title="map-drilldown-geographic · pygal · pyplots.ai",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    legend_box_size=50,
    print_values=False,
    print_labels=False,
    margin=60,
    margin_bottom=220,
    explicit_size=True,
)

# Group countries by sales tier for visual hierarchy
tier1 = {"us": hierarchy["us"]["value"]}
tier2 = {"jp": hierarchy["jp"]["value"]}
tier3 = {"de": hierarchy["de"]["value"], "br": hierarchy["br"]["value"]}
tier4 = {"au": hierarchy["au"]["value"]}

png_map.add(">$1B", tier1)
png_map.add("$500M-1B", tier2)
png_map.add("$300-500M", tier3)
png_map.add("<$300M", tier4)

# Breadcrumb showing current level (static PNG overview)
png_map.x_title = "Static World Overview · Open HTML for Interactive Drill-Down"

png_map.render_to_png("plot.png")

# HTML interactive version - world map SVG
html_style = Style(
    background="transparent",
    plot_background="transparent",
    foreground="#333333",
    foreground_strong="#111111",
    foreground_subtle="#666666",
    colors=COLORS,
    title_font_size=24,
    label_font_size=16,
    legend_font_size=16,
    major_label_font_size=14,
    value_font_size=14,
    tooltip_font_size=14,
)

world_map = World(
    style=html_style,
    width=800,
    height=500,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=5,
    legend_box_size=20,
    print_values=False,
    print_labels=False,
    explicit_size=True,
)
countries_data = {c: hierarchy[c]["value"] for c in hierarchy["world"]["children"]}
world_map.add("Sales ($M)", countries_data)
world_svg = world_map.render(is_unicode=True)

# Generate bar charts for each drillable node
svg_data = {"world": world_svg}
bar_style = Style(
    background="transparent",
    plot_background="transparent",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=COLORS,
    title_font_size=20,
    label_font_size=14,
    legend_font_size=14,
    value_font_size=12,
    tooltip_font_size=14,
)

for node_id, node_data in hierarchy.items():
    if node_id != "world" and node_data.get("children"):
        children_ids = node_data["children"]
        if children_ids:
            chart = pygal.Bar(
                style=bar_style,
                width=800,
                height=450,
                legend_at_bottom=False,
                show_legend=False,
                show_y_guides=True,
                y_title="Sales ($M)",
                print_values=True,
                print_values_position="top",
                value_formatter=lambda x: f"${x}M",
                human_readable=True,
                explicit_size=True,
            )
            names = [hierarchy[cid]["name"] for cid in children_ids]
            values = [hierarchy[cid]["value"] for cid in children_ids]
            chart.add("Sales", values)
            chart.x_labels = names
            svg_data[node_id] = chart.render(is_unicode=True)

# Build JSON for JavaScript using json module
hierarchy_json = json.dumps(hierarchy)

# Build HTML content
html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>map-drilldown-geographic · pygal · pyplots.ai</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .container {
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            padding: 30px;
            max-width: 950px;
            width: 100%;
        }
        h1 {
            color: #333;
            text-align: center;
            margin: 0 0 10px 0;
            font-size: 24px;
        }
        .breadcrumb {
            background: #1B4F72;
            color: white;
            padding: 14px 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 18px;
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
        }
        .breadcrumb span {
            cursor: pointer;
            padding: 2px 6px;
            border-radius: 4px;
        }
        .breadcrumb span:hover:not(.current):not(.separator) {
            background: rgba(255,255,255,0.2);
            text-decoration: underline;
        }
        .breadcrumb .separator { opacity: 0.7; cursor: default; }
        .breadcrumb .current { font-weight: bold; cursor: default; background: rgba(255,255,255,0.15); }
        .back-btn {
            background: #E67E22;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            font-size: 16px;
            cursor: pointer;
            font-weight: bold;
            transition: background 0.2s;
        }
        .back-btn:hover:not(:disabled) { background: #D35400; }
        .back-btn:disabled { opacity: 0.5; cursor: not-allowed; }
        #chart-container {
            width: 100%;
            min-height: 450px;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        #chart-container svg { max-width: 100%; height: auto; }
        .hint {
            text-align: center;
            color: #666;
            margin-top: 15px;
            font-size: 14px;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 6px;
        }
        .level-info {
            text-align: center;
            color: #1B4F72;
            font-size: 16px;
            margin-bottom: 15px;
            font-weight: 500;
        }
        .country, .bar, rect.rect { cursor: pointer; transition: opacity 0.2s; }
        .country:hover, .bar:hover, rect.rect:hover { opacity: 0.7; }
    </style>
</head>
<body>
    <div class="container">
        <h1>map-drilldown-geographic · pygal · pyplots.ai</h1>
        <div class="breadcrumb">
            <button class="back-btn" id="backBtn" disabled>← Back</button>
            <div id="breadcrumb-path"><span class="current">World</span></div>
        </div>
        <div class="level-info" id="level-info">World View - Sales by Country</div>
        <div id="chart-container"></div>
        <p class="hint" id="hint">Click on a country to drill down to states/provinces</p>
    </div>
    <script>
        const hierarchy = """
html_content += hierarchy_json
html_content += """;
        const svgCharts = {
"""
for level_id, svg_content in svg_data.items():
    escaped_svg = svg_content.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
    html_content += f'            "{level_id}": `{escaped_svg}`,\n'
html_content += """        };
        let currentLevel = 'world';
        let historyStack = [];
        function getBreadcrumbPath() {
            const path = [];
            let current = currentLevel;
            while (current && hierarchy[current]) {
                path.unshift({ id: current, name: hierarchy[current].name });
                current = hierarchy[current].parent;
            }
            return path;
        }
        function getLevelType(id) {
            const depth = getBreadcrumbPath().length;
            if (id === 'world') return 'World View - Sales by Country';
            if (depth === 2) return 'Country Level - Sales by State/Province';
            if (depth === 3) return 'State Level - Sales by City';
            return 'City Level - Detailed Sales';
        }
        function updateBreadcrumb() {
            const pathDiv = document.getElementById('breadcrumb-path');
            const backBtn = document.getElementById('backBtn');
            const levelInfo = document.getElementById('level-info');
            const path = getBreadcrumbPath();
            let html = '';
            path.forEach((item, index) => {
                if (index > 0) html += '<span class="separator"> > </span>';
                if (item.id === currentLevel) {
                    html += `<span class="current">${item.name}</span>`;
                } else {
                    html += `<span onclick="navigateTo('${item.id}')">${item.name}</span>`;
                }
            });
            pathDiv.innerHTML = html;
            backBtn.disabled = currentLevel === 'world';
            levelInfo.textContent = getLevelType(currentLevel);
        }
        function renderChart(levelId) {
            const container = document.getElementById('chart-container');
            const hint = document.getElementById('hint');
            const levelData = hierarchy[levelId];
            if (svgCharts[levelId]) {
                container.innerHTML = svgCharts[levelId];
                if (levelId === 'world') {
                    const countries = container.querySelectorAll('.country');
                    countries.forEach(country => {
                        const countryClass = Array.from(country.classList).find(c => c !== 'country' && c !== 'reactive');
                        if (countryClass && hierarchy[countryClass] && hierarchy[countryClass].children.length > 0) {
                            country.style.cursor = 'pointer';
                            country.onclick = () => drillDown(countryClass);
                        }
                    });
                    hint.textContent = 'Click on a highlighted country to drill down to states/provinces';
                } else {
                    const children = levelData.children || [];
                    const bars = container.querySelectorAll('.bar, rect.rect');
                    let barIndex = 0;
                    bars.forEach((bar) => {
                        if (barIndex < children.length) {
                            const childId = children[barIndex];
                            const childData = hierarchy[childId];
                            if (childData && childData.children && childData.children.length > 0) {
                                bar.style.cursor = 'pointer';
                                bar.onclick = () => drillDown(childId);
                            }
                            barIndex++;
                        }
                    });
                    const hasDrillable = children.some(cid =>
                        hierarchy[cid] && hierarchy[cid].children && hierarchy[cid].children.length > 0
                    );
                    hint.textContent = hasDrillable
                        ? 'Click on a bar to drill down further'
                        : 'Leaf level reached - no further drill-down available';
                }
            } else {
                container.innerHTML = '<p style="text-align:center;color:#666;padding:50px;">No detailed view</p>';
                hint.textContent = '';
            }
        }
        function drillDown(id) {
            if (!hierarchy[id] || !svgCharts[id]) return;
            historyStack.push(currentLevel);
            currentLevel = id;
            updateBreadcrumb();
            renderChart(currentLevel);
        }
        function goBack() {
            if (historyStack.length > 0) {
                currentLevel = historyStack.pop();
                updateBreadcrumb();
                renderChart(currentLevel);
            }
        }
        function navigateTo(id) {
            const newStack = [];
            let current = id;
            while (current && hierarchy[current] && hierarchy[current].parent) {
                newStack.unshift(hierarchy[current].parent);
                current = hierarchy[current].parent;
            }
            historyStack = newStack.slice(0, -1);
            currentLevel = id;
            updateBreadcrumb();
            renderChart(currentLevel);
        }
        document.getElementById('backBtn').addEventListener('click', goBack);
        updateBreadcrumb();
        renderChart('world');
    </script>
</body>
</html>"""

with open("plot.html", "w") as f:
    f.write(html_content)
