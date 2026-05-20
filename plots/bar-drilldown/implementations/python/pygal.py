"""anyplot.ai
bar-drilldown: Column Chart with Hierarchical Drilling
Library: pygal 3.1.0 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-20
"""

import json
import os
import sys


# This file is named pygal.py — without this fix it shadows the installed pygal package.
_d = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _d]
os.chdir(_d)  # ensure relative output paths (plot-*.png/html) land next to this script

import pygal
from pygal.style import Style


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

OKABE_ITO = ("#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442")

# Hierarchical data: Company -> Divisions -> Teams -> Sub-teams
hierarchy = {
    "root": {"name": "Company", "value": None, "parent": None, "children": ["tech", "sales", "ops"]},
    "tech": {"name": "Technology", "value": 4200, "parent": "root", "children": ["dev", "infra", "data"]},
    "sales": {"name": "Sales", "value": 3100, "parent": "root", "children": ["retail", "enterprise", "partner"]},
    "ops": {"name": "Operations", "value": 2400, "parent": "root", "children": ["hr", "finance", "legal"]},
    "dev": {"name": "Development", "value": 1800, "parent": "tech", "children": ["frontend", "backend", "mobile"]},
    "infra": {"name": "Infrastructure", "value": 1400, "parent": "tech", "children": ["cloud", "security", "network"]},
    "data": {"name": "Data Science", "value": 1000, "parent": "tech", "children": ["ml", "analytics", "etl"]},
    "retail": {"name": "Retail", "value": 1200, "parent": "sales", "children": []},
    "enterprise": {"name": "Enterprise", "value": 1400, "parent": "sales", "children": []},
    "partner": {"name": "Partners", "value": 500, "parent": "sales", "children": []},
    "hr": {"name": "Human Resources", "value": 800, "parent": "ops", "children": []},
    "finance": {"name": "Finance", "value": 1000, "parent": "ops", "children": []},
    "legal": {"name": "Legal", "value": 600, "parent": "ops", "children": []},
    "frontend": {"name": "Frontend", "value": 600, "parent": "dev", "children": []},
    "backend": {"name": "Backend", "value": 800, "parent": "dev", "children": []},
    "mobile": {"name": "Mobile", "value": 400, "parent": "dev", "children": []},
    "cloud": {"name": "Cloud", "value": 600, "parent": "infra", "children": []},
    "security": {"name": "Security", "value": 500, "parent": "infra", "children": []},
    "network": {"name": "Network", "value": 300, "parent": "infra", "children": []},
    "ml": {"name": "Machine Learning", "value": 450, "parent": "data", "children": []},
    "analytics": {"name": "Analytics", "value": 350, "parent": "data", "children": []},
    "etl": {"name": "ETL Pipeline", "value": 200, "parent": "data", "children": []},
}

# Use primary INK for foreground_subtle in dark theme so value labels stay fully readable
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK if THEME == "dark" else INK_MUTED,
    colors=OKABE_ITO,
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    tooltip_font_size=36,
    stroke_width=2.5,
    opacity=0.9,
    opacity_hover=1.0,
    transition="400ms ease-in-out",
)

# Pre-render SVGs for all drillable levels; save PNG from root
level_svgs = {}
for level_id, level_node in hierarchy.items():
    if not level_node["children"]:
        continue

    # Build breadcrumb for this level
    level_trail = []
    level_cursor = level_id
    while level_cursor and level_cursor in hierarchy:
        level_trail.insert(0, hierarchy[level_cursor]["name"])
        level_cursor = hierarchy[level_cursor]["parent"]
    level_breadcrumb = " > ".join(level_trail)

    level_children = level_node["children"]
    level_names = [hierarchy[cid]["name"] for cid in level_children]
    level_values = [hierarchy[cid]["value"] for cid in level_children]
    level_has_children_flags = [bool(hierarchy[cid]["children"]) for cid in level_children]

    level_chart = pygal.Bar(
        width=3200,
        height=1800,
        style=custom_style,
        title="bar-drilldown · python · pygal · anyplot.ai",
        x_title=f"Breadcrumb: {level_breadcrumb}",
        y_title="Budget (thousands $)",
        show_legend=False,
        show_y_guides=False,
        show_x_guides=False,
        x_label_rotation=0,
        print_values=True,
        print_values_position="top",
        value_formatter=lambda x: f"${x:,.0f}K",
        human_readable=True,
        spacing=30,
        margin=60,
        margin_top=100,
        margin_bottom=120,
        truncate_legend=-1,
        truncate_label=-1,
    )

    level_data = []
    for i, (lname, lval, lhas_child, lcid) in enumerate(
        zip(level_names, level_values, level_has_children_flags, level_children, strict=True)
    ):
        # Per-bar Okabe-Ito colors: visually distinguish categories and emphasize the dominant bar
        lcolor = OKABE_ITO[i % len(OKABE_ITO)]
        llabel = f"{lname}: ${lval:,}K — click to drill down" if lhas_child else f"{lname}: ${lval:,}K (leaf node)"
        level_data.append({"value": lval, "label": llabel, "xlink": f"javascript:drillDown('{lcid}')", "color": lcolor})

    level_chart.add("Divisions", level_data)
    level_chart.x_labels = level_names

    if level_id == "root":
        level_chart.render_to_png(f"plot-{THEME}.png")

    level_svg_bytes = level_chart.render()
    level_svgs[level_id] = level_svg_bytes.decode("utf-8") if isinstance(level_svg_bytes, bytes) else level_svg_bytes

