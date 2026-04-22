""" pyplots.ai
hierarchy-toggle-view: Interactive Treemap-Sunburst Toggle View
Library: pygal 3.1.0 | Python 3.13.11
Quality: 90/100 | Created: 2026-01-11
"""

# Workaround: ensure we import the pygal package, not this file
import sys
from pathlib import Path


_this_dir = Path(__file__).parent
if str(_this_dir) in sys.path:
    sys.path.remove(str(_this_dir))

import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


# Hierarchical data: Company budget allocation (in thousands)
# Structure: Company -> Departments -> Teams
hierarchy = [
    {"id": "company", "parent": "", "label": "Company", "value": 0},
    # Level 1: Departments
    {"id": "engineering", "parent": "company", "label": "Engineering", "value": 0},
    {"id": "marketing", "parent": "company", "label": "Marketing", "value": 0},
    {"id": "sales", "parent": "company", "label": "Sales", "value": 0},
    {"id": "operations", "parent": "company", "label": "Operations", "value": 0},
    # Level 2: Engineering teams
    {"id": "backend", "parent": "engineering", "label": "Backend", "value": 1800},
    {"id": "frontend", "parent": "engineering", "label": "Frontend", "value": 1200},
    {"id": "data_science", "parent": "engineering", "label": "Data Science", "value": 900},
    {"id": "devops", "parent": "engineering", "label": "DevOps", "value": 600},
    # Level 2: Marketing teams
    {"id": "digital", "parent": "marketing", "label": "Digital", "value": 900},
    {"id": "brand", "parent": "marketing", "label": "Brand", "value": 600},
    {"id": "content", "parent": "marketing", "label": "Content", "value": 600},
    # Level 2: Sales teams
    {"id": "enterprise", "parent": "sales", "label": "Enterprise", "value": 1000},
    {"id": "smb", "parent": "sales", "label": "SMB", "value": 500},
    {"id": "partners", "parent": "sales", "label": "Partners", "value": 300},
    # Level 2: Operations teams
    {"id": "it", "parent": "operations", "label": "IT", "value": 500},
    {"id": "hr", "parent": "operations", "label": "HR", "value": 400},
    {"id": "finance", "parent": "operations", "label": "Finance", "value": 300},
]

# Build lookup and calculate parent values
id_to_node = {n["id"]: n for n in hierarchy}
for node in reversed(hierarchy):
    if node["value"] == 0:
        children_sum = sum(n["value"] for n in hierarchy if n["parent"] == node["id"])
        node["value"] = children_sum

# Color palette - consistent across both views
# Using Python Blue (#306998) and Yellow (#FFD43B) as primary
colors = {"engineering": "#306998", "marketing": "#FFD43B", "sales": "#2CA02C", "operations": "#9467BD"}

# Lighter shades for teams within departments
team_colors = {
    "backend": "#4A87B8",
    "frontend": "#6A9FC8",
    "data_science": "#8AB7D8",
    "devops": "#AAD0E8",
    "digital": "#FFE066",
    "brand": "#FFE899",
    "content": "#FFF0CC",
    "enterprise": "#4ABF4A",
    "smb": "#7AD17A",
    "partners": "#A9E3A9",
    "it": "#B08ED3",
    "hr": "#C8AEDF",
    "finance": "#E0CEEB",
}

# Custom style for better visibility - larger fonts for HTML version
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333",
    foreground_strong="#333",
    foreground_subtle="#666",
    colors=(colors["engineering"], colors["marketing"], colors["sales"], colors["operations"]),
    title_font_size=40,
    label_font_size=22,
    major_label_font_size=20,
    legend_font_size=20,
    value_font_size=18,
    value_label_font_size=18,
)

# Get departments (level 1) and their children (level 2)
departments = [n for n in hierarchy if n["parent"] == "company"]
dept_ids = [d["id"] for d in departments]

