"""anyplot.ai
heatmap-risk-matrix: Risk Assessment Matrix (Probability vs Impact)
Library: pygal 3.1.3 | Python 3.14.10
Quality: pending | Updated: 2026-11-28
"""

import importlib
import os
import re
import sys

import numpy as np
import pandas as pd


# Remove this script's directory so 'pygal' resolves to the installed package, not this file
_script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _script_dir]
pygal = importlib.import_module("pygal")
Style = importlib.import_module("pygal.style").Style

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
LIGHT_INK = "#F0EFE8"
DARK_INK = "#1A1A17"

# Imprint palette: all eight positions, one per category in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
LIKELIHOOD_LEVELS = ["Rare", "Unlikely", "Possible", "Likely", "Almost Certain"]
IMPACT_LEVELS = ["Negligible", "Minor", "Moderate", "Major", "Catastrophic"]
# Risk zones by upper score bound, with the ink that reads on each fill. Low is a pale green
# (Imprint fields ramp) so the brand-green markers stand out from it; High is Imprint ochre.
ZONES = [
    (4, "Low", "#66E2B2", DARK_INK),
    (9, "Medium", "#DDCC77", DARK_INK),
    (16, "High", "#BD8233", DARK_INK),
    (25, "Critical", "#AE3030", LIGHT_INK),
]
GAP = 0.05  # share of a cell left as page-colored gutter

# Columns: set these to your table's column names
RISK = "Risk"  # role: risk_name
LIKELIHOOD = "Likelihood"  # role: likelihood
IMPACT = "Impact"  # role: impact
CATEGORY = "Category"  # role: category

# Data: replace this block with your own table, for example df = pd.read_csv("risks.csv")
df = pd.DataFrame(
    {
        RISK: [
            "Server Outage",
            "Data Breach",
            "Bgt. Overrun",
            "Currency Risk",
            "Vendor Delay",
            "Staff Turnover",
            "Scope Creep",
            "Reg. Change",
            "Supply Chain",
            "Market Shift",
            "Tech Debt",
            "Cyber Attack",
            "Key Person",
            "Pandemic",
        ],
        LIKELIHOOD: [3, 2, 4, 3, 4, 4, 5, 2, 3, 2, 4, 1, 4, 1],
        IMPACT: [4, 5, 3, 2, 2, 1, 2, 4, 5, 3, 4, 4, 5, 5],
        CATEGORY: [
            "Technical",
            "Technical",
            "Financial",
            "Financial",
            "Operational",
            "Operational",
            "Operational",
            "External",
            "External",
            "Financial",
            "Technical",
            "Technical",
            "Operational",
            "External",
        ],
    }
)

# Plot: reads only df and the constants above
df = df.dropna(subset=[RISK, LIKELIHOOD, IMPACT, CATEGORY])
n_rows = len(LIKELIHOOD_LEVELS)
n_cols = len(IMPACT_LEVELS)
df = df[df[LIKELIHOOD].between(1, n_rows) & df[IMPACT].between(1, n_cols)]
categories = list(dict.fromkeys(df[CATEGORY]))
rng = np.random.default_rng(42)

# Zone of every cell (score = likelihood x impact); cell (i, j) is centered at (j + 0.5, i + 0.5)
cells = []
for lik in range(1, n_rows + 1):
    for imp in range(1, n_cols + 1):
        zone = next(z for z in ZONES if lik * imp <= z[0])
        cells.append((lik, imp, zone))

# Risk markers: items sharing a cell are spread sideways, every item gets a small jitter
markers = []
for (lik, imp), items in df.groupby([LIKELIHOOD, IMPACT], sort=False):
    n_items = len(items)
    for idx, (_, item) in enumerate(items.iterrows()):
        spread = 0.5 * (idx / (n_items - 1) - 0.5) if n_items > 1 else 0.0
        x = imp - 0.5 + spread + rng.uniform(-0.04, 0.04)
        y = lik - 0.5 + rng.uniform(-0.03, 0.03)
        markers.append((item, lik, imp, x, y))

