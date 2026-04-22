""" pyplots.ai
hierarchy-toggle-view: Interactive Treemap-Sunburst Toggle View
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 90/100 | Created: 2026-01-11
"""

import json
import math

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_blank,
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

np.random.seed(42)

# Hierarchical data - Company budget allocation (3 levels: root -> department -> team)
hierarchy_data = {
    "root": {"id": "root", "parent": None, "label": "Company", "value": 0, "level": 0},
    # Level 1: Departments
    "engineering": {"id": "engineering", "parent": "root", "label": "Engineering", "value": 0, "level": 1},
    "sales": {"id": "sales", "parent": "root", "label": "Sales", "value": 0, "level": 1},
    "marketing": {"id": "marketing", "parent": "root", "label": "Marketing", "value": 0, "level": 1},
    "operations": {"id": "operations", "parent": "root", "label": "Operations", "value": 0, "level": 1},
    # Level 2: Teams under Engineering
    "eng_backend": {"id": "eng_backend", "parent": "engineering", "label": "Backend", "value": 180, "level": 2},
    "eng_frontend": {"id": "eng_frontend", "parent": "engineering", "label": "Frontend", "value": 150, "level": 2},
    "eng_devops": {"id": "eng_devops", "parent": "engineering", "label": "DevOps", "value": 120, "level": 2},
    # Level 2: Teams under Sales
    "sales_north": {"id": "sales_north", "parent": "sales", "label": "North", "value": 160, "level": 2},
    "sales_south": {"id": "sales_south", "parent": "sales", "label": "South", "value": 120, "level": 2},
    "sales_east": {"id": "sales_east", "parent": "sales", "label": "East", "value": 100, "level": 2},
    # Level 2: Teams under Marketing
    "mkt_digital": {"id": "mkt_digital", "parent": "marketing", "label": "Digital", "value": 130, "level": 2},
    "mkt_brand": {"id": "mkt_brand", "parent": "marketing", "label": "Brand", "value": 90, "level": 2},
    # Level 2: Teams under Operations
    "ops_facilities": {"id": "ops_facilities", "parent": "operations", "label": "Facilities", "value": 85, "level": 2},
    "ops_logistics": {"id": "ops_logistics", "parent": "operations", "label": "Logistics", "value": 65, "level": 2},
}

# Calculate aggregated values for parent nodes
for node_id, node in hierarchy_data.items():
    if node["level"] == 1:
        children_sum = sum(n["value"] for n in hierarchy_data.values() if n["parent"] == node_id)
        node["value"] = children_sum

total_value = sum(n["value"] for n in hierarchy_data.values() if n["level"] == 1)

# Color palette - consistent across both views (by department)
dept_colors = {"Engineering": "#306998", "Sales": "#FFD43B", "Marketing": "#4CAF50", "Operations": "#E07A5F"}

# Child colors (slightly lighter variants)
child_colors = {
    "Backend": "#4A8BBE",
    "Frontend": "#6BA3D6",
    "DevOps": "#8CBBEE",
    "North": "#F5C800",
    "South": "#E6BE35",
    "East": "#D4A72C",
    "Digital": "#66BB6A",
    "Brand": "#81C784",
    "Facilities": "#EF9A9A",
    "Logistics": "#F48FB1",
}

all_colors = {**dept_colors, **child_colors}

# Get departments (level 1) and leaves (level 2)
departments = [n for n in hierarchy_data.values() if n["level"] == 1]
departments = sorted(departments, key=lambda x: x["value"], reverse=True)
leaves = [n for n in hierarchy_data.values() if n["level"] == 2]


# ========== TREEMAP with nested rectangles ==========
# First layout departments, then subdivide each into children


