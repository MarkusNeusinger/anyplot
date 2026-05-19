""" anyplot.ai
hierarchy-toggle-view: Interactive Treemap-Sunburst Toggle View
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 80/100 | Updated: 2026-05-19
"""

import json
import math
import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_blank,
    element_rect,
    element_text,
    geom_polygon,
    geom_rect,
    geom_text,
    gggrid,
    ggplot,
    ggsize,
    labs,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

np.random.seed(42)

# Data: company budget allocation (3-level hierarchy)
hierarchy_data = {
    "root": {"id": "root", "parent": None, "label": "Company", "value": 0, "level": 0},
    "engineering": {"id": "engineering", "parent": "root", "label": "Engineering", "value": 0, "level": 1},
    "sales": {"id": "sales", "parent": "root", "label": "Sales", "value": 0, "level": 1},
    "marketing": {"id": "marketing", "parent": "root", "label": "Marketing", "value": 0, "level": 1},
    "operations": {"id": "operations", "parent": "root", "label": "Operations", "value": 0, "level": 1},
    "eng_backend": {"id": "eng_backend", "parent": "engineering", "label": "Backend", "value": 180, "level": 2},
    "eng_frontend": {"id": "eng_frontend", "parent": "engineering", "label": "Frontend", "value": 150, "level": 2},
    "eng_devops": {"id": "eng_devops", "parent": "engineering", "label": "DevOps", "value": 120, "level": 2},
    "sales_north": {"id": "sales_north", "parent": "sales", "label": "North", "value": 160, "level": 2},
    "sales_south": {"id": "sales_south", "parent": "sales", "label": "South", "value": 120, "level": 2},
    "sales_east": {"id": "sales_east", "parent": "sales", "label": "East", "value": 100, "level": 2},
    "mkt_digital": {"id": "mkt_digital", "parent": "marketing", "label": "Digital", "value": 130, "level": 2},
    "mkt_brand": {"id": "mkt_brand", "parent": "marketing", "label": "Brand", "value": 90, "level": 2},
    "ops_facilities": {"id": "ops_facilities", "parent": "operations", "label": "Facilities", "value": 85, "level": 2},
    "ops_logistics": {"id": "ops_logistics", "parent": "operations", "label": "Logistics", "value": 65, "level": 2},
}

for node in hierarchy_data.values():
    if node["level"] == 1:
        node["value"] = sum(n["value"] for n in hierarchy_data.values() if n["parent"] == node["id"])

total_value = sum(n["value"] for n in hierarchy_data.values() if n["level"] == 1)

# Okabe-Ito positions 1-4 for departments; lighter variants for children
DEPT_COLORS = {"Engineering": "#009E73", "Sales": "#D55E00", "Marketing": "#0072B2", "Operations": "#CC79A7"}
CHILD_COLORS = {
    "Backend": "#4DC4A0",
    "Frontend": "#80D5B8",
    "DevOps": "#B3E6D0",
    "North": "#E08040",
    "South": "#E89A66",
    "East": "#F0B48C",
    "Digital": "#3399CC",
    "Brand": "#66B2D9",
    "Facilities": "#DDA0BE",
    "Logistics": "#E8C0D3",
}

departments = sorted([n for n in hierarchy_data.values() if n["level"] == 1], key=lambda x: x["value"], reverse=True)
leaves = [n for n in hierarchy_data.values() if n["level"] == 2]

# ===== TREEMAP: proportional-width columns per dept, children stacked vertically =====
treemap_rects = []
treemap_labels = []
pad = 1.5
cumx = 0.0

for dept in departments:
    dw = dept["value"] / total_value * 100
    treemap_rects.append({"xmin": cumx, "ymin": 0, "xmax": cumx + dw, "ymax": 100, "label": dept["label"], "level": 1})
    dept_children = sorted([n for n in leaves if n["parent"] == dept["id"]], key=lambda x: x["value"], reverse=True)
    child_total = sum(c["value"] for c in dept_children)
    cumy = 0.0
    for child in dept_children:
        ch = child["value"] / child_total * 90
        treemap_rects.append(
            {
                "xmin": cumx + pad,
                "ymin": cumy + pad,
                "xmax": cumx + dw - pad,
                "ymax": cumy + ch - pad,
                "label": child["label"],
                "level": 2,
            }
        )
        pct = child["value"] / total_value * 100
        if dw - 2 * pad > 5 and ch > 5:
            treemap_labels.append(
                {"x": cumx + dw / 2, "y": cumy + ch / 2, "label": f"{child['label']}\n{pct:.0f}%", "level": 2}
            )
        cumy += ch
    treemap_labels.append({"x": cumx + dw / 2, "y": 95, "label": dept["label"], "level": 1})
    cumx += dw

