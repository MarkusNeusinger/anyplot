"""pyplots.ai
column-stratigraphic: Stratigraphic Column with Lithology Patterns
Library: pygal 3.1.0 | Python 3.14.3
"""

import re

import cairosvg
import pygal
from pygal.style import Style


# Data: Synthetic sedimentary section (depth in meters, increasing downward)
layers = [
    {"top": 0, "bottom": 12, "lithology": "sandstone", "formation": "Red Mesa Fm", "age": "Eocene"},
    {"top": 12, "bottom": 25, "lithology": "shale", "formation": "Grey Basin Fm", "age": "Paleocene"},
    {"top": 25, "bottom": 38, "lithology": "limestone", "formation": "Chalk Bluff Fm", "age": "Paleocene"},
    {"top": 38, "bottom": 50, "lithology": "siltstone", "formation": "Iron Creek Mbr", "age": "L. Cretaceous"},
    {"top": 50, "bottom": 68, "lithology": "sandstone", "formation": "Canyon Wall Fm", "age": "L. Cretaceous"},
    {"top": 68, "bottom": 82, "lithology": "shale", "formation": "Dark Hollow Fm", "age": "E. Cretaceous"},
    {"top": 82, "bottom": 90, "lithology": "conglomerate", "formation": "Boulder Bed Mbr", "age": "E. Cretaceous"},
    {"top": 90, "bottom": 108, "lithology": "limestone", "formation": "Shell Bank Fm", "age": "Jurassic"},
    {"top": 108, "bottom": 118, "lithology": "mudstone", "formation": "Quiet Water Fm", "age": "Jurassic"},
    {"top": 118, "bottom": 135, "lithology": "dolomite", "formation": "Crystal Ridge Fm", "age": "Triassic"},
]

# Lithology colors - distinct for accessibility (siltstone green vs conglomerate brown)
LITH_COLORS = {
    "sandstone": "#FFD700",
    "shale": "#808080",
    "limestone": "#87CEEB",
    "siltstone": "#8FBC8F",
    "conglomerate": "#CD853F",
    "mudstone": "#A9A9A9",
    "dolomite": "#DDA0DD",
}

total_depth = layers[-1]["bottom"]

# Custom style with monospace scientific typography
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#dddddd",
    colors=tuple(LITH_COLORS[layer["lithology"]] for layer in layers),
    title_font_size=48,
    label_font_size=28,
    major_label_font_size=30,
    legend_font_size=24,
    value_font_size=22,
    font_family="Consolas, 'Courier New', monospace",
    title_font_family="Consolas, 'Courier New', monospace",
    label_font_family="Consolas, 'Courier New', monospace",
    legend_font_family="Consolas, 'Courier New', monospace",
    value_font_family="Consolas, 'Courier New', monospace",
)

# StackedBar: each layer is a series with actual thickness data
chart = pygal.StackedBar(
    width=3600,
    height=3600,
    style=custom_style,
    title="column-stratigraphic · pygal · pyplots.ai",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    legend_box_size=20,
    show_x_labels=False,
    show_y_labels=True,
    y_title="Stratigraphic Thickness (m)",
    print_values=True,
    value_formatter=lambda x: f"{int(x)}m" if x >= 10 else "",
    margin=60,
    margin_top=140,
    margin_left=520,
    margin_right=80,
    margin_bottom=260,
    range=(0, 140),
    show_y_guides=True,
    show_x_guides=False,
    human_readable=True,
    tooltip_fancy_mode=True,
    explicit_size=True,
    rounded_bars=2,
)

# Add layers from oldest (bottom) to youngest (top) for correct geological stacking
for layer in reversed(layers):
    thickness = layer["bottom"] - layer["top"]
    chart.add(
        f"{layer['formation']} \u00b7 {layer['age']}",
        [{"value": thickness, "label": f"{layer['lithology'].title()} \u00b7 {thickness}m"}],
    )

# Render SVG via pygal's charting engine
svg_string = chart.render().decode("utf-8")

