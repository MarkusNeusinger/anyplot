"""pyplots.ai
circlepacking-basic: Circle Packing Chart
Library: plotly 6.5.0 | Python 3.13.11
Quality: 88/100 | Created: 2025-12-30
"""

import numpy as np
import plotly.graph_objects as go


np.random.seed(42)

# Data: File system hierarchy with sizes (in MB) - simplified for clarity
hierarchy = {
    "Documents": {
        "Reports": {"Q1": 45, "Q2": 52, "Annual": 78},
        "Sheets": {"Budget": 28, "Expenses": 32, "Forecast": 41},
        "Slides": {"Sales": 65, "Training": 48},
    },
    "Media": {
        "Photos": {"Vacation": 120, "Family": 95, "Events": 75},
        "Videos": {"Tutorials": 180, "Recordings": 210},
        "Music": {"Playlists": 85, "Podcasts": 95},
    },
    "Projects": {
        "Python": {"ML": 68, "Scripts": 42, "Tests": 38},
        "Web": {"Frontend": 52, "Backend": 48, "Assets": 65},
    },
    "System": {"Logs": {"App": 35, "System": 28, "Error": 22}, "Cache": {"Browser": 65, "Temp": 38}},
}

# Color palette by category (colorblind-safe)
category_colors = {
    "Root": "#2E4057",
    "Documents": "#306998",
    "Media": "#FFD43B",
    "Projects": "#4B8BBE",
    "System": "#646464",
}

subcat_colors = {"Documents": "#5A93B8", "Media": "#FFE580", "Projects": "#7AB8E0", "System": "#909090"}

leaf_colors = {"Documents": "#8AB8D8", "Media": "#FFF0B3", "Projects": "#A8D4F0", "System": "#B8B8B8"}

# Calculate total size
total_size = sum(sum(sum(items.values()) for items in subcats.values()) for subcats in hierarchy.values())

# Build all circles
all_circles = []

# Root circle
root_radius = 420
all_circles.append(
    {
        "x": 0,
        "y": 0,
        "r": root_radius,
        "label": "Storage",
        "value": total_size,
        "color": category_colors["Root"],
        "level": -1,
    }
)

# Calculate category data and sort by size
cat_data = []
for cat, subcats in hierarchy.items():
    total = sum(sum(items.values()) for items in subcats.values())
    cat_data.append((cat, total, subcats))
cat_data.sort(key=lambda x: x[1], reverse=True)

# Calculate category radii
cat_radii = [(cat, np.sqrt(total) * 6.0, total, subcats) for cat, total, subcats in cat_data]

# Pack top-level categories inline (no helper function)
packed_cats = []
for i, (name, radius, value, subcats) in enumerate(cat_radii):
    if i == 0:
        packed_cats.append({"name": name, "r": radius, "value": value, "subcats": subcats, "x": 0, "y": radius * 0.3})
    else:
        best_pos = None
        min_dist_from_center = float("inf")
        for existing in packed_cats:
            for angle in np.linspace(0, 2 * np.pi, 36):
                dist = existing["r"] + radius + 10
                nx = existing["x"] + dist * np.cos(angle)
                ny = existing["y"] + dist * np.sin(angle)
                d_to_center = np.sqrt(nx**2 + ny**2)
                if d_to_center + radius > root_radius * 0.95:
                    continue
                overlaps = False
                for other in packed_cats:
                    d = np.sqrt((nx - other["x"]) ** 2 + (ny - other["y"]) ** 2)
                    if d < other["r"] + radius + 8:
                        overlaps = True
                        break
                if not overlaps and d_to_center < min_dist_from_center:
                    min_dist_from_center = d_to_center
                    best_pos = (nx, ny)
        if best_pos:
            packed_cats.append(
                {"name": name, "r": radius, "value": value, "subcats": subcats, "x": best_pos[0], "y": best_pos[1]}
            )

