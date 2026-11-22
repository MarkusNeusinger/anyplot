""" anyplot.ai
mosaic-categorical: Mosaic Plot for Categorical Association Analysis
Library: pygal 3.1.3 | Python 3.14.10
Quality: 87/100 | Updated: 2026-11-22
"""

import os

import pandas as pd
from pygal.graph.graph import Graph
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: one position per row category, in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
DEVICE = "Device type"  # role: category_2
APP_CATEGORY = "App category"  # role: category_1
SESSIONS = "Sessions"  # role: frequency

# Data: replace this block with your own table, for example df = pd.read_csv("usage.csv")
df = pd.DataFrame(
    {
        APP_CATEGORY: ["Social Media", "Gaming", "Productivity", "Entertainment"] * 3,
        DEVICE: ["Mobile"] * 4 + ["Tablet"] * 4 + ["Desktop"] * 4,
        SESSIONS: [450, 320, 180, 290, 120, 200, 230, 290, 80, 150, 480, 130],
    }
)

# Plot: reads only df and the constants above
table = df.pivot_table(index=APP_CATEGORY, columns=DEVICE, values=SESSIONS, aggfunc="sum", sort=False)
row_labels = [str(r) for r in table.index]
col_labels = [str(c) for c in table.columns]
counts = table.fillna(0).to_numpy()  # an empty combination is an empty tile
col_totals = counts.sum(axis=0)
shares = counts / col_totals  # conditional proportions within each column

# Key insight: the row category whose conditional share differs most between two columns
insight = ""
best_ratio = 1.0
for i, row in enumerate(row_labels):
    lo, hi = shares[i].argmin(), shares[i].argmax()
    if shares[i, lo] > 0 and shares[i, hi] / shares[i, lo] > best_ratio:
        best_ratio = shares[i, hi] / shares[i, lo]
        insight = (
            f"Key insight: {col_labels[hi]} skews towards {row} ({shares[i, hi] * 100:.0f}%)"
            f" — {best_ratio:.1f}× the {col_labels[lo]} rate ({shares[i, lo] * 100:.0f}%)"
        )


