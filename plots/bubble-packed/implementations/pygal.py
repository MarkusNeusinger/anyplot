"""pyplots.ai
bubble-packed: Basic Packed Bubble Chart
Library: pygal 3.1.0 | Python 3.14.3
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
FONT_FAMILY = "'Trebuchet MS', 'Lucida Grande', sans-serif"

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
# then by descending radius within each group
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

            valid = True
            for other in placed:
                ddx = nx - other["x"]
                ddy = ny - other["y"]
                min_gap = circle["r"] + other["r"] + PADDING * 0.5
                if math.sqrt(ddx * ddx + ddy * ddy) < min_gap:
                    valid = False
                    break

            if valid:
                d_center = math.sqrt((nx - cx) ** 2 + (ny - cy) ** 2)
                if same_group:
                    d_group = sum(math.sqrt((nx - p["x"]) ** 2 + (ny - p["y"]) ** 2) for p in same_group) / len(
                        same_group
                    )
                    score = d_center * 0.3 + d_group * 0.7
                else:
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

# Recenter layout using area-weighted centroid for balanced visual appearance
avail_top = 180
avail_bottom = HEIGHT - 300
target_cy = (avail_top + avail_bottom) / 2
target_cx = WIDTH / 2

total_area = sum(c["r"] ** 2 for c in placed)
weighted_cx = sum(c["x"] * c["r"] ** 2 for c in placed) / total_area
weighted_cy = sum(c["y"] * c["r"] ** 2 for c in placed) / total_area
dx = target_cx - weighted_cx
dy = target_cy - weighted_cy

for c in placed:
    c["x"] += dx
    c["y"] += dy

# Compute group centroids and bounds
group_info = {}
for c in placed:
    g = c["item"]["group"]
    if g not in group_info:
        group_info[g] = {"xs": [], "ys": [], "rs": []}
    group_info[g]["xs"].append(c["x"])
    group_info[g]["ys"].append(c["y"])
    group_info[g]["rs"].append(c["r"])

packed = [(c["x"], c["y"], c["r"], c["item"]) for c in placed]

# Pygal style with explicit typography
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333",
    foreground_strong="#222",
    foreground_subtle="#888",
    colors=list(GROUP_COLORS.values()),
    font_family=FONT_FAMILY,
    title_font_size=72,
    legend_font_size=42,
    value_font_size=32,
)

# Pygal chart scaffold (Pie provides legend/title infrastructure)
chart = pygal.Pie(
    width=WIDTH,
    height=HEIGHT,
    style=custom_style,
    title="bubble-packed \u00b7 pygal \u00b7 pyplots.ai",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    legend_box_size=28,
    inner_radius=0,
    margin=80,
    no_data_text="",
    tooltip_fancy_mode=True,
    pretty_print=True,
    truncate_legend=-1,
)

# Legend entries with formatted group totals
for group in GROUP_NAMES:
    chart.add(f"{group}: ${group_totals[group]:,}K", [])


def add_packed_bubbles(root):
    """Render packed bubble clusters via pygal's SVG filter pipeline."""

    def _text(parent, x, y, label, size, color, bold=False):
        """Create an SVG text element with consistent styling."""
        t = etree.SubElement(parent, "text")
        t.set("x", f"{x:.0f}")
        t.set("y", f"{y:.0f}")
        t.set("text-anchor", "middle")
        t.set("dominant-baseline", "middle")
        t.set("fill", color)
        t.set("font-size", f"{size}")
        t.set("font-family", FONT_FAMILY)
        if bold:
            t.set("font-weight", "bold")
        t.text = label

    # SVG defs: radial gradients for polished 3D bubble appearance
    defs = etree.SubElement(root, "defs")
    for gname, color in GROUP_COLORS.items():
        grad = etree.SubElement(defs, "radialGradient")
        grad.set("id", f"grad-{gname.lower()}")
        grad.set("cx", "35%")
        grad.set("cy", "35%")
        grad.set("r", "65%")
        rgb = [int(color[i : i + 2], 16) for i in (1, 3, 5)]
        light = [min(255, c + 60) for c in rgb]
        stop1 = etree.SubElement(grad, "stop")
        stop1.set("offset", "0%")
        stop1.set("stop-color", f"#{light[0]:02x}{light[1]:02x}{light[2]:02x}")
        stop1.set("stop-opacity", "0.95")
        stop2 = etree.SubElement(grad, "stop")
        stop2.set("offset", "100%")
        stop2.set("stop-color", color)
        stop2.set("stop-opacity", "0.90")

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
        bg.set("r", f"{extent + 24:.0f}")
        bg.set("fill", GROUP_COLORS[gname])
        bg.set("fill-opacity", "0.05")
        bg.set("stroke", GROUP_COLORS[gname])
        bg.set("stroke-opacity", "0.18")
        bg.set("stroke-width", "2")
        bg.set("stroke-dasharray", "12,8")

    # Data circles with gradient fills
    for x, y, r, item in packed:
        grad_id = f"grad-{item['group'].lower()}"
        circ = etree.SubElement(g, "circle")
        circ.set("cx", f"{x:.1f}")
        circ.set("cy", f"{y:.1f}")
        circ.set("r", f"{r:.1f}")
        circ.set("fill", f"url(#{grad_id})")
        circ.set("stroke", "white")
        circ.set("stroke-width", "4")

        title = etree.SubElement(circ, "title")
        title.text = f"{item['label']}: ${item['value']}K ({item['group']})"

    # Highlight ring on the largest circle for visual emphasis
    top = max(packed, key=lambda c: c[2])
    ring = etree.SubElement(g, "circle")
    ring.set("cx", f"{top[0]:.1f}")
    ring.set("cy", f"{top[1]:.1f}")
    ring.set("r", f"{top[2] + 8:.1f}")
    ring.set("fill", "none")
    ring.set("stroke", GROUP_COLORS[top[3]["group"]])
    ring.set("stroke-width", "3")
    ring.set("stroke-opacity", "0.40")
    ring.set("stroke-dasharray", "8,5")

    # Circle labels (consolidated via _text helper)
    for x, y, r, item in packed:
        text_color = "#333" if item["group"] == "Marketing" else "white"
        if r > 110:
            fs = max(int(r * 0.22), 28)
            _text(g, x, y - fs * 0.55, item["label"].split()[0], fs, text_color, bold=True)
            _text(g, x, y + fs * 0.65, f"${item['value']}K", int(fs * 0.82), text_color)
        elif r > 55:
            fs = max(int(r * 0.30), 24)
            _text(g, x, y, f"${item['value']}K", fs, text_color, bold=True)
        else:
            fs = max(int(r * 0.38), 22)
            _text(g, x, y, f"${item['value']}K", fs, text_color)

    # Group labels with consistent outward placement and increased padding
    for gname, gdata in group_info.items():
        gcx = sum(gdata["xs"]) / len(gdata["xs"])
        gcy = sum(gdata["ys"]) / len(gdata["ys"])

        if gcy < overall_cy:
            label_y = min(y - r for y, r in zip(gdata["ys"], gdata["rs"], strict=True)) - 40
        else:
            label_y = max(y + r for y, r in zip(gdata["ys"], gdata["rs"], strict=True)) + 60

        lbl = etree.SubElement(g, "text")
        lbl.set("x", f"{gcx:.0f}")
        lbl.set("y", f"{label_y:.0f}")
        lbl.set("text-anchor", "middle")
        lbl.set("fill", GROUP_COLORS[gname])
        lbl.set("font-size", "38")
        lbl.set("font-family", FONT_FAMILY)
        lbl.set("font-weight", "bold")
        lbl.set("letter-spacing", "1.5")
        lbl.text = f"{gname}: ${group_totals[gname]:,}K"

    return root


chart.add_xml_filter(add_packed_bubbles)

chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