# JSON-safe embedding: escape </script> sequences that would break the HTML parser
hierarchy_json = json.dumps({k: {**v} for k, v in hierarchy.items()}).replace("</", r"<\/")
level_svgs_json = json.dumps(level_svgs).replace("</", r"<\/")

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>bar-drilldown · python · pygal · anyplot.ai</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: {PAGE_BG};
            color: {INK};
        }}
        .container {{ max-width: 100%; padding: 20px; }}
        .nav-bar {{
            display: flex;
            align-items: center;
            gap: 16px;
            margin-bottom: 16px;
            padding: 12px 20px;
            background: {ELEVATED_BG};
            border-radius: 4px;
        }}
        #breadcrumb {{
            font-size: 20px;
            color: {OKABE_ITO[0]};
            font-weight: 600;
            flex: 1;
        }}
        #back-btn {{
            display: none;
            padding: 8px 18px;
            background: {OKABE_ITO[0]};
            color: {PAGE_BG};
            border: none;
            border-radius: 4px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
        }}
        #back-btn:hover {{ opacity: 0.85; }}
        .instructions {{
            font-size: 16px;
            margin-bottom: 16px;
            padding: 12px 20px;
            background: {ELEVATED_BG};
            border-radius: 4px;
            border-left: 4px solid {OKABE_ITO[0]};
        }}
        #chart-container svg {{ width: 100%; height: auto; }}
        #chart-container svg a {{ cursor: pointer; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="nav-bar">
            <button id="back-btn" onclick="drillUp()">&#8592; Back</button>
            <div id="breadcrumb">Company</div>
        </div>
        <div class="instructions">
            <strong>Interactive Drilldown:</strong> Click any bar to explore its sub-categories.
            Use the Back button to navigate up the hierarchy.
        </div>
        <div id="chart-container">{level_svgs.get("root", "")}</div>
    </div>
    <script type="text/javascript">
    var hierarchy = {hierarchy_json};
    var levelSvgs = {level_svgs_json};
    var navHistory = ["root"];

    function getBreadcrumbText(nodeId) {{
        var trail = [];
        var cur = nodeId;
        while (cur && hierarchy[cur]) {{
            trail.unshift(hierarchy[cur].name);
            cur = hierarchy[cur].parent;
        }}
        return trail.join(' > ');
    }}

    function updateNav() {{
        var btn = document.getElementById("back-btn");
        btn.style.display = navHistory.length > 1 ? "inline-block" : "none";
        document.getElementById("breadcrumb").textContent = getBreadcrumbText(navHistory[navHistory.length - 1]);
    }}

    function renderLevel(nodeId) {{
        if (!levelSvgs[nodeId]) return;
        document.getElementById("chart-container").innerHTML = levelSvgs[nodeId];
        updateNav();
    }}

    function drillDown(nodeId) {{
        if (!hierarchy[nodeId] || !hierarchy[nodeId].children.length || !levelSvgs[nodeId]) return;
        navHistory.push(nodeId);
        renderLevel(nodeId);
    }}

    function drillUp() {{
        if (navHistory.length <= 1) return;
        navHistory.pop();
        renderLevel(navHistory[navHistory.length - 1]);
    }}

    // Event delegation: intercept xlink:href clicks on SVG anchors for drilldown
    document.getElementById("chart-container").addEventListener("click", function(e) {{
        var target = e.target;
        while (target && target !== this) {{
            var href = target.getAttribute("xlink:href") || target.getAttribute("href") || "";
            if (href.indexOf("drillDown") !== -1) {{
                e.preventDefault();
                var m = href.match(/drillDown\\('([^']+)'\\)/);
                if (m) drillDown(m[1]);
                return;
            }}
            target = target.parentElement;
        }}
    }});
    </script>
</body>
</html>
"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)