# Create treemap - showing team-level breakdown
treemap = pygal.Treemap(
    width=2400,
    height=2700,
    style=custom_style,
    title="Treemap View - Budget by Team",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    print_values=True,
    print_values_position="center",
    value_formatter=lambda x: f"${x}K",
)

# Add data grouped by department (each department as a series)
for dept in departments:
    dept_teams = [n for n in hierarchy if n["parent"] == dept["id"]]
    team_data = [
        {"value": t["value"], "label": t["label"], "color": team_colors.get(t["id"], colors[dept["id"]])}
        for t in dept_teams
    ]
    treemap.add(f"{dept['label']} (${dept['value']}K)", team_data)

# Create pie/sunburst chart - nested rings showing hierarchy
# Pygal Pie can create sunburst-like effect with inner_radius
sunburst = pygal.Pie(
    width=2400,
    height=2700,
    style=custom_style,
    title="Sunburst View - Budget Hierarchy",
    inner_radius=0.35,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    print_values=True,
    value_formatter=lambda x: f"${x}K",
)

# Add all leaf nodes (teams) to show full hierarchy
# Group by department for color consistency
for dept in departments:
    dept_teams = [n for n in hierarchy if n["parent"] == dept["id"]]
    for team in dept_teams:
        sunburst.add(
            f"{dept['label']}: {team['label']}",
            [{"value": team["value"], "color": team_colors.get(team["id"], colors[dept["id"]])}],
        )

# Create combined HTML with toggle functionality
# Render both charts to SVG strings
treemap_svg = treemap.render(is_unicode=True)
sunburst_svg = sunburst.render(is_unicode=True)

