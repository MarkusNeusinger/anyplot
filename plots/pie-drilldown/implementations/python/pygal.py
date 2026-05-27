""" anyplot.ai
pie-drilldown: Drilldown Pie Chart with Click Navigation
Library: pygal 3.1.0 | Python 3.13.13
Quality: 82/100 | Updated: 2026-05-15
"""

import os
import sys


_script_dir = os.path.dirname(os.path.abspath(__file__))
if _script_dir in sys.path:
    sys.path.remove(_script_dir)

import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)

os.chdir(_script_dir)

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

IMPRINT = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477")

# Sales data hierarchy: region > country > product category
data = {
    "root": {"name": "Global Sales", "children": ["americas", "europe", "asia_pacific"]},
    "americas": {"name": "Americas", "parent": "root", "value": 2800000, "children": ["us", "canada", "latam"]},
    "us": {
        "name": "United States",
        "parent": "americas",
        "value": 1800000,
        "children": ["us_electronics", "us_software", "us_services"],
    },
    "us_electronics": {"name": "Electronics", "parent": "us", "value": 900000},
    "us_software": {"name": "Software", "parent": "us", "value": 650000},
    "us_services": {"name": "Services", "parent": "us", "value": 250000},
    "canada": {
        "name": "Canada",
        "parent": "americas",
        "value": 650000,
        "children": ["ca_electronics", "ca_software", "ca_services"],
    },
    "ca_electronics": {"name": "Electronics", "parent": "canada", "value": 320000},
    "ca_software": {"name": "Software", "parent": "canada", "value": 220000},
    "ca_services": {"name": "Services", "parent": "canada", "value": 110000},
    "latam": {
        "name": "Latin America",
        "parent": "americas",
        "value": 350000,
        "children": ["la_electronics", "la_software", "la_services"],
    },
    "la_electronics": {"name": "Electronics", "parent": "latam", "value": 170000},
    "la_software": {"name": "Software", "parent": "latam", "value": 115000},
    "la_services": {"name": "Services", "parent": "latam", "value": 65000},
    "europe": {"name": "Europe", "parent": "root", "value": 2200000, "children": ["uk", "germany", "france"]},
    "uk": {
        "name": "United Kingdom",
        "parent": "europe",
        "value": 950000,
        "children": ["uk_electronics", "uk_software", "uk_services"],
    },
    "uk_electronics": {"name": "Electronics", "parent": "uk", "value": 480000},
    "uk_software": {"name": "Software", "parent": "uk", "value": 320000},
    "uk_services": {"name": "Services", "parent": "uk", "value": 150000},
    "germany": {
        "name": "Germany",
        "parent": "europe",
        "value": 780000,
        "children": ["de_electronics", "de_software", "de_services"],
    },
    "de_electronics": {"name": "Electronics", "parent": "germany", "value": 390000},
    "de_software": {"name": "Software", "parent": "germany", "value": 260000},
    "de_services": {"name": "Services", "parent": "germany", "value": 130000},
    "france": {
        "name": "France",
        "parent": "europe",
        "value": 470000,
        "children": ["fr_electronics", "fr_software", "fr_services"],
    },
    "fr_electronics": {"name": "Electronics", "parent": "france", "value": 235000},
    "fr_software": {"name": "Software", "parent": "france", "value": 160000},
    "fr_services": {"name": "Services", "parent": "france", "value": 75000},
    "asia_pacific": {
        "name": "Asia Pacific",
        "parent": "root",
        "value": 1900000,
        "children": ["japan", "china", "india"],
    },
    "japan": {
        "name": "Japan",
        "parent": "asia_pacific",
        "value": 850000,
        "children": ["jp_electronics", "jp_software", "jp_services"],
    },
    "jp_electronics": {"name": "Electronics", "parent": "japan", "value": 425000},
    "jp_software": {"name": "Software", "parent": "japan", "value": 300000},
    "jp_services": {"name": "Services", "parent": "japan", "value": 125000},
    "china": {
        "name": "China",
        "parent": "asia_pacific",
        "value": 680000,
        "children": ["cn_electronics", "cn_software", "cn_services"],
    },
    "cn_electronics": {"name": "Electronics", "parent": "china", "value": 340000},
    "cn_software": {"name": "Software", "parent": "china", "value": 230000},
    "cn_services": {"name": "Services", "parent": "china", "value": 110000},
    "india": {
        "name": "India",
        "parent": "asia_pacific",
        "value": 370000,
        "children": ["in_electronics", "in_software", "in_services"],
    },
    "in_electronics": {"name": "Electronics", "parent": "india", "value": 185000},
    "in_software": {"name": "Software", "parent": "india", "value": 130000},
    "in_services": {"name": "Services", "parent": "india", "value": 55000},
}

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT,
    title_font_size=28,
    label_font_size=22,
    major_label_font_size=18,
    legend_font_size=16,
    value_font_size=14,
    tooltip_font_size=14,
    stroke_width=2,
)


