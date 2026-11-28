"""anyplot.ai
heatmap-risk-matrix: Risk Assessment Matrix (Probability vs Impact)
Library: pygal 3.1.3 | Python 3.13.14
Quality: pending | Updated: 2026-06-20
"""

import importlib
import os
import sys

import numpy as np
import pandas as pd


# Remove this script's directory so 'pygal' resolves to the installed package, not this file
_script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _script_dir]
Graph = importlib.import_module("pygal.graph.graph").Graph
Style = importlib.import_module("pygal.style").Style

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, one per category in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
LIKELIHOOD_LEVELS = ["Rare", "Unlikely", "Possible", "Likely", "Almost Certain"]
IMPACT_LEVELS = ["Negligible", "Minor", "Moderate", "Major", "Catastrophic"]
# Risk zones by upper score bound; Low is a pale green so the brand-green markers stand out from it
ZONES = [(4, "Low", "#A9DCC3"), (9, "Medium", "#DDCC77"), (16, "High", "#CC7830"), (25, "Critical", "#AE3030")]

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
categories = list(dict.fromkeys(df[CATEGORY]))
cat_colors = {cat: IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] for i, cat in enumerate(categories)}
n_rows = len(LIKELIHOOD_LEVELS)
n_cols = len(IMPACT_LEVELS)
products = sorted({a * b for a in range(1, n_rows + 1) for b in range(1, n_cols + 1)})


def zone_of(score):
    """The (name, color) of the first zone whose upper bound holds the score."""
    return next((name, color) for bound, name, color in ZONES if score <= bound)