treemap_df = pd.DataFrame(treemap_rects)
treemap_lbl_df = pd.DataFrame(treemap_labels)
tm_dept = treemap_df[treemap_df["level"] == 1].reset_index(drop=True)
tm_child = treemap_df[treemap_df["level"] == 2].reset_index(drop=True)
lbl_dept = treemap_lbl_df[treemap_lbl_df["level"] == 1].reset_index(drop=True)
lbl_child = treemap_lbl_df[treemap_lbl_df["level"] == 2].reset_index(drop=True)

dept_fill = [DEPT_COLORS.get(lbl, "#888") for lbl in tm_dept["label"]]
child_fill = [CHILD_COLORS.get(lbl, "#888") for lbl in tm_child["label"]]

treemap_plot = (
    ggplot()
    + geom_rect(
        aes(xmin="xmin", ymin="ymin", xmax="xmax", ymax="ymax", fill="label"),
        data=tm_dept,
        color="white",
        size=3,
        alpha=0.35,
    )
    + geom_rect(
        aes(xmin="xmin", ymin="ymin", xmax="xmax", ymax="ymax", fill="label"),
        data=tm_child,
        color="white",
        size=1.5,
        alpha=0.92,
    )
    + geom_text(aes(x="x", y="y", label="label"), data=lbl_dept, size=16, color=INK, fontface="bold")
    + geom_text(aes(x="x", y="y", label="label"), data=lbl_child, size=11, color="white", fontface="bold")
    + scale_fill_manual(values=dept_fill + child_fill)
    + labs(title="Treemap View")
    + theme(
        plot_title=element_text(size=22, hjust=0.5, face="bold", color=INK),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        legend_position="none",
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_grid=element_blank(),
    )
    + ggsize(750, 750)
)

# ===== SUNBURST: concentric rings =====
sunburst_polys = []
sunburst_lbls = []
seg_id = 0
n_pts = 40
r0, r1, r2 = 15, 45, 80  # hole, inner ring, outer ring

# Inner ring: departments
start_a = math.pi / 2
dept_angles = {}

for dept in departments:
    end_a = start_a - dept["value"] / total_value * 2 * math.pi
    dept_angles[dept["id"]] = (start_a, end_a)
    angles = [end_a + (start_a - end_a) * i / n_pts for i in range(n_pts + 1)]
    rev_a = list(reversed(angles))
    xs = [r1 * math.cos(a) for a in angles] + [r0 * math.cos(a) for a in rev_a]
    ys = [r1 * math.sin(a) for a in angles] + [r0 * math.sin(a) for a in rev_a]
    for x, y in zip(xs, ys, strict=False):
        sunburst_polys.append({"x": x, "y": y, "seg": seg_id, "label": dept["label"], "ring": 1})
    mid_a = (start_a + end_a) / 2
    lr = (r0 + r1) / 2
    sunburst_lbls.append({"x": lr * math.cos(mid_a), "y": lr * math.sin(mid_a), "label": dept["label"], "ring": 1})
    seg_id += 1
    start_a = end_a

# Outer ring: children
for dept in departments:
    d_start, d_end = dept_angles[dept["id"]]
    d_span = d_start - d_end
    dept_children = sorted([n for n in leaves if n["parent"] == dept["id"]], key=lambda x: x["value"], reverse=True)
    child_total = sum(c["value"] for c in dept_children)
    c_start = d_start
    for child in dept_children:
        c_span = (child["value"] / child_total if child_total > 0 else 0) * d_span
        c_end = c_start - c_span
        angles = [c_end + (c_start - c_end) * i / n_pts for i in range(n_pts + 1)]
        rev_a = list(reversed(angles))
        xs = [r2 * math.cos(a) for a in angles] + [r1 * math.cos(a) for a in rev_a]
        ys = [r2 * math.sin(a) for a in angles] + [r1 * math.sin(a) for a in rev_a]
        for x, y in zip(xs, ys, strict=False):
            sunburst_polys.append({"x": x, "y": y, "seg": seg_id, "label": child["label"], "ring": 2})
        if child["value"] / total_value > 0.05:
            mid_a = (c_start + c_end) / 2
            lr = (r1 + r2) / 2
            sunburst_lbls.append(
                {"x": lr * math.cos(mid_a), "y": lr * math.sin(mid_a), "label": child["label"], "ring": 2}
            )
        seg_id += 1
        c_start = c_end

