"""anyplot.ai
bar-drilldown: Column Chart with Hierarchical Drilling
Library: pygal | Python 3.13
Quality: 91/100 | Updated: 2026-05-20
"""

import json
import os

import pygal
from pygal.style import Style


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

OKABE_ITO = ("#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442")

# Hierarchical data: Company -> Divisions -> Teams
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

# Build breadcrumb trail from root to current node
current_level = "root"
trail = []
node = current_level
while node and node in hierarchy:
    trail.insert(0, hierarchy[node]["name"])
    node = hierarchy[node]["parent"]
breadcrumb = " > ".join(trail)

# Get children data for current level
children_ids = hierarchy[current_level]["children"]
names = [hierarchy[cid]["name"] for cid in children_ids]
values = [hierarchy[cid]["value"] for cid in children_ids]
has_children = [len(hierarchy[cid]["children"]) > 0 for cid in children_ids]

# Custom style for 3200×1800 canvas
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
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

chart = pygal.Bar(
    width=3200,
    height=1800,
    style=custom_style,
    title="bar-drilldown · python · pygal · anyplot.ai",
    x_title=f"Breadcrumb: {breadcrumb}",
    y_title="Budget (thousands $)",
    show_legend=False,
    show_y_guides=True,
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

# Add data with tooltips indicating drilldown capability
chart_data = []
for name, value, has_child, cid in zip(names, values, has_children, children_ids, strict=True):
    if has_child:
        label = f"{name}: ${value:,}K — click to drill down"
    else:
        label = f"{name}: ${value:,}K (leaf node)"
    chart_data.append({"value": value, "label": label, "xlink": f"javascript:drillDown('{cid}')"})

chart.add("Divisions", chart_data)
chart.x_labels = names

# Save PNG (static view of root level)
chart.render_to_png(f"plot-{THEME}.png")

# JSON-safe serialization for JavaScript
hierarchy_json = json.dumps({k: {**v} for k, v in hierarchy.items()})

drilldown_js = f"""
<script type="text/javascript">
var hierarchy = {hierarchy_json};

function getBreadcrumb(nodeId) {{
    var trail = [];
    var current = nodeId;
    while (current && hierarchy[current]) {{
        trail.unshift(hierarchy[current].name);
        current = hierarchy[current].parent;
    }}
    return trail.join(' > ');
}}

function drillDown(nodeId) {{
    if (!hierarchy[nodeId] || hierarchy[nodeId].children.length === 0) {{
        alert('This is a leaf node — no further drill-down available.');
        return;
    }}

    var children = hierarchy[nodeId].children;
    var message = 'Drilling into: ' + hierarchy[nodeId].name + '\\n\\n';
    message += 'Breadcrumb: ' + getBreadcrumb(nodeId) + '\\n\\n';
    message += 'Sub-categories:\\n';

    for (var i = 0; i < children.length; i++) {{
        var child = hierarchy[children[i]];
        var suffix = child.children.length > 0 ? ' (has sub-levels)' : ' (leaf)';
        message += '- ' + child.name + ': $' + child.value.toLocaleString() + 'K' + suffix + '\\n';
    }}

    message += '\\n(In a full implementation, this would render a new chart)';
    alert(message);
}}
</script>
"""

svg_content = chart.render()
svg_str = svg_content.decode("utf-8") if isinstance(svg_content, bytes) else svg_content

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
        .container {{
            max-width: 100%;
            background: {PAGE_BG};
            padding: 20px;
        }}
        .breadcrumb {{
            font-size: 24px;
            color: {OKABE_ITO[0]};
            margin-bottom: 20px;
            padding: 10px 20px;
            background: {ELEVATED_BG};
            border-radius: 4px;
        }}
        .instructions {{
            font-size: 18px;
            color: {INK};
            margin-bottom: 20px;
            padding: 15px;
            background: {ELEVATED_BG};
            border-radius: 4px;
            border-left: 4px solid {OKABE_ITO[0]};
        }}
        svg {{
            width: 100%;
            height: auto;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="breadcrumb">{breadcrumb}</div>
        <div class="instructions">
            <strong>Interactive Drilldown:</strong> Click on any bar to explore its sub-categories.
            Hover over bars to see details.
        </div>
        {svg_str}
    </div>
    {drilldown_js}
</body>
</html>
"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)
