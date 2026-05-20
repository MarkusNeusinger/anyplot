""" anyplot.ai
bar-drilldown: Column Chart with Hierarchical Drilling
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-20
"""

import json
import os

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_bar,
    geom_text,
    ggplot,
    ggsize,
    labs,
    scale_fill_manual,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
RULE = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7"]

# Hierarchical data: regional sales breakdown (region → quarterly)
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

region_color_map = {
    "North Region": OKABE_ITO[0],
    "South Region": OKABE_ITO[1],
    "East Region": OKABE_ITO[2],
    "West Region": OKABE_ITO[3],
}

# Root-level dataframe for static PNG
root_children = hierarchy_data["root"]["children"]
categories = [hierarchy_data[cid]["name"] for cid in root_children]
values = [hierarchy_data[cid]["value"] for cid in root_children]
value_labels = [f"${v // 1000}K" for v in values]

df = pd.DataFrame({"category": categories, "value": values, "value_label": value_labels})
df["category"] = pd.Categorical(df["category"], categories=categories, ordered=True)

# Static PNG using letsplot ggplot grammar
plot = (
    ggplot(df, aes(x="category", y="value", fill="category"))
    + geom_bar(stat="identity", width=0.7, show_legend=False, color=PAGE_BG, size=0.5)
    + geom_text(aes(label="value_label"), vjust=-0.3, size=8, color=INK, fontface="bold")
    + scale_fill_manual(values=OKABE_ITO)
    + scale_y_continuous(format="${,.0f}", limits=[0, 680000], expand=[0, 0])
    + labs(
        title="bar-drilldown · python · letsplot · anyplot.ai",
        subtitle="Regional Sales · Open HTML for interactive drilldown",
        x="Region",
        y="Sales ($)",
    )
    + ggsize(800, 450)
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color=RULE, size=0.3),
        axis_title=element_text(color=INK, size=12),
        axis_text=element_text(color=INK_SOFT, size=10),
        axis_line=element_line(color=INK_SOFT),
        plot_title=element_text(color=INK, size=16, face="bold", hjust=0.5),
        plot_subtitle=element_text(color=INK_MUTED, size=10, hjust=0.5),
        plot_margin=[30, 30, 30, 30],
    )
)

ggsave(plot, filename=f"plot-{THEME}.png", path=".", scale=4)

# Prepare data for all hierarchy levels (used in HTML drilldown)
levels_data = {}
for level_id in ["root", "north", "south", "east", "west"]:
    level_data = hierarchy_data[level_id]
    if "children" in level_data:
        children_ids = level_data["children"]
        cats = [hierarchy_data[cid]["name"] for cid in children_ids]
        vals = [hierarchy_data[cid]["value"] for cid in children_ids]
        if level_id == "root":
            level_colors = [region_color_map.get(cat, OKABE_ITO[0]) for cat in cats]
        else:
            base_color = region_color_map.get(hierarchy_data[level_id]["name"], OKABE_ITO[0])
            level_colors = [base_color] * len(cats)
        levels_data[level_id] = {
            "name": hierarchy_data[level_id]["name"],
            "categories": cats,
            "values": vals,
            "colors": level_colors,
            "children": children_ids,
            "parent": hierarchy_data[level_id].get("parent"),
        }