class RiskMatrixHeatmap(Graph):
    _series_margin = 0

    def _plot(self):
        margin_left, margin_right, margin_top, margin_bottom = 500, 450, 0, 330
        avail_w = self.view.width - margin_left - margin_right
        avail_h = self.view.height - margin_bottom - margin_top

        cell_size = min(avail_w / n_cols, avail_h / n_rows) * 0.97
        gap = cell_size * 0.04
        grid_w = n_cols * (cell_size + gap) - gap
        grid_h = n_rows * (cell_size + gap) - gap

        x0 = self.view.x(0) + margin_left + (avail_w - grid_w) / 2
        y0 = self.view.y(n_rows) + margin_top + (avail_h - grid_h) / 2

        group = self.svg.node(self.nodes["plot"], class_="risk-matrix")

        score_font = int(cell_size * 0.24)
        zone_font = int(cell_size * 0.15)
        marker_font = int(cell_size * 0.12)
        marker_r = int(cell_size * 0.09)
        label_font = int(cell_size * 0.14)
        title_font = int(cell_size * 0.22)
        legend_font = int(cell_size * 0.155)
        legend_box = int(cell_size * 0.14)

        # Cells: colored by zone of likelihood x impact, with score and zone name
        for i in range(n_rows):
            for j in range(n_cols):
                score = (n_rows - i) * (j + 1)
                zone, color = zone_of(score)
                r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
                tc = "#1A1A17" if (r * 299 + g * 587 + b * 114) / 1000 > 140 else "#F0EFE8"

                x = x0 + j * (cell_size + gap)
                y = y0 + i * (cell_size + gap)

                cell_group = self.svg.node(group, "g", class_="cell")
                rect = self.svg.node(cell_group, "rect", x=x, y=y, width=cell_size, height=cell_size, rx=8, ry=8)
                rect.set("fill", color)
                rect.set("stroke", PAGE_BG)
                rect.set("stroke-width", "4")

                title_el = self.svg.node(cell_group, "title")
                title_el.text = f"Risk Score: {score} ({zone})"

                txt = self.svg.node(cell_group, "text", x=x + cell_size / 2, y=y + cell_size * 0.34)
                txt.set("text-anchor", "middle")
                txt.set("fill", tc)
                txt.set("style", f"font-size:{score_font}px;font-weight:bold;font-family:sans-serif")
                txt.text = str(score)

                zt = self.svg.node(cell_group, "text", x=x + cell_size / 2, y=y + cell_size * 0.52)
                zt.set("text-anchor", "middle")
                zt.set("fill", tc)
                zt.set("opacity", "0.75")
                zt.set("style", f"font-size:{zone_font}px;font-weight:500;font-family:sans-serif")
                zt.text = zone

        # Risk markers: items sharing a cell are spread sideways with a small vertical jitter
        rng = np.random.default_rng(42)
        for (lik, imp), items in df.groupby([LIKELIHOOD, IMPACT], sort=False):
            lik, imp = int(lik), int(imp)
            if not (1 <= lik <= n_rows and 1 <= imp <= n_cols):
                continue
            cell_x = x0 + (imp - 1) * (cell_size + gap)
            cell_y = y0 + (n_rows - lik) * (cell_size + gap)
            n_items = len(items)

            for idx, (_, item) in enumerate(items.iterrows()):
                spread = cell_size * 0.48
                offset_x = 0 if n_items == 1 else -spread / 2 + idx * spread / (n_items - 1)
                jitter_y = rng.uniform(-cell_size * 0.04, cell_size * 0.04)

                pad = marker_r + 8
                cx = max(cell_x + pad, min(cell_x + cell_size / 2 + offset_x, cell_x + cell_size - pad))
                cy = max(cell_y + pad, min(cell_y + cell_size * 0.70 + jitter_y, cell_y + cell_size - pad))

                mg = self.svg.node(group, "g", class_="risk-marker")
                circle = self.svg.node(mg, "circle", cx=cx, cy=cy, r=marker_r)
                circle.set("fill", cat_colors[item[CATEGORY]])
                circle.set("stroke", INK)
                circle.set("stroke-width", "3")

                zone_color = zone_of(lik * imp)[1]
                zr, zg, zb = int(zone_color[1:3], 16), int(zone_color[3:5], 16), int(zone_color[5:7], 16)
                label_ink = "#1A1A17" if (zr * 299 + zg * 587 + zb * 114) / 1000 > 140 else "#F0EFE8"
                fit_font = min(marker_font, int(cell_size * 0.94 / (len(item[RISK]) * 0.64)))
                label_y = min(cy + marker_r + marker_font + 2, cell_y + cell_size - 5)
                lbl = self.svg.node(mg, "text", x=cx, y=label_y)
                lbl.set("text-anchor", "middle")
                lbl.set("fill", label_ink)
                lbl.set("stroke", zone_color)
                lbl.set("stroke-width", "5")
                lbl.set("paint-order", "stroke fill")
                lbl.set("style", f"font-size:{fit_font}px;font-weight:700;font-family:sans-serif")
                lbl.text = item[RISK]

                tip = self.svg.node(mg, "title")
                tip.text = f"{item[RISK]} — {item[CATEGORY]}, L:{lik} × I:{imp} = {lik * imp}"

        # Tick labels on both axes
        for i in range(n_rows):
            y = y0 + i * (cell_size + gap) + cell_size / 2
            ytick = self.svg.node(group, "text", x=x0 - 18, y=y + label_font * 0.15)
            ytick.set("text-anchor", "end")
            ytick.set("fill", INK_SOFT)
            ytick.set("style", f"font-size:{label_font}px;font-weight:600;font-family:sans-serif")
            ytick.text = f"{n_rows - i}. {LIKELIHOOD_LEVELS[n_rows - 1 - i]}"

        for j in range(n_cols):
            x = x0 + j * (cell_size + gap) + cell_size / 2
            y = y0 + grid_h + 30
            xtick = self.svg.node(group, "text", x=x, y=y)
            xtick.set("text-anchor", "end")
            xtick.set("fill", INK_SOFT)
            xtick.set("style", f"font-size:{label_font}px;font-weight:600;font-family:sans-serif")
            xtick.set("transform", f"rotate(-35, {x}, {y})")
            xtick.text = f"{j + 1}. {IMPACT_LEVELS[j]}"

        # Axis titles
        mid_y = y0 + grid_h / 2
        yt = self.svg.node(group, "text", x=x0 - 450, y=mid_y)
        yt.set("text-anchor", "middle")
        yt.set("fill", INK)
        yt.set("style", f"font-size:{title_font}px;font-weight:bold;font-family:sans-serif;letter-spacing:3px")
        yt.set("transform", f"rotate(-90, {x0 - 450}, {mid_y})")
        yt.text = LIKELIHOOD.upper()

        xt = self.svg.node(group, "text", x=x0 + grid_w / 2, y=y0 + grid_h + 290)
        xt.set("text-anchor", "middle")
        xt.set("fill", INK)
        xt.set("style", f"font-size:{title_font}px;font-weight:bold;font-family:sans-serif;letter-spacing:3px")
        xt.text = IMPACT.upper()

        # Legends on the right: risk zones, then categories
        lx = x0 + grid_w + 55
        ly = y0 + 10
        lt = self.svg.node(group, "text", x=lx, y=ly)
        lt.set("fill", INK)
        lt.set("style", f"font-size:{legend_font}px;font-weight:bold;font-family:sans-serif")
        lt.text = "Risk Zones"
        ly += legend_font + 14

        for _, name, color in ZONES:
            rect = self.svg.node(group, "rect", x=lx, y=ly, width=legend_box, height=legend_box, rx=4, ry=4)
            rect.set("fill", color)
            rect.set("stroke", INK_MUTED)
            rect.set("stroke-width", "2")

            in_zone = [v for v in products if zone_of(v)[0] == name]
            low, high = min(in_zone), max(in_zone)
            txt = self.svg.node(group, "text", x=lx + legend_box + 12, y=ly + legend_box * 0.76)
            txt.set("fill", INK_SOFT)
            txt.set("style", f"font-size:{legend_font}px;font-weight:500;font-family:sans-serif")
            txt.text = f"{name} ({low}–{high})"
            ly += legend_box + 20

        ly += 70
        ct = self.svg.node(group, "text", x=lx, y=ly)
        ct.set("fill", INK)
        ct.set("style", f"font-size:{legend_font}px;font-weight:bold;font-family:sans-serif")
        ct.text = CATEGORY
        ly += legend_font + 12

        for cat, color in cat_colors.items():
            circ = self.svg.node(group, "circle", cx=lx + legend_box / 2, cy=ly + legend_box / 2 - 2, r=marker_r)
            circ.set("fill", color)
            circ.set("stroke", INK)
            circ.set("stroke-width", "3")

            txt = self.svg.node(group, "text", x=lx + legend_box + 12, y=ly + legend_box * 0.73)
            txt.set("fill", INK_SOFT)
            txt.set("style", f"font-size:{legend_font}px;font-weight:500;font-family:sans-serif")
            txt.text = cat
            ly += legend_box + 18

    def _compute(self):
        self._box.xmin = 0
        self._box.xmax = n_cols
        self._box.ymin = 0
        self._box.ymax = n_rows


# Style: pygal Style carries all theme-adaptive chrome tokens
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    guide_stroke_color=INK_MUTED,
    major_guide_stroke_color=INK_MUTED,
    colors=tuple(IMPRINT_PALETTE),
    title_font_size=66,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=2.5,
    font_family="sans-serif",
)

# Square canvas for a symmetric heatmap
chart = RiskMatrixHeatmap(
    width=2400,
    height=2400,
    style=custom_style,
    title="heatmap-risk-matrix · python · pygal · anyplot.ai",
    show_legend=False,
    margin=40,
    margin_top=50,
    margin_bottom=60,
    margin_left=60,
    margin_right=60,
    show_x_labels=False,
    show_y_labels=False,
    tooltip_border_radius=6,
)
chart.add("", [0])

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