# --- SVG lithology patterns (use rgb() fills to avoid collision with hex replacement) ---
patterns_svg = (
    '<pattern id="pat-sandstone" patternUnits="userSpaceOnUse" width="24" height="24">'
    '<rect width="24" height="24" fill="rgb(255,215,0)"/>'
    '<circle cx="6" cy="6" r="2" fill="rgb(184,134,11)" opacity="0.6"/>'
    '<circle cx="18" cy="18" r="2" fill="rgb(184,134,11)" opacity="0.6"/>'
    '<circle cx="18" cy="6" r="1.4" fill="rgb(184,134,11)" opacity="0.4"/>'
    '<circle cx="6" cy="18" r="1.4" fill="rgb(184,134,11)" opacity="0.4"/>'
    "</pattern>"
    '<pattern id="pat-shale" patternUnits="userSpaceOnUse" width="36" height="14">'
    '<rect width="36" height="14" fill="rgb(128,128,128)"/>'
    '<line x1="2" y1="7" x2="24" y2="7" stroke="rgb(68,68,68)" stroke-width="1.5"/>'
    "</pattern>"
    '<pattern id="pat-limestone" patternUnits="userSpaceOnUse" width="48" height="28">'
    '<rect width="48" height="28" fill="rgb(135,206,235)"/>'
    '<line x1="0" y1="0" x2="48" y2="0" stroke="rgb(65,105,225)" stroke-width="1.2"/>'
    '<line x1="0" y1="14" x2="48" y2="14" stroke="rgb(65,105,225)" stroke-width="1.2"/>'
    '<line x1="24" y1="0" x2="24" y2="14" stroke="rgb(65,105,225)" stroke-width="1.2"/>'
    '<line x1="0" y1="14" x2="0" y2="28" stroke="rgb(65,105,225)" stroke-width="1.2"/>'
    '<line x1="48" y1="14" x2="48" y2="28" stroke="rgb(65,105,225)" stroke-width="1.2"/>'
    "</pattern>"
    '<pattern id="pat-siltstone" patternUnits="userSpaceOnUse" width="28" height="20">'
    '<rect width="28" height="20" fill="rgb(143,188,143)"/>'
    '<line x1="3" y1="5" x2="12" y2="5" stroke="rgb(46,139,87)" stroke-width="1.2"/>'
    '<line x1="16" y1="12" x2="25" y2="12" stroke="rgb(46,139,87)" stroke-width="1.2"/>'
    "</pattern>"
    '<pattern id="pat-conglomerate" patternUnits="userSpaceOnUse" width="36" height="36">'
    '<rect width="36" height="36" fill="rgb(205,133,63)"/>'
    '<circle cx="10" cy="10" r="6" fill="none" stroke="rgb(139,69,19)" stroke-width="1.6"/>'
    '<circle cx="26" cy="24" r="7" fill="none" stroke="rgb(139,69,19)" stroke-width="1.6"/>'
    '<circle cx="24" cy="6" r="4" fill="none" stroke="rgb(139,69,19)" stroke-width="1.4"/>'
    "</pattern>"
    '<pattern id="pat-mudstone" patternUnits="userSpaceOnUse" width="24" height="10">'
    '<rect width="24" height="10" fill="rgb(169,169,169)"/>'
    '<line x1="0" y1="5" x2="24" y2="5" stroke="rgb(85,85,85)" stroke-width="0.8"/>'
    "</pattern>"
    '<pattern id="pat-dolomite" patternUnits="userSpaceOnUse" width="28" height="28">'
    '<rect width="28" height="28" fill="rgb(221,160,221)"/>'
    '<polyline points="14,2 26,14 14,26 2,14 14,2" fill="none" stroke="rgb(139,0,139)" stroke-width="1.2"/>'
    "</pattern>"
)

svg_string = svg_string.replace("<defs>", "<defs>" + patterns_svg, 1)

# Replace solid color fills in CSS with pattern fills (pygal uses CSS classes)
for lith_type, color in LITH_COLORS.items():
    svg_string = re.sub(rf"fill:{re.escape(color)}\b", f"fill:url(#pat-{lith_type})", svg_string, flags=re.IGNORECASE)

# Boost fill-opacity for pattern clarity on reactive elements
svg_string = svg_string.replace("fill-opacity:.7", "fill-opacity:1")

# --- Add age brackets on the left side ---
# Find the graph group transform to convert local to absolute coordinates
tx, ty = 0.0, 0.0
transform_match = re.search(r'<g[^>]*class="graph[^"]*"[^>]*transform="translate\(([^,]+),\s*([^)]+)\)"', svg_string)
if not transform_match:
    # Try alternate format without class before transform
    for m in re.finditer(r"<g[^>]*transform=\"translate\(([^,]+),\s*([^)]+)\)\"", svg_string):
        tx, ty = float(m.group(1)), float(m.group(2))
        break