class MosaicPlot(Graph):
    """pygal has no mosaic type: draw the tiles straight into the SVG plot node."""

    def __init__(self, *args, **kwargs):
        self.counts = kwargs.pop("counts")
        self.row_labels = kwargs.pop("row_labels")
        self.col_labels = kwargs.pop("col_labels")
        self.x_name = kwargs.pop("x_name")
        self.y_name = kwargs.pop("y_name")
        self.insight = kwargs.pop("insight")
        super().__init__(*args, **kwargs)

    def _text(self, parent, x, y, text, size, fill, weight=400, italic=False, anchor="middle"):
        node = self.svg.node(parent, "text", x=x, y=y)
        node.set("text-anchor", anchor)
        node.set("dominant-baseline", "middle")
        node.set("fill", fill)
        node.set(
            "style",
            f"font-size:{size}px;font-weight:{weight};font-family:sans-serif"
            + (";font-style:italic" if italic else ""),
        )
        node.text = text
        return node

    def _plot(self):
        n_rows, n_cols = len(self.row_labels), len(self.col_labels)
        col_tot = self.counts.sum(axis=0)
        grand = col_tot.sum()

        margin_left, margin_bottom = 500, 330
        avail_w = self.view.width - margin_left - 20
        avail_h = self.view.height - 20 - margin_bottom
        gap = 0.012
        col_gap, row_gap = avail_w * gap, avail_h * gap
        draw_w = avail_w - col_gap * (n_cols - 1)
        draw_h = avail_h - row_gap * (n_rows - 1)
        x0 = self.view.x(0) + margin_left
        y0 = self.view.y(n_rows) + 20

        group = self.svg.node(self.nodes["plot"], class_="mosaic-plot")
        x = x0
        for j, col in enumerate(self.col_labels):
            col_w = draw_w * col_tot[j] / grand
            y = y0
            for i, row in enumerate(self.row_labels):
                freq = self.counts[i, j]
                share = freq / col_tot[j]
                h = draw_h * share
                color = IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)]
                rect = self.svg.node(group, "rect", x=x, y=y, width=col_w, height=h, rx=6, ry=6)
                rect.set("fill", color)
                rect.set("stroke", PAGE_BG)
                rect.set("stroke-width", "4")
                tip = self.svg.node(rect, "title")
                tip.text = f"{row} · {col}: {freq:,.0f} ({share * 100:.1f}% of {col})"

                # Dark text on the light tiles, white on the dark ones
                r, g, b = (int(color[k : k + 2], 16) for k in (1, 3, 5))
                text_fill = "#1A1A17" if (0.299 * r + 0.587 * g + 0.114 * b) > 150 else "#FFFFFF"
                cx = x + col_w / 2
                if h > 90 and col_w > 120:
                    size = min(58, int(min(col_w, h) * 0.26))
                    if h > 150 and col_w > 180:
                        self._text(group, cx, y + h / 2 - size * 0.3, f"{freq:,.0f}", size, text_fill, 700)
                        pct_size = max(int(size * 0.65), 28)
                        self._text(group, cx, y + h / 2 + size * 0.55, f"{share * 100:.0f}%", pct_size, text_fill, 500)
                    else:
                        self._text(group, cx, y + h / 2, f"{freq:,.0f}", size, text_fill, 700)
                y += h + row_gap

            # Column label and its share of all sessions
            self._text(group, x + col_w / 2, y0 + avail_h + 50, col, 52, INK, 700)
            share_text = f"{col_tot[j] / grand * 100:.1f}% of sessions"
            self._text(group, x + col_w / 2, y0 + avail_h + 105, share_text, 36, INK_MUTED, 400, True)
            x += col_w + col_gap

        # Row legend, aligned with the tiles of the first column
        y = y0
        for i, row in enumerate(self.row_labels):
            h = draw_h * self.counts[i, 0] / col_tot[0]
            cy = y + h / 2
            swatch = self.svg.node(group, "rect", x=x0 - 400, y=cy - 22, width=44, height=44, rx=6, ry=6)
            swatch.set("fill", IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)])
            swatch.set("stroke", INK_SOFT)
            swatch.set("stroke-width", "1.5")
            self._text(group, x0 - 340, cy, row, 44, INK, 500, anchor="start")
            y += h + row_gap

        # Axis titles
        self._text(group, x0 + avail_w / 2, y0 + avail_h + 175, self.x_name.upper(), 48, INK_SOFT, 700)
        ty = y0 + avail_h / 2
        title = self._text(group, x0 - 470, ty, self.y_name.upper(), 48, INK_SOFT, 700)
        title.set("transform", f"rotate(-90, {x0 - 470}, {ty})")
        if self.insight:
            self._text(group, x0 + avail_w / 2, y0 + avail_h + 250, self.insight, 38, INK_MUTED, 400, True)

    def _compute(self):
        self._box.xmin, self._box.xmax = 0, len(self.col_labels)
        self._box.ymin, self._box.ymax = 0, len(self.row_labels)


style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=tuple(IMPRINT_PALETTE),
    title_font_size=66,
    label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    font_family="sans-serif",
)

chart = MosaicPlot(
    width=3200,
    height=1800,
    style=style,
    title="App Usage by Device · mosaic-categorical · python · pygal · anyplot.ai",
    counts=counts,
    row_labels=row_labels,
    col_labels=col_labels,
    x_name=DEVICE,
    y_name=APP_CATEGORY,
    insight=insight,
    show_legend=False,
    show_x_labels=False,
    show_y_labels=False,
    margin=60,
    margin_top=120,
    margin_bottom=40,
)
chart.add("", [0])  # pygal only runs its pipeline when a series exists

chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
