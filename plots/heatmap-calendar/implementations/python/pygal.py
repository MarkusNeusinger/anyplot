"""anyplot.ai
heatmap-calendar: Basic Calendar Heatmap
Library: pygal 3.1.0 | Python 3.14.4
Quality: 82/100 | Updated: 2026-04-27
"""

import os
import sys
from datetime import datetime, timedelta

import numpy as np


# Pop script directory so local files (pygal.py itself) don't shadow packages
_script_dir = sys.path.pop(0)

from pygal.graph.graph import Graph  # noqa: E402
from pygal.style import Style  # noqa: E402


sys.path.insert(0, _script_dir)

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
EMPTY_COLOR = "#D8D7CF" if THEME == "light" else "#2A2A27"

# Viridis sequential palette (perceptually uniform, colorblind-safe)
VIRIDIS = [EMPTY_COLOR, "#42337A", "#2A788E", "#38B277", "#BCDC3B"]
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Module-level data (avoids __init__ override, satisfying KISS)
_PLOT_DATA: dict = {}  # datetime → int


def _cell_color(value: int, lo: int, hi: int) -> str:
    if not value:
        return VIRIDIS[0]
    if hi == lo:
        return VIRIDIS[-1]
    return VIRIDIS[min(int((value - lo) / (hi - lo) * 4) + 1, 4)]


def _longest_streak(vals) -> int:
    best = cur = 0
    for v in vals:
        cur = cur + 1 if v > 0 else 0
        best = max(best, cur)
    return best


