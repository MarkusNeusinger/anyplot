""" anyplot.ai
map-drilldown-geographic: Drillable Geographic Map
Library: pygal 3.1.0 | Python 3.13.13
Quality: 74/100 | Updated: 2026-05-23
"""

import json
import os
import sys


# Remove the script's own directory from sys.path so `import pygal` finds the
# installed package rather than this file (which shares the same name).
_here = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _here]

import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

ANYPLOT_PALETTE = ("#009E73", "#9418DB", "#B71D27", "#16B8F3", "#99B314", "#D359A7", "#BA843E")

# Title — 54 chars, under the 67-char baseline so default size applies
title_str = "map-drilldown-geographic · python · pygal · anyplot.ai"
title_font_size = 66

# Hierarchical regional sales data (millions USD): World -> Country -> State -> City
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

# PNG — Treemap showing world geographic hierarchy (countries subdivided into states)
# Each country series gets a distinct anyplot palette color; block area encodes sales $M
png_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=ANYPLOT_PALETTE,
    title_font_size=title_font_size,
    label_font_size=56,
    legend_font_size=50,
    major_label_font_size=44,
    value_font_size=40,
    tooltip_font_size=40,
    no_data_font_size=44,
)

png_chart = pygal.Treemap(
    style=png_style,
    width=3200,
    height=1800,
    title=title_str,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=5,
    legend_box_size=50,
    print_values=True,
    margin=40,
    margin_bottom=160,
    explicit_size=True,
)

# Add each country as a series — states are the sub-values; each country gets a distinct color
country_ids = hierarchy["world"]["children"]
for country_id in country_ids:
    country = hierarchy[country_id]
    state_values = [{"value": hierarchy[sid]["value"], "label": hierarchy[sid]["name"]} for sid in country["children"]]
    png_chart.add(f"{country['name']} (${country['value']}M)", state_values)

png_chart.render_to_png(f"plot-{THEME}.png")

# HTML — Interactive drill-down: Treemap world view -> Bar charts for states/cities
html_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=ANYPLOT_PALETTE,
    title_font_size=20,
    label_font_size=14,
    legend_font_size=14,
    major_label_font_size=12,
    value_font_size=12,
    tooltip_font_size=14,
)

# World-level treemap SVG
world_treemap = pygal.Treemap(
    style=html_style,
    width=860,
    height=480,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=5,
    legend_box_size=18,
    print_values=False,
    explicit_size=True,
)
for country_id in country_ids:
    country = hierarchy[country_id]
    state_values = [{"value": hierarchy[sid]["value"], "label": hierarchy[sid]["name"]} for sid in country["children"]]
    world_treemap.add(country["name"], state_values)

world_svg = world_treemap.render(is_unicode=True)

# Bar chart SVGs for each drillable node (countries and states with children)
svg_data = {"world": world_svg}
bar_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=ANYPLOT_PALETTE,
    title_font_size=18,
    label_font_size=13,
    legend_font_size=13,
    value_font_size=11,
    tooltip_font_size=13,
)

