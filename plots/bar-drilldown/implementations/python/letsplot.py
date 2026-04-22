""" pyplots.ai
bar-drilldown: Column Chart with Hierarchical Drilling
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-16
"""

import json

import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Hierarchical data: Sales breakdown by region (following spec's data format)
# Structure: id, name, value, parent (null for root level)
hierarchy_data = {
    "root": {"id": "root", "name": "Total Sales", "children": ["north", "south", "east", "west"]},
    "north": {
        "id": "north",
        "name": "North Region",
        "parent": "root",
        "value": 485000,
        "children": ["north_q1", "north_q2", "north_q3", "north_q4"],
    },
    "north_q1": {"id": "north_q1", "name": "Q1", "parent": "north", "value": 98000},
    "north_q2": {"id": "north_q2", "name": "Q2", "parent": "north", "value": 125000},
    "north_q3": {"id": "north_q3", "name": "Q3", "parent": "north", "value": 142000},
    "north_q4": {"id": "north_q4", "name": "Q4", "parent": "north", "value": 120000},
    "south": {
        "id": "south",
        "name": "South Region",
        "parent": "root",
        "value": 392000,
        "children": ["south_q1", "south_q2", "south_q3", "south_q4"],
    },
    "south_q1": {"id": "south_q1", "name": "Q1", "parent": "south", "value": 85000},
    "south_q2": {"id": "south_q2", "name": "Q2", "parent": "south", "value": 98000},
    "south_q3": {"id": "south_q3", "name": "Q3", "parent": "south", "value": 112000},
    "south_q4": {"id": "south_q4", "name": "Q4", "parent": "south", "value": 97000},
    "east": {
        "id": "east",
        "name": "East Region",
        "parent": "root",
        "value": 528000,
        "children": ["east_q1", "east_q2", "east_q3", "east_q4"],
    },
    "east_q1": {"id": "east_q1", "name": "Q1", "parent": "east", "value": 115000},
    "east_q2": {"id": "east_q2", "name": "Q2", "parent": "east", "value": 138000},
    "east_q3": {"id": "east_q3", "name": "Q3", "parent": "east", "value": 155000},
    "east_q4": {"id": "east_q4", "name": "Q4", "parent": "east", "value": 120000},
    "west": {
        "id": "west",
        "name": "West Region",
        "parent": "root",
        "value": 445000,
        "children": ["west_q1", "west_q2", "west_q3", "west_q4"],
    },
    "west_q1": {"id": "west_q1", "name": "Q1", "parent": "west", "value": 92000},
    "west_q2": {"id": "west_q2", "name": "Q2", "parent": "west", "value": 118000},
    "west_q3": {"id": "west_q3", "name": "Q3", "parent": "west", "value": 128000},
    "west_q4": {"id": "west_q4", "name": "Q4", "parent": "west", "value": 107000},
}

# Color palette - Python Blue primary, colorblind-safe for categories
colors = {
    "North Region": "#306998",
    "South Region": "#FFD43B",
    "East Region": "#4CAF50",
    "West Region": "#E07A5F",
    # Quarter colors (shades within each region)
    "Q1": "#5A8BBF",
    "Q2": "#7BA3D1",
    "Q3": "#9CBBE3",
    "Q4": "#BDD3F5",
}

# Create data for root level (main regions)
root_children = hierarchy_data["root"]["children"]
categories = [hierarchy_data[child_id]["name"] for child_id in root_children]
values = [hierarchy_data[child_id]["value"] for child_id in root_children]

# Format value labels
value_labels = [f"${v // 1000}K" for v in values]

df = pd.DataFrame({"category": categories, "value": values, "value_label": value_labels})

# Preserve category order
df["category"] = pd.Categorical(df["category"], categories=categories, ordered=True)

# Define colors in order
slice_colors = [colors[cat] for cat in categories]

# Create main bar chart for static PNG
plot = (
    ggplot(df, aes(x="category", y="value", fill="category"))  # noqa: F405
    + geom_bar(  # noqa: F405
        stat="identity", width=0.7, show_legend=False, color="white", size=1
    )
    + geom_text(  # noqa: F405
        aes(label="value_label"),  # noqa: F405
        vjust=-0.5,
        size=16,
        fontface="bold",
    )
    + scale_fill_manual(values=slice_colors)  # noqa: F405
    + scale_y_continuous(format="${,.0f}", expand=[0.1, 0, 0.15, 0])  # noqa: F405
    + labs(  # noqa: F405
        title="bar-drilldown · letsplot · pyplots.ai",
        subtitle="Regional Sales · Click column to drill down (HTML)",
        x="",
        y="Sales ($)",
    )
    + ggsize(1600, 900)  # noqa: F405
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        plot_title=element_text(size=32, hjust=0.5, face="bold"),  # noqa: F405
        plot_subtitle=element_text(size=18, hjust=0.5, color="#666666"),  # noqa: F405
        axis_title_y=element_text(size=20),  # noqa: F405
        axis_text_x=element_text(size=18),  # noqa: F405
        axis_text_y=element_text(size=16),  # noqa: F405
        panel_grid_major_x=element_blank(),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
        panel_grid_major_y=element_line(color="#E0E0E0", size=0.5),  # noqa: F405
        plot_margin=[40, 40, 40, 40],
    )
)