def squarify_layout(values, x, y, w, h):
    """Simple squarify algorithm for treemap layout."""
    rects = []
    total = sum(values)
    if total == 0 or not values:
        return rects

    remaining = list(values)
    rx, ry, rw, rh = x, y, w, h

    while remaining:
        if rw >= rh:
            row, row_sum = [], 0
            best_ratio = float("inf")

            for v in remaining:
                test_row = row + [v]
                test_sum = row_sum + v
                row_width = (test_sum / total) * w if total > 0 else 0

                if row_width > 0:
                    worst = 0
                    for rv in test_row:
                        rect_h = (rv / test_sum) * rh if test_sum > 0 else 0
                        ratio = max(row_width / rect_h, rect_h / row_width) if rect_h > 0 else float("inf")
                        worst = max(worst, ratio)
                    if worst <= best_ratio:
                        best_ratio = worst
                        row = test_row
                        row_sum = test_sum
                    else:
                        break
                else:
                    row = test_row
                    row_sum = test_sum

            row_width = (row_sum / total) * w if total > 0 else 0
            cy = ry
            for rv in row:
                rect_h = (rv / row_sum) * rh if row_sum > 0 else 0
                rects.append((rx, cy, row_width, rect_h))
                cy += rect_h
            rx += row_width
            rw -= row_width
            remaining = remaining[len(row) :]
        else:
            col, col_sum = [], 0
            best_ratio = float("inf")

            for v in remaining:
                test_col = col + [v]
                test_sum = col_sum + v
                col_height = (test_sum / total) * h if total > 0 else 0

                if col_height > 0:
                    worst = 0
                    for cv in test_col:
                        rect_w = (cv / test_sum) * rw if test_sum > 0 else 0
                        ratio = max(col_height / rect_w, rect_w / col_height) if rect_w > 0 else float("inf")
                        worst = max(worst, ratio)
                    if worst <= best_ratio:
                        best_ratio = worst
                        col = test_col
                        col_sum = test_sum
                    else:
                        break
                else:
                    col = test_col
                    col_sum = test_sum

            col_height = (col_sum / total) * h if total > 0 else 0
            cx = rx
            for cv in col:
                rect_w = (cv / col_sum) * rw if col_sum > 0 else 0
                rects.append((cx, ry, rect_w, col_height))
                cx += rect_w
            ry += col_height
            rh -= col_height
            remaining = remaining[len(col) :]

    return rects


# Layout departments at top level
dept_values = [d["value"] for d in departments]
dept_rects = squarify_layout(dept_values, 0, 0, 100, 100)

treemap_data = []
label_data = []
padding = 1.5  # Padding inside department rectangles

for i, dept in enumerate(departments):
    dx, dy, dw, dh = dept_rects[i]

    # Add department rectangle (outer border)
    treemap_data.append({"xmin": dx, "ymin": dy, "xmax": dx + dw, "ymax": dy + dh, "label": dept["label"], "level": 1})

    # Get children of this department
    children = [n for n in leaves if n["parent"] == dept["id"]]
    children = sorted(children, key=lambda x: x["value"], reverse=True)

    if children:
        child_values = [c["value"] for c in children]
        # Layout children inside department with padding
        inner_x = dx + padding
        inner_y = dy + padding
        inner_w = dw - 2 * padding
        inner_h = dh - 2 * padding - 8  # Extra space for department label at top

        child_rects = squarify_layout(child_values, inner_x, inner_y, inner_w, inner_h)

        for j, child in enumerate(children):
            cx, cy, cw, ch = child_rects[j]
            treemap_data.append(
                {"xmin": cx, "ymin": cy, "xmax": cx + cw, "ymax": cy + ch, "label": child["label"], "level": 2}
            )

            # Child label
            pct = child["value"] / total_value * 100
            if cw > 12 and ch > 10:
                label_data.append(
                    {"x": cx + cw / 2, "y": cy + ch / 2, "label": f"{child['label']}\n{pct:.0f}%", "level": 2}
                )
            elif cw > 6 and ch > 6:
                label_data.append({"x": cx + cw / 2, "y": cy + ch / 2, "label": f"{pct:.0f}%", "level": 2})

    # Department label at top of its rectangle
    label_data.append({"x": dx + dw / 2, "y": dy + dh - 4, "label": dept["label"], "level": 1})

treemap_df = pd.DataFrame(treemap_data)
label_df = pd.DataFrame(label_data)

# Separate level 1 and level 2 for different styling
treemap_dept = treemap_df[treemap_df["level"] == 1].reset_index(drop=True)
treemap_child = treemap_df[treemap_df["level"] == 2].reset_index(drop=True)
label_dept = label_df[label_df["level"] == 1].reset_index(drop=True)
label_child = label_df[label_df["level"] == 2].reset_index(drop=True)

dept_colors_list = [dept_colors.get(lbl, "#888888") for lbl in treemap_dept["label"]]
child_colors_list = [child_colors.get(lbl, "#888888") for lbl in treemap_child["label"]]

