""" pyplots.ai
bubble-packed: Basic Packed Bubble Chart
Library: pygal 3.1.0 | Python 3.14.3
Quality: 85/100 | Updated: 2026-02-23
"""

import math

import pygal
from pygal.etree import etree
from pygal.style import Style


# Department budget allocation data ($K, determines circle area)
data = [
    {"label": "Software Development", "value": 450, "group": "Technology"},
    {"label": "Cloud Infrastructure", "value": 280, "group": "Technology"},
    {"label": "Data Analytics", "value": 180, "group": "Technology"},
    {"label": "Security", "value": 120, "group": "Technology"},
    {"label": "Digital Marketing", "value": 350, "group": "Marketing"},
    {"label": "Brand & Creative", "value": 220, "group": "Marketing"},
    {"label": "Events", "value": 150, "group": "Marketing"},
    {"label": "PR", "value": 90, "group": "Marketing"},
    {"label": "Facilities", "value": 280, "group": "Operations"},
    {"label": "HR & Recruiting", "value": 200, "group": "Operations"},
    {"label": "Legal", "value": 160, "group": "Operations"},
    {"label": "Admin", "value": 100, "group": "Operations"},
    {"label": "Enterprise", "value": 380, "group": "Sales"},
    {"label": "SMB", "value": 250, "group": "Sales"},
    {"label": "Partners", "value": 170, "group": "Sales"},
    {"label": "Support", "value": 110, "group": "Sales"},
]

WIDTH = 4800
HEIGHT = 2700
PADDING = 15

# Colorblind-safe palette with strong contrast on white
GROUP_COLORS = {"Technology": "#306998", "Marketing": "#CC8400", "Operations": "#1A8A72", "Sales": "#C94D46"}
GROUP_NAMES = ["Technology", "Marketing", "Operations", "Sales"]

# Compute group totals for labels and sorting
group_totals = {}
for item in data:
    group_totals[item["group"]] = group_totals.get(item["group"], 0) + item["value"]

# Scale values to radii (sqrt for area-based visual perception)
max_val = max(item["value"] for item in data)
max_radius = min(WIDTH, HEIGHT) * 0.11

circles = []
for item in data:
    r = math.sqrt(item["value"] / max_val) * max_radius
    circles.append({"r": r, "item": item, "x": 0.0, "y": 0.0})

# Sort by group (largest budget group first for central placement),
# then by descending radius within each group — enables spatial clustering
sorted_groups = sorted(GROUP_NAMES, key=lambda g: -group_totals[g])
group_order = {g: i for i, g in enumerate(sorted_groups)}
circles.sort(key=lambda c: (group_order[c["item"]["group"]], -c["r"]))

# Packing center
cx, cy = WIDTH / 2, HEIGHT / 2

# Place first circle at center
circles[0]["x"] = cx
circles[0]["y"] = cy
placed = [circles[0]]

# Greedy circle packing with group-affinity clustering
for circle in circles[1:]:
    best_pos = None
    best_score = float("inf")
    same_group = [p for p in placed if p["item"]["group"] == circle["item"]["group"]]

    for existing in placed:
        for angle_deg in range(0, 360, 6):
            angle = math.radians(angle_deg)
            dist = existing["r"] + circle["r"] + PADDING
            nx = existing["x"] + math.cos(angle) * dist
            ny = existing["y"] + math.sin(angle) * dist

            # Check for overlaps with all placed circles
            valid = True
            for other in placed:
                dx = nx - other["x"]
                dy = ny - other["y"]
                min_gap = circle["r"] + other["r"] + PADDING * 0.5
                if math.sqrt(dx * dx + dy * dy) < min_gap:
                    valid = False
                    break

            if valid:
                d_center = math.sqrt((nx - cx) ** 2 + (ny - cy) ** 2)

                if same_group:
                    # Strongly prefer positions near same-group circles
                    d_group = sum(math.sqrt((nx - p["x"]) ** 2 + (ny - p["y"]) ** 2) for p in same_group) / len(
                        same_group
                    )
                    score = d_center * 0.3 + d_group * 0.7
                else:
                    # First circle of a new group: minimize distance to center
                    score = d_center

                if score < best_score:
                    best_score = score
                    best_pos = (nx, ny)

    if best_pos:
        circle["x"], circle["y"] = best_pos
    else:
        circle["x"] = cx
        circle["y"] = max(c["y"] + c["r"] for c in placed) + circle["r"] + PADDING

    placed.append(circle)

# Recenter bubble layout vertically in available canvas area
min_y_all = min(c["y"] - c["r"] for c in placed)
max_y_all = max(c["y"] + c["r"] for c in placed)
min_x_all = min(c["x"] - c["r"] for c in placed)
max_x_all = max(c["x"] + c["r"] for c in placed)

# Available area: title ~180px from top, legend ~300px from bottom
avail_top = 180
avail_bottom = HEIGHT - 300
target_cy = (avail_top + avail_bottom) / 2
target_cx = WIDTH / 2

dy = target_cy - (min_y_all + max_y_all) / 2
dx = target_cx - (min_x_all + max_x_all) / 2

for c in placed:
    c["x"] += dx
    c["y"] += dy

# Compute group centroids and bounds for visual indicators
group_info = {}
for c in placed:
    g = c["item"]["group"]
    if g not in group_info:
        group_info[g] = {"xs": [], "ys": [], "rs": []}
    group_info[g]["xs"].append(c["x"])
    group_info[g]["ys"].append(c["y"])
    group_info[g]["rs"].append(c["r"])

packed = [(c["x"], c["y"], c["r"], c["item"]) for c in placed]

# Pygal style
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333",
    foreground_strong="#333",
    foreground_subtle="#666",
    colors=list(GROUP_COLORS.values()),
    title_font_size=72,
    legend_font_size=42,
    value_font_size=32,
)