class CalendarHeatmap(Graph):
    """Calendar heatmap via pygal's SVG engine; data supplied via _PLOT_DATA."""

    def _compute(self):
        self._box.xmin = 0
        self._box.xmax = 53
        self._box.ymin = 0
        self._box.ymax = 7

    def _plot(self):
        if not _PLOT_DATA:
            return

        dates = sorted(_PLOT_DATA)
        values = [_PLOT_DATA[d] for d in dates]
        active = [v for v in values if v > 0]
        lo, hi = (min(active), max(active)) if active else (0, 1)

        W, H = self.width, self.height
        left, right = 240, 110
        avail = W - left - right
        first = dates[0] - timedelta(days=dates[0].weekday())
        n_weeks = ((dates[-1] - first).days + 7) // 7

        cell = avail / (n_weeks + (n_weeks - 1) * 0.08)
        gap = cell * 0.08
        gw = n_weeks * cell + (n_weeks - 1) * gap
        gh = 7 * cell + 6 * gap

        title_h, month_h, legend_h = 200, 110, 390
        vpad = max(80, (H - title_h - month_h - gh - legend_h) / 2)
        x0 = left + (avail - gw) / 2
        y0 = title_h + vpad + month_h

        root = self.nodes["graph"]
        g = self.svg.node(root, class_="calendar-heatmap")
        fs = max(56, int(cell * 0.72))

        # Weekday labels
        for i, label in enumerate(WEEKDAYS):
            t = self.svg.node(g, "text", x=x0 - 28, y=y0 + i * (cell + gap) + cell * 0.85)
            t.set("text-anchor", "end")
            t.set("fill", INK)
            t.set("style", f"font-size:{fs}px;font-weight:bold;font-family:sans-serif")
            t.text = label

        # Calendar cells + month label positions
        month_col: dict = {}
        cur, wk = first, 0
        while cur <= dates[-1]:
            wd = cur.weekday()
            if cur >= dates[0] and cur.day <= 7:
                month_col.setdefault((cur.year, cur.month), wk)
            if cur >= dates[0]:
                c = _cell_color(_PLOT_DATA.get(cur, 0), lo, hi)
                x = x0 + wk * (cell + gap)
                y = y0 + wd * (cell + gap)
                self.svg.node(
                    g,
                    "rect",
                    x=x,
                    y=y,
                    width=cell,
                    height=cell,
                    fill=c,
                    rx=cell * 0.12,
                    ry=cell * 0.12,
                    class_="calendar-cell reactive",
                )
            if wd == 6:
                wk += 1
            cur += timedelta(days=1)

        # Month labels (skip if too close to right edge)
        right_bound = x0 + gw - cell * 2.5
        for (_, m), col in month_col.items():
            mx = x0 + col * (cell + gap)
            if mx > right_bound:
                continue
            t = self.svg.node(g, "text", x=mx, y=y0 - 38)
            t.set("fill", INK)
            t.set("style", f"font-size:{fs}px;font-weight:bold;font-family:sans-serif")
            t.text = MONTHS[m - 1]

        # Color scale legend
        ly = y0 + gh + 165
        lcs = cell * 1.5
        lsp = cell * 0.40
        lx = x0 + gw / 2 - len(VIRIDIS) * (lcs + lsp) / 2
        fs_l = max(58, int(cell * 0.72))

        for txt, anch, tx in [
            ("Less", "end", lx - lsp * 1.5),
            ("More", "start", lx + len(VIRIDIS) * (lcs + lsp) + lsp * 1.5),
        ]:
            t = self.svg.node(g, "text", x=tx, y=ly + lcs * 0.72)
            t.set("text-anchor", anch)
            t.set("fill", INK)
            t.set("style", f"font-size:{fs_l}px;font-weight:bold;font-family:sans-serif")
            t.text = txt

        span = (hi - lo) / 4 if hi > lo else 1
        range_labels = ["0"] + [
            f"{int(lo + i * span)}+" if i == 3 else f"{int(lo + i * span)}-{int(lo + (i + 1) * span)}" for i in range(4)
        ]
        for i, (color, lbl) in enumerate(zip(VIRIDIS, range_labels, strict=True)):
            bx = lx + i * (lcs + lsp)
            self.svg.node(g, "rect", x=bx, y=ly, width=lcs, height=lcs, fill=color, rx=lcs * 0.12, ry=lcs * 0.12)
            t = self.svg.node(g, "text", x=bx + lcs / 2, y=ly + lcs + 52)
            t.set("text-anchor", "middle")
            t.set("fill", INK_MUTED)
            t.set("style", f"font-size:{int(fs_l * 0.78)}px;font-family:sans-serif")
            t.text = lbl

        # Summary statistics
        total = sum(v for v in values if v > 0)
        n_active = sum(1 for v in values if v > 0)
        streak = _longest_streak(values)
        avg = total / max(n_active, 1)
        fs_s = max(62, int(cell * 0.72))
        st_y = ly + lcs + 155
        cx = x0 + gw / 2

        t = self.svg.node(g, "text", x=cx, y=st_y)
        t.set("text-anchor", "middle")
        t.set("fill", INK)
        t.set("style", f"font-size:{fs_s}px;font-weight:bold;font-family:sans-serif")
        t.text = f"{total} contributions · {n_active} active days"

        t = self.svg.node(g, "text", x=cx, y=st_y + int(fs_s * 1.4))
        t.set("text-anchor", "middle")
        t.set("fill", INK_MUTED)
        t.set("style", f"font-size:{int(fs_s * 0.88)}px;font-family:sans-serif")
        t.text = f"Longest streak: {streak} days · Avg: {avg:.1f} per active day"


# Data — GitHub-style contribution pattern for 2024
np.random.seed(42)
start_date = datetime(2024, 1, 1)
end_date = datetime(2024, 12, 31)

cur = start_date
while cur <= end_date:
    wd = cur.weekday()
    base = 0 if wd >= 5 else np.random.choice([0, 0, 1, 2, 3], p=[0.3, 0.2, 0.25, 0.15, 0.1])
    if np.random.random() < 0.05:
        base = np.random.randint(5, 15)
    if np.random.random() < 0.25:
        base = 0
    _PLOT_DATA[cur] = int(base)
    cur += timedelta(days=1)

# Style
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=("#009E73",),
    title_font_size=72,
    legend_font_size=48,
    label_font_size=42,
    value_font_size=36,
    font_family="sans-serif",
)

# Plot
chart = CalendarHeatmap(
    width=4800,
    height=2700,
    style=custom_style,
    title="heatmap-calendar · pygal · anyplot.ai",
    show_legend=False,
    margin=20,
    margin_top=280,
    margin_bottom=100,
    show_x_labels=False,
    show_y_labels=False,
)

chart.add("", [0])

# Save
chart.render_to_file(f"plot-{THEME}.html")
chart.render_to_png(f"plot-{THEME}.png")