# Create treemap plot with nested rectangles
treemap_plot = (
    ggplot()
    # Department rectangles (outer, semi-transparent)
    + geom_rect(
        aes(xmin="xmin", ymin="ymin", xmax="xmax", ymax="ymax", fill="label"),
        data=treemap_dept,
        color="white",
        size=3,
        alpha=0.4,
    )
    # Child rectangles (inner, more opaque)
    + geom_rect(
        aes(xmin="xmin", ymin="ymin", xmax="xmax", ymax="ymax", fill="label"),
        data=treemap_child,
        color="white",
        size=1.5,
        alpha=0.92,
    )
    # Department labels
    + geom_text(aes(x="x", y="y", label="label"), data=label_dept, size=16, color="#333333", fontface="bold")
    # Child labels
    + geom_text(aes(x="x", y="y", label="label"), data=label_child, size=11, color="white", fontface="bold")
    + scale_fill_manual(values=dept_colors_list + child_colors_list)
    + labs(title="Treemap View")
    + theme(
        plot_title=element_text(size=22, hjust=0.5, face="bold"),
        legend_position="none",
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_grid=element_blank(),
        panel_background=element_blank(),
    )
    + ggsize(750, 750)
)


# ========== SUNBURST with concentric rings ==========
# Ring 1 (inner): Departments
# Ring 2 (outer): Teams/leaves

sunburst_polygons = []
sunburst_labels = []
segment_id = 0
n_points = 40

# Ring radii
r0, r1, r2 = 15, 45, 80  # center hole, inner ring outer edge, outer ring outer edge

# First pass: departments (inner ring)
start_angle = math.pi / 2
dept_angles = {}  # Store start/end angles for each department

for dept in departments:
    pct = dept["value"] / total_value
    end_angle = start_angle - pct * 2 * math.pi
    dept_angles[dept["id"]] = (start_angle, end_angle)

    # Create wedge polygon for department
    angles_outer = [end_angle + (start_angle - end_angle) * i / n_points for i in range(n_points + 1)]
    angles_inner = angles_outer[::-1]

    x_outer = [r1 * math.cos(a) for a in angles_outer]
    y_outer = [r1 * math.sin(a) for a in angles_outer]
    x_inner = [r0 * math.cos(a) for a in angles_inner]
    y_inner = [r0 * math.sin(a) for a in angles_inner]

    x_pts = x_outer + x_inner
    y_pts = y_outer + y_inner

    for x, y in zip(x_pts, y_pts, strict=True):
        sunburst_polygons.append({"x": x, "y": y, "segment_id": segment_id, "label": dept["label"], "ring": 1})

    # Department label
    mid_angle = (start_angle + end_angle) / 2
    label_r = (r0 + r1) / 2
    sunburst_labels.append(
        {"x": label_r * math.cos(mid_angle), "y": label_r * math.sin(mid_angle), "label": dept["label"], "ring": 1}
    )

    segment_id += 1
    start_angle = end_angle

# Second pass: children (outer ring)
for dept in departments:
    dept_start, dept_end = dept_angles[dept["id"]]
    dept_span = dept_start - dept_end

    children = [n for n in leaves if n["parent"] == dept["id"]]
    children = sorted(children, key=lambda x: x["value"], reverse=True)
    children_total = sum(c["value"] for c in children)

    child_start = dept_start
    for child in children:
        child_pct = child["value"] / children_total if children_total > 0 else 0
        child_span = child_pct * dept_span
        child_end = child_start - child_span

        # Create wedge polygon for child
        angles_outer = [child_end + (child_start - child_end) * i / n_points for i in range(n_points + 1)]
        angles_inner = angles_outer[::-1]

        x_outer = [r2 * math.cos(a) for a in angles_outer]
        y_outer = [r2 * math.sin(a) for a in angles_outer]
        x_inner = [r1 * math.cos(a) for a in angles_inner]
        y_inner = [r1 * math.sin(a) for a in angles_inner]

        x_pts = x_outer + x_inner
        y_pts = y_outer + y_inner

        for x, y in zip(x_pts, y_pts, strict=True):
            sunburst_polygons.append({"x": x, "y": y, "segment_id": segment_id, "label": child["label"], "ring": 2})

        # Child label - only for larger segments to avoid overlap
        child_global_pct = child["value"] / total_value
        if child_global_pct > 0.05:
            mid_angle = (child_start + child_end) / 2
            label_r = (r1 + r2) / 2
            sunburst_labels.append(
                {
                    "x": label_r * math.cos(mid_angle),
                    "y": label_r * math.sin(mid_angle),
                    "label": child["label"],
                    "ring": 2,
                }
            )

        segment_id += 1
        child_start = child_end

