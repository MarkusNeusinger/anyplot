""" pyplots.ai
pie-drilldown: Drilldown Pie Chart with Click Navigation
Library: pygal 3.1.0 | Python 3.13.11
Quality: 90/100 | Created: 2025-12-31
"""

import pygal
from pygal.style import Style


# Define hierarchical data structure for company budget
# Root level: main departments
# Level 2: sub-categories within each department
data = {
    "root": {"name": "Company Budget", "children": ["engineering", "marketing", "operations", "hr"]},
    "engineering": {
        "name": "Engineering",
        "parent": "root",
        "value": 450000,
        "children": ["eng_salaries", "eng_tools", "eng_cloud", "eng_training"],
    },
    "eng_salaries": {"name": "Salaries", "parent": "engineering", "value": 280000},
    "eng_tools": {"name": "Tools & Software", "parent": "engineering", "value": 75000},
    "eng_cloud": {"name": "Cloud Services", "parent": "engineering", "value": 65000},
    "eng_training": {"name": "Training", "parent": "engineering", "value": 30000},
    "marketing": {
        "name": "Marketing",
        "parent": "root",
        "value": 280000,
        "children": ["mkt_digital", "mkt_content", "mkt_events", "mkt_brand"],
    },
    "mkt_digital": {"name": "Digital Ads", "parent": "marketing", "value": 120000},
    "mkt_content": {"name": "Content Creation", "parent": "marketing", "value": 65000},
    "mkt_events": {"name": "Events", "parent": "marketing", "value": 55000},
    "mkt_brand": {"name": "Brand Design", "parent": "marketing", "value": 40000},
    "operations": {
        "name": "Operations",
        "parent": "root",
        "value": 180000,
        "children": ["ops_facilities", "ops_equipment", "ops_supplies"],
    },
    "ops_facilities": {"name": "Facilities", "parent": "operations", "value": 95000},
    "ops_equipment": {"name": "Equipment", "parent": "operations", "value": 55000},
    "ops_supplies": {"name": "Supplies", "parent": "operations", "value": 30000},
    "hr": {
        "name": "Human Resources",
        "parent": "root",
        "value": 90000,
        "children": ["hr_recruiting", "hr_benefits", "hr_development"],
    },
    "hr_recruiting": {"name": "Recruiting", "parent": "hr", "value": 35000},
    "hr_benefits": {"name": "Benefits Admin", "parent": "hr", "value": 30000},
    "hr_development": {"name": "Development", "parent": "hr", "value": 25000},
}

# Colorblind-friendly palette with more distinct colors (avoid similar blues)
# Using: blue, yellow, orange, green (distinct from each other)
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=(
        "#306998",  # Blue (Engineering)
        "#FFD43B",  # Yellow (Marketing)
        "#E07A5F",  # Coral/Orange (Operations - distinctly different from blue)
        "#7FB069",  # Green (HR)
        "#9B59B6",  # Purple
        "#3498DB",  # Light blue
        "#E67E22",  # Orange
        "#1ABC9C",  # Teal
    ),
    title_font_size=56,
    label_font_size=36,
    major_label_font_size=32,
    legend_font_size=36,  # Increased for better readability on large canvas
    value_font_size=28,
    tooltip_font_size=28,
)

# Calculate total for percentages
root_children = data["root"]["children"]
total_value = sum(data[child_id]["value"] for child_id in root_children)

# Create main pie chart showing top-level departments
pie_chart = pygal.Pie(
    width=3600,
    height=3600,
    style=custom_style,
    inner_radius=0.35,  # Creates a donut effect for better visual
    title="pie-drilldown · pygal · pyplots.ai",  # Correct title format
    legend_at_bottom=True,
    legend_box_size=36,  # Larger legend boxes
    print_values=True,
    print_labels=True,
    margin=80,
)


# Custom formatter to show both value and percentage
def format_value_with_percent(value):
    percentage = (value / total_value) * 100
    return f"${value:,.0f} ({percentage:.1f}%)"


