""" anyplot.ai
pie-portfolio-interactive: Interactive Portfolio Allocation Chart
Library: pygal 3.1.0 | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-27
"""

import os
import re
import sys


# "pygal.py" shadows the installed pygal package — remove this file's directory
# from sys.path before importing so Python finds the installed package.
_here = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.realpath(p or ".") != os.path.realpath(_here)]
del _here

import cairosvg
import pygal
from pygal.style import Style


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

IMPRINT_PALETTE = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Data — balanced multi-asset portfolio with individual holdings
holdings = {
    "Equities": {"US Large Cap": 25.0, "US Mid Cap": 10.0, "International Developed": 12.0, "Emerging Markets": 8.0},
    "Fixed Income": {"US Treasury": 15.0, "Corporate Bonds": 8.0, "Municipal Bonds": 5.0},
    "Alternatives": {"Real Estate": 7.0, "Commodities": 5.0, "Private Equity": 5.0},
}

category_totals = {cat: sum(assets.values()) for cat, assets in holdings.items()}
n_holdings = sum(len(v) for v in holdings.values())
dominant_cat = max(category_totals, key=category_totals.get)
dominant_pct = category_totals[dominant_cat]

title = "pie-portfolio-interactive · python · pygal · anyplot.ai"
n = len(title)
ratio = 67 / n if n > 67 else 1.0
title_font_size = max(44, round(66 * ratio))

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT_PALETTE,
    title_font_size=title_font_size,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=38,
    tooltip_font_size=36,
)

# Wide donut (inner_radius=0.60) for modern look and center annotation space
chart = pygal.Pie(
    width=2400,
    height=2400,
    style=custom_style,
    inner_radius=0.60,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    legend_box_size=40,
    title=title,
    print_values=True,
    value_formatter=lambda x: f"{x:.1f}%",
    margin=80,
    margin_bottom=200,
    spacing=20,
)

# Legend labels include category totals for data storytelling
for category, assets in holdings.items():
    total = category_totals[category]
    chart.add(
        f"{category} · {total:.1f}%",
        [{"value": weight, "label": f"{name}: {weight:.1f}%"} for name, weight in assets.items()],
    )

svg_str = chart.render().decode("utf-8")

# Locate pie center: scan donut arc paths (M x y A ...) to find starting points,
# then average them — all arcs share the same geometric center.
arc_starts = re.findall(r'\bd="M\s+([\d.]+)[, ]+([\d.]+)\s+A\b', svg_str)
if arc_starts:
    pts = [(float(x), float(y)) for x, y in arc_starts[:20]]
    # The arithmetic mean of arc start points approximates the center
    avg_x = sum(p[0] for p in pts) / len(pts)
    avg_y = sum(p[1] for p in pts) / len(pts)
    # For a donut, arc starts lie on the inner circle; the center is their centroid
    cx, cy = avg_x, avg_y
else:
    # Fallback: estimated center for 2400×2400 with given margins + title
    cx = 1200.0
    cy = (80 + title_font_size * 2 + (2400 - 80 - 200 - 80)) / 2

# Inject center annotation highlighting the dominant asset class
center_svg = (
    f'<g class="center-annotation">'
    f'<text x="{cx:.0f}" y="{cy - 55:.0f}" text-anchor="middle" dominant-baseline="middle" '
    f'font-family="sans-serif" font-size="80" font-weight="bold" fill="{INK}">'
    f"{dominant_pct:.0f}%"
    f"</text>"
    f'<text x="{cx:.0f}" y="{cy + 25:.0f}" text-anchor="middle" dominant-baseline="middle" '
    f'font-family="sans-serif" font-size="52" fill="{INK_MUTED}">'
    f"{dominant_cat}"
    f"</text>"
    f'<text x="{cx:.0f}" y="{cy + 95:.0f}" text-anchor="middle" dominant-baseline="middle" '
    f'font-family="sans-serif" font-size="44" fill="{INK_MUTED}">'
    f"{n_holdings} holdings"
    f"</text>"
    f"</g>"
)
annotated_svg = (svg_str.replace("</svg>", f"{center_svg}\n</svg>")).encode("utf-8")

# PNG: render annotated SVG via cairosvg (same pipeline as render_to_png)
cairosvg.svg2png(bytestring=annotated_svg, write_to=f"plot-{THEME}.png")

# HTML: embed annotated SVG (center annotation visible in both static and interactive views)
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(annotated_svg)