sunburst_df = pd.DataFrame(sunburst_polygons)
sunburst_label_df = pd.DataFrame(sunburst_labels)

# Separate rings for different styling
sunburst_ring1 = sunburst_df[sunburst_df["ring"] == 1].reset_index(drop=True)
sunburst_ring2 = sunburst_df[sunburst_df["ring"] == 2].reset_index(drop=True)
label_ring1 = sunburst_label_df[sunburst_label_df["ring"] == 1].reset_index(drop=True)
label_ring2 = sunburst_label_df[sunburst_label_df["ring"] == 2].reset_index(drop=True)

ring1_colors = [dept_colors.get(lbl, "#888888") for lbl in sunburst_ring1["label"].unique()]
ring2_colors = [child_colors.get(lbl, "#888888") for lbl in sunburst_ring2["label"].unique()]

sunburst_plot = (
    ggplot()
    # Inner ring (departments)
    + geom_polygon(
        aes(x="x", y="y", fill="label", group="segment_id"), data=sunburst_ring1, color="white", size=2, alpha=0.95
    )
    # Outer ring (children)
    + geom_polygon(
        aes(x="x", y="y", fill="label", group="segment_id"), data=sunburst_ring2, color="white", size=1.2, alpha=0.9
    )
    # Ring 1 labels
    + geom_text(aes(x="x", y="y", label="label"), data=label_ring1, size=11, color="white", fontface="bold")
    # Ring 2 labels
    + geom_text(aes(x="x", y="y", label="label"), data=label_ring2, size=10, color="#333333", fontface="bold")
    + scale_fill_manual(values=ring1_colors + ring2_colors)
    + coord_fixed(ratio=1)
    + scale_x_continuous(limits=(-100, 100))
    + scale_y_continuous(limits=(-100, 100))
    + labs(title="Sunburst View")
    + ggsize(750, 750)
    + theme(
        plot_title=element_text(size=22, hjust=0.5, face="bold"),
        legend_position="none",
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_grid=element_blank(),
        panel_background=element_blank(),
    )
)

# Combine both views side by side for static PNG
combined_plot = gggrid([treemap_plot, sunburst_plot], ncol=2)
final_plot = (
    combined_plot
    + ggsize(1600, 900)
    + labs(
        title="hierarchy-toggle-view · letsplot · pyplots.ai",
        subtitle="Company Budget Allocation · Toggle between views in HTML (interactive)",
    )
    + theme(
        plot_title=element_text(size=24, hjust=0.5, face="bold"),
        plot_subtitle=element_text(size=16, hjust=0.5, color="#666666"),
    )
)

# Save static PNG (scale 3 for 4800x2700)
ggsave(final_plot, "plot.png", path=".", scale=3)