pie_chart.value_formatter = format_value_with_percent

# Add main category slices with drill-down links via xlink
for child_id in root_children:
    child_data = data[child_id]
    # Each slice has xlink for SVG interactivity
    pie_chart.add(
        child_data["name"], [{"value": child_data["value"], "label": child_data["name"], "xlink": f"#{child_id}"}]
    )

# Add a subtitle showing breadcrumb
pie_chart.x_title = "All Departments  |  Click slice to drill down"

# Render to PNG for static preview
pie_chart.render_to_png("plot.png")

# Create interactive HTML using pygal's native SVG rendering with JavaScript for drilldown
# Generate SVG charts for each level using pygal (native pygal rendering)


def create_pygal_chart(level_id, level_data):
    """Create a pygal pie chart for a specific level."""
    children_ids = level_data.get("children", [])
    if not children_ids:
        return None

    total = sum(data[cid]["value"] for cid in children_ids)

    chart = pygal.Pie(
        width=800,
        height=600,
        style=Style(
            background="transparent",
            plot_background="transparent",
            foreground="#333333",
            foreground_strong="#333333",
            foreground_subtle="#666666",
            colors=("#306998", "#FFD43B", "#E07A5F", "#7FB069", "#9B59B6", "#3498DB", "#E67E22", "#1ABC9C"),
            title_font_size=24,
            label_font_size=14,
            legend_font_size=14,
            value_font_size=12,
            tooltip_font_size=14,
        ),
        inner_radius=0.35,
        legend_at_bottom=True,
        legend_box_size=18,
        print_values=True,
        print_labels=True,
        show_legend=True,
        explicit_size=True,
    )

    def format_val(value):
        pct = (value / total) * 100
        return f"${value:,.0f} ({pct:.1f}%)"

    chart.value_formatter = format_val

    for cid in children_ids:
        child = data[cid]
        chart.add(child["name"], [{"value": child["value"], "label": child["name"]}])

    return chart.render(is_unicode=True)


# Generate SVG for root level
root_svg = create_pygal_chart("root", data["root"])

# Generate SVGs for each department
svg_data = {"root": root_svg}
for dept_id in data["root"]["children"]:
    dept_svg = create_pygal_chart(dept_id, data[dept_id])
    if dept_svg:
        svg_data[dept_id] = dept_svg