# The chart is built twice: the first pass measures the plot area, the second sizes the thick
# line segments that act as cell fills to one cell, so the grid always fills the plot exactly.
LABEL_PX = 36  # value-label size; pygal prints each label this many pixels right of its point
cell_h = cell_w = 300.0
for _ in range(2):
    style = Style(
        background=PAGE_BG,
        plot_background=PAGE_BG,
        foreground=INK,
        foreground_strong=INK,
        foreground_subtle=INK_MUTED,
        guide_stroke_color=INK_MUTED,
        major_guide_stroke_color=INK_MUTED,
        colors=tuple(
            [c[2][2] for c in cells]
            + [IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] for i in range(len(categories))]
            + [INK, INK]
        ),
        value_colors=tuple([INK] * (len(cells) + len(categories)) + [DARK_INK, LIGHT_INK]),
        value_label_font_size=LABEL_PX,
        title_font_size=66,
        label_font_size=44,
        major_label_font_size=44,
        legend_font_size=44,
        value_font_size=LABEL_PX,
        stroke_width=cell_h * (1 - GAP),
        opacity=1.0,
        opacity_hover=1.0,
        font_family="sans-serif",
    )
    chart = pygal.XY(
        width=2400,
        height=2400,
        style=style,
        title="heatmap-risk-matrix · python · pygal · anyplot.ai",
        x_title=IMPACT.upper(),
        y_title=LIKELIHOOD.upper(),
        range=(0, n_rows),
        xrange=(0, n_cols),
        x_labels=[{"label": f"{j + 1}. {name}", "value": j + 0.5} for j, name in enumerate(IMPACT_LEVELS)],
        y_labels=[{"label": f"{i + 1}. {name}", "value": i + 0.5} for i, name in enumerate(LIKELIHOOD_LEVELS)],
        x_label_rotation=-30,
        show_x_guides=False,
        show_y_guides=False,
        legend_at_bottom=True,
        legend_at_bottom_columns=4,
        legend_box_size=36,
        truncate_legend=-1,
        print_labels=True,
        css=[
            "file://style.css",
            "file://graph.css",
            "inline:.legend rect {stroke-width: 2px !important} .text-overlay text {text-anchor: middle} "
            ".series .line {stroke-opacity: 1 !important}",
        ],
        stroke_style={"linecap": "butt"},
        margin=40,
        tooltip_border_radius=6,
    )

    # Cell fills: one series per zone, each cell a thick horizontal segment, None breaks the line
    gx = GAP * cell_h / cell_w
    text_dx = LABEL_PX / cell_w
    legend_done = set()
    for lik, imp, zone in cells:
        name = zone[1]
        scores = [a * b for a, b, z in cells if z[1] == name]
        title = None if name in legend_done else f"{name} ({min(scores)}–{max(scores)})"
        legend_done.add(name)
        chart.add(title, [(imp - 1 + gx, lik - 0.5), (imp - gx, lik - 0.5)], show_dots=False)

    # Risk markers: one dot series per category, the label comes from the text series below
    for cat in categories:
        chart.add(
            cat, [(x, y) for item, lik, imp, x, y in markers if item[CATEGORY] == cat], stroke=False, dots_size=20
        )

    # Text on the cells (score above the marker) and on the markers (name below it), one series per ink
    for ink in (DARK_INK, LIGHT_INK):
        texts = [
            {"value": (imp - 0.5 - text_dx, lik - 0.2), "label": str(lik * imp)}
            for lik, imp, zone in cells
            if zone[3] == ink
        ]
        texts += [
            {"value": (x - text_dx, y - 0.2), "label": str(item[RISK])}
            for item, lik, imp, x, y in markers
            if next(z for z in ZONES if lik * imp <= z[0])[3] == ink
        ]
        chart.add(None, texts, stroke=False, dots_size=0)

    plot_box = re.search(r'class="plot">\s*<rect[^>]*width="([\d.]+)" height="([\d.]+)"', chart.render(is_unicode=True))
    cell_w = float(plot_box.group(1)) / n_cols
    cell_h = float(plot_box.group(2)) / n_rows

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
