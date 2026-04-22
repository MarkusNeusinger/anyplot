""" pyplots.ai
pie-drilldown: Drilldown Pie Chart with Click Navigation
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 82/100 | Created: 2025-12-31
"""

import json

import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Hierarchical data: Company budget breakdown by department
# Structure: id, name, value, parent (following spec's data format)
hierarchy_data = {
    "root": {"name": "All Departments", "children": ["engineering", "marketing", "operations", "hr"]},
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

# Color palette - Python Blue first, then colorblind-safe
colors = {
    "Engineering": "#306998",
    "Marketing": "#FFD43B",
    "Operations": "#4CAF50",
    "Human Resources": "#E07A5F",
    # Engineering sub-colors (blue shades)
    "Salaries": "#4A8BBE",
    "Tools & Software": "#6BA3D6",
    "Cloud Services": "#8CBBEE",
    "Training": "#ADD3F5",
    # Marketing sub-colors (yellow/gold shades)
    "Digital Ads": "#F5C800",
    "Content Creation": "#E6BE35",
    "Events": "#D4A72C",
    "Brand Design": "#C49022",
    # Operations sub-colors (green shades)
    "Facilities": "#66BB6A",
    "Equipment": "#81C784",
    "Supplies": "#A5D6A7",
    # HR sub-colors (coral shades)
    "Recruiting": "#EF9A9A",
    "Benefits Admin": "#F48FB1",
    "Development": "#CE93D8",
}

# Create data for root level (main departments)
# Order slices so labels are distributed around the circle without overlap
# Large slices get their labels far apart, small slices fill gaps
root_children = hierarchy_data["root"]["children"]
# Order by size descending, then interleave to spread labels
# Eng (45%), Mkt (28%), Ops (18%), HR (9%) - put largest at top, smallest at bottom
reordered_children = ["engineering", "marketing", "operations", "hr"]
categories = [hierarchy_data[child_id]["name"] for child_id in reordered_children]
values = [hierarchy_data[child_id]["value"] for child_id in reordered_children]
total = sum(values)
percentages = [(v / total) * 100 for v in values]

# Format value labels with dollar amounts (e.g., "$450K")
value_labels = [f"${v // 1000}K" for v in values]

df = pd.DataFrame({"category": categories, "value": values, "pct": percentages, "value_label": value_labels})

# Preserve category order
df["category"] = pd.Categorical(df["category"], categories=categories, ordered=True)

# Define colors in order
slice_colors = [colors[cat] for cat in categories]

# Create percentage label column for proper formatting
df["pct_label"] = [f"{p:.1f}%" for p in percentages]

# Create combined label with category name, value, and percentage on one line
df["combined_label"] = [
    f"{cat}: {lbl} ({pct:.0f}%)" for cat, lbl, pct in zip(categories, value_labels, percentages, strict=True)
]

# Create main pie chart for static PNG
# Use pie labels inside the slices to avoid overlap issues
plot = (
    ggplot(df)  # noqa: F405
    + geom_pie(  # noqa: F405
        aes(slice="value", fill="category"),  # noqa: F405
        stat="identity",
        size=50,  # Good size for visibility
        hole=0.35,  # Donut style
        stroke=3,  # White borders between slices
        color="white",  # Border color
        spacer_width=0.3,  # Small gaps between slices
        labels=layer_labels()  # noqa: F405
        .line("@{pct_label}")  # Only show percentage inside
        .size(18),
    )
    + scale_fill_manual(values=slice_colors)  # noqa: F405
    + labs(  # noqa: F405
        title="pie-drilldown · letsplot · pyplots.ai",
        subtitle="Company Budget Breakdown · Click slice to drill down (HTML)",
        fill="",  # No legend title needed
    )
    + ggsize(1600, 900)  # noqa: F405 - Landscape format
    + guides(fill=guide_legend(ncol=1))  # noqa: F405 - Single column legend
    + scale_fill_manual(  # noqa: F405
        values=slice_colors, labels=[f"{cat} - {lbl}" for cat, lbl in zip(categories, value_labels, strict=True)]
    )
    + theme_void()  # noqa: F405
    + theme(  # noqa: F405
        plot_title=element_text(size=32, hjust=0.5, face="bold"),  # noqa: F405
        plot_subtitle=element_text(size=18, hjust=0.5, color="#666666"),  # noqa: F405
        legend_title=element_text(size=20),  # noqa: F405
        legend_text=element_text(size=20),  # noqa: F405
        legend_position="right",
        plot_margin=[40, 60, 40, 60],
    )
)

# Save static PNG (scale 3 for 4800x2700)
export_ggsave(plot, filename="plot.png", path=".", scale=3)


# Prepare data for all levels as JSON (inline, no function)
levels_data = {}
for level_id in ["root", "engineering", "marketing", "operations", "hr"]:
    level_data = hierarchy_data[level_id]
    if "children" in level_data:
        children_ids = level_data["children"]
        cats = [hierarchy_data[cid]["name"] for cid in children_ids]
        vals = [hierarchy_data[cid]["value"] for cid in children_ids]
        tot = sum(vals)
        pcts = [(v / tot) * 100 for v in vals]
        levels_data[level_id] = {
            "name": hierarchy_data[level_id]["name"],
            "categories": cats,
            "values": vals,
            "percentages": pcts,
            "colors": [colors.get(cat, "#306998") for cat in cats],
            "children": hierarchy_data[level_id].get("children", []),
            "parent": hierarchy_data[level_id].get("parent"),
        }

# HTML template with embedded JavaScript for drilldown
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>pie-drilldown · letsplot · pyplots.ai</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }}
        .container {{
            background: white;
            border-radius: 16px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            padding: 40px;
            max-width: 900px;
            width: 100%;
        }}
        h1 {{
            color: #333;
            text-align: center;
            font-size: 28px;
            margin-bottom: 8px;
        }}
        .subtitle {{
            color: #666;
            text-align: center;
            font-size: 16px;
            margin-bottom: 24px;
        }}
        .breadcrumb {{
            background: #306998;
            color: white;
            padding: 14px 20px;
            border-radius: 10px;
            margin-bottom: 24px;
            font-size: 18px;
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .back-btn {{
            background: #FFD43B;
            color: #333;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .back-btn:hover {{
            background: #E6BE35;
            transform: translateX(-2px);
        }}
        .back-btn:disabled {{
            opacity: 0.4;
            cursor: not-allowed;
            transform: none;
        }}
        .breadcrumb-path {{
            display: flex;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
        }}
        .breadcrumb-path span {{
            cursor: pointer;
            transition: opacity 0.2s;
        }}
        .breadcrumb-path span:hover:not(.current) {{
            text-decoration: underline;
            opacity: 0.9;
        }}
        .breadcrumb-path .separator {{
            opacity: 0.6;
        }}
        .breadcrumb-path .current {{
            font-weight: 600;
            cursor: default;
        }}
        #chart-container {{
            position: relative;
            width: 100%;
            height: 500px;
        }}
        #pie-canvas {{
            width: 100%;
            height: 100%;
        }}
        .legend {{
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 16px;
            margin-top: 24px;
            padding: 16px;
            background: #f8f9fa;
            border-radius: 10px;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 14px;
            color: #333;
            cursor: pointer;
            padding: 6px 12px;
            border-radius: 6px;
            transition: background 0.2s;
        }}
        .legend-item:hover {{
            background: #e9ecef;
        }}
        .legend-color {{
            width: 16px;
            height: 16px;
            border-radius: 4px;
        }}
        .hint {{
            text-align: center;
            color: #888;
            margin-top: 16px;
            font-size: 14px;
        }}
        .total-display {{
            text-align: center;
            margin-top: 16px;
            font-size: 20px;
            color: #333;
        }}
        .total-display .amount {{
            font-weight: 700;
            color: #306998;
            font-size: 28px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>pie-drilldown · letsplot · pyplots.ai</h1>
        <p class="subtitle">Company Budget Breakdown with Interactive Navigation</p>

        <div class="breadcrumb">
            <button class="back-btn" id="backBtn" disabled>← Back</button>
            <div class="breadcrumb-path" id="breadcrumb-path">
                <span class="current">All Departments</span>
            </div>
        </div>

        <div id="chart-container">
            <canvas id="pie-canvas"></canvas>
        </div>

        <div class="legend" id="legend"></div>

        <div class="total-display">
            Total: <span class="amount" id="total-amount">$1,000,000</span>
        </div>

        <p class="hint" id="hint">Click on a slice to drill down into subcategories</p>
    </div>

    <script>
        // Hierarchy data from Python
        const hierarchyData = {json.dumps(hierarchy_data)};
        const levelsData = {json.dumps(levels_data)};
        const colorMap = {json.dumps(colors)};

        let currentLevel = 'root';
        let history = [];

        const canvas = document.getElementById('pie-canvas');
        const ctx = canvas.getContext('2d');
        const legendEl = document.getElementById('legend');
        const totalEl = document.getElementById('total-amount');
        const hintEl = document.getElementById('hint');
        const backBtn = document.getElementById('backBtn');

        // High DPI canvas setup
        function setupCanvas() {{
            const rect = canvas.parentElement.getBoundingClientRect();
            const dpr = window.devicePixelRatio || 1;
            canvas.width = rect.width * dpr;
            canvas.height = rect.height * dpr;
            canvas.style.width = rect.width + 'px';
            canvas.style.height = rect.height + 'px';
            ctx.scale(dpr, dpr);
        }}

        // Draw pie chart
        function drawPie(levelId, animated = true) {{
            const data = levelsData[levelId];
            if (!data) return;

            setupCanvas();
            const rect = canvas.parentElement.getBoundingClientRect();
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            const outerRadius = Math.min(centerX, centerY) - 60;
            const innerRadius = outerRadius * 0.4; // Donut hole

            ctx.clearRect(0, 0, rect.width, rect.height);

            const total = data.values.reduce((a, b) => a + b, 0);
            let startAngle = -Math.PI / 2;

            // Store slice positions for click detection
            window.slices = [];

            data.values.forEach((value, i) => {{
                const sliceAngle = (value / total) * 2 * Math.PI;
                const endAngle = startAngle + sliceAngle;

                // Store slice info
                window.slices.push({{
                    startAngle,
                    endAngle,
                    category: data.categories[i],
                    value,
                    childId: data.children[i],
                    color: data.colors[i]
                }});

                // Draw slice
                ctx.beginPath();
                ctx.moveTo(centerX + innerRadius * Math.cos(startAngle),
                          centerY + innerRadius * Math.sin(startAngle));
                ctx.arc(centerX, centerY, outerRadius, startAngle, endAngle);
                ctx.lineTo(centerX + innerRadius * Math.cos(endAngle),
                          centerY + innerRadius * Math.sin(endAngle));
                ctx.arc(centerX, centerY, innerRadius, endAngle, startAngle, true);
                ctx.closePath();

                ctx.fillStyle = data.colors[i];
                ctx.fill();
                ctx.strokeStyle = 'white';
                ctx.lineWidth = 3;
                ctx.stroke();

                // Draw label
                const midAngle = startAngle + sliceAngle / 2;
                const labelRadius = outerRadius + 30;
                const labelX = centerX + labelRadius * Math.cos(midAngle);
                const labelY = centerY + labelRadius * Math.sin(midAngle);

                const pct = ((value / total) * 100).toFixed(1);

                ctx.fillStyle = '#333';
                ctx.font = 'bold 14px -apple-system, sans-serif';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(data.categories[i], labelX, labelY - 10);
                ctx.font = '13px -apple-system, sans-serif';
                ctx.fillStyle = '#666';
                ctx.fillText(`${{(value/1000).toFixed(0)}}K ({{pct}}%)`, labelX, labelY + 10);

                startAngle = endAngle;
            }});

            // Draw center text
            ctx.fillStyle = '#333';
            ctx.font = 'bold 18px -apple-system, sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText(data.name, centerX, centerY - 10);
            ctx.font = '14px -apple-system, sans-serif';
            ctx.fillStyle = '#666';
            ctx.fillText(`${{(total/1000000).toFixed(2)}}M`, centerX, centerY + 15);

            // Update legend
            updateLegend(data);

            // Update total display
            totalEl.textContent = `${{total.toLocaleString()}}`;

            // Update hint
            const hasDrillable = data.children.some(cid => hierarchyData[cid]?.children);
            hintEl.style.display = hasDrillable ? 'block' : 'none';
            hintEl.textContent = hasDrillable
                ? 'Click on a slice to drill down into subcategories'
                : 'This is the lowest level - no further breakdown available';
        }}

        function updateLegend(data) {{
            legendEl.innerHTML = data.categories.map((cat, i) => `
                <div class="legend-item" data-index="${{i}}">
                    <div class="legend-color" style="background: ${{data.colors[i]}}"></div>
                    <span>${{cat}}</span>
                </div>
            `).join('');
        }}

        function updateBreadcrumb() {{
            const pathDiv = document.getElementById('breadcrumb-path');
            const fullPath = ['root', ...history];
            if (!fullPath.includes(currentLevel)) fullPath.push(currentLevel);

            let html = '';
            fullPath.forEach((id, index) => {{
                if (index > 0) html += '<span class="separator"> > </span>';
                const name = hierarchyData[id]?.name || id;
                if (id === currentLevel) {{
                    html += `<span class="current">${{name}}</span>`;
                }} else {{
                    html += `<span onclick="navigateTo('${{id}}')">${{name}}</span>`;
                }}
            }});

            pathDiv.innerHTML = html;
            backBtn.disabled = currentLevel === 'root';
        }}

        function drillDown(childId) {{
            if (levelsData[childId]) {{
                history.push(currentLevel);
                currentLevel = childId;
                updateBreadcrumb();
                drawPie(currentLevel);
            }}
        }}

        function goBack() {{
            if (history.length > 0) {{
                currentLevel = history.pop();
                updateBreadcrumb();
                drawPie(currentLevel);
            }}
        }}

        function navigateTo(id) {{
            const idx = history.indexOf(id);
            if (idx >= 0) {{
                history = history.slice(0, idx);
            }} else {{
                history = [];
            }}
            currentLevel = id;
            updateBreadcrumb();
            drawPie(currentLevel);
        }}

        // Click detection
        canvas.addEventListener('click', function(e) {{
            const rect = canvas.getBoundingClientRect();
            const x = e.clientX - rect.left - rect.width / 2;
            const y = e.clientY - rect.top - rect.height / 2;
            const angle = Math.atan2(y, x);
            const distance = Math.sqrt(x * x + y * y);

            const outerRadius = (Math.min(rect.width, rect.height) / 2) - 60;
            const innerRadius = outerRadius * 0.4;

            if (distance < innerRadius || distance > outerRadius) return;

            // Normalize angle to match our drawing
            let clickAngle = angle;
            if (clickAngle < -Math.PI / 2) clickAngle += 2 * Math.PI;

            window.slices?.forEach(slice => {{
                let start = slice.startAngle;
                let end = slice.endAngle;

                // Normalize angles for comparison
                if (start < -Math.PI / 2) start += 2 * Math.PI;
                if (end < -Math.PI / 2) end += 2 * Math.PI;

                if ((clickAngle >= start && clickAngle < end) ||
                    (start > end && (clickAngle >= start || clickAngle < end))) {{
                    if (hierarchyData[slice.childId]?.children) {{
                        drillDown(slice.childId);
                    }}
                }}
            }});
        }});

        // Hover effect for cursor
        canvas.addEventListener('mousemove', function(e) {{
            const rect = canvas.getBoundingClientRect();
            const x = e.clientX - rect.left - rect.width / 2;
            const y = e.clientY - rect.top - rect.height / 2;
            const distance = Math.sqrt(x * x + y * y);

            const outerRadius = (Math.min(rect.width, rect.height) / 2) - 60;
            const innerRadius = outerRadius * 0.4;

            if (distance >= innerRadius && distance <= outerRadius) {{
                const angle = Math.atan2(y, x);
                let clickAngle = angle;
                if (clickAngle < -Math.PI / 2) clickAngle += 2 * Math.PI;

                let isClickable = false;
                window.slices?.forEach(slice => {{
                    let start = slice.startAngle;
                    let end = slice.endAngle;
                    if (start < -Math.PI / 2) start += 2 * Math.PI;
                    if (end < -Math.PI / 2) end += 2 * Math.PI;

                    if ((clickAngle >= start && clickAngle < end) ||
                        (start > end && (clickAngle >= start || clickAngle < end))) {{
                        if (hierarchyData[slice.childId]?.children) {{
                            isClickable = true;
                        }}
                    }}
                }});
                canvas.style.cursor = isClickable ? 'pointer' : 'default';
            }} else {{
                canvas.style.cursor = 'default';
            }}
        }});

        backBtn.addEventListener('click', goBack);

        // Handle window resize
        window.addEventListener('resize', () => drawPie(currentLevel, false));

        // Initial render
        updateBreadcrumb();
        drawPie('root');
    </script>
</body>
</html>"""

with open("plot.html", "w") as f:
    f.write(html_content)