def create_pygal_chart(level_id, level_data):
    """Create a pygal pie chart for a specific level."""
    children_ids = level_data.get("children", [])
    if not children_ids:
        return None

    total = sum(data[cid]["value"] for cid in children_ids)

    chart = pygal.Pie(
        width=4800,
        height=2700,
        style=custom_style,
        title=f"{level_data['name']} · pie-drilldown · pygal · anyplot.ai",
        legend_at_bottom=True,
        print_values=True,
        print_labels=True,
    )

    def format_val(value):
        pct = (value / total) * 100
        return f"${value:,.0f} ({pct:.1f}%)"

    chart.value_formatter = format_val

    for cid in children_ids:
        child = data[cid]
        chart.add(child["name"], [{"value": child["value"], "label": child["name"]}])

    return chart.render(is_unicode=True)


# Generate SVG for all levels
svg_data = {}
for level_id in list(data.keys()):
    level_svg = create_pygal_chart(level_id, data[level_id])
    if level_svg:
        svg_data[level_id] = level_svg

html_content = (
    """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>pie-drilldown · pygal · anyplot.ai</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: """
    + PAGE_BG
    + """;
            color: """
    + INK
    + """;
            padding: 40px 20px;
            min-height: 100vh;
        }
        .container {
            background: """
    + PAGE_BG
    + """;
            border: 1px solid """
    + INK_MUTED
    + """;
            border-radius: 8px;
            padding: 40px;
            max-width: 1200px;
            margin: 0 auto;
        }
        h1 {
            text-align: center;
            margin-bottom: 30px;
            font-size: 28px;
            color: """
    + INK
    + """;
        }
        .controls {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 30px;
            justify-content: center;
        }
        .breadcrumb {
            display: flex;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
            font-size: 16px;
        }
        .breadcrumb-item {
            cursor: pointer;
            color: """
    + IMPRINT[0]
    + """;
            text-decoration: underline;
            transition: opacity 0.2s;
        }
        .breadcrumb-item:hover {
            opacity: 0.7;
        }
        .breadcrumb-item.current {
            color: """
    + INK
    + """;
            cursor: default;
            text-decoration: none;
            font-weight: 500;
        }
        .breadcrumb-separator {
            color: """
    + INK_SOFT
    + """;
            margin: 0 4px;
        }
        .back-btn {
            background: """
    + IMPRINT[0]
    + """;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            font-size: 14px;
            cursor: pointer;
            font-weight: 500;
            transition: opacity 0.2s;
        }
        .back-btn:hover:not(:disabled) {
            opacity: 0.85;
        }
        .back-btn:disabled {
            opacity: 0.4;
            cursor: not-allowed;
        }
        #chart-container {
            width: 100%;
            display: flex;
            justify-content: center;
            margin-bottom: 30px;
        }
        #chart-container svg {
            max-width: 100%;
            height: auto;
        }
        .hint {
            text-align: center;
            color: """
    + INK_SOFT
    + """;
            font-size: 14px;
            margin-top: 20px;
        }
        .hint.hidden {
            display: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Global Sales Drilldown · pygal · anyplot.ai</h1>
        <div class="controls">
            <button class="back-btn" id="backBtn" disabled>← Back</button>
            <div class="breadcrumb" id="breadcrumb-path"></div>
        </div>
        <div id="chart-container"></div>
        <p class="hint" id="hint">Click on a slice to explore regional sales breakdown</p>
    </div>

    <script>
        const hierarchyData = {
"""
)

