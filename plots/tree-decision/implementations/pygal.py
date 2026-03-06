""" pyplots.ai
tree-decision: Decision Tree Visualization with Probabilities
Library: pygal 3.1.0 | Python 3.14.3
Quality: 85/100 | Created: 2026-03-06
"""

import cairosvg
import pygal
from pygal.style import Style


# Decision tree data: New Product Launch
# EMV rollback:
#   C1 (Launch):  0.6 * $500K + 0.4 * (-$100K) = $260K  [OPTIMAL]
#   C2 (License): 0.7 * $250K + 0.3 * $50K     = $190K  [PRUNED]
#   T5 (Nothing): $0K                                     [PRUNED]
#   D1 (Root):    max($260K, $190K, $0K)         = $260K

nodes = {
    "D1": {"type": "decision", "x": 550, "y": 1200, "emv": 260, "label": "Strategy\nChoice"},
    "C1": {"type": "chance", "x": 2200, "y": 480, "emv": 260, "label": "Market\nOutcome"},
    "C2": {"type": "chance", "x": 2200, "y": 1700, "emv": 190, "label": "License\nResult"},
    "T1": {"type": "terminal", "x": 3800, "y": 270, "payoff": 500},
    "T2": {"type": "terminal", "x": 3800, "y": 690, "payoff": -100},
    "T3": {"type": "terminal", "x": 3800, "y": 1460, "payoff": 250},
    "T4": {"type": "terminal", "x": 3800, "y": 1940, "payoff": 50},
    "T5": {"type": "terminal", "x": 2200, "y": 2300, "payoff": 0},
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

# Colorblind-safe palette (Okabe-Ito inspired)
DECISION_CLR = "#306998"
CHANCE_CLR = "#E8833A"
GAIN_CLR = "#0072B2"
LOSS_CLR = "#D55E00"
ZERO_CLR = "#7F8C8D"
OPTIMAL_CLR = "#306998"
PRUNED_CLR = "#AAAAAA"
TXT = "#333333"
TXT_DIM = "#666666"

DEC_HALF = 70
CHC_R = 55
TRI = 60

# pygal Style — typography, background, and series palette
style = Style(
    background="white",
    plot_background="white",
    foreground=TXT,
    foreground_strong=TXT,
    foreground_subtle=TXT_DIM,
    colors=(DECISION_CLR, CHANCE_CLR, GAIN_CLR, LOSS_CLR, ZERO_CLR),
    title_font_size=72,
    legend_font_size=34,
    label_font_size=36,
    value_font_size=30,
    tooltip_font_size=28,
    font_family="DejaVu Sans, sans-serif",
)


def fmt_currency(val):
    """pygal value_formatter for currency display."""
    return f"${val:,.0f}K" if val >= 0 else f"\u2212${abs(val):,.0f}K"


# Build pygal XY chart with tooltips and native legend
chart = pygal.XY(
    width=4800,
    height=2700,
    style=style,
    title="tree-decision \u00b7 pygal \u00b7 pyplots.ai",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=5,
    legend_box_size=26,
    show_x_guides=False,
    show_y_guides=False,
    show_x_labels=False,
    show_y_labels=False,
    dots_size=0,
    stroke=False,
    range=(0, 2700),
    xrange=(0, 4800),
    margin=10,
    margin_bottom=5,
    spacing=10,
    tooltip_border_radius=8,
    tooltip_fancy_mode=True,
    value_formatter=fmt_currency,
    css=["file://style.css", "inline:", ".tooltip .value { font-size: 28px; }", ".legend { font-size: 34px; }"],
)

# Data series with pygal tooltips — each point gets an interactive tooltip
chart.add(
    "Decision Node",
    [
        {
            "value": (n["x"], n["y"]),
            "label": n["label"].replace("\n", " "),
            "xlink": {"title": f"EMV: ${n['emv']}K | Best: Launch Product"},
        }
        for n in nodes.values()
        if n["type"] == "decision"
    ],
)
chart.add(
    "Chance Node",
    [
        {"value": (n["x"], n["y"]), "label": n["label"].replace("\n", " "), "xlink": {"title": f"EMV: ${n['emv']}K"}}
        for n in nodes.values()
        if n["type"] == "chance"
    ],
)
chart.add(
    "Terminal (Gain)",
    [
        {"value": (n["x"], n["y"]), "label": fmt_currency(n["payoff"])}
        for n in nodes.values()
        if n["type"] == "terminal" and n["payoff"] > 0
    ],
)
chart.add(
    "Terminal (Loss)",
    [
        {"value": (n["x"], n["y"]), "label": fmt_currency(n["payoff"])}
        for n in nodes.values()
        if n["type"] == "terminal" and n["payoff"] < 0
    ],
)
chart.add(
    "Terminal (Neutral)",
    [
        {"value": (n["x"], n["y"]), "label": fmt_currency(n["payoff"])}
        for n in nodes.values()
        if n["type"] == "terminal" and n["payoff"] == 0
    ],
)

# Render pygal SVG (title, legend, tooltips, background, plot structure)
base_svg = chart.render().decode("utf-8")

# Build tree overlay SVG
svg = ['<g id="decision-tree" font-family="DejaVu Sans, sans-serif">']

# Subtle highlight region behind optimal path
svg.append(
    '<path d="M 490,1050 L 1350,1050 L 1350,190 L 3960,190 L 3960,800 '
    'L 1350,800 L 1350,1050 Z" fill="#306998" opacity="0.04" />'
)

# Branches (elbow connectors)
for src, dst, label, prob, pruned in branches:
    p, c = nodes[src], nodes[dst]
    mx = p["x"] + (c["x"] - p["x"]) * 0.55
    clr, w = (PRUNED_CLR, 3) if pruned else (OPTIMAL_CLR, 5)
    dash = ' stroke-dasharray="20,12"' if pruned else ""
    alpha = "0.45" if pruned else "1.0"
    svg.append(
        f'<path d="M {p["x"]},{p["y"]} L {mx},{p["y"]} L {mx},{c["y"]} '
        f'L {c["x"]},{c["y"]}" fill="none" stroke="{clr}" '
        f'stroke-width="{w}" opacity="{alpha}"{dash}/>'
    )
    vy = p["y"] + (c["y"] - p["y"]) * 0.45
    lc, fw = (TXT_DIM, "normal") if pruned else (TXT, "bold")
    svg.append(
        f'<text x="{mx - 22}" y="{vy}" text-anchor="end" font-size="36" fill="{lc}" font-weight="{fw}">{label}</text>'
    )
    if prob is not None:
        pc = TXT_DIM if pruned else CHANCE_CLR
        svg.append(
            f'<text x="{mx + 22}" y="{vy}" text-anchor="start" '
            f'font-size="34" fill="{pc}" font-style="italic">p = {prob}</text>'
        )
    if pruned:
        sy = p["y"] + (c["y"] - p["y"]) * 0.2
        svg.append(
            f'<line x1="{mx - 16}" y1="{sy - 14}" x2="{mx + 16}" y2="{sy + 14}" '
            f'stroke="{LOSS_CLR}" stroke-width="4" opacity="0.8"/>'
            f'<line x1="{mx - 16}" y1="{sy + 14}" x2="{mx + 16}" y2="{sy - 14}" '
            f'stroke="{LOSS_CLR}" stroke-width="4" opacity="0.8"/>'
        )

# Nodes
for _nid, nd in nodes.items():
    x, y, ntype = nd["x"], nd["y"], nd["type"]
    if ntype == "decision":
        svg.append(
            f'<rect x="{x - DEC_HALF}" y="{y - DEC_HALF}" width="{DEC_HALF * 2}" '
            f'height="{DEC_HALF * 2}" fill="{DECISION_CLR}" stroke="white" '
            f'stroke-width="4" rx="10" filter="url(#shadow)"/>'
        )
        svg.append(
            f'<text x="{x}" y="{y - 8}" text-anchor="middle" font-size="30" '
            f'font-weight="bold" fill="white">EMV</text>'
            f'<text x="{x}" y="{y + 30}" text-anchor="middle" font-size="34" '
            f'font-weight="bold" fill="white">${nd["emv"]}K</text>'
        )
        for i, line in enumerate(nd["label"].split("\n")):
            svg.append(
                f'<text x="{x}" y="{y + DEC_HALF + 42 + i * 44}" text-anchor="middle" '
                f'font-size="38" font-weight="bold" fill="{DECISION_CLR}">{line}</text>'
            )
    elif ntype == "chance":
        svg.append(
            f'<circle cx="{x}" cy="{y}" r="{CHC_R}" fill="{CHANCE_CLR}" '
            f'stroke="white" stroke-width="4" filter="url(#shadow)"/>'
        )
        svg.append(
            f'<text x="{x}" y="{y - 8}" text-anchor="middle" font-size="28" '
            f'font-weight="bold" fill="white">EMV</text>'
            f'<text x="{x}" y="{y + 28}" text-anchor="middle" font-size="30" '
            f'font-weight="bold" fill="white">${nd["emv"]}K</text>'
        )
        for i, line in enumerate(nd["label"].split("\n")):
            svg.append(
                f'<text x="{x}" y="{y + CHC_R + 40 + i * 40}" text-anchor="middle" '
                f'font-size="34" font-weight="bold" fill="{CHANCE_CLR}">{line}</text>'
            )
    elif ntype == "terminal":
        payoff = nd["payoff"]
        fill = GAIN_CLR if payoff > 0 else (LOSS_CLR if payoff < 0 else ZERO_CLR)
        pts = f"{x - TRI},{y - TRI} {x - TRI},{y + TRI} {x + TRI},{y}"
        svg.append(f'<polygon points="{pts}" fill="{fill}" stroke="white" stroke-width="3" filter="url(#shadow)"/>')
        val = fmt_currency(payoff)
        svg.append(
            f'<text x="{x + TRI + 25}" y="{y + 10}" text-anchor="start" '
            f'font-size="40" font-weight="bold" fill="{fill}">{val}</text>'
        )

svg.append("</g>")

# SVG filter for subtle drop shadow on nodes
shadow_filter = (
    '<defs><filter id="shadow" x="-10%" y="-10%" width="130%" height="130%">'
    '<feDropShadow dx="3" dy="3" stdDeviation="4" flood-opacity="0.15"/>'
    "</filter></defs>"
)

# Merge tree overlay + shadow filter into pygal's SVG
tree_svg = "\n".join(svg)
svg_output = base_svg.replace("</svg>", f"{shadow_filter}\n{tree_svg}\n</svg>")

# Save outputs using pygal's rendering pipeline
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
