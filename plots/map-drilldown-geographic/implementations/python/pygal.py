""" anyplot.ai
map-drilldown-geographic: Drillable Geographic Map
Library: pygal 3.1.0 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-23
"""

import json
import os
import sys


# Remove this script's own directory from sys.path so 'pygal.py' doesn't shadow
# the installed pygal package when the filename matches the package name.
_here = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != _here]

import pygal
from pygal.style import Style
from pygal_maps_world.maps import World


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# anyplot_seq: #003D94 (low) → #009E73 (high), 5 equally-spaced stops
# lerp("#003D94", "#009E73", i/4) for i in 0..4
SEQ_COLORS = (
    "#003D94",  # lowest — dark azure
    "#00558C",
    "#006D83",
    "#00867B",
    "#009E73",  # highest — brand green
)

# anyplot categorical palette (first series always #009E73)
ANYPLOT_PALETTE = ("#009E73", "#9418DB", "#B71D27", "#16B8F3", "#99B314", "#D359A7", "#BA843E")

# Hierarchical sales data: World → Country → State → City (values in $M USD)
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

# PNG: static world choropleth (anyplot_seq palette, low→high = dark azure→brand green)
png_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=SEQ_COLORS,
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=2.5,
)

png_map = World(
    style=png_style,
    width=3200,
    height=1800,
    title="map-drilldown-geographic · python · pygal · anyplot.ai",
    x_title="World Sales Overview ($M) — Open HTML for Interactive Drill-Down",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=5,
    legend_box_size=40,
    print_values=False,
    print_labels=False,
    margin=60,
    margin_bottom=140,
    explicit_size=True,
)

# Add countries ordered lowest→highest so SEQ_COLORS[0..4] map correctly
png_map.add("Australia ($380M)", {"au": hierarchy["au"]["value"]})
png_map.add("Brazil ($520M)", {"br": hierarchy["br"]["value"]})
png_map.add("Germany ($580M)", {"de": hierarchy["de"]["value"]})
png_map.add("Japan ($850M)", {"jp": hierarchy["jp"]["value"]})
png_map.add("United States ($2,100M)", {"us": hierarchy["us"]["value"]})

png_map.render_to_png(f"plot-{THEME}.png")

# HTML: interactive drill-down with theme-adaptive colours
html_map_style = Style(
    background="transparent",
    plot_background="transparent",
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=SEQ_COLORS,
    title_font_size=20,
    label_font_size=14,
    major_label_font_size=12,
    legend_font_size=14,
    value_font_size=12,
)

world_map = World(
    style=html_map_style,
    width=820,
    height=500,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=5,
    legend_box_size=16,
    print_values=False,
    print_labels=False,
    explicit_size=True,
)
world_map.add("Australia ($380M)", {"au": hierarchy["au"]["value"]})
world_map.add("Brazil ($520M)", {"br": hierarchy["br"]["value"]})
world_map.add("Germany ($580M)", {"de": hierarchy["de"]["value"]})
world_map.add("Japan ($850M)", {"jp": hierarchy["jp"]["value"]})
world_map.add("United States ($2,100M)", {"us": hierarchy["us"]["value"]})
world_svg = world_map.render(is_unicode=True)

# Bar charts for each drillable node (sub-country levels)
html_bar_style = Style(
    background="transparent",
    plot_background="transparent",
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=ANYPLOT_PALETTE,
    title_font_size=18,
    label_font_size=13,
    major_label_font_size=12,
    value_font_size=12,
    legend_font_size=13,
)

svg_data = {"world": world_svg}
for node_id, node_data in hierarchy.items():
    if node_id != "world" and node_data.get("children"):
        children_ids = node_data["children"]
        if children_ids:
            chart = pygal.Bar(
                style=html_bar_style,
                width=820,
                height=440,
                show_legend=False,
                show_y_guides=True,
                y_title="Sales ($M)",
                print_values=True,
                print_values_position="top",
                value_formatter=lambda x: f"${x}M",
                human_readable=True,
                explicit_size=True,
            )
            chart.add("Sales", [hierarchy[cid]["value"] for cid in children_ids])
            chart.x_labels = [hierarchy[cid]["name"] for cid in children_ids]
            svg_data[node_id] = chart.render(is_unicode=True)

hierarchy_json = json.dumps(hierarchy)