else:
    tx, ty = float(transform_match.group(1)), float(transform_match.group(2))

# Parse bar rect positions from pygal's rendered SVG
bar_info = []
for match in re.finditer(r"<rect([^>]*)/>", svg_string):
    attrs = match.group(1)
    if "rect reactive" not in attrs or "tooltip-box" in attrs:
        continue
    x_m = re.search(r'x="([^"]*)"', attrs)
    y_m = re.search(r'y="([^"]*)"', attrs)
    w_m = re.search(r'width="([^"]*)"', attrs)
    h_m = re.search(r'height="([^"]*)"', attrs)
    if x_m and y_m and w_m and h_m:
        bar_info.append(
            {
                "x": float(x_m.group(1)) + tx,
                "y": float(y_m.group(1)) + ty,
                "w": float(w_m.group(1)),
                "h": float(h_m.group(1)),
            }
        )

if bar_info:
    bar_info.sort(key=lambda b: b["y"])

    # Map: reversed_layers[i] (oldest first) → bar_info[n-1-i] (largest y = bottom)
    reversed_layers = list(reversed(layers))
    n = len(bar_info)
    layer_bars = [
        {"layer": reversed_layers[i], "bar": bar_info[n - 1 - i]} for i in range(min(n, len(reversed_layers)))
    ]

    # Group consecutive layers by age
    age_groups = []
    current_age = layer_bars[0]["layer"]["age"]
    group_bars = [layer_bars[0]["bar"]]
    for lb in layer_bars[1:]:
        if lb["layer"]["age"] != current_age:
            age_groups.append({"age": current_age, "bars": group_bars})
            current_age = lb["layer"]["age"]
            group_bars = [lb["bar"]]
        else:
            group_bars.append(lb["bar"])
    age_groups.append({"age": current_age, "bars": group_bars})

    # Draw age brackets using absolute SVG coordinates
    bracket_elements = []
    bar_left = min(b["x"] for b in bar_info)
    bracket_x = bar_left - 40

    for group in age_groups:
        bars = group["bars"]
        y_positions = [b["y"] for b in bars] + [b["y"] + b["h"] for b in bars]
        y_top = min(y_positions) + 2
        y_bottom = max(y_positions) - 2
        y_mid = (y_top + y_bottom) / 2

        bracket_elements.append(
            f'<line x1="{bracket_x}" y1="{y_top:.1f}" '
            f'x2="{bracket_x}" y2="{y_bottom:.1f}" '
            f'stroke="#555" stroke-width="2.5"/>'
        )
        bracket_elements.append(
            f'<line x1="{bracket_x - 12}" y1="{y_top:.1f}" '
            f'x2="{bracket_x}" y2="{y_top:.1f}" '
            f'stroke="#555" stroke-width="2.5"/>'
        )
        bracket_elements.append(
            f'<line x1="{bracket_x - 12}" y1="{y_bottom:.1f}" '
            f'x2="{bracket_x}" y2="{y_bottom:.1f}" '
            f'stroke="#555" stroke-width="2.5"/>'
        )
        bracket_elements.append(
            f'<text x="{bracket_x - 20}" y="{y_mid:.1f}" '
            f'font-family="Consolas, monospace" font-size="24" fill="#555" '
            f'text-anchor="end" dominant-baseline="central">{group["age"]}</text>'
        )

    # Age header
    first_bar_y = min(b["y"] for b in bar_info)
    bracket_elements.append(
        f'<text x="{bracket_x - 20}" y="{first_bar_y - 30:.1f}" '
        f'font-family="Consolas, monospace" font-size="28" fill="#333" '
        f'text-anchor="end" font-weight="bold">Age</text>'
    )

    svg_string = svg_string.replace("</svg>", "\n".join(bracket_elements) + "\n</svg>")

# Remove "No data" text if present
svg_string = svg_string.replace(">No data<", "><")

# Save HTML (preserves pygal's interactive SVG tooltips - distinctive feature)
with open("plot.html", "w") as f:
    f.write(svg_string)

# Save PNG
cairosvg.svg2png(bytestring=svg_string.encode(), write_to="plot.png")