sb_df = pd.DataFrame(sunburst_polys)
sb_lbl_df = pd.DataFrame(sunburst_lbls)
sb_r1 = sb_df[sb_df["ring"] == 1].reset_index(drop=True)
sb_r2 = sb_df[sb_df["ring"] == 2].reset_index(drop=True)
sb_l1 = sb_lbl_df[sb_lbl_df["ring"] == 1].reset_index(drop=True)
sb_l2 = sb_lbl_df[sb_lbl_df["ring"] == 2].reset_index(drop=True)

r1_fill = [DEPT_COLORS.get(lbl, "#888") for lbl in sb_r1["label"].unique()]
r2_fill = [CHILD_COLORS.get(lbl, "#888") for lbl in sb_r2["label"].unique()]

sunburst_plot = (
    ggplot()
    + geom_polygon(aes(x="x", y="y", fill="label", group="seg"), data=sb_r1, color="white", size=2, alpha=0.95)
    + geom_polygon(aes(x="x", y="y", fill="label", group="seg"), data=sb_r2, color="white", size=1.2, alpha=0.9)
    + geom_text(aes(x="x", y="y", label="label"), data=sb_l1, size=11, color="white", fontface="bold")
    + geom_text(aes(x="x", y="y", label="label"), data=sb_l2, size=10, color=INK, fontface="bold")
    + scale_fill_manual(values=r1_fill + r2_fill)
    + coord_fixed(ratio=1)
    + scale_x_continuous(limits=(-100, 100))
    + scale_y_continuous(limits=(-100, 100))
    + labs(title="Sunburst View")
    + ggsize(750, 750)
    + theme(
        plot_title=element_text(size=22, hjust=0.5, face="bold", color=INK),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        legend_position="none",
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_grid=element_blank(),
    )
)

# Combine side-by-side
combined = gggrid([treemap_plot, sunburst_plot], ncol=2)
final_plot = (
    combined
    + ggsize(1600, 900)
    + labs(
        title="hierarchy-toggle-view · python · letsplot · anyplot.ai",
        subtitle="Company Budget Allocation · Toggle between views in the HTML version",
    )
    + theme(
        plot_title=element_text(size=24, hjust=0.5, face="bold", color=INK),
        plot_subtitle=element_text(size=16, hjust=0.5, color=INK_SOFT),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    )
)

ggsave(final_plot, f"plot-{THEME}.png", path=".", scale=3)

