"""pyplots.ai
tree-decision: Decision Tree Visualization with Probabilities
Library: pygal 3.1.0 | Python 3.14.3
"""

import cairosvg
import pygal
from pygal.style import Style


# Decision tree data: New Product Launch
# EMV rollback:
#   C1 (Launch):  0.6 × $500K + 0.4 × (−$100K) = $260K  [OPTIMAL]
#   C2 (License): 0.7 × $250K + 0.3 × $50K     = $190K  [PRUNED]
#   T5 (Nothing): $0K                                     [PRUNED]
#   D1 (Root):    max($260K, $190K, $0K)         = $260K

nodes = {
    "D1": {"type": "decision", "x": 600, "y": 1150, "emv": 260, "label": "Strategy\nChoice"},
    "C1": {"type": "chance", "x": 2050, "y": 500, "emv": 260, "label": "Market\nOutcome"},
    "C2": {"type": "chance", "x": 2050, "y": 1600, "emv": 190, "label": "License\nResult"},
    "T1": {"type": "terminal", "x": 3450, "y": 280, "payoff": 500},
    "T2": {"type": "terminal", "x": 3450, "y": 720, "payoff": -100},
    "T3": {"type": "terminal", "x": 3450, "y": 1380, "payoff": 250},
    "T4": {"type": "terminal", "x": 3450, "y": 1820, "payoff": 50},
    "T5": {"type": "terminal", "x": 2050, "y": 2150, "payoff": 0},
}

branches = [
    ("D1", "C1", "Launch Product", None, False),
    ("D1", "C2", "Sell License", None, True),
    ("D1", "T5", "Do Nothing", None, True),
    ("C1", "T1", "High Demand", 0.6, False),
    ("C1", "T2", "Low Demand", 0.4, False),
    ("C2", "T3", "Accepted", 0.7, True),
    ("C2", "T4", "Rejected", 0.3, True),
]

# Colorblind-safe palette (Wong/Okabe-Ito inspired)
DECISION_CLR = "#306998"
CHANCE_CLR = "#E8833A"
GAIN_CLR = "#0072B2"  # teal-blue for positive payoffs
LOSS_CLR = "#D55E00"  # vermilion for negative payoffs
ZERO_CLR = "#7F8C8D"
OPTIMAL_CLR = "#306998"
PRUNED_CLR = "#AAAAAA"
TXT = "#333333"
TXT_DIM = "#666666"

# Node dimensions
DEC_HALF = 70
CHC_R = 55
TRI = 60  # increased from 40

# pygal Style — full control over typography, background, and series palette
style = Style(
    background="white",
    plot_background="white",
    foreground=TXT,
    foreground_strong=TXT,
    foreground_subtle=TXT_DIM,
    colors=(DECISION_CLR, CHANCE_CLR, GAIN_CLR, LOSS_CLR, ZERO_CLR),
    title_font_size=72,
    legend_font_size=32,
    label_font_size=36,
    value_font_size=30,
    font_family="DejaVu Sans, sans-serif",
)

# Build pygal XY chart — use real data series for pygal-native legend
chart = pygal.XY(
    width=4800,
    height=2700,
    style=style,
    title="tree-decision \u00b7 pygal \u00b7 pyplots.ai",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=5,
    legend_box_size=24,
    show_x_guides=False,
    show_y_guides=False,
    show_x_labels=False,
    show_y_labels=False,
    dots_size=0,
    stroke=False,
    range=(0, 2700),
    xrange=(0, 4800),
    margin=20,
    spacing=15,
    print_labels=False,
)

# Add real node-position data per type — pygal generates legend entries automatically
chart.add(
    "Decision Node",
    [{"value": (n["x"], n["y"]), "label": f"EMV ${n['emv']}K"} for n in nodes.values() if n["type"] == "decision"],
)
chart.add(
    "Chance Node",
    [{"value": (n["x"], n["y"]), "label": f"EMV ${n['emv']}K"} for n in nodes.values() if n["type"] == "chance"],
)
chart.add(
    "Terminal (Gain)",
    [
        {"value": (n["x"], n["y"]), "label": f"${n['payoff']}K"}
        for n in nodes.values()
        if n["type"] == "terminal" and n["payoff"] > 0
    ],
)
chart.add(
    "Terminal (Loss)",
    [
        {"value": (n["x"], n["y"]), "label": f"${n['payoff']}K"}
        for n in nodes.values()
        if n["type"] == "terminal" and n["payoff"] < 0
    ],
)
chart.add(
    "Terminal (Neutral)",
    [
        {"value": (n["x"], n["y"]), "label": f"${n['payoff']}K"}
        for n in nodes.values()
        if n["type"] == "terminal" and n["payoff"] == 0
    ],
)

# Render pygal SVG (handles title, legend, background, plot structure)
base_svg = chart.render().decode("utf-8")

# Tree overlay — branches and shaped nodes injected into pygal's SVG
parts = ['<g id="decision-tree" font-family="DejaVu Sans, sans-serif">']