# Pygal chart scaffold (Pie provides legend and title infrastructure)
chart = pygal.Pie(
    width=WIDTH,
    height=HEIGHT,
    style=custom_style,
    title="bubble-packed \u00b7 pygal \u00b7 pyplots.ai",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    inner_radius=0,
    margin=80,
    no_data_text="",
    tooltip_fancy_mode=True,
    pretty_print=True,
    truncate_legend=-1,
)

# Legend entries showing group totals for context
for group in GROUP_NAMES:
    chart.add(f"{group}: ${group_totals[group]}K", [])


def add_packed_bubbles(root):
    """Render packed bubble clusters via pygal's SVG filter pipeline."""
    g = etree.SubElement(root, "g")
    g.set("class", "packed-bubbles")

    overall_cy = sum(c[1] for c in packed) / len(packed)

    # Subtle dashed group boundary indicators
    for gname, gdata in group_info.items():
        gcx = sum(gdata["xs"]) / len(gdata["xs"])
        gcy = sum(gdata["ys"]) / len(gdata["ys"])
        extent = max(
            math.sqrt((x - gcx) ** 2 + (y - gcy) ** 2) + r
            for x, y, r in zip(gdata["xs"], gdata["ys"], gdata["rs"], strict=True)
        )
        bg = etree.SubElement(g, "circle")
        bg.set("cx", f"{gcx:.0f}")
        bg.set("cy", f"{gcy:.0f}")
        bg.set("r", f"{extent + 22:.0f}")
        bg.set("fill", GROUP_COLORS[gname])
        bg.set("fill-opacity", "0.06")
        bg.set("stroke", GROUP_COLORS[gname])
        bg.set("stroke-opacity", "0.20")
        bg.set("stroke-width", "2.5")
        bg.set("stroke-dasharray", "10,7")

    # Data circles with labels
    for x, y, r, item in packed:
        color = GROUP_COLORS[item["group"]]

        circ = etree.SubElement(g, "circle")
        circ.set("cx", f"{x:.1f}")
        circ.set("cy", f"{y:.1f}")
        circ.set("r", f"{r:.1f}")
        circ.set("fill", color)
        circ.set("fill-opacity", "0.85")
        circ.set("stroke", "white")
        circ.set("stroke-width", "4")

        # SVG-native tooltip
        title = etree.SubElement(circ, "title")
        title.text = f"{item['label']}: ${item['value']}K ({item['group']})"

        # Dark text on light backgrounds, white on dark
        text_color = "#333" if item["group"] == "Marketing" else "white"

        # Large circles: name + value on two lines
        if r > 110:
            fs = max(int(r * 0.22), 28)
            t1 = etree.SubElement(g, "text")
            t1.set("x", f"{x:.0f}")
            t1.set("y", f"{y - fs * 0.55:.0f}")
            t1.set("text-anchor", "middle")
            t1.set("dominant-baseline", "middle")
            t1.set("fill", text_color)
            t1.set("font-size", f"{fs}")
            t1.set("font-family", "sans-serif")
            t1.set("font-weight", "bold")
            t1.text = item["label"].split()[0]

            t2 = etree.SubElement(g, "text")
            t2.set("x", f"{x:.0f}")
            t2.set("y", f"{y + fs * 0.65:.0f}")
            t2.set("text-anchor", "middle")
            t2.set("dominant-baseline", "middle")
            t2.set("fill", text_color)
            t2.set("font-size", f"{int(fs * 0.82)}")
            t2.set("font-family", "sans-serif")
            t2.text = f"${item['value']}K"

        # Medium circles: value only
        elif r > 55:
            fs = max(int(r * 0.30), 24)
            t = etree.SubElement(g, "text")
            t.set("x", f"{x:.0f}")
            t.set("y", f"{y:.0f}")
            t.set("text-anchor", "middle")
            t.set("dominant-baseline", "middle")
            t.set("fill", text_color)
            t.set("font-size", f"{fs}")
            t.set("font-family", "sans-serif")
            t.set("font-weight", "bold")
            t.text = f"${item['value']}K"

        # Small circles: value
        else:
            fs = max(int(r * 0.38), 22)
            t = etree.SubElement(g, "text")
            t.set("x", f"{x:.0f}")
            t.set("y", f"{y:.0f}")
            t.set("text-anchor", "middle")
            t.set("dominant-baseline", "middle")
            t.set("fill", text_color)
            t.set("font-size", f"{fs}")
            t.set("font-family", "sans-serif")
            t.text = f"${item['value']}K"

    # Group labels with aggregated totals
    for gname, gdata in group_info.items():
        gcx = sum(gdata["xs"]) / len(gdata["xs"])
        gcy = sum(gdata["ys"]) / len(gdata["ys"])

        # Place above for upper groups, below for lower groups
        if gcy < overall_cy:
            label_y = min(y - r for y, r in zip(gdata["ys"], gdata["rs"], strict=True)) - 28
        else:
            label_y = max(y + r for y, r in zip(gdata["ys"], gdata["rs"], strict=True)) + 52

        lbl = etree.SubElement(g, "text")
        lbl.set("x", f"{gcx:.0f}")
        lbl.set("y", f"{label_y:.0f}")
        lbl.set("text-anchor", "middle")
        lbl.set("fill", GROUP_COLORS[gname])
        lbl.set("font-size", "38")
        lbl.set("font-family", "sans-serif")
        lbl.set("font-weight", "bold")
        lbl.set("letter-spacing", "1")
        lbl.text = f"{gname}: ${group_totals[gname]}K"

    return root


chart.add_xml_filter(add_packed_bubbles)

chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