# Build hierarchy with subcategories and leaves
for cat_info in packed_cats:
    cat = cat_info["name"]
    cx, cy = cat_info["x"], cat_info["y"]
    cat_radius = cat_info["r"]
    subcats = cat_info["subcats"]

    all_circles.append(
        {
            "x": cx,
            "y": cy,
            "r": cat_radius,
            "label": cat,
            "value": cat_info["value"],
            "color": category_colors[cat],
            "level": 0,
        }
    )

    # Pack subcategories within category (inline)
    subcat_list = sorted(
        [(name, sum(items.values()), items) for name, items in subcats.items()], key=lambda x: x[1], reverse=True
    )
    packed_subs = []
    sub_scale = 3.0

    for j, (sub_name, sub_value, sub_items) in enumerate(subcat_list):
        sub_r = np.sqrt(sub_value) * sub_scale
        if j == 0:
            packed_subs.append({"name": sub_name, "value": sub_value, "items": sub_items, "r": sub_r, "x": cx, "y": cy})
        else:
            best_pos = None
            min_dist = float("inf")
            for existing in packed_subs:
                for angle in np.linspace(0, 2 * np.pi, 24):
                    dist = existing["r"] + sub_r + 4
                    nx = existing["x"] + dist * np.cos(angle)
                    ny = existing["y"] + dist * np.sin(angle)
                    d_to_parent = np.sqrt((nx - cx) ** 2 + (ny - cy) ** 2)
                    if d_to_parent + sub_r > cat_radius * 0.88:
                        continue
                    overlaps = False
                    for other in packed_subs:
                        d = np.sqrt((nx - other["x"]) ** 2 + (ny - other["y"]) ** 2)
                        if d < other["r"] + sub_r + 3:
                            overlaps = True
                            break
                    if not overlaps:
                        d_center = np.sqrt((nx - cx) ** 2 + (ny - cy) ** 2)
                        if d_center < min_dist:
                            min_dist = d_center
                            best_pos = (nx, ny)
            if best_pos:
                packed_subs.append(
                    {
                        "name": sub_name,
                        "value": sub_value,
                        "items": sub_items,
                        "r": sub_r,
                        "x": best_pos[0],
                        "y": best_pos[1],
                    }
                )

    for sub in packed_subs:
        sub_x, sub_y, sub_r = sub["x"], sub["y"], sub["r"]
        all_circles.append(
            {
                "x": sub_x,
                "y": sub_y,
                "r": sub_r,
                "label": sub["name"],
                "value": sub["value"],
                "color": subcat_colors[cat],
                "level": 1,
                "parent": cat,
            }
        )

        # Pack leaf nodes within subcategory (inline)
        leaf_list = sorted(sub["items"].items(), key=lambda x: x[1], reverse=True)
        packed_leaves = []
        leaf_scale = 1.8

        for k, (leaf_name, leaf_value) in enumerate(leaf_list):
            leaf_r = np.sqrt(leaf_value) * leaf_scale
            if k == 0:
                packed_leaves.append({"name": leaf_name, "value": leaf_value, "r": leaf_r, "x": sub_x, "y": sub_y})
            else:
                best_pos = None
                min_dist = float("inf")
                for existing in packed_leaves:
                    for angle in np.linspace(0, 2 * np.pi, 24):
                        dist = existing["r"] + leaf_r + 2
                        nx = existing["x"] + dist * np.cos(angle)
                        ny = existing["y"] + dist * np.sin(angle)
                        d_to_parent = np.sqrt((nx - sub_x) ** 2 + (ny - sub_y) ** 2)
                        if d_to_parent + leaf_r > sub_r * 0.85:
                            continue
                        overlaps = False
                        for other in packed_leaves:
                            d = np.sqrt((nx - other["x"]) ** 2 + (ny - other["y"]) ** 2)
                            if d < other["r"] + leaf_r + 1:
                                overlaps = True
                                break
                        if not overlaps:
                            d_center = np.sqrt((nx - sub_x) ** 2 + (ny - sub_y) ** 2)
                            if d_center < min_dist:
                                min_dist = d_center
                                best_pos = (nx, ny)
                if best_pos:
                    packed_leaves.append(
                        {"name": leaf_name, "value": leaf_value, "r": leaf_r, "x": best_pos[0], "y": best_pos[1]}
                    )

        for leaf in packed_leaves:
            all_circles.append(
                {
                    "x": leaf["x"],
                    "y": leaf["y"],
                    "r": leaf["r"],
                    "label": leaf["name"],
                    "value": leaf["value"],
                    "color": leaf_colors[cat],
                    "level": 2,
                    "parent": sub["name"],
                }
            )

# Create figure
fig = go.Figure()