# Branches (elbow connectors)
for src, dst, label, prob, pruned in branches:
    p, c = nodes[src], nodes[dst]
    mid_x = p["x"] + (c["x"] - p["x"]) * 0.55
    clr = PRUNED_CLR if pruned else OPTIMAL_CLR
    w = 3 if pruned else 5
    dash = ' stroke-dasharray="20,12"' if pruned else ""
    alpha = "0.5" if pruned else "1.0"
    parts.append(
        f'<path d="M {p["x"]},{p["y"]} L {mid_x},{p["y"]} '
        f'L {mid_x},{c["y"]} L {c["x"]},{c["y"]}" '
        f'fill="none" stroke="{clr}" stroke-width="{w}" opacity="{alpha}"{dash}/>'
    )
    # Branch label
    vy = p["y"] + (c["y"] - p["y"]) * 0.45
    lc = TXT_DIM if pruned else TXT
    fw = "normal" if pruned else "bold"
    parts.append(
        f'<text x="{mid_x - 22}" y="{vy}" text-anchor="end" '
        f'font-size="36" fill="{lc}" font-weight="{fw}">{label}</text>'
    )
    # Probability
    if prob is not None:
        pc = TXT_DIM if pruned else CHANCE_CLR
        parts.append(
            f'<text x="{mid_x + 22}" y="{vy}" text-anchor="start" '
            f'font-size="34" fill="{pc}" font-style="italic">p = {prob}</text>'
        )
    # Pruned X mark
    if pruned:
        sy = p["y"] + (c["y"] - p["y"]) * 0.2
        for dx, dy in [((-16, -14), (16, 14)), ((-16, 14), (16, -14))]:
            parts.append(
                f'<line x1="{mid_x + dx[0]}" y1="{sy + dx[1]}" '
                f'x2="{mid_x + dy[0]}" y2="{sy + dy[1]}" '
                f'stroke="{LOSS_CLR}" stroke-width="4" opacity="0.8"/>'
            )

# Nodes (drawn on top of branches)
for _nid, node in nodes.items():
    x, y, ntype = node["x"], node["y"], node["type"]

    if ntype == "decision":
        parts.append(
            f'<rect x="{x - DEC_HALF}" y="{y - DEC_HALF}" '
            f'width="{DEC_HALF * 2}" height="{DEC_HALF * 2}" '
            f'fill="{DECISION_CLR}" stroke="white" stroke-width="4" rx="8"/>'
        )
        parts.append(
            f'<text x="{x}" y="{y - 8}" text-anchor="middle" font-size="30" font-weight="bold" fill="white">EMV</text>'
        )
        parts.append(
            f'<text x="{x}" y="{y + 30}" text-anchor="middle" '
            f'font-size="34" font-weight="bold" fill="white">${node["emv"]}K</text>'
        )
        for i, line in enumerate(node["label"].split("\n")):
            parts.append(
                f'<text x="{x}" y="{y + DEC_HALF + 42 + i * 44}" text-anchor="middle" '
                f'font-size="38" font-weight="bold" fill="{DECISION_CLR}">{line}</text>'
            )

    elif ntype == "chance":
        parts.append(f'<circle cx="{x}" cy="{y}" r="{CHC_R}" fill="{CHANCE_CLR}" stroke="white" stroke-width="4"/>')
        parts.append(
            f'<text x="{x}" y="{y - 8}" text-anchor="middle" font-size="28" font-weight="bold" fill="white">EMV</text>'
        )
        parts.append(
            f'<text x="{x}" y="{y + 28}" text-anchor="middle" '
            f'font-size="30" font-weight="bold" fill="white">${node["emv"]}K</text>'
        )
        for i, line in enumerate(node["label"].split("\n")):
            parts.append(
                f'<text x="{x}" y="{y + CHC_R + 40 + i * 40}" text-anchor="middle" '
                f'font-size="34" font-weight="bold" fill="{CHANCE_CLR}">{line}</text>'
            )

    elif ntype == "terminal":
        payoff = node["payoff"]
        fill = GAIN_CLR if payoff > 0 else (LOSS_CLR if payoff < 0 else ZERO_CLR)
        pts = f"{x - TRI},{y - TRI} {x - TRI},{y + TRI} {x + TRI},{y}"
        parts.append(f'<polygon points="{pts}" fill="{fill}" stroke="white" stroke-width="3"/>')
        val = f"${payoff}K" if payoff >= 0 else f"\u2212${abs(payoff)}K"
        parts.append(
            f'<text x="{x + TRI + 25}" y="{y + 10}" text-anchor="start" '
            f'font-size="40" font-weight="bold" fill="{fill}">{val}</text>'
        )

parts.append("</g>")

# Merge tree overlay into pygal's SVG
svg_output = base_svg.replace("</svg>", "\n".join(parts) + "\n</svg>")

# Save outputs
with open("plot.svg", "w") as f:
    f.write(svg_output)

cairosvg.svg2png(bytestring=svg_output.encode("utf-8"), write_to="plot.png")

with open("plot.html", "w") as f:
    f.write(
        "<!DOCTYPE html>\n<html>\n<head>\n"
        "    <title>tree-decision &middot; pygal &middot; pyplots.ai</title>\n"
        "    <style>\n"
        "        body { margin: 0; padding: 20px; background: #f5f5f5; font-family: sans-serif; }\n"
        "        .container { max-width: 100%; margin: 0 auto; text-align: center; }\n"
        "        object { width: 100%; max-width: 4800px; height: auto; }\n"
        "    </style>\n</head>\n<body>\n"
        '    <div class="container">\n'
        '        <object type="image/svg+xml" data="plot.svg">Decision tree not supported</object>\n'
        "    </div>\n</body>\n</html>"
    )