for node_id, node_data in hierarchy.items():
    if node_id != "world" and node_data.get("children"):
        children_ids = node_data["children"]
        if children_ids:
            bar = pygal.Bar(
                style=bar_style,
                width=860,
                height=480,
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
            bar.add("Sales", values)
            bar.x_labels = names
            svg_data[node_id] = bar.render(is_unicode=True)

hierarchy_json = json.dumps(hierarchy)

# Build HTML — theme-adaptive colors baked in
html_bg = PAGE_BG
html_elevated = ELEVATED_BG
html_ink = INK
html_ink_soft = INK_SOFT
html_ink_muted = INK_MUTED
brand_color = ANYPLOT_PALETTE[0]
accent_color = ANYPLOT_PALETTE[1]

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{title_str}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: {html_bg};
            color: {html_ink};
            padding: 24px;
            display: flex;
            flex-direction: column;
            align-items: center;
            min-height: 100vh;
        }}
        .container {{
            background: {html_elevated};
            border-radius: 12px;
            box-shadow: 0 4px 24px rgba(0,0,0,0.12);
            padding: 28px 32px;
            max-width: 980px;
            width: 100%;
        }}
        h1 {{
            color: {html_ink};
            text-align: center;
            margin-bottom: 18px;
            font-size: 20px;
            font-weight: 600;
        }}
        .nav-bar {{
            display: flex;
            align-items: center;
            gap: 12px;
            background: {brand_color};
            color: #fff;
            padding: 12px 18px;
            border-radius: 8px;
            margin-bottom: 16px;
            flex-wrap: wrap;
        }}
        .back-btn {{
            background: rgba(255,255,255,0.15);
            color: #fff;
            border: 1px solid rgba(255,255,255,0.3);
            padding: 6px 16px;
            border-radius: 6px;
            font-size: 14px;
            cursor: pointer;
            font-weight: 600;
            transition: background 0.15s;
            white-space: nowrap;
        }}
        .back-btn:hover:not(:disabled) {{ background: rgba(255,255,255,0.25); }}
        .back-btn:disabled {{ opacity: 0.4; cursor: not-allowed; }}
        #breadcrumb-path {{
            font-size: 15px;
            display: flex;
            align-items: center;
            gap: 6px;
            flex-wrap: wrap;
        }}
        #breadcrumb-path .crumb {{ cursor: pointer; padding: 2px 4px; border-radius: 4px; }}
        #breadcrumb-path .crumb:hover {{ background: rgba(255,255,255,0.2); text-decoration: underline; }}
        #breadcrumb-path .current {{ font-weight: 700; cursor: default; }}
        #breadcrumb-path .sep {{ opacity: 0.6; }}
        .level-info {{
            text-align: center;
            font-size: 13px;
            color: {html_ink_muted};
            margin-bottom: 12px;
        }}
        #chart-container {{ width: 100%; min-height: 480px; }}
        #chart-container svg {{ max-width: 100%; height: auto; display: block; margin: 0 auto; }}
        .hint {{
            text-align: center;
            color: {html_ink_muted};
            margin-top: 14px;
            font-size: 13px;
            padding: 8px 14px;
            background: {html_bg};
            border-radius: 6px;
        }}
        .reactive {{ cursor: pointer; transition: opacity 0.15s; }}
        .reactive:hover {{ opacity: 0.75; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title_str}</h1>
        <div class="nav-bar">
            <button class="back-btn" id="backBtn" disabled>&#8592; Back</button>
            <div id="breadcrumb-path"><span class="current">World</span></div>
        </div>
        <div class="level-info" id="level-info">World View — Sales by Country (click to drill down)</div>
        <div id="chart-container"></div>
        <p class="hint" id="hint">Click any region or bar to explore sub-regions</p>
    </div>
    <script>
        const hierarchy = {hierarchy_json};
        const svgCharts = {{
"""

for level_id, svg_content in svg_data.items():
    escaped = svg_content.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
    html_content += f'            "{level_id}": `{escaped}`,\n'

html_content += """        };
        let currentLevel = "world";
        let historyStack = [];

        function getPath() {
            const path = [];
            let cur = currentLevel;
            while (cur && hierarchy[cur]) {
                path.unshift({ id: cur, name: hierarchy[cur].name });
                cur = hierarchy[cur].parent;
            }
            return path;
        }

        function levelLabel(id) {
            const depth = getPath().length;
            if (id === "world") return "World View — Sales by Country (click to drill down)";
            if (depth === 2) return "Country Level — Sales by State/Province";
            if (depth === 3) return "State Level — Sales by City";
            return "City Level — Leaf Data";
        }

        function updateNav() {
            const pathDiv = document.getElementById("breadcrumb-path");
            const backBtn = document.getElementById("backBtn");
            document.getElementById("level-info").textContent = levelLabel(currentLevel);
            const path = getPath();
            pathDiv.innerHTML = path.map((item, i) => {
                const isLast = i === path.length - 1;
                const sep = i > 0 ? '<span class="sep"> › </span>' : "";
                if (isLast) return sep + `<span class="current">${item.name}</span>`;
                return sep + `<span class="crumb" onclick="navigateTo('${item.id}')">${item.name}</span>`;
            }).join("");
            backBtn.disabled = currentLevel === "world";
        }

        function renderChart(levelId) {
            const container = document.getElementById("chart-container");
            const hint = document.getElementById("hint");
            if (!svgCharts[levelId]) {
                container.innerHTML = "<p style='text-align:center;padding:40px;'>No data at this level.</p>";
                return;
            }
            container.innerHTML = svgCharts[levelId];
            const node = hierarchy[levelId];
            if (levelId === "world") {
                // Treemap: make reactive cells drillable by country index
                const cells = container.querySelectorAll(".cell");
                const countries = hierarchy.world.children;
                let idx = 0;
                cells.forEach(cell => {
                    if (idx < countries.length) {
                        const cid = countries[idx];
                        cell.classList.add("reactive");
                        cell.onclick = () => drillDown(cid);
                        idx++;
                    }
                });
                hint.textContent = "Click a country block to explore its states";
            } else {
                const children = node.children || [];
                const bars = container.querySelectorAll(".bar, rect.rect");
                let bi = 0;
                bars.forEach(bar => {
                    if (bi < children.length) {
                        const cid = children[bi];
                        const child = hierarchy[cid];
                        if (child && child.children && child.children.length > 0) {
                            bar.classList.add("reactive");
                            bar.onclick = () => drillDown(cid);
                        }
                        bi++;
                    }
                });
                const hasDrill = children.some(cid => hierarchy[cid] && hierarchy[cid].children && hierarchy[cid].children.length > 0);
                hint.textContent = hasDrill ? "Click a bar to drill into its sub-regions" : "Leaf level — no further detail available";
            }
        }

        function drillDown(id) {
            if (!hierarchy[id] || !svgCharts[id]) return;
            historyStack.push(currentLevel);
            currentLevel = id;
            updateNav();
            renderChart(currentLevel);
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
            updateNav();
            renderChart(currentLevel);
        }

        document.getElementById("backBtn").addEventListener("click", () => {
            if (historyStack.length > 0) {
                currentLevel = historyStack.pop();
                updateNav();
                renderChart(currentLevel);
            }
        });

        updateNav();
        renderChart("world");
    </script>
</body>
</html>"""

with open(f"plot-{THEME}.html", "w") as f:
    f.write(html_content)