# Interactive HTML with toggle functionality
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>hierarchy-toggle-view · letsplot · pyplots.ai</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
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
            font-size: 24px;
            margin-bottom: 8px;
        }}
        .subtitle {{
            color: #666;
            text-align: center;
            font-size: 14px;
            margin-bottom: 24px;
        }}
        .toggle-container {{
            display: flex;
            justify-content: center;
            gap: 0;
            margin-bottom: 24px;
        }}
        .toggle-btn {{
            padding: 14px 32px;
            font-size: 16px;
            font-weight: 600;
            border: 2px solid #306998;
            background: white;
            color: #306998;
            cursor: pointer;
            transition: all 0.3s;
        }}
        .toggle-btn:first-child {{
            border-radius: 8px 0 0 8px;
        }}
        .toggle-btn:last-child {{
            border-radius: 0 8px 8px 0;
            border-left: none;
        }}
        .toggle-btn.active {{
            background: #306998;
            color: white;
        }}
        .toggle-btn:hover:not(.active) {{
            background: #f0f4f8;
        }}
        #chart-container {{
            position: relative;
            width: 100%;
            height: 550px;
        }}
        canvas {{
            width: 100%;
            height: 100%;
        }}
        .legend {{
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 12px;
            margin-top: 20px;
            padding: 16px;
            background: #f8f9fa;
            border-radius: 10px;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 13px;
            color: #333;
        }}
        .legend-color {{
            width: 14px;
            height: 14px;
            border-radius: 3px;
        }}
        .view-label {{
            text-align: center;
            color: #306998;
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 16px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>hierarchy-toggle-view · letsplot · pyplots.ai</h1>
        <p class="subtitle">Company Budget Allocation - Toggle between Treemap and Sunburst views</p>

        <div class="toggle-container">
            <button class="toggle-btn active" id="treemapBtn" onclick="showTreemap()">Treemap</button>
            <button class="toggle-btn" id="sunburstBtn" onclick="showSunburst()">Sunburst</button>
        </div>

        <div class="view-label" id="viewLabel">Treemap View - Nested rectangles show hierarchy</div>

        <div id="chart-container">
            <canvas id="chart-canvas"></canvas>
        </div>

        <div class="legend" id="legend"></div>
    </div>

    <script>
        const hierarchyData = {json.dumps(dict(hierarchy_data.items()))};
        const deptColors = {json.dumps(dept_colors)};
        const childColors = {json.dumps(child_colors)};
        const allColors = {{...deptColors, ...childColors}};

        // Get departments and leaves
        const departments = Object.values(hierarchyData).filter(n => n.level === 1).sort((a,b) => b.value - a.value);
        const leaves = Object.values(hierarchyData).filter(n => n.level === 2);
        const totalValue = departments.reduce((sum, d) => sum + d.value, 0);

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

        function squarify(values, x, y, w, h) {{
            const rects = [];
            const total = values.reduce((a,b) => a+b, 0);
            if (total === 0 || values.length === 0) return rects;

            let remaining = [...values];
            let rx = x, ry = y, rw = w, rh = h;

            while (remaining.length > 0) {{
                if (rw >= rh) {{
                    let row = [], rowSum = 0, bestRatio = Infinity;
                    for (const v of remaining) {{
                        const testRow = [...row, v];
                        const testSum = rowSum + v;
                        const rowWidth = (testSum / total) * w;
                        if (rowWidth > 0) {{
                            let worst = 0;
                            for (const rv of testRow) {{
                                const rectH = (rv / testSum) * rh;
                                const ratio = rectH > 0 ? Math.max(rowWidth / rectH, rectH / rowWidth) : Infinity;
                                worst = Math.max(worst, ratio);
                            }}
                            if (worst <= bestRatio) {{
                                bestRatio = worst;
                                row = testRow;
                                rowSum = testSum;
                            }} else break;
                        }} else {{
                            row = testRow;
                            rowSum = testSum;
                        }}
                    }}
                    const rowWidth = (rowSum / total) * w;
                    let cy = ry;
                    for (const rv of row) {{
                        const rectH = (rv / rowSum) * rh;
                        rects.push({{x: rx, y: cy, w: rowWidth, h: rectH}});
                        cy += rectH;
                    }}
                    rx += rowWidth;
                    rw -= rowWidth;
                    remaining = remaining.slice(row.length);
                }} else {{
                    let col = [], colSum = 0, bestRatio = Infinity;
                    for (const v of remaining) {{
                        const testCol = [...col, v];
                        const testSum = colSum + v;
                        const colHeight = (testSum / total) * h;
                        if (colHeight > 0) {{
                            let worst = 0;
                            for (const cv of testCol) {{
                                const rectW = (cv / testSum) * rw;
                                const ratio = rectW > 0 ? Math.max(colHeight / rectW, rectW / colHeight) : Infinity;
                                worst = Math.max(worst, ratio);
                            }}
                            if (worst <= bestRatio) {{
                                bestRatio = worst;
                                col = testCol;
                                colSum = testSum;
                            }} else break;
                        }} else {{
                            col = testCol;
                            colSum = testSum;
                        }}
                    }}
                    const colHeight = (colSum / total) * h;
                    let cx = rx;
                    for (const cv of col) {{
                        const rectW = (cv / colSum) * rw;
                        rects.push({{x: cx, y: ry, w: rectW, h: colHeight}});
                        cx += rectW;
                    }}
                    ry += colHeight;
                    rh -= colHeight;
                    remaining = remaining.slice(col.length);
                }}
            }}
            return rects;
        }}

        function drawTreemap() {{
            setupCanvas();
            const rect = canvas.parentElement.getBoundingClientRect();
            const padding = 30;
            const width = rect.width - 2 * padding;
            const height = rect.height - 2 * padding;

            ctx.clearRect(0, 0, rect.width, rect.height);

            // Layout departments
            const deptValues = departments.map(d => d.value);
            const deptRects = squarify(deptValues, padding, padding, width, height);
            const innerPad = 4;

            deptRects.forEach((dr, i) => {{
                const dept = departments[i];
                const color = deptColors[dept.label] || '#888';

                // Draw department background (semi-transparent)
                ctx.fillStyle = color;
                ctx.globalAlpha = 0.3;
                ctx.fillRect(dr.x, dr.y, dr.w, dr.h);
                ctx.globalAlpha = 1;
                ctx.strokeStyle = 'white';
                ctx.lineWidth = 3;
                ctx.strokeRect(dr.x, dr.y, dr.w, dr.h);

                // Get children
                const children = leaves.filter(l => l.parent === dept.id).sort((a,b) => b.value - a.value);
                const childValues = children.map(c => c.value);
                const childRects = squarify(
                    childValues,
                    dr.x + innerPad,
                    dr.y + innerPad,
                    dr.w - 2 * innerPad,
                    dr.h - 2 * innerPad - 20
                );

                childRects.forEach((cr, j) => {{
                    const child = children[j];
                    const cColor = childColors[child.label] || '#888';

                    ctx.fillStyle = cColor;
                    ctx.fillRect(cr.x, cr.y, cr.w, cr.h);
                    ctx.strokeStyle = 'white';
                    ctx.lineWidth = 2;
                    ctx.strokeRect(cr.x, cr.y, cr.w, cr.h);

                    // Child label
                    const pct = (child.value / totalValue * 100).toFixed(0);
                    if (cr.w > 50 && cr.h > 35) {{
                        ctx.fillStyle = 'white';
                        ctx.font = 'bold 12px -apple-system, sans-serif';
                        ctx.textAlign = 'center';
                        ctx.textBaseline = 'middle';
                        ctx.fillText(child.label, cr.x + cr.w/2, cr.y + cr.h/2 - 8);
                        ctx.font = '11px -apple-system, sans-serif';
                        ctx.fillText(pct + '%', cr.x + cr.w/2, cr.y + cr.h/2 + 8);
                    }} else if (cr.w > 25 && cr.h > 20) {{
                        ctx.fillStyle = 'white';
                        ctx.font = 'bold 10px -apple-system, sans-serif';
                        ctx.textAlign = 'center';
                        ctx.textBaseline = 'middle';
                        ctx.fillText(pct + '%', cr.x + cr.w/2, cr.y + cr.h/2);
                    }}
                }});

                // Department label at bottom
                ctx.fillStyle = '#333';
                ctx.font = 'bold 14px -apple-system, sans-serif';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(dept.label, dr.x + dr.w/2, dr.y + dr.h - 10);
            }});
        }}

        function drawSunburst() {{
            setupCanvas();
            const rect = canvas.parentElement.getBoundingClientRect();
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            const maxR = Math.min(centerX, centerY) - 40;

            // Two rings: inner for departments, outer for children
            const r0 = maxR * 0.15;  // center hole
            const r1 = maxR * 0.5;   // inner ring outer edge
            const r2 = maxR;         // outer ring outer edge

            ctx.clearRect(0, 0, rect.width, rect.height);

            let startAngle = -Math.PI / 2;
            const deptAngles = {{}};

            // Draw inner ring (departments)
            departments.forEach(dept => {{
                const pct = dept.value / totalValue;
                const endAngle = startAngle + pct * 2 * Math.PI;
                deptAngles[dept.id] = {{start: startAngle, end: endAngle}};
                const color = deptColors[dept.label] || '#888';

                ctx.beginPath();
                ctx.moveTo(centerX + r0 * Math.cos(startAngle), centerY + r0 * Math.sin(startAngle));
                ctx.arc(centerX, centerY, r1, startAngle, endAngle);
                ctx.lineTo(centerX + r0 * Math.cos(endAngle), centerY + r0 * Math.sin(endAngle));
                ctx.arc(centerX, centerY, r0, endAngle, startAngle, true);
                ctx.closePath();
                ctx.fillStyle = color;
                ctx.fill();
                ctx.strokeStyle = 'white';
                ctx.lineWidth = 2;
                ctx.stroke();

                // Department label
                const midAngle = (startAngle + endAngle) / 2;
                const labelR = (r0 + r1) / 2;
                ctx.fillStyle = 'white';
                ctx.font = 'bold 13px -apple-system, sans-serif';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(dept.label, centerX + labelR * Math.cos(midAngle), centerY + labelR * Math.sin(midAngle));

                startAngle = endAngle;
            }});

            // Draw outer ring (children)
            departments.forEach(dept => {{
                const {{start: dStart, end: dEnd}} = deptAngles[dept.id];
                const dSpan = dEnd - dStart;
                const children = leaves.filter(l => l.parent === dept.id).sort((a,b) => b.value - a.value);
                const childTotal = children.reduce((s, c) => s + c.value, 0);

                let cStart = dStart;
                children.forEach(child => {{
                    const cPct = childTotal > 0 ? child.value / childTotal : 0;
                    const cSpan = cPct * dSpan;
                    const cEnd = cStart + cSpan;
                    const color = childColors[child.label] || '#888';

                    ctx.beginPath();
                    ctx.moveTo(centerX + r1 * Math.cos(cStart), centerY + r1 * Math.sin(cStart));
                    ctx.arc(centerX, centerY, r2, cStart, cEnd);
                    ctx.lineTo(centerX + r1 * Math.cos(cEnd), centerY + r1 * Math.sin(cEnd));
                    ctx.arc(centerX, centerY, r1, cEnd, cStart, true);
                    ctx.closePath();
                    ctx.fillStyle = color;
                    ctx.fill();
                    ctx.strokeStyle = 'white';
                    ctx.lineWidth = 1.5;
                    ctx.stroke();

                    // Child label (only for larger segments)
                    const globalPct = child.value / totalValue;
                    if (globalPct > 0.05) {{
                        const midAngle = (cStart + cEnd) / 2;
                        const labelR = (r1 + r2) / 2;
                        ctx.fillStyle = '#333';
                        ctx.font = 'bold 11px -apple-system, sans-serif';
                        ctx.textAlign = 'center';
                        ctx.textBaseline = 'middle';
                        ctx.fillText(child.label, centerX + labelR * Math.cos(midAngle), centerY + labelR * Math.sin(midAngle));
                    }}

                    cStart = cEnd;
                }});
            }});

            // Center label
            ctx.fillStyle = '#333';
            ctx.font = 'bold 16px -apple-system, sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText('Total', centerX, centerY - 8);
            ctx.font = '13px -apple-system, sans-serif';
            ctx.fillText('$' + (totalValue/1000).toFixed(1) + 'M', centerX, centerY + 10);
        }}

        function showTreemap() {{
            currentView = 'treemap';
            document.getElementById('treemapBtn').classList.add('active');
            document.getElementById('sunburstBtn').classList.remove('active');
            document.getElementById('viewLabel').textContent = 'Treemap View - Nested rectangles show hierarchy';
            drawTreemap();
        }}

        function showSunburst() {{
            currentView = 'sunburst';
            document.getElementById('sunburstBtn').classList.add('active');
            document.getElementById('treemapBtn').classList.remove('active');
            document.getElementById('viewLabel').textContent = 'Sunburst View - Concentric rings show hierarchy depth';
            drawSunburst();
        }}

        // Build legend (departments only for clarity)
        const legend = document.getElementById('legend');
        legend.innerHTML = departments.map(dept => {{
            const color = deptColors[dept.label] || '#888';
            const pct = (dept.value / totalValue * 100).toFixed(1);
            return `<div class="legend-item">
                <div class="legend-color" style="background: ${{color}}"></div>
                <span>${{dept.label}} (${{pct}}%)</span>
            </div>`;
        }}).join('');

        window.addEventListener('resize', () => {{
            if (currentView === 'treemap') drawTreemap();
            else drawSunburst();
        }});

        drawTreemap();
    </script>
</body>
</html>"""

with open("plot.html", "w") as f:
    f.write(html_content)