# HTML theme tokens for interactive output
html_body_bg = PAGE_BG
html_container_bg = ELEVATED_BG
html_text = INK
html_text_soft = INK_SOFT
html_grid = "rgba(26,26,23,0.12)" if THEME == "light" else "rgba(240,239,232,0.12)"
html_tooltip_bg = "rgba(0,0,0,0.88)" if THEME == "light" else "rgba(36,36,32,0.95)"
html_back_btn_border = INK_SOFT
html_brand = OKABE_ITO[0]

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>bar-drilldown · python · letsplot · anyplot.ai</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: {html_body_bg};
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }}
        .container {{
            background: {html_container_bg};
            border-radius: 16px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.15);
            padding: 40px;
            max-width: 1000px;
            width: 100%;
        }}
        h1 {{
            color: {html_text};
            text-align: center;
            font-size: 26px;
            margin-bottom: 8px;
        }}
        .subtitle {{
            color: {html_text_soft};
            text-align: center;
            font-size: 15px;
            margin-bottom: 24px;
        }}
        .breadcrumb {{
            background: {html_brand};
            color: #ffffff;
            padding: 12px 18px;
            border-radius: 10px;
            margin-bottom: 24px;
            font-size: 16px;
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .back-btn {{
            background: transparent;
            color: #ffffff;
            border: 1.5px solid rgba(255,255,255,0.6);
            padding: 8px 16px;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            white-space: nowrap;
        }}
        .back-btn:hover {{
            background: rgba(255,255,255,0.15);
        }}
        .back-btn:disabled {{
            opacity: 0.35;
            cursor: not-allowed;
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
            opacity: 0.85;
        }}
        .breadcrumb-path .separator {{
            opacity: 0.55;
        }}
        .breadcrumb-path .current {{
            font-weight: 700;
            cursor: default;
        }}
        #chart-container {{
            position: relative;
            width: 100%;
            height: 440px;
        }}
        #bar-canvas {{
            width: 100%;
            height: 100%;
        }}
        .total-display {{
            text-align: center;
            margin-top: 18px;
            font-size: 18px;
            color: {html_text_soft};
        }}
        .total-display .amount {{
            font-weight: 700;
            color: {html_brand};
            font-size: 26px;
        }}
        .hint {{
            text-align: center;
            color: {html_text_soft};
            margin-top: 14px;
            font-size: 13px;
            opacity: 0.75;
        }}
        .tooltip {{
            position: absolute;
            background: {html_tooltip_bg};
            color: #F0EFE8;
            padding: 10px 14px;
            border-radius: 8px;
            font-size: 13px;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.15s;
            z-index: 100;
        }}
        .tooltip.visible {{
            opacity: 1;
        }}
        .tooltip .tip-title {{
            font-weight: 600;
            font-size: 15px;
            margin-bottom: 4px;
        }}
        .tooltip .tip-value {{
            color: {html_brand};
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>bar-drilldown · python · letsplot · anyplot.ai</h1>
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
        const hierarchyData = {json.dumps(hierarchy_data)};
        const levelsData = {json.dumps(levels_data)};
        const textColor = '{html_text}';
        const textSoft = '{html_text_soft}';
        const gridColor = '{html_grid}';

        let currentLevel = 'root';
        let history = [];

        const canvas = document.getElementById('bar-canvas');
        const ctx = canvas.getContext('2d');
        const totalEl = document.getElementById('total-amount');
        const hintEl = document.getElementById('hint');
        const backBtn = document.getElementById('backBtn');
        const tooltipEl = document.getElementById('tooltip');

        let bars = [];
        let animationFrame = null;

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

        function drawBars(levelId, animate) {{
            if (animate === undefined) animate = true;
            const data = levelsData[levelId];
            if (!data) return;

            const rect = setupCanvas();
            const pad = {{ top: 50, right: 30, bottom: 55, left: 90 }};
            const chartW = rect.width - pad.left - pad.right;
            const chartH = rect.height - pad.top - pad.bottom;

            const maxValue = Math.max(...data.values) * 1.18;
            const slotW = chartW / data.categories.length;
            const barW = slotW * 0.62;
            const barGap = slotW * 0.38;

            function render(progress) {{
                ctx.clearRect(0, 0, rect.width, rect.height);

                // Grid lines
                const gridCount = 5;
                for (let i = 0; i <= gridCount; i++) {{
                    const gy = pad.top + (chartH / gridCount) * i;
                    ctx.strokeStyle = gridColor;
                    ctx.lineWidth = 1;
                    ctx.beginPath();
                    ctx.moveTo(pad.left, gy);
                    ctx.lineTo(rect.width - pad.right, gy);
                    ctx.stroke();

                    const gVal = maxValue * (1 - i / gridCount);
                    ctx.fillStyle = textSoft;
                    ctx.font = '13px -apple-system, sans-serif';
                    ctx.textAlign = 'right';
                    ctx.textBaseline = 'middle';
                    ctx.fillText('$' + (gVal / 1000).toFixed(0) + 'K', pad.left - 10, gy);
                }}

                // Y-axis label
                ctx.save();
                ctx.translate(18, pad.top + chartH / 2);
                ctx.rotate(-Math.PI / 2);
                ctx.fillStyle = textColor;
                ctx.font = 'bold 14px -apple-system, sans-serif';
                ctx.textAlign = 'center';
                ctx.fillText('Sales ($)', 0, 0);
                ctx.restore();

                // Bars
                bars = [];
                data.values.forEach((value, i) => {{
                    const barH = (value / maxValue) * chartH * progress;
                    const bx = pad.left + i * slotW + barGap / 2;
                    const by = pad.top + chartH - barH;

                    bars.push({{
                        x: bx, y: pad.top + chartH - (value / maxValue) * chartH,
                        width: barW, height: (value / maxValue) * chartH,
                        category: data.categories[i],
                        value: value,
                        childId: data.children[i],
                        color: data.colors[i],
                    }});

                    ctx.fillStyle = data.colors[i];
                    ctx.beginPath();
                    ctx.roundRect(bx, by, barW, barH, [5, 5, 0, 0]);
                    ctx.fill();

                    if (progress > 0.85) {{
                        ctx.fillStyle = textColor;
                        ctx.font = 'bold 14px -apple-system, sans-serif';
                        ctx.textAlign = 'center';
                        ctx.textBaseline = 'bottom';
                        ctx.fillText('$' + (value / 1000).toFixed(0) + 'K', bx + barW / 2, by - 6);
                    }}

                    ctx.fillStyle = textColor;
                    ctx.font = '14px -apple-system, sans-serif';
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'top';
                    ctx.fillText(data.categories[i], bx + barW / 2, pad.top + chartH + 10);
                }});
            }}

            if (animate) {{
                if (animationFrame) cancelAnimationFrame(animationFrame);
                const startTime = performance.now();
                const duration = 480;
                function step(now) {{
                    const t = Math.min((now - startTime) / duration, 1);
                    const eased = 1 - Math.pow(1 - t, 3);
                    render(eased);
                    if (t < 1) animationFrame = requestAnimationFrame(step);
                }}
                animationFrame = requestAnimationFrame(step);
            }} else {{
                render(1);
            }}

            const total = data.values.reduce((a, b) => a + b, 0);
            totalEl.textContent = '$' + total.toLocaleString();

            const hasDrillable = data.children.some(cid => hierarchyData[cid]?.children);
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
                if (index > 0) html += '<span class="separator"> › </span>';
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
            history = idx >= 0 ? history.slice(0, idx) : [];
            currentLevel = id;
            updateBreadcrumb();
            drawBars(currentLevel);
        }};

        canvas.addEventListener('click', function(e) {{
            const rect = canvas.getBoundingClientRect();
            const mx = e.clientX - rect.left;
            const my = e.clientY - rect.top;
            bars.forEach(bar => {{
                if (mx >= bar.x && mx <= bar.x + bar.width &&
                    my >= bar.y && my <= bar.y + bar.height) {{
                    if (hierarchyData[bar.childId]?.children) drillDown(bar.childId);
                }}
            }});
        }});

        canvas.addEventListener('mousemove', function(e) {{
            const rect = canvas.getBoundingClientRect();
            const mx = e.clientX - rect.left;
            const my = e.clientY - rect.top;

            let hovered = null;
            bars.forEach(bar => {{
                if (mx >= bar.x && mx <= bar.x + bar.width &&
                    my >= bar.y && my <= bar.y + bar.height) hovered = bar;
            }});

            if (hovered) {{
                const drillable = hierarchyData[hovered.childId]?.children;
                canvas.style.cursor = drillable ? 'pointer' : 'default';
                tooltipEl.innerHTML =
                    `<div class="tip-title">${{hovered.category}}</div>` +
                    `<div><span class="tip-value">${{hovered.value.toLocaleString('en-US', {{style:'currency',currency:'USD',minimumFractionDigits:0}})}}</span></div>` +
                    (drillable ? `<div style="margin-top:5px;font-size:11px;opacity:0.75">Click to drill down</div>` : '');
                tooltipEl.style.left = (e.clientX - rect.left + 14) + 'px';
                tooltipEl.style.top = (e.clientY - rect.top - 12) + 'px';
                tooltipEl.classList.add('visible');
            }} else {{
                canvas.style.cursor = 'default';
                tooltipEl.classList.remove('visible');
            }}
        }});

        canvas.addEventListener('mouseleave', () => tooltipEl.classList.remove('visible'));
        backBtn.addEventListener('click', goBack);
        window.addEventListener('resize', () => drawBars(currentLevel, false));

        updateBreadcrumb();
        drawBars('root');
    </script>
</body>
</html>"""

with open(f"plot-{THEME}.html", "w") as f:
    f.write(html_content)
