""" pyplots.ai
tree-decision: Decision Tree Visualization with Probabilities
Library: pygal 3.1.0 | Python 3.14.3
Quality: 86/100 | Created: 2026-03-06
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
    "D1": {"type": "decision", "x": 600, "y": 1300, "emv": 260, "label": "Strategy\nChoice"},
    "C1": {"type": "chance", "x": 2250, "y": 520, "emv": 260, "label": "Market\nOutcome"},
    "C2": {"type": "chance", "x": 2250, "y": 1820, "emv": 190, "label": "License\nResult"},
    "T1": {"type": "terminal", "x": 3850, "y": 310, "payoff": 500},
    "T2": {"type": "terminal", "x": 3850, "y": 730, "payoff": -100},
    "T3": {"type": "terminal", "x": 3850, "y": 1580, "payoff": 250},
    "T4": {"type": "terminal", "x": 3850, "y": 2060, "payoff": 50},
    "T5": {"type": "terminal", "x": 2250, "y": 2450, "payoff": 0},
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
PRUNED_CLR = "#BBBBBB"
TXT = "#2C3E50"
TXT_DIM = "#7F8C8D"
FONT = "DejaVu Sans, sans-serif"
FONT_SZ = {"title": 72, "node_emv": 32, "node_label": 36, "branch": 36, "prob": 34, "payoff": 40}

DEC_HALF = 72
CHC_R = 58
TRI = 62

# pygal Style — typography, background, and series palette
style = Style(
    background="white",
    plot_background="white",
    foreground=TXT,
    foreground_strong=TXT,
    foreground_subtle=TXT_DIM,
    colors=(DECISION_CLR, CHANCE_CLR, GAIN_CLR, LOSS_CLR, ZERO_CLR),
    title_font_size=FONT_SZ["title"],
    legend_font_size=34,
    label_font_size=36,
    value_font_size=30,
    tooltip_font_size=28,
    font_family=FONT,
)


def fmt_currency(val):
    """pygal value_formatter for currency display."""
    return f"${val:,.0f}K" if val >= 0 else f"\u2212${abs(val):,.0f}K"


def elbow(x1, y1, x2, y2, ratio=0.55):
    """Elbow connector path."""
    mx = x1 + (x2 - x1) * ratio
    return f"M {x1},{y1} L {mx},{y1} L {mx},{y2} L {x2},{y2}", mx


def svg_text(x, y, text, size, fill=TXT, weight="normal", anchor="middle", style_attr=""):
    """SVG text element."""
    extra = f' font-style="{style_attr}"' if style_attr else ""
    return (
        f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-size="{size}" '
        f'fill="{fill}" font-weight="{weight}" font-family="{FONT}"{extra}>{text}</text>'
    )


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
    spacing=8,
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

# SVG defs: gradients for nodes + drop shadow filter
defs = (
    "<defs>"
    '<filter id="shadow" x="-15%" y="-15%" width="140%" height="140%">'
    '<feGaussianBlur in="SourceAlpha" stdDeviation="5" result="blur"/>'
    '<feOffset dx="3" dy="4" result="shifted"/>'
    '<feFlood flood-color="#000" flood-opacity="0.12" result="color"/>'
    '<feComposite in="color" in2="shifted" operator="in" result="shadow"/>'
    '<feMerge><feMergeNode in="shadow"/><feMergeNode in="SourceGraphic"/></feMerge>'
    "</filter>"
    f'<linearGradient id="grad_dec" x1="0%" y1="0%" x2="100%" y2="100%">'
    f'<stop offset="0%" stop-color="#4A90D9"/><stop offset="100%" stop-color="{DECISION_CLR}"/>'
    "</linearGradient>"
    f'<linearGradient id="grad_chance" x1="0%" y1="0%" x2="100%" y2="100%">'
    f'<stop offset="0%" stop-color="#F0A060"/><stop offset="100%" stop-color="{CHANCE_CLR}"/>'
    "</linearGradient>"
    "</defs>"
)

# Build tree overlay SVG
svg = [f'<g id="decision-tree" font-family="{FONT}">']

# Subtle highlight region behind optimal path (rounded)
svg.append(
    '<path d="M 530,1130 Q 530,350 700,350 L 3980,350 Q 4010,350 4010,380 '
    'L 4010,800 Q 4010,830 3980,830 L 1420,830 L 1420,1130 Z" '
    f'fill="{DECISION_CLR}" opacity="0.04" />'
)

# Branches (elbow connectors)
for src, dst, label, prob, pruned in branches:
    p, c = nodes[src], nodes[dst]
    path_d, mx = elbow(p["x"], p["y"], c["x"], c["y"])
    clr, w = (PRUNED_CLR, 3) if pruned else (OPTIMAL_CLR, 5)
    dash = ' stroke-dasharray="18,10"' if pruned else ""
    alpha = "0.5" if pruned else "1.0"
    svg.append(f'<path d="{path_d}" fill="none" stroke="{clr}" stroke-width="{w}" opacity="{alpha}"{dash}/>')
    vy = p["y"] + (c["y"] - p["y"]) * 0.45
    lc, fw = (TXT_DIM, "normal") if pruned else (TXT, "bold")
    svg.append(svg_text(mx - 24, vy, label, FONT_SZ["branch"], fill=lc, weight=fw, anchor="end"))
    if prob is not None:
        pc = TXT_DIM if pruned else CHANCE_CLR
        svg.append(svg_text(mx + 24, vy, f"p = {prob}", FONT_SZ["prob"], fill=pc, anchor="start", style_attr="italic"))
    if pruned:
        sy = p["y"] + (c["y"] - p["y"]) * 0.15
        svg.append(
            f'<line x1="{mx - 16}" y1="{sy - 14}" x2="{mx + 16}" y2="{sy + 14}" '
            f'stroke="{LOSS_CLR}" stroke-width="4" opacity="0.75"/>'
            f'<line x1="{mx - 16}" y1="{sy + 14}" x2="{mx + 16}" y2="{sy - 14}" '
            f'stroke="{LOSS_CLR}" stroke-width="4" opacity="0.75"/>'
        )

# Nodes
for _nid, nd in nodes.items():
    x, y, ntype = nd["x"], nd["y"], nd["type"]
    if ntype == "decision":
        svg.append(
            f'<rect x="{x - DEC_HALF}" y="{y - DEC_HALF}" width="{DEC_HALF * 2}" '
            f'height="{DEC_HALF * 2}" fill="url(#grad_dec)" stroke="white" '
            f'stroke-width="4" rx="12" filter="url(#shadow)"/>'
        )
        svg.append(svg_text(x, y - 8, "EMV", FONT_SZ["node_emv"], fill="white", weight="bold"))
        svg.append(svg_text(x, y + 32, f"${nd['emv']}K", FONT_SZ["node_label"], fill="white", weight="bold"))
        for i, line in enumerate(nd["label"].split("\n")):
            svg.append(
                svg_text(x, y + DEC_HALF + 44 + i * 44, line, FONT_SZ["node_label"], fill=DECISION_CLR, weight="bold")
            )
    elif ntype == "chance":
        svg.append(
            f'<circle cx="{x}" cy="{y}" r="{CHC_R}" fill="url(#grad_chance)" '
            f'stroke="white" stroke-width="4" filter="url(#shadow)"/>'
        )
        svg.append(svg_text(x, y - 8, "EMV", FONT_SZ["node_emv"] - 2, fill="white", weight="bold"))
        svg.append(svg_text(x, y + 28, f"${nd['emv']}K", FONT_SZ["node_emv"], fill="white", weight="bold"))
        for i, line in enumerate(nd["label"].split("\n")):
            svg.append(
                svg_text(x, y + CHC_R + 42 + i * 40, line, FONT_SZ["node_label"], fill=CHANCE_CLR, weight="bold")
            )
    elif ntype == "terminal":
        payoff = nd["payoff"]
        fill = GAIN_CLR if payoff > 0 else (LOSS_CLR if payoff < 0 else ZERO_CLR)
        pts = f"{x - TRI},{y - TRI} {x - TRI},{y + TRI} {x + TRI},{y}"
        svg.append(f'<polygon points="{pts}" fill="{fill}" stroke="white" stroke-width="3" filter="url(#shadow)"/>')
        svg.append(
            svg_text(
                x + TRI + 28, y + 12, fmt_currency(payoff), FONT_SZ["payoff"], fill=fill, weight="bold", anchor="start"
            )
        )

svg.append("</g>")

# Merge tree overlay + defs into pygal's SVG
tree_svg = "\n".join(svg)
svg_output = base_svg.replace("</svg>", f"{defs}\n{tree_svg}\n</svg>")

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