# Save static PNG (scale 3 for 4800x2700)
export_ggsave(plot, filename="plot.png", path=".", scale=3)

# Prepare data for all levels as JSON
levels_data = {}
for level_id in ["root", "north", "south", "east", "west"]:
    level_data = hierarchy_data[level_id]
    if "children" in level_data:
        children_ids = level_data["children"]
        cats = [hierarchy_data[cid]["name"] for cid in children_ids]
        vals = [hierarchy_data[cid]["value"] for cid in children_ids]
        tot = sum(vals)
        # Use parent's color for quarter breakdown, or individual colors for regions
        if level_id == "root":
            level_colors = [colors.get(cat, "#306998") for cat in cats]
        else:
            # For quarterly breakdown, use gradient of parent color
            parent_name = hierarchy_data[level_id]["name"]
            base_color = colors.get(parent_name, "#306998")
            level_colors = [base_color] * len(cats)
        levels_data[level_id] = {
            "name": hierarchy_data[level_id]["name"],
            "categories": cats,
            "values": vals,
            "colors": level_colors,
            "children": children_ids,
            "parent": hierarchy_data[level_id].get("parent"),
        }

# HTML template with embedded JavaScript for drilldown
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>bar-drilldown · letsplot · pyplots.ai</title>
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
            max-width: 1000px;
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
            height: 450px;
        }}
        #bar-canvas {{
            width: 100%;
            height: 100%;
        }}
        .total-display {{
            text-align: center;
            margin-top: 20px;
            font-size: 20px;
            color: #333;
        }}
        .total-display .amount {{
            font-weight: 700;
            color: #306998;
            font-size: 28px;
        }}
        .hint {{
            text-align: center;
            color: #888;
            margin-top: 16px;
            font-size: 14px;
        }}
        .tooltip {{
            position: absolute;
            background: rgba(0, 0, 0, 0.85);
            color: white;
            padding: 12px 16px;
            border-radius: 8px;
            font-size: 14px;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.2s;
            z-index: 100;
        }}
        .tooltip.visible {{
            opacity: 1;
        }}
        .tooltip .title {{
            font-weight: 600;
            font-size: 16px;
            margin-bottom: 6px;
        }}
        .tooltip .value {{
            color: #FFD43B;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>bar-drilldown · letsplot · pyplots.ai</h1>
        <p class="subtitle">Regional Sales Breakdown with Interactive Drilling</p>

        <div class="breadcrumb">
            <button class="back-btn" id="backBtn" disabled>← Back</button>
            <div class="breadcrumb-path" id="breadcrumb-path">
                <span class="current">Total Sales</span>
            </div>
        </div>

        <div id="chart-container">
            <canvas id="bar-canvas"></canvas>
            <div class="tooltip" id="tooltip"></div>
        </div>

        <div class="total-display">
            Level Total: <span class="amount" id="total-amount">$1,850,000</span>
        </div>

        <p class="hint" id="hint">Click on a column to drill down into quarterly breakdown</p>
    </div>

    <script>
        // Hierarchy data from Python
        const hierarchyData = {json.dumps(hierarchy_data)};
        const levelsData = {json.dumps(levels_data)};

        let currentLevel = 'root';
        let history = [];

        const canvas = document.getElementById('bar-canvas');
        const ctx = canvas.getContext('2d');
        const totalEl = document.getElementById('total-amount');
        const hintEl = document.getElementById('hint');
        const backBtn = document.getElementById('backBtn');
        const tooltipEl = document.getElementById('tooltip');

        // Bar positions for click/hover detection
        let bars = [];

        // High DPI canvas setup
        function setupCanvas() {{
            const rect = canvas.parentElement.getBoundingClientRect();
            const dpr = window.devicePixelRatio || 1;
            canvas.width = rect.width * dpr;
            canvas.height = rect.height * dpr;
            canvas.style.width = rect.width + 'px';
            canvas.style.height = rect.height + 'px';
            ctx.scale(dpr, dpr);
            return rect;
        }}

        // Animation variables
        let animationProgress = 0;
        let animationFrame = null;

        // Draw bar chart with animation
        function drawBars(levelId, animate = true) {{
            const data = levelsData[levelId];
            if (!data) return;

            const rect = setupCanvas();
            const padding = {{ top: 60, right: 40, bottom: 60, left: 100 }};
            const chartWidth = rect.width - padding.left - padding.right;
            const chartHeight = rect.height - padding.top - padding.bottom;

            const maxValue = Math.max(...data.values) * 1.15;
            const barWidth = (chartWidth / data.categories.length) * 0.65;
            const barGap = (chartWidth / data.categories.length) * 0.35;

            bars = [];

            function render(progress) {{
                ctx.clearRect(0, 0, rect.width, rect.height);

                // Draw gridlines
                ctx.strokeStyle = '#E0E0E0';
                ctx.lineWidth = 1;
                const gridLines = 5;
                for (let i = 0; i <= gridLines; i++) {{
                    const y = padding.top + (chartHeight / gridLines) * i;
                    ctx.beginPath();
                    ctx.moveTo(padding.left, y);
                    ctx.lineTo(rect.width - padding.right, y);
                    ctx.stroke();

                    // Y-axis labels
                    const value = maxValue * (1 - i / gridLines);
                    ctx.fillStyle = '#666';
                    ctx.font = '14px -apple-system, sans-serif';
                    ctx.textAlign = 'right';
                    ctx.textBaseline = 'middle';
                    ctx.fillText('$' + (value / 1000).toFixed(0) + 'K', padding.left - 12, y);
                }}

                // Draw bars
                bars = [];
                data.values.forEach((value, i) => {{
                    const barHeight = (value / maxValue) * chartHeight * progress;
                    const x = padding.left + (i * (barWidth + barGap)) + barGap / 2;
                    const y = padding.top + chartHeight - barHeight;

                    bars.push({{
                        x, y: padding.top + chartHeight - (value / maxValue) * chartHeight,
                        width: barWidth,
                        height: (value / maxValue) * chartHeight,
                        category: data.categories[i],
                        value: value,
                        childId: data.children[i],
                        color: data.colors[i]
                    }});

                    // Bar fill
                    ctx.fillStyle = data.colors[i];
                    ctx.beginPath();
                    ctx.roundRect(x, y, barWidth, barHeight, [6, 6, 0, 0]);
                    ctx.fill();

                    // Bar border
                    ctx.strokeStyle = 'white';
                    ctx.lineWidth = 2;
                    ctx.stroke();

                    // Value label on top
                    if (progress > 0.9) {{
                        ctx.fillStyle = '#333';
                        ctx.font = 'bold 16px -apple-system, sans-serif';
                        ctx.textAlign = 'center';
                        ctx.textBaseline = 'bottom';
                        ctx.fillText('$' + (value / 1000).toFixed(0) + 'K', x + barWidth / 2, y - 8);
                    }}

                    // X-axis labels
                    ctx.fillStyle = '#333';
                    ctx.font = '15px -apple-system, sans-serif';
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'top';
                    ctx.fillText(data.categories[i], x + barWidth / 2, padding.top + chartHeight + 12);
                }});

                // Y-axis title
                ctx.save();
                ctx.translate(25, padding.top + chartHeight / 2);
                ctx.rotate(-Math.PI / 2);
                ctx.fillStyle = '#333';
                ctx.font = 'bold 16px -apple-system, sans-serif';
                ctx.textAlign = 'center';
                ctx.fillText('Sales ($)', 0, 0);
                ctx.restore();
            }}

            if (animate) {{
                if (animationFrame) cancelAnimationFrame(animationFrame);
                animationProgress = 0;
                const startTime = performance.now();
                const duration = 500;

                function animateStep(currentTime) {{
                    const elapsed = currentTime - startTime;
                    animationProgress = Math.min(elapsed / duration, 1);
                    // Ease out cubic
                    const easedProgress = 1 - Math.pow(1 - animationProgress, 3);
                    render(easedProgress);

                    if (animationProgress < 1) {{
                        animationFrame = requestAnimationFrame(animateStep);
                    }}
                }}
                animationFrame = requestAnimationFrame(animateStep);
            }} else {{
                render(1);
            }}

            // Update total display
            const total = data.values.reduce((a, b) => a + b, 0);
            totalEl.textContent = '$' + total.toLocaleString();

            // Update hint
            const hasDrillable = data.children.some(cid => hierarchyData[cid]?.children);
            hintEl.style.display = 'block';
            hintEl.textContent = hasDrillable
                ? 'Click on a column to drill down into quarterly breakdown'
                : 'Lowest level reached · Click breadcrumb to navigate back';
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
                drawBars(currentLevel);
            }}
        }}

        function goBack() {{
            if (history.length > 0) {{
                currentLevel = history.pop();
                updateBreadcrumb();
                drawBars(currentLevel);
            }}
        }}

        window.navigateTo = function(id) {{
            const idx = history.indexOf(id);
            if (idx >= 0) {{
                history = history.slice(0, idx);
            }} else {{
                history = [];
            }}
            currentLevel = id;
            updateBreadcrumb();
            drawBars(currentLevel);
        }};

        // Click detection
        canvas.addEventListener('click', function(e) {{
            const rect = canvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            bars.forEach(bar => {{
                if (x >= bar.x && x <= bar.x + bar.width &&
                    y >= bar.y && y <= bar.y + bar.height) {{
                    if (hierarchyData[bar.childId]?.children) {{
                        drillDown(bar.childId);
                    }}
                }}
            }});
        }});

        // Hover effects
        canvas.addEventListener('mousemove', function(e) {{
            const rect = canvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            let hoveredBar = null;
            bars.forEach(bar => {{
                if (x >= bar.x && x <= bar.x + bar.width &&
                    y >= bar.y && y <= bar.y + bar.height) {{
                    hoveredBar = bar;
                }}
            }});

            if (hoveredBar) {{
                const isClickable = hierarchyData[hoveredBar.childId]?.children;
                canvas.style.cursor = isClickable ? 'pointer' : 'default';

                // Show tooltip
                tooltipEl.innerHTML = `
                    <div class="title">${{hoveredBar.category}}</div>
                    <div><span class="value">${{(hoveredBar.value).toLocaleString('en-US', {{style: 'currency', currency: 'USD', minimumFractionDigits: 0}})}}</span></div>
                    ${{isClickable ? '<div style="margin-top:6px;font-size:12px;opacity:0.8">Click to drill down</div>' : ''}}
                `;
                tooltipEl.style.left = (e.clientX - rect.left + 15) + 'px';
                tooltipEl.style.top = (e.clientY - rect.top - 10) + 'px';
                tooltipEl.classList.add('visible');
            }} else {{
                canvas.style.cursor = 'default';
                tooltipEl.classList.remove('visible');
            }}
        }});

        canvas.addEventListener('mouseleave', function() {{
            tooltipEl.classList.remove('visible');
        }});

        backBtn.addEventListener('click', goBack);

        // Handle window resize
        window.addEventListener('resize', () => drawBars(currentLevel, false));

        // Initial render
        updateBreadcrumb();
        drawBars('root');
    </script>
</body>
</html>"""

with open("plot.html", "w") as f:
    f.write(html_content)