for level_id, level_info in data.items():
    html_content += '            "' + level_id + '": {"name": "' + level_info["name"] + '"'
    if "children" in level_info:
        html_content += ', "children": ' + str(level_info["children"]).replace("'", '"')
    html_content += "},\n"

html_content += """        };

        const svgCharts = {
"""

for level_id, svg_content in svg_data.items():
    escaped_svg = svg_content.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
    html_content += '            "' + level_id + '": `' + escaped_svg + "`,\n"

html_content += (
    """        };

        let currentLevel = 'root';
        let history = [];

        function updateBreadcrumb() {
            const pathDiv = document.getElementById('breadcrumb-path');
            const backBtn = document.getElementById('backBtn');

            let html = '';
            const fullPath = ['root'];
            for (const id of history) {
                if (!fullPath.includes(id)) {
                    fullPath.push(id);
                }
            }
            if (!fullPath.includes(currentLevel)) {
                fullPath.push(currentLevel);
            }

            fullPath.forEach((id, index) => {
                if (index > 0) {
                    html += '<span class="breadcrumb-separator">›</span>';
                }
                if (id === currentLevel) {
                    html += `<span class="breadcrumb-item current">${hierarchyData[id].name}</span>`;
                } else {
                    html += `<span class="breadcrumb-item" onclick="navigateTo('${id}')">${hierarchyData[id].name}</span>`;
                }
            });

            pathDiv.innerHTML = html;
            backBtn.disabled = currentLevel === 'root';
        }

        function getChildrenAtLevel(levelId) {
            return hierarchyData[levelId]?.children || [];
        }

        function renderChart(levelId) {
            const container = document.getElementById('chart-container');
            const hint = document.getElementById('hint');

            if (svgCharts[levelId]) {
                container.innerHTML = svgCharts[levelId];

                const children = getChildrenAtLevel(levelId);
                const slices = container.querySelectorAll('.slice');

                slices.forEach((slice, index) => {
                    if (index < children.length) {
                        const childId = children[index];
                        const childData = hierarchyData[childId];

                        if (childData && childData.children) {
                            slice.style.cursor = 'pointer';
                            slice.classList.add('clickable');
                            slice.onclick = () => drillDown(childId);
                        }
                    }
                });

                const hasDrillable = children.some(cid => hierarchyData[cid]?.children);
                hint.classList.toggle('hidden', !hasDrillable);
            } else {
                container.innerHTML = '<p style="text-align:center;color:"""
    + INK_SOFT
    + """;">No breakdown available</p>';
                hint.classList.add('hidden');
            }
        }

        function drillDown(id) {
            if (svgCharts[id]) {
                history.push(currentLevel);
                currentLevel = id;
                updateBreadcrumb();
                renderChart(currentLevel);
            }
        }

        function goBack() {
            if (history.length > 0) {
                currentLevel = history.pop();
                updateBreadcrumb();
                renderChart(currentLevel);
            }
        }

        function navigateTo(id) {
            const idx = history.indexOf(id);
            if (idx >= 0) {
                history = history.slice(0, idx);
            } else {
                history = [];
            }
            currentLevel = id;
            updateBreadcrumb();
            renderChart(currentLevel);
        }

        document.getElementById('backBtn').addEventListener('click', goBack);

        updateBreadcrumb();
        renderChart('root');
    </script>
</body>
</html>"""
)

# Save theme-specific files
with open(f"plot-{THEME}.html", "w") as f:
    f.write(html_content)

# Render static PNG
root_svg = create_pygal_chart("root", data["root"])
if root_svg:
    # Create a temporary chart to render PNG
    root_children = data["root"]["children"]
    root_total = sum(data[cid]["value"] for cid in root_children)

    pie_chart = pygal.Pie(
        width=4800,
        height=2700,
        style=custom_style,
        title="pie-drilldown · pygal · anyplot.ai",
        legend_at_bottom=True,
        print_values=True,
        print_labels=True,
    )

    def format_val(value):
        pct = (value / root_total) * 100
        return f"${value:,.0f} ({pct:.1f}%)"

    pie_chart.value_formatter = format_val

    for child_id in root_children:
        child = data[child_id]
        pie_chart.add(child["name"], [{"value": child["value"], "label": child["name"]}])

    pie_chart.render_to_png(f"plot-{THEME}.png")