# Draw circles by level (background to foreground)
for level in [-1, 0, 1, 2]:
    for circle in all_circles:
        if circle["level"] == level:
            if level == -1:
                opacity, line_width = 0.12, 3
            elif level == 0:
                opacity, line_width = 0.85, 4
            elif level == 1:
                opacity, line_width = 0.75, 3
            else:
                opacity, line_width = 0.9, 2

            fig.add_shape(
                type="circle",
                xref="x",
                yref="y",
                x0=circle["x"] - circle["r"],
                y0=circle["y"] - circle["r"],
                x1=circle["x"] + circle["r"],
                y1=circle["y"] + circle["r"],
                fillcolor=circle["color"],
                opacity=opacity,
                line={"color": "white", "width": line_width},
            )

# Add labels - positioned to avoid overlap
for circle in all_circles:
    level = circle["level"]

    if level == -1:
        fig.add_annotation(
            x=circle["x"],
            y=circle["y"] - circle["r"] * 0.88,
            text=f"<b>{circle['label']}</b><br>{circle['value']:,} MB",
            showarrow=False,
            font={"size": 20, "color": "#333333"},
        )
    elif level == 0:
        text_color = "white" if circle["color"] in ["#306998", "#4B8BBE", "#646464"] else "#333333"
        fig.add_annotation(
            x=circle["x"],
            y=circle["y"] + circle["r"] * 0.7,
            text=f"<b>{circle['label']}</b>",
            showarrow=False,
            font={"size": 16, "color": text_color},
        )
        fig.add_annotation(
            x=circle["x"],
            y=circle["y"] + circle["r"] * 0.55,
            text=f"{circle['value']} MB",
            showarrow=False,
            font={"size": 13, "color": text_color},
        )
    elif level == 1 and circle["r"] > 35:
        text_color = "#333333" if circle["color"] == "#FFE580" else "white"
        fig.add_annotation(
            x=circle["x"],
            y=circle["y"] - circle["r"] * 0.6,
            text=f"<b>{circle['label']}</b>",
            showarrow=False,
            font={"size": 12, "color": text_color},
        )
    elif level == 2 and circle["r"] > 10:
        text_color = "#444444"
        fig.add_annotation(
            x=circle["x"],
            y=circle["y"],
            text=circle["label"][:6] if len(circle["label"]) > 6 else circle["label"],
            showarrow=False,
            font={"size": 9, "color": text_color},
        )

# Add hover traces for interactivity
for circle in all_circles:
    level_names = {-1: "Root", 0: "Category", 1: "Subcategory", 2: "File"}
    fig.add_trace(
        go.Scatter(
            x=[circle["x"]],
            y=[circle["y"]],
            mode="markers",
            marker={"size": max(circle["r"], 12), "opacity": 0},
            hovertemplate=f"<b>{circle['label']}</b><br>{level_names[circle['level']]}: {circle['value']} MB<extra></extra>",
            showlegend=False,
        )
    )

# Add legend traces
for name, color in [("Documents", "#306998"), ("Media", "#FFD43B"), ("Projects", "#4B8BBE"), ("System", "#646464")]:
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            marker={"size": 14, "color": color, "line": {"color": "white", "width": 1}},
            name=name,
            showlegend=True,
        )
    )

# Layout
fig.update_layout(
    title={
        "text": "circlepacking-basic · plotly · pyplots.ai",
        "font": {"size": 28},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.97,
    },
    xaxis={
        "showgrid": False,
        "zeroline": False,
        "showticklabels": False,
        "range": [-500, 500],
        "scaleanchor": "y",
        "scaleratio": 1,
    },
    yaxis={"showgrid": False, "zeroline": False, "showticklabels": False, "range": [-500, 500]},
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin={"t": 80, "l": 40, "r": 40, "b": 40},
    showlegend=True,
    legend={
        "x": 0.98,
        "y": 0.98,
        "xanchor": "right",
        "yanchor": "top",
        "bgcolor": "rgba(255,255,255,0.9)",
        "bordercolor": "#ccc",
        "borderwidth": 1,
        "font": {"size": 12},
        "title": {"text": "Categories", "font": {"size": 14}},
    },
)

# Save outputs
fig.write_image("plot.png", width=1200, height=1200, scale=3)
fig.write_html("plot.html")