# Theme-adaptive CSS tokens for HTML
css_bg = PAGE_BG
css_elevated = ELEVATED_BG
css_ink = INK
css_ink_soft = INK_SOFT
css_brand = "#009E73"
css_brand_dark = "#007A59"

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>map-drilldown-geographic · python · pygal · anyplot.ai</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: {css_bg};
            color: {css_ink};
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
        .container {{
            background: {css_elevated};
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.12);
            padding: 30px;
            max-width: 980px;
            width: 100%;
        }}
        h1 {{
            color: {css_ink};
            text-align: center;
            margin: 0 0 16px 0;
            font-size: 22px;
            font-weight: 600;
        }}
        .breadcrumb {{
            background: {css_brand};
            color: #fff;
            padding: 12px 18px;
            border-radius: 8px;
            margin-bottom: 16px;
            font-size: 16px;
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
        }}
        .breadcrumb span {{
            cursor: pointer;
            padding: 2px 5px;
            border-radius: 4px;
        }}
        .breadcrumb span:hover:not(.current):not(.sep) {{
            background: rgba(255,255,255,0.25);
            text-decoration: underline;
        }}
        .breadcrumb .sep {{ opacity: 0.7; cursor: default; }}
        .breadcrumb .current {{
            font-weight: 700;
            cursor: default;
            background: rgba(255,255,255,0.2);
        }}
        .back-btn {{
            background: {css_brand_dark};
            color: #fff;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-size: 14px;
            cursor: pointer;
            font-weight: 600;
            transition: background 0.2s;
            white-space: nowrap;
        }}
        .back-btn:hover:not(:disabled) {{ background: #005c42; }}
        .back-btn:disabled {{ opacity: 0.4; cursor: not-allowed; }}
        .level-info {{
            text-align: center;
            color: {css_ink_soft};
            font-size: 14px;
            margin-bottom: 12px;
            font-weight: 500;
        }}
        #chart-container {{
            width: 100%;
            min-height: 440px;
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        #chart-container svg {{ max-width: 100%; height: auto; }}
        .hint {{
            text-align: center;
            color: {css_ink_soft};
            margin-top: 12px;
            font-size: 13px;
            padding: 8px 12px;
            background: {css_bg};
            border-radius: 6px;
            border: 1px solid rgba(128,128,128,0.15);
        }}
        .country, .bar, rect.rect {{ cursor: pointer; transition: opacity 0.2s; }}
        .country:hover, .bar:hover, rect.rect:hover {{ opacity: 0.72; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>map-drilldown-geographic · python · pygal · anyplot.ai</h1>
        <div class="breadcrumb">
            <button class="back-btn" id="backBtn" disabled>← Back</button>
            <div id="breadcrumb-path"><span class="current">World</span></div>
        </div>
        <div class="level-info" id="level-info">World View — Sales by Country</div>
        <div id="chart-container"></div>
        <p class="hint" id="hint">Click a highlighted country to drill down to states/provinces</p>
    </div>
    <script>
        const hierarchy = {hierarchy_json};
        const svgCharts = {{
"""

for level_id, svg_content in svg_data.items():
    escaped = svg_content.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
    html_content += f'            "{level_id}": `{escaped}`,\n'

html_content += """        };
        let currentLevel = 'world';
        let historyStack = [];

        function getBreadcrumbPath() {
            const path = [];
            let cur = currentLevel;
            while (cur && hierarchy[cur]) {
                path.unshift({ id: cur, name: hierarchy[cur].name });
                cur = hierarchy[cur].parent;
            }
            return path;
        }

        function getLevelLabel(id) {
            const depth = getBreadcrumbPath().length;
            if (id === 'world') return 'World View — Sales by Country';
            if (depth === 2) return 'Country Level — Sales by State/Province';
            if (depth === 3) return 'State Level — Sales by City';
            return 'City Level — Detailed Sales';
        }

        function updateBreadcrumb() {
            const pathDiv = document.getElementById('breadcrumb-path');
            const backBtn = document.getElementById('backBtn');
            const path = getBreadcrumbPath();
            let html = '';
            path.forEach((item, i) => {
                if (i > 0) html += '<span class="sep"> › </span>';
                if (item.id === currentLevel) {
                    html += `<span class="current">${item.name}</span>`;
                } else {
                    html += `<span onclick="navigateTo('${item.id}')">${item.name}</span>`;
                }
            });
            pathDiv.innerHTML = html;
            backBtn.disabled = currentLevel === 'world';
            document.getElementById('level-info').textContent = getLevelLabel(currentLevel);
        }

        function renderChart(levelId) {
            const container = document.getElementById('chart-container');
            const hint = document.getElementById('hint');
            const levelData = hierarchy[levelId];
            if (!svgCharts[levelId]) {
                container.innerHTML = '<p style="text-align:center;padding:50px;opacity:0.5;">No detail available</p>';
                hint.textContent = '';
                return;
            }
            container.innerHTML = svgCharts[levelId];
            if (levelId === 'world') {
                container.querySelectorAll('.country').forEach(el => {
                    const cls = Array.from(el.classList).find(c => c !== 'country' && c !== 'reactive');
                    if (cls && hierarchy[cls] && hierarchy[cls].children.length > 0) {
                        el.style.cursor = 'pointer';
                        el.onclick = () => drillDown(cls);
                    }
                });
                hint.textContent = 'Click a highlighted country to drill down to states/provinces';
            } else {
                const children = levelData.children || [];
                const bars = container.querySelectorAll('.bar, rect.rect');
                let idx = 0;
                bars.forEach(bar => {
                    if (idx < children.length) {
                        const childId = children[idx];
                        const childData = hierarchy[childId];
                        if (childData && childData.children && childData.children.length > 0) {
                            bar.style.cursor = 'pointer';
                            bar.onclick = () => drillDown(childId);
                        }
                        idx++;
                    }
                });
                const hasDrillable = children.some(cid =>
                    hierarchy[cid] && hierarchy[cid].children && hierarchy[cid].children.length > 0
                );
                hint.textContent = hasDrillable
                    ? 'Click a bar to drill down further'
                    : 'Leaf level — no further drill-down available';
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
            let cur = id;
            while (cur && hierarchy[cur] && hierarchy[cur].parent) {
                newStack.unshift(hierarchy[cur].parent);
                cur = hierarchy[cur].parent;
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

with open(f"plot-{THEME}.html", "w") as f:
    f.write(html_content)