html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>pie-drilldown · pygal · pyplots.ai</title>
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
            max-width: 900px;
            width: 100%;
        }
        h1 {
            color: #333;
            text-align: center;
            margin: 0 0 10px 0;
            font-size: 28px;
        }
        .breadcrumb {
            background: #306998;
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 18px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .breadcrumb span {
            cursor: pointer;
        }
        .breadcrumb span:hover {
            text-decoration: underline;
        }
        .breadcrumb .separator {
            opacity: 0.7;
        }
        .breadcrumb .current {
            font-weight: bold;
            cursor: default;
        }
        .breadcrumb .current:hover {
            text-decoration: none;
        }
        #chart-container {
            width: 100%;
            min-height: 500px;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        #chart-container svg {
            max-width: 100%;
            height: auto;
        }
        .back-btn {
            background: #FFD43B;
            color: #333;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            font-size: 16px;
            cursor: pointer;
            margin-right: 15px;
            font-weight: bold;
            transition: background 0.2s;
        }
        .back-btn:hover {
            background: #E6BE35;
        }
        .back-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .hint {
            text-align: center;
            color: #666;
            margin-top: 15px;
            font-size: 14px;
        }
        /* Make pygal SVG slices interactive */
        .slice {
            cursor: pointer;
            transition: opacity 0.2s;
        }
        .slice:hover {
            opacity: 0.8;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>pie-drilldown · pygal · pyplots.ai</h1>
        <div class="breadcrumb">
            <button class="back-btn" id="backBtn" disabled>← Back</button>
            <div id="breadcrumb-path">
                <span class="current">All Departments</span>
            </div>
        </div>
        <div id="chart-container"></div>
        <p class="hint" id="hint">Click on a slice to drill down into its subcategories</p>
    </div>

    <script>
        // Hierarchical data structure
        const hierarchyData = {
            root: {
                name: "All Departments",
                children: ["engineering", "marketing", "operations", "hr"]
            },
            engineering: {
                name: "Engineering",
                parent: "root",
                value: 450000,
                children: ["eng_salaries", "eng_tools", "eng_cloud", "eng_training"]
            },
            eng_salaries: { name: "Salaries", parent: "engineering", value: 280000 },
            eng_tools: { name: "Tools & Software", parent: "engineering", value: 75000 },
            eng_cloud: { name: "Cloud Services", parent: "engineering", value: 65000 },
            eng_training: { name: "Training", parent: "engineering", value: 30000 },
            marketing: {
                name: "Marketing",
                parent: "root",
                value: 280000,
                children: ["mkt_digital", "mkt_content", "mkt_events", "mkt_brand"]
            },
            mkt_digital: { name: "Digital Ads", parent: "marketing", value: 120000 },
            mkt_content: { name: "Content Creation", parent: "marketing", value: 65000 },
            mkt_events: { name: "Events", parent: "marketing", value: 55000 },
            mkt_brand: { name: "Brand Design", parent: "marketing", value: 40000 },
            operations: {
                name: "Operations",
                parent: "root",
                value: 180000,
                children: ["ops_facilities", "ops_equipment", "ops_supplies"]
            },
            ops_facilities: { name: "Facilities", parent: "operations", value: 95000 },
            ops_equipment: { name: "Equipment", parent: "operations", value: 55000 },
            ops_supplies: { name: "Supplies", parent: "operations", value: 30000 },
            hr: {
                name: "Human Resources",
                parent: "root",
                value: 90000,
                children: ["hr_recruiting", "hr_benefits", "hr_development"]
            },
            hr_recruiting: { name: "Recruiting", parent: "hr", value: 35000 },
            hr_benefits: { name: "Benefits Admin", parent: "hr", value: 30000 },
            hr_development: { name: "Development", parent: "hr", value: 25000 }
        };

        // Pre-rendered pygal SVG charts (native pygal output)
        const svgCharts = {
"""

# Insert SVG data as JavaScript strings
for level_id, svg_content in svg_data.items():
    # Escape backticks and backslashes for JavaScript template literal
    escaped_svg = svg_content.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
    html_content += f'            "{level_id}": `{escaped_svg}`,\n'

html_content += """        };

        let currentLevel = 'root';
        let history = [];

        function updateBreadcrumb() {
            const pathDiv = document.getElementById('breadcrumb-path');
            const backBtn = document.getElementById('backBtn');

            let html = '';
            const fullPath = ['root', ...history, currentLevel].filter((v, i, a) => a.indexOf(v) === i);

            fullPath.forEach((id, index) => {
                if (index > 0) {
                    html += '<span class="separator"> > </span>';
                }
                if (id === currentLevel) {
                    html += `<span class="current">${hierarchyData[id].name}</span>`;
                } else {
                    html += `<span onclick="navigateTo('${id}')">${hierarchyData[id].name}</span>`;
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

                // Add click handlers to pygal slices
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

                // Show/hide hint based on whether there are drillable slices
                const hasDrillable = children.some(cid => hierarchyData[cid]?.children);
                hint.style.display = hasDrillable ? 'block' : 'none';
            } else {
                container.innerHTML = '<p style="text-align:center;color:#666;">No sub-categories available</p>';
                hint.style.display = 'none';
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

        // Initial render
        updateBreadcrumb();
        renderChart('root');
    </script>
</body>
</html>"""

with open("plot.html", "w") as f:
    f.write(html_content)
