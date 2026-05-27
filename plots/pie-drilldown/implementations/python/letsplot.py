""" anyplot.ai
pie-drilldown: Drilldown Pie Chart with Click Navigation
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-15
"""

import json
import os

import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Okabe-Ito palette (using position 1 as first series)
IMPRINT = [
    "#009E73",  # bluish green (brand)
    "#C475FD",  # vermillion
    "#4467A3",  # blue
    "#BD8233",  # reddish purple
]

# Hierarchical data: Company budget breakdown by department
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

# Color scheme: Okabe-Ito for main departments, with shade variations for subcategories
colors = {
    "Engineering": IMPRINT[0],  # #009E73
    "Marketing": IMPRINT[1],  # #C475FD
    "Operations": IMPRINT[2],  # #4467A3
    "Human Resources": IMPRINT[3],  # #BD8233
    # Engineering sub-colors (green shades)
    "Salaries": "#4A8BBE",
    "Tools & Software": "#6BA3D6",
    "Cloud Services": "#8CBBEE",
    "Training": "#ADD3F5",
    # Marketing sub-colors (orange/red shades)
    "Digital Ads": "#E89A3C",
    "Content Creation": "#E6A84E",
    "Events": "#E3B660",
    "Brand Design": "#E0C472",
    # Operations sub-colors (blue shades)
    "Facilities": "#5A9BD4",
    "Equipment": "#75AAE0",
    "Supplies": "#90B9EC",
    # HR sub-colors (purple shades)
    "Recruiting": "#D8A7C7",
    "Benefits Admin": "#DFB5D3",
    "Development": "#E6C3DF",
}

# Create data for root level (main departments)
root_children = hierarchy_data["root"]["children"]
categories = [hierarchy_data[child_id]["name"] for child_id in root_children]
values = [hierarchy_data[child_id]["value"] for child_id in root_children]
total = sum(values)
percentages = [(v / total) * 100 for v in values]

# Format value labels
value_labels = [f"${v // 1000}K" for v in values]
df = pd.DataFrame({"category": categories, "value": values, "pct": percentages, "value_label": value_labels})

# Preserve category order
df["category"] = pd.Categorical(df["category"], categories=categories, ordered=True)

# Define colors in order
slice_colors = [colors[cat] for cat in categories]

# Create labels for display
df["pct_label"] = [f"{p:.1f}%" for p in percentages]
df["combined_label"] = [
    f"{cat}: {lbl} ({pct:.0f}%)" for cat, lbl, pct in zip(categories, value_labels, percentages, strict=True)
]

# Create main pie chart for static PNG
anyplot_theme = (  # noqa: F405
    theme(  # noqa: F405
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),  # noqa: F405
        panel_background=element_rect(fill=PAGE_BG),  # noqa: F405
        axis_title=element_text(color=INK),  # noqa: F405
        axis_text=element_text(color=INK_SOFT),  # noqa: F405
        plot_title=element_text(color=INK, size=24),  # noqa: F405
        plot_subtitle=element_text(color=INK_SOFT, size=16),  # noqa: F405
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),  # noqa: F405
        legend_text=element_text(color=INK_SOFT, size=14),  # noqa: F405
        legend_title=element_text(color=INK, size=16),  # noqa: F405
    )
)

plot = (  # noqa: F405
    ggplot(df)  # noqa: F405
    + geom_pie(  # noqa: F405
        aes(slice="value", fill="category"),  # noqa: F405
        stat="identity",
        size=50,
        hole=0.35,
        stroke=3,
        color=PAGE_BG,
        spacer_width=0.3,
        labels=layer_labels().line("@{pct_label}").size(18),  # noqa: F405
    )
    + scale_fill_manual(values=slice_colors)  # noqa: F405
    + labs(  # noqa: F405
        title="pie-drilldown · letsplot · anyplot.ai",
        subtitle="Company Budget Breakdown · Click slices to explore (interactive HTML available)",
        fill="Department",
    )
    + ggsize(1600, 900)  # noqa: F405
    + guides(fill=guide_legend(ncol=1))  # noqa: F405
    + anyplot_theme
    + theme_void()  # noqa: F405
    + theme(  # noqa: F405
        plot_title=element_text(size=24, hjust=0.5, face="bold"),  # noqa: F405
        plot_subtitle=element_text(size=16, hjust=0.5),  # noqa: F405
        legend_position="right",
        plot_margin=[40, 60, 40, 60],
    )
)

