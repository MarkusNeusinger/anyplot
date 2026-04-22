""" pyplots.ai
bar-drilldown: Column Chart with Hierarchical Drilling
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-16
"""

import pygal
from pygal.style import Style


# Hierarchical data: Company -> Divisions -> Teams
# Structure: {id: {"name": str, "value": num, "parent": str or None, "children": [ids]}}
hierarchy = {
    # Root level - Company divisions
    "root": {"name": "Company", "value": None, "parent": None, "children": ["tech", "sales", "ops"]},
    "tech": {"name": "Technology", "value": 4200, "parent": "root", "children": ["dev", "infra", "data"]},
    "sales": {"name": "Sales", "value": 3100, "parent": "root", "children": ["retail", "enterprise", "partner"]},
    "ops": {"name": "Operations", "value": 2400, "parent": "root", "children": ["hr", "finance", "legal"]},
    # Level 2 - Technology teams
    "dev": {"name": "Development", "value": 1800, "parent": "tech", "children": ["frontend", "backend", "mobile"]},
    "infra": {"name": "Infrastructure", "value": 1400, "parent": "tech", "children": ["cloud", "security", "network"]},
    "data": {"name": "Data Science", "value": 1000, "parent": "tech", "children": ["ml", "analytics", "etl"]},
    # Level 2 - Sales teams
    "retail": {"name": "Retail", "value": 1200, "parent": "sales", "children": []},
    "enterprise": {"name": "Enterprise", "value": 1400, "parent": "sales", "children": []},
    "partner": {"name": "Partners", "value": 500, "parent": "sales", "children": []},
    # Level 2 - Operations teams
    "hr": {"name": "Human Resources", "value": 800, "parent": "ops", "children": []},
    "finance": {"name": "Finance", "value": 1000, "parent": "ops", "children": []},
    "legal": {"name": "Legal", "value": 600, "parent": "ops", "children": []},
    # Level 3 - Development sub-teams
    "frontend": {"name": "Frontend", "value": 600, "parent": "dev", "children": []},
    "backend": {"name": "Backend", "value": 800, "parent": "dev", "children": []},
    "mobile": {"name": "Mobile", "value": 400, "parent": "dev", "children": []},
    # Level 3 - Infrastructure sub-teams
    "cloud": {"name": "Cloud", "value": 600, "parent": "infra", "children": []},
    "security": {"name": "Security", "value": 500, "parent": "infra", "children": []},
    "network": {"name": "Network", "value": 300, "parent": "infra", "children": []},
    # Level 3 - Data Science sub-teams
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

# Custom style for large canvas (4800x2700)
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998", "#FFD43B", "#4CAF50", "#FF5722", "#9C27B0", "#00BCD4", "#FF9800", "#795548"),
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=42,
    legend_font_size=42,
    value_font_size=36,
    tooltip_font_size=36,
    stroke_width=2,
    opacity=0.9,
    opacity_hover=1.0,
    transition="400ms ease-in-out",
)

# Create bar chart with drilldown indication
chart = pygal.Bar(
    width=4800,
    height=2700,
    style=custom_style,
    title="bar-drilldown · pygal · pyplots.ai",
    x_title=f"Breadcrumb: {breadcrumb}",
    y_title="Budget (in thousands $)",
    show_legend=True,
    legend_at_bottom=False,
    legend_box_size=24,
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
# Bars with children show "Click to drill down" in tooltip
chart_data = []
for name, value, has_child, cid in zip(names, values, has_children, children_ids, strict=True):
    if has_child:
        label = f"{name}: ${value:,}K - Click to drill down"
    else:
        label = f"{name}: ${value:,}K (leaf node)"
    chart_data.append({"value": value, "label": label, "xlink": f"javascript:drillDown('{cid}')"})

chart.add("Divisions", chart_data)
chart.x_labels = names

# Custom JavaScript for drilldown functionality (embedded in HTML output)
hierarchy_json = (
    str(hierarchy).replace("'", '"').replace("None", "null").replace("True", "true").replace("False", "false")
)
drilldown_js = f"""
<script type="text/javascript">
// Hierarchical data for client-side navigation
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
        alert('This is a leaf node - no further drill-down available.');
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

function drillUp() {{
    alert('Click on the breadcrumb trail to navigate back up the hierarchy.');
}}
</script>
"""

# Save PNG (static view of root level)
chart.render_to_png("plot.png")

# Save HTML with embedded drilldown JavaScript
svg_content = chart.render()
svg_str = svg_content.decode("utf-8") if isinstance(svg_content, bytes) else svg_content
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>bar-drilldown - pygal - pyplots.ai</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 100%;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .breadcrumb {{
            font-size: 24px;
            color: #306998;
            margin-bottom: 20px;
            padding: 10px 20px;
            background: #f0f4f8;
            border-radius: 4px;
            cursor: pointer;
        }}
        .breadcrumb:hover {{
            background: #e0e8f0;
        }}
        .instructions {{
            font-size: 18px;
            color: #666;
            margin-bottom: 20px;
            padding: 15px;
            background: #fff3cd;
            border-radius: 4px;
            border-left: 4px solid #FFD43B;
        }}
        svg {{
            width: 100%;
            height: auto;
        }}
        svg rect:hover {{
            cursor: pointer;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="breadcrumb" onclick="drillUp()">
            {breadcrumb} (click bars to drill down)
        </div>
        <div class="instructions">
            <strong>Interactive Drilldown:</strong> Click on any bar to drill into its sub-categories.
            Hover over bars to see details.
        </div>
        {svg_str}
    </div>
    {drilldown_js}
</body>
</html>
"""

with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)