# HTML with CSS toggle between views
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>hierarchy-toggle-view · pygal · pyplots.ai</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            background: white;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 2400px;
            margin: 0 auto;
        }}
        h1 {{
            text-align: center;
            color: #306998;
            font-size: 32px;
            margin-bottom: 10px;
        }}
        .subtitle {{
            text-align: center;
            color: #666;
            font-size: 18px;
            margin-bottom: 20px;
        }}
        .toggle-container {{
            text-align: center;
            margin-bottom: 20px;
        }}
        .toggle-btn {{
            padding: 12px 30px;
            font-size: 18px;
            margin: 0 10px;
            cursor: pointer;
            border: 2px solid #306998;
            background: white;
            color: #306998;
            border-radius: 6px;
            transition: all 0.3s ease;
        }}
        .toggle-btn.active {{
            background: #306998;
            color: white;
        }}
        .toggle-btn:hover {{
            background: #FFD43B;
            border-color: #FFD43B;
            color: #333;
        }}
        .chart-container {{
            position: relative;
            width: 100%;
        }}
        .chart {{
            width: 100%;
            display: none;
        }}
        .chart.active {{
            display: block;
        }}
        .chart svg {{
            max-width: 100%;
            height: auto;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>hierarchy-toggle-view · pygal · pyplots.ai</h1>
        <p class="subtitle">Company Budget Allocation - Toggle between Treemap and Sunburst views</p>
        <div class="toggle-container">
            <button class="toggle-btn active" onclick="showTreemap()">Treemap View</button>
            <button class="toggle-btn" onclick="showSunburst()">Sunburst View</button>
        </div>
        <div class="chart-container">
            <div id="treemap" class="chart active">
                {treemap_svg}
            </div>
            <div id="sunburst" class="chart">
                {sunburst_svg}
            </div>
        </div>
    </div>
    <script>
        function showTreemap() {{
            document.getElementById('treemap').classList.add('active');
            document.getElementById('sunburst').classList.remove('active');
            document.querySelectorAll('.toggle-btn')[0].classList.add('active');
            document.querySelectorAll('.toggle-btn')[1].classList.remove('active');
        }}
        function showSunburst() {{
            document.getElementById('treemap').classList.remove('active');
            document.getElementById('sunburst').classList.add('active');
            document.querySelectorAll('.toggle-btn')[0].classList.remove('active');
            document.querySelectorAll('.toggle-btn')[1].classList.add('active');
        }}
    </script>
</body>
</html>
"""

# Save HTML for interactive version
with open("plot.html", "w") as f:
    f.write(html_content)

# For PNG, create a combined side-by-side view
# Update style for combined image - much larger fonts for 4800x2700 canvas for perfect legibility
combined_style = Style(
    background="white",
    plot_background="white",
    foreground="#333",
    foreground_strong="#333",
    foreground_subtle="#666",
    colors=(colors["engineering"], colors["marketing"], colors["sales"], colors["operations"]),
    title_font_size=64,
    label_font_size=36,
    major_label_font_size=32,
    legend_font_size=32,
    value_font_size=28,
    value_label_font_size=28,
)

# Create treemap for left side
treemap_left = pygal.Treemap(
    width=2300,
    height=2400,
    style=combined_style,
    title="Treemap View",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=2,
    print_values=True,
    print_values_position="center",
    value_formatter=lambda x: f"${x}K",
    margin_left=20,
    margin_right=20,
)

for dept in departments:
    dept_teams = [n for n in hierarchy if n["parent"] == dept["id"]]
    team_data = [
        {"value": t["value"], "label": t["label"], "color": team_colors.get(t["id"], colors[dept["id"]])}
        for t in dept_teams
    ]
    treemap_left.add(f"{dept['label']}", team_data)

# Create sunburst for right side
sunburst_right = pygal.Pie(
    width=2300,
    height=2400,
    style=combined_style,
    title="Sunburst View",
    inner_radius=0.35,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    print_values=True,
    value_formatter=lambda x: f"${x}K",
    margin_left=20,
    margin_right=20,
)

for dept in departments:
    dept_teams = [n for n in hierarchy if n["parent"] == dept["id"]]
    for team in dept_teams:
        sunburst_right.add(
            f"{team['label']}", [{"value": team["value"], "color": team_colors.get(team["id"], colors[dept["id"]])}]
        )

# Render each chart to PNG separately
treemap_left.render_to_png("treemap_temp.png")
sunburst_right.render_to_png("sunburst_temp.png")

# Combine using PIL
import os  # noqa: E402

from PIL import Image, ImageDraw, ImageFont  # noqa: E402


# Create combined image
combined = Image.new("RGB", (4800, 2700), "white")
draw = ImageDraw.Draw(combined)

# Add title - using larger fonts for 4800x2700 canvas
try:
    title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
    subtitle_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
except OSError:
    title_font = ImageFont.load_default()
    subtitle_font = ImageFont.load_default()

# Draw title centered
title = "Company Budget · hierarchy-toggle-view · pygal · pyplots.ai"
title_bbox = draw.textbbox((0, 0), title, font=title_font)
title_width = title_bbox[2] - title_bbox[0]
draw.text(((4800 - title_width) // 2, 40), title, fill="#306998", font=title_font)

# Draw subtitle
subtitle = "Toggle between rectangle (Treemap) and radial (Sunburst) hierarchy views"
subtitle_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
draw.text(((4800 - subtitle_width) // 2, 130), subtitle, fill="#666666", font=subtitle_font)

# Load and paste treemap (left) - adjusted y-position for larger title
treemap_img = Image.open("treemap_temp.png")
treemap_img = treemap_img.resize((2200, 2400), Image.Resampling.LANCZOS)
combined.paste(treemap_img, (100, 220))

# Load and paste sunburst (right) - adjusted y-position for larger title
sunburst_img = Image.open("sunburst_temp.png")
sunburst_img = sunburst_img.resize((2200, 2400), Image.Resampling.LANCZOS)
combined.paste(sunburst_img, (2500, 220))

# Save combined image
combined.save("plot.png", "PNG")

# Clean up temporary files
os.remove("treemap_temp.png")
os.remove("sunburst_temp.png")