# Save static PNG (scale 3 for 4800x2700)
export_ggsave(plot, filename=f"plot-{THEME}.png", path=".", scale=3)

# Prepare data for all levels as JSON (for HTML interactivity)
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
            "colors": [colors.get(cat, IMPRINT[0]) for cat in cats],
            "children": hierarchy_data[level_id].get("children", []),
            "parent": hierarchy_data[level_id].get("parent"),
        }

# HTML template with embedded JavaScript for drilldown
html_bg = "#FAF8F1" if THEME == "light" else "#1A1A17"
html_text = "#1A1A17" if THEME == "light" else "#F0EFE8"
html_text_soft = "#4A4A44" if THEME == "light" else "#B8B7B0"
html_elevated = "#FFFDF6" if THEME == "light" else "#242420"

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>pie-drilldown · letsplot · anyplot.ai</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: {html_bg};
            color: {html_text};
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }}
        .container {{
            background: {html_bg};
            border-radius: 12px;
            padding: 40px;
            max-width: 950px;
            width: 100%;
            box-shadow: 0 2px 16px rgba(0,0,0,0.08);
        }}
        h1 {{
            color: {html_text};
            text-align: center;
            font-size: 26px;
            margin-bottom: 8px;
            font-weight: 500;
        }}
        .subtitle {{
            color: {html_text_soft};
            text-align: center;
            font-size: 15px;
            margin-bottom: 24px;
        }}
        .breadcrumb {{
            background: {html_elevated};
            color: {html_text};
            padding: 12px 16px;
            border-radius: 8px;
            margin-bottom: 24px;
            font-size: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .back-btn {{
            background: {IMPRINT[0]};
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .back-btn:hover {{
            opacity: 0.85;
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
            opacity: 0.8;
        }}
        .breadcrumb-path .separator {{
            opacity: 0.5;
        }}
        .breadcrumb-path .current {{
            font-weight: 500;
            cursor: default;
        }}
        #chart-container {{
            position: relative;
            width: 100%;
            height: 480px;
            margin-bottom: 24px;
        }}
        #pie-canvas {{
            width: 100%;
            height: 100%;
            cursor: grab;
        }}
        #pie-canvas:active {{
            cursor: grabbing;
        }}
        .legend {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 12px;
            padding: 16px;
            background: {html_elevated};
            border-radius: 8px;
            margin-bottom: 16px;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 14px;
            color: {html_text_soft};
            padding: 6px;
            border-radius: 4px;
            transition: background 0.2s;
        }}
        .legend-item:hover {{
            background: rgba(0, 158, 115, 0.1);
        }}
        .legend-color {{
            width: 14px;
            height: 14px;
            border-radius: 3px;
            flex-shrink: 0;
        }}
        .info-row {{
            display: flex;
            justify-content: space-between;
            gap: 16px;
            margin-top: 16px;
            padding: 12px 0;
            color: {html_text_soft};
            font-size: 14px;
            border-top: 1px solid rgba(26,26,23,0.1) if "{THEME}" == "light" else rgba(240,239,232,0.1);
        }}
        .hint {{
            text-align: center;
            color: {html_text_soft};
            margin-top: 12px;
            font-size: 13px;
            font-style: italic;
        }}
        .total-display {{
            text-align: center;
            font-size: 18px;
            color: {html_text};
            font-weight: 500;
        }}
        .total-display .amount {{
            font-weight: 700;
            color: {IMPRINT[0]};
            font-size: 24px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>pie-drilldown · letsplot · anyplot.ai</h1>
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

        function setupCanvas() {{
            const rect = canvas.parentElement.getBoundingClientRect();
            const dpr = window.devicePixelRatio || 1;
            canvas.width = rect.width * dpr;
            canvas.height = rect.height * dpr;
            canvas.style.width = rect.width + 'px';
            canvas.style.height = rect.height + 'px';
            ctx.scale(dpr, dpr);
        }}

        function drawPie(levelId) {{
            const data = levelsData[levelId];
            if (!data) return;

            setupCanvas();
            const rect = canvas.parentElement.getBoundingClientRect();
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            const outerRadius = Math.min(centerX, centerY) - 60;
            const innerRadius = outerRadius * 0.35;

            ctx.clearRect(0, 0, rect.width, rect.height);

            const total = data.values.reduce((a, b) => a + b, 0);
            let startAngle = -Math.PI / 2;

            window.slices = [];

            data.values.forEach((value, i) => {{
                const sliceAngle = (value / total) * 2 * Math.PI;
                const endAngle = startAngle + sliceAngle;

                window.slices.push({{
                    startAngle,
                    endAngle,
                    category: data.categories[i],
                    value,
                    childId: data.children[i],
                    color: data.colors[i]
                }});

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
                ctx.strokeStyle = '{html_bg}';
                ctx.lineWidth = 3;
                ctx.stroke();

                const midAngle = startAngle + sliceAngle / 2;
                const labelRadius = outerRadius + 35;
                const labelX = centerX + labelRadius * Math.cos(midAngle);
                const labelY = centerY + labelRadius * Math.sin(midAngle);

                const pct = ((value / total) * 100).toFixed(1);

                ctx.fillStyle = '{html_text}';
                ctx.font = 'bold 14px -apple-system, sans-serif';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(data.categories[i], labelX, labelY - 10);
                ctx.font = '13px -apple-system, sans-serif';
                ctx.fillStyle = '{html_text_soft}';
                ctx.fillText(`${{(value/1000).toFixed(0)}}K ({{pct}}%)`, labelX, labelY + 10);

                startAngle = endAngle;
            }});

            ctx.fillStyle = '{html_text}';
            ctx.font = 'bold 18px -apple-system, sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText(data.name, centerX, centerY - 8);
            ctx.font = '14px -apple-system, sans-serif';
            ctx.fillStyle = '{html_text_soft}';
            ctx.fillText(`${{(total/1000000).toFixed(2)}}M`, centerX, centerY + 12);

            updateLegend(data);
            totalEl.textContent = `${{total.toLocaleString()}}`;

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
                    <span>${{cat}} - $${{(data.values[i]/1000).toFixed(0)}}K</span>
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

        canvas.addEventListener('click', function(e) {{
            const rect = canvas.getBoundingClientRect();
            const x = e.clientX - rect.left - rect.width / 2;
            const y = e.clientY - rect.top - rect.height / 2;
            const angle = Math.atan2(y, x);
            const distance = Math.sqrt(x * x + y * y);

            const outerRadius = (Math.min(rect.width, rect.height) / 2) - 60;
            const innerRadius = outerRadius * 0.35;

            if (distance < innerRadius || distance > outerRadius) return;

            let clickAngle = angle;
            if (clickAngle < -Math.PI / 2) clickAngle += 2 * Math.PI;

            window.slices?.forEach(slice => {{
                let start = slice.startAngle;
                let end = slice.endAngle;

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

        canvas.addEventListener('mousemove', function(e) {{
            const rect = canvas.getBoundingClientRect();
            const x = e.clientX - rect.left - rect.width / 2;
            const y = e.clientY - rect.top - rect.height / 2;
            const distance = Math.sqrt(x * x + y * y);

            const outerRadius = (Math.min(rect.width, rect.height) / 2) - 60;
            const innerRadius = outerRadius * 0.35;

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
        window.addEventListener('resize', () => drawPie(currentLevel));

        updateBreadcrumb();
        drawPie('root');
    </script>
</body>
</html>"""

with open(f"plot-{THEME}.html", "w") as f:
    f.write(html_content)
