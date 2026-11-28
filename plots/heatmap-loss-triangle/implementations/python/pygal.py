"""anyplot.ai
heatmap-loss-triangle: Actuarial Loss Development Triangle
Library: pygal 3.1.0 | Python 3.13.13
Quality: 86/100 | Updated: 2026-06-03
"""

import os

import numpy as np
import pandas as pd
from pygal.graph.graph import Graph
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
# Imprint sequential ramp for fields (cells that fill the plot), low -> high, per theme
SEQ_FIELDS = (
    [(0.0, "#66E2B2"), (0.369, "#009E73"), (0.803, "#024582"), (1.0, "#351E45")]
    if THEME == "light"
    else [(0.0, "#404C02"), (0.487, "#009E73"), (1.0, "#CDD9FF")]
)
DARK_TEXT, LIGHT_TEXT = "#1A1A17", "#F0EFE8"  # the two text inks printed on colored cells


def ramp_color(stops, t):
    """The hex at t (0 to 1) along (position, hex) stops, blended linearly in sRGB."""
    t = min(max(t, 0.0), 1.0)
    (p0, c0), (p1, c1) = next((a, b) for a, b in zip(stops, stops[1:], strict=False) if t <= b[0])
    share = (t - p0) / (p1 - p0)
    return "#" + "".join(
        f"{round(int(c0[i : i + 2], 16) * (1 - share) + int(c1[i : i + 2], 16) * share):02X}" for i in (1, 3, 5)
    )


def luminance(hex_color):
    """WCAG relative luminance of a hex color."""
    lin = [
        (v / 255) / 12.92 if v / 255 <= 0.04045 else (((v / 255) + 0.055) / 1.055) ** 2.4
        for v in (int(hex_color[i : i + 2], 16) for i in (1, 3, 5))
    ]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def text_on(hex_color):
    """Whichever of the two inks has the higher contrast on the given cell color."""
    lum = luminance(hex_color)
    contrast_dark = (lum + 0.05) / (luminance(DARK_TEXT) + 0.05)
    contrast_light = (luminance(LIGHT_TEXT) + 0.05) / (lum + 0.05)
    return DARK_TEXT if contrast_dark >= contrast_light else LIGHT_TEXT


# Columns: set these to your table's column names
ACCIDENT_YEAR = "Accident Year"  # role: accident_year
DEV_PERIOD = "Development Period (Years)"  # role: development_period
CUMULATIVE = "Cumulative ($k)"  # role: cumulative_amount
IS_PROJECTED = "Projected"  # role: is_projected

# Data: replace this block with your own table, for example df = pd.read_csv("triangle.csv")
np.random.seed(42)
years = np.arange(2015, 2025)
periods = np.arange(1, 11)
base_ultimate = np.array([4200, 4500, 4800, 5100, 5400, 5700, 6000, 6300, 6600, 7000], dtype=float)
dev_pattern = np.array([0.15, 0.35, 0.52, 0.66, 0.78, 0.87, 0.93, 0.97, 0.99, 1.00])
rows = []
for i, year in enumerate(years):
    for j, period in enumerate(periods):
        expected = base_ultimate[i] * dev_pattern[j]
        amount = round(expected + np.random.normal(0, expected * 0.03), 0)
        rows.append((year, period, amount, bool(year + period > years.max() + 1)))
df = pd.DataFrame(rows, columns=[ACCIDENT_YEAR, DEV_PERIOD, CUMULATIVE, IS_PROJECTED])

# Plot: reads only df and the constants above
amounts = df.pivot_table(index=ACCIDENT_YEAR, columns=DEV_PERIOD, values=CUMULATIVE, sort=False)
projected = df.pivot_table(index=ACCIDENT_YEAR, columns=DEV_PERIOD, values=IS_PROJECTED, sort=False, aggfunc="max")
n_rows, n_cols = amounts.shape

# Age-to-age development factors: volume-weighted over the observed cells only
observed = amounts.where(projected.eq(False))
dev_factors = [
    observed.iloc[:, j + 1].sum() / observed.iloc[:, j][observed.iloc[:, j + 1].notna()].sum()
    if observed.iloc[:, j + 1].notna().any()
    else np.nan
    for j in range(n_cols - 1)
]

# Evaluation date: the boundary after each row's last observed cell
last_observed = observed.notna().sum(axis=1).to_numpy()
boundary_cols = [c for c in last_observed for _ in (0, 1)]  # each row contributes its top and bottom corner

lo, hi = np.nanmin(amounts.to_numpy()), np.nanmax(amounts.to_numpy())