# Interactive HTML with theme-aware toggle
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>hierarchy-toggle-view · python · letsplot · anyplot.ai</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: {PAGE_BG};
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }}
        .container {{
            background: {ELEVATED_BG};
            border-radius: 16px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.15);
            padding: 40px;
            max-width: 900px;
            width: 100%;
        }}
        h1 {{ color: {INK}; text-align: center; font-size: 20px; margin-bottom: 8px; }}
        .subtitle {{ color: {INK_SOFT}; text-align: center; font-size: 13px; margin-bottom: 24px; }}
        .toggle-container {{ display: flex; justify-content: center; margin-bottom: 24px; }}
        .toggle-btn {{
            padding: 12px 28px; font-size: 15px; font-weight: 600;
            border: 2px solid #009E73; background: transparent;
            color: #009E73; cursor: pointer; transition: all 0.25s;
        }}
        .toggle-btn:first-child {{ border-radius: 8px 0 0 8px; }}
        .toggle-btn:last-child {{ border-radius: 0 8px 8px 0; border-left: none; }}
        .toggle-btn.active {{ background: #009E73; color: white; }}
        .toggle-btn:hover:not(.active) {{ opacity: 0.7; }}
        #chart-container {{ position: relative; width: 100%; height: 520px; }}
        canvas {{ width: 100%; height: 100%; }}
        .legend {{
            display: flex; flex-wrap: wrap; justify-content: center;
            gap: 12px; margin-top: 20px; padding: 14px;
            background: {PAGE_BG}; border-radius: 10px;
        }}
        .legend-item {{ display: flex; align-items: center; gap: 6px; font-size: 13px; color: {INK}; }}
        .legend-dot {{ width: 13px; height: 13px; border-radius: 3px; flex-shrink: 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>hierarchy-toggle-view · python · letsplot · anyplot.ai</h1>
        <p class="subtitle">Company Budget Allocation</p>
        <div class="toggle-container">
            <button class="toggle-btn active" id="treemapBtn" onclick="showView('treemap')">Treemap</button>
            <button class="toggle-btn" id="sunburstBtn" onclick="showView('sunburst')">Sunburst</button>
        </div>
        <div id="chart-container">
            <canvas id="chart-canvas"></canvas>
        </div>
        <div class="legend" id="legend"></div>
    </div>
    <script>
        const DATA = {json.dumps(dict(hierarchy_data))};
        const DEPT_C = {json.dumps(dict(DEPT_COLORS))};
        const CHILD_C = {json.dumps(dict(CHILD_COLORS))};
        const INK_COLOR = '{INK}';
        const CONTAINER_BG = '{ELEVATED_BG}';

        const departments = Object.values(DATA).filter(n => n.level === 1).sort((a,b) => b.value - a.value);
        const leaves = Object.values(DATA).filter(n => n.level === 2);
        const totalValue = departments.reduce((s, d) => s + d.value, 0);

        let currentView = 'treemap';
        const canvas = document.getElementById('chart-canvas');
        const ctx = canvas.getContext('2d');

        function setupCanvas() {{
            const rect = canvas.parentElement.getBoundingClientRect();
            const dpr = window.devicePixelRatio || 1;
            canvas.width = rect.width * dpr;
            canvas.height = rect.height * dpr;
            canvas.style.width = rect.width + 'px';
            canvas.style.height = rect.height + 'px';
            ctx.scale(dpr, dpr);
        }}

        function drawTreemap() {{
            setupCanvas();
            const rect = canvas.parentElement.getBoundingClientRect();
            const pad = 20;
            const W = rect.width - 2 * pad, H = rect.height - 2 * pad;
            ctx.clearRect(0, 0, rect.width, rect.height);
            let cx = pad;
            departments.forEach(dept => {{
                const dw = dept.value / totalValue * W;
                ctx.fillStyle = DEPT_C[dept.label] || '#888';
                ctx.globalAlpha = 0.3;
                ctx.fillRect(cx, pad, dw, H);
                ctx.globalAlpha = 1;
                ctx.strokeStyle = CONTAINER_BG;
                ctx.lineWidth = 3;
                ctx.strokeRect(cx, pad, dw, H);
                const children = leaves.filter(l => l.parent === dept.id).sort((a,b) => b.value - a.value);
                const childTotal = children.reduce((s,c) => s + c.value, 0);
                const innerH = H - 22;
                let cy = pad + 2;
                children.forEach(child => {{
                    const ch = childTotal > 0 ? child.value / childTotal * innerH : 0;
                    ctx.fillStyle = CHILD_C[child.label] || '#888';
                    ctx.fillRect(cx + 2, cy, dw - 4, ch);
                    ctx.strokeStyle = CONTAINER_BG;
                    ctx.lineWidth = 1.5;
                    ctx.strokeRect(cx + 2, cy, dw - 4, ch);
                    const pct = (child.value / totalValue * 100).toFixed(0);
                    if (dw > 50 && ch > 30) {{
                        ctx.fillStyle = 'white';
                        ctx.font = 'bold 12px -apple-system,sans-serif';
                        ctx.textAlign = 'center';
                        ctx.textBaseline = 'middle';
                        ctx.fillText(child.label, cx + dw / 2, cy + ch / 2 - 7);
                        ctx.font = '10px -apple-system,sans-serif';
                        ctx.fillText(pct + '%', cx + dw / 2, cy + ch / 2 + 7);
                    }} else if (dw > 25 && ch > 18) {{
                        ctx.fillStyle = 'white';
                        ctx.font = '10px -apple-system,sans-serif';
                        ctx.textAlign = 'center';
                        ctx.textBaseline = 'middle';
                        ctx.fillText(pct + '%', cx + dw / 2, cy + ch / 2);
                    }}
                    cy += ch;
                }});
                ctx.fillStyle = INK_COLOR;
                ctx.font = 'bold 12px -apple-system,sans-serif';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(dept.label, cx + dw / 2, pad + H - 9);
                cx += dw;
            }});
        }}

        function drawSunburst() {{
            setupCanvas();
            const rect = canvas.parentElement.getBoundingClientRect();
            const cx = rect.width / 2, cy = rect.height / 2;
            const maxR = Math.min(cx, cy) - 30;
            const r0 = maxR * 0.15, r1 = maxR * 0.5, r2 = maxR;
            ctx.clearRect(0, 0, rect.width, rect.height);
            let startA = -Math.PI / 2;
            const deptAngles = {{}};
            departments.forEach(dept => {{
                const endA = startA + dept.value / totalValue * 2 * Math.PI;
                deptAngles[dept.id] = {{ start: startA, end: endA }};
                ctx.beginPath();
                ctx.moveTo(cx + r0 * Math.cos(startA), cy + r0 * Math.sin(startA));
                ctx.arc(cx, cy, r1, startA, endA);
                ctx.lineTo(cx + r0 * Math.cos(endA), cy + r0 * Math.sin(endA));
                ctx.arc(cx, cy, r0, endA, startA, true);
                ctx.closePath();
                ctx.fillStyle = DEPT_C[dept.label] || '#888';
                ctx.fill();
                ctx.strokeStyle = CONTAINER_BG;
                ctx.lineWidth = 2;
                ctx.stroke();
                const midA = (startA + endA) / 2, lr = (r0 + r1) / 2;
                ctx.fillStyle = 'white';
                ctx.font = 'bold 12px -apple-system,sans-serif';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(dept.label, cx + lr * Math.cos(midA), cy + lr * Math.sin(midA));
                startA = endA;
            }});
            departments.forEach(dept => {{
                const {{ start: ds, end: de }} = deptAngles[dept.id];
                const span = de - ds;
                const children = leaves.filter(l => l.parent === dept.id).sort((a,b) => b.value - a.value);
                const childTotal = children.reduce((s,c) => s + c.value, 0);
                let cs = ds;
                children.forEach(child => {{
                    const cSpan = childTotal > 0 ? child.value / childTotal * span : 0;
                    const ce = cs + cSpan;
                    ctx.beginPath();
                    ctx.moveTo(cx + r1 * Math.cos(cs), cy + r1 * Math.sin(cs));
                    ctx.arc(cx, cy, r2, cs, ce);
                    ctx.lineTo(cx + r1 * Math.cos(ce), cy + r1 * Math.sin(ce));
                    ctx.arc(cx, cy, r1, ce, cs, true);
                    ctx.closePath();
                    ctx.fillStyle = CHILD_C[child.label] || '#888';
                    ctx.fill();
                    ctx.strokeStyle = CONTAINER_BG;
                    ctx.lineWidth = 1.5;
                    ctx.stroke();
                    if (child.value / totalValue > 0.05) {{
                        const midA = (cs + ce) / 2, lr = (r1 + r2) / 2;
                        ctx.fillStyle = INK_COLOR;
                        ctx.font = 'bold 11px -apple-system,sans-serif';
                        ctx.textAlign = 'center';
                        ctx.textBaseline = 'middle';
                        ctx.fillText(child.label, cx + lr * Math.cos(midA), cy + lr * Math.sin(midA));
                    }}
                    cs = ce;
                }});
            }});
            ctx.fillStyle = INK_COLOR;
            ctx.font = 'bold 14px -apple-system,sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText('Budget', cx, cy - 8);
            ctx.font = '12px -apple-system,sans-serif';
            ctx.fillText('$' + (totalValue / 1000).toFixed(1) + 'M', cx, cy + 10);
        }}

        function showView(view) {{
            currentView = view;
            document.getElementById('treemapBtn').classList.toggle('active', view === 'treemap');
            document.getElementById('sunburstBtn').classList.toggle('active', view === 'sunburst');
            if (view === 'treemap') drawTreemap();
            else drawSunburst();
        }}

        const legend = document.getElementById('legend');
        legend.innerHTML = departments.map(d => {{
            const color = DEPT_C[d.label] || '#888';
            const pct = (d.value / totalValue * 100).toFixed(1);
            return `<div class="legend-item"><div class="legend-dot" style="background:${{color}}"></div><span>${{d.label}} (${{pct}}%)</span></div>`;
        }}).join('');

        window.addEventListener('resize', () => {{
            if (currentView === 'treemap') drawTreemap();
            else drawSunburst();
        }});

        drawTreemap();
    </script>
</body>
</html>"""

with open(f"plot-{THEME}.html", "w") as f:
    f.write(html_content)