class LossTriangleHeatmap(Graph):
    _series_margin = 0

    def __init__(self, *args, **kwargs):
        self.table = kwargs.pop("table")
        super().__init__(*args, **kwargs)

    def _compute(self):
        self._box.xmin, self._box.xmax = 0, n_cols
        self._box.ymin, self._box.ymax = 0, n_rows

    def _put(self, text, x, y, size, fill, weight="400", anchor="middle"):
        node = self.svg.node(self.nodes["plot"], "text", x=x, y=y)
        node.set("text-anchor", anchor)
        node.set("fill", fill)
        node.set("style", f"font-size:{size}px;font-weight:{weight};font-family:sans-serif")
        node.text = text

    def _plot(self):
        # Margins within the view area for the row titles and the colorbar
        left, right, top, bottom = 200, 195, 90, 10
        aw = self.view.width - left - right
        ah = self.view.height - top - bottom
        cw = aw / n_cols
        ch = ah / (n_rows + 1.25)  # one extra band for the development factors
        gap = 3
        gw = n_cols * (cw + gap) - gap
        gh = n_rows * (ch + gap) - gap
        xo = self.view.x(0) + left + (aw - gw) / 2
        yo = self.view.y(n_rows) + top + (ah - gh - ch * 1.1) / 2
        pn = self.nodes["plot"]

        # Hatch patterns for projected cells (one per text ink) and the colorbar gradient
        defs = self.svg.node(pn, "defs")
        for pid, ink in (("hatch-dark", DARK_TEXT), ("hatch-light", LIGHT_TEXT)):
            pat = self.svg.node(
                defs,
                "pattern",
                id=pid,
                patternUnits="userSpaceOnUse",
                width="12",
                height="12",
                patternTransform="rotate(45)",
            )
            hl = self.svg.node(pat, "line", x1="0", y1="0", x2="0", y2="12")
            hl.set("stroke", ink)
            hl.set("stroke-width", "2.5")
            hl.set("opacity", "0.35")

        hf = max(26, min(34, int(cw * 0.15)))  # axis titles
        cf = max(22, min(30, int(cw * 0.42)))  # column and row labels
        vf = max(20, min(32, int(min(cw, ch) * 0.48)))  # cell values
        ff = max(18, min(24, int(cw * 0.32)))  # development factors

        put = self._put

        # Axis titles, column headers and row labels
        put(DEV_PERIOD, xo + gw / 2, yo - 62, hf, INK_SOFT, "600")
        for j, period in enumerate(self.table.columns):
            put(str(period), xo + j * (cw + gap) + cw / 2, yo - 16, cf, INK, "700")
        for i, year in enumerate(self.table.index):
            put(str(year), xo - 16, yo + i * (ch + gap) + ch / 2 + cf * 0.35, cf, INK, "600", "end")
        ty = yo + gh / 2
        title_node = self.svg.node(pn, "text", x=xo - 148, y=ty)
        title_node.set("text-anchor", "middle")
        title_node.set("fill", INK_SOFT)
        title_node.set("style", f"font-size:{hf}px;font-weight:600;font-family:sans-serif")
        title_node.set("transform", f"rotate(-90,{xo - 148},{ty})")
        title_node.text = ACCIDENT_YEAR

        # Cells: opaque Imprint ramp color; projected cells add hatching, a dashed border, italic text
        for i in range(n_rows):
            for j in range(n_cols):
                val = self.table.iat[i, j]
                if np.isnan(val):
                    continue
                is_proj = bool(pd.notna(projected.iat[i, j]) and projected.iat[i, j])
                fill = ramp_color(SEQ_FIELDS, (val - lo) / (hi - lo) if hi > lo else 0.5)
                ink = text_on(fill)
                cx, cy = xo + j * (cw + gap), yo + i * (ch + gap)
                cell = self.svg.node(pn, "g", class_="cell")
                rect = self.svg.node(cell, "rect", x=cx, y=cy, width=cw, height=ch, rx=3, ry=3)
                rect.set("fill", fill)
                if is_proj:
                    hatch = self.svg.node(cell, "rect", x=cx, y=cy, width=cw, height=ch, rx=3, ry=3)
                    hatch.set("fill", "url(#hatch-dark)" if ink == DARK_TEXT else "url(#hatch-light)")
                    border = self.svg.node(cell, "rect", x=cx + 3, y=cy + 3, width=cw - 6, height=ch - 6, rx=2, ry=2)
                    border.set("fill", "none")
                    border.set("stroke", ink)
                    border.set("stroke-width", "2")
                    border.set("stroke-dasharray", "6,4")
                    border.set("opacity", "0.6")
                label = (
                    f"{self.table.index[i]} / period {self.table.columns[j]} ({'projected' if is_proj else 'actual'})"
                )
                self._tooltip_data(cell, self.value_formatter(val), cx + cw / 2, cy + ch / 2, xlabel=label)
                text_node = self.svg.node(cell, "text", x=cx + cw / 2, y=cy + ch / 2 + vf * 0.35)
                text_node.set("text-anchor", "middle")
                text_node.set("fill", ink)
                text_node.set(
                    "style",
                    f"font-size:{vf}px;font-weight:{'400' if is_proj else '600'};"
                    f"font-style:{'italic' if is_proj else 'normal'};font-family:sans-serif",
                )
                text_node.text = self.value_formatter(val)

        # Evaluation date diagonal: the boundary between observed and projected cells
        points = [
            (xo + c * (cw + gap) - gap / 2, yo + (k // 2 + k % 2) * (ch + gap) - gap / 2)
            for k, c in enumerate(boundary_cols)
        ]
        if len(points) > 1:
            diag = self.svg.line(pn, points, close=False, class_="eval-date-line")
            diag.set("fill", "none")
            diag.set("stroke", INK)
            diag.set("stroke-width", "5")
            diag.set("stroke-dasharray", "14,7")

        # Development factors: one band below the triangle, each between the two periods it links
        fy = yo + gh + 34
        rule = self.svg.node(pn, "line", x1=xo, y1=yo + gh + 12, x2=xo + gw, y2=yo + gh + 12)
        rule.set("stroke", INK_MUTED)
        rule.set("stroke-width", "1.5")
        put("Dev Factor", xo - 16, fy + ff * 0.35, ff, INK_SOFT, "700", "end")
        for j, factor in enumerate(dev_factors):
            if not np.isnan(factor):
                put(f"{factor:.3f}", xo + (j + 1) * (cw + gap) - gap / 2, fy + ff * 0.35, ff, INK_SOFT, "500")

        # Colorbar: SVG gradient along the same ramp, high values on top
        cbw, cbh = 32, gh * 0.6
        cbx, cby = xo + gw + 44, yo + (gh - cbh) / 2
        grad = self.svg.node(defs, "linearGradient", id="cb-grad", x1="0", y1="0", x2="0", y2="1")
        for step in range(21):
            stop = self.svg.node(grad, "stop", offset=f"{step * 5}%")
            stop.set("stop-color", ramp_color(SEQ_FIELDS, 1 - step / 20))
        bar = self.svg.node(pn, "rect", x=cbx, y=cby, width=cbw, height=cbh, rx=4, ry=4)
        bar.set("fill", "url(#cb-grad)")
        bar.set("stroke", INK_MUTED)
        bar.set("stroke-width", "1.5")
        for share in (0.0, 0.25, 0.5, 0.75, 1.0):
            tick_y = cby + cbh * share
            tick = self.svg.node(pn, "line", x1=cbx + cbw, y1=tick_y, x2=cbx + cbw + 6, y2=tick_y)
            tick.set("stroke", INK_MUTED)
            tick.set("stroke-width", "1.5")
            put(self.value_formatter(hi - (hi - lo) * share), cbx + cbw + 10, tick_y + 8, 22, INK_SOFT, anchor="start")
        put(CUMULATIVE, cbx + cbw / 2, cby - 40, 24, INK_SOFT, "600")

        # Legend: three items centered under the triangle, widths from the text lengths
        lf = 24
        items = [("Actual (Observed)", "actual"), ("Projected (IBNR)", "projected"), ("Evaluation Date", "line")]
        widths = [46 + len(text) * lf * 0.6 for text, _ in items]
        lx = xo + (gw - sum(widths) - 60 * (len(items) - 1)) / 2
        ly = fy + ff + 22
        mid = ramp_color(SEQ_FIELDS, 0.5)
        for k, (text, kind) in enumerate(items):
            if kind != "line":
                swatch = self.svg.node(pn, "rect", x=lx, y=ly, width=30, height=22, fill=mid, rx=3, ry=3)
                swatch.set("stroke", INK_MUTED)
            if kind == "projected":
                hatch = self.svg.node(pn, "rect", x=lx, y=ly, width=30, height=22, rx=3, ry=3)
                hatch.set("fill", f"url(#hatch-{'dark' if text_on(mid) == DARK_TEXT else 'light'})")
                border = self.svg.node(pn, "rect", x=lx + 3, y=ly + 3, width=24, height=16, rx=2, ry=2)
                border.set("fill", "none")
                border.set("stroke", text_on(mid))
                border.set("stroke-width", "1.5")
                border.set("stroke-dasharray", "4,3")
                border.set("opacity", "0.6")
            if kind == "line":
                key = self.svg.node(pn, "line", x1=lx, y1=ly + 11, x2=lx + 34, y2=ly + 11)
                key.set("stroke", INK)
                key.set("stroke-width", "4")
                key.set("stroke-dasharray", "9,4")
            put(text, lx + 42, ly + 18, lf, INK, "600", "start")
            lx += widths[k] + 60


chart_title = "heatmap-loss-triangle · python · pygal · anyplot.ai"
title_fs = round(66 * 67 / len(chart_title)) if len(chart_title) > 67 else 66

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    guide_stroke_color=INK_MUTED,
    major_guide_stroke_color=INK_MUTED,
    colors=IMPRINT_PALETTE,
    title_font_size=title_fs,
    legend_font_size=44,
    label_font_size=44,
    major_label_font_size=44,
    value_font_size=36,
    tooltip_font_size=28,
    font_family="sans-serif",
)

chart = LossTriangleHeatmap(
    width=2400,
    height=2400,
    style=custom_style,
    title=chart_title,
    table=amounts,
    value_formatter=lambda x: f"{x:,.0f}",
    show_legend=False,
    margin=80,
    margin_top=160,
    margin_bottom=80,
    margin_left=80,
    margin_right=80,
    show_x_labels=False,
    show_y_labels=False,
)
chart.add("", [0])

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
