"""anyplot.ai
bump-basic: Basic Bump Chart
Library: pygal 3.1.0 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-29
"""

import os

import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, one per entity in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants: teams with a livery cue keep a semantic Imprint color, the rest follow the palette
SEMANTIC = {"McLaren": "#009E73", "Ferrari": "#AE3030", "Red Bull Racing": "#4467A3"}

# Columns: set these to your table's column names
ENTITY = "Constructor"  # role: entity
PERIOD = "Grand Prix"  # role: period
RANK = "Constructor Standing"  # role: rank

# Data: replace this block with your own table, for example df = pd.read_csv("standings.csv")
# F1 constructor standings across six Grand Prix weekends (1 = leading)
_periods = ["Bahrain", "Jeddah", "Melbourne", "Imola", "Monaco", "Barcelona"]
_ranks = {
    "McLaren": [4, 3, 1, 1, 1, 1],
    "Ferrari": [2, 2, 3, 3, 2, 2],
    "Red Bull Racing": [1, 1, 2, 2, 3, 3],
    "Mercedes": [3, 4, 4, 4, 4, 4],
    "Aston Martin": [5, 5, 5, 5, 5, 5],
}
df = pd.DataFrame(
    {
        ENTITY: [e for e, r in _ranks.items() for _ in r],
        PERIOD: _periods * len(_ranks),
        RANK: [v for r in _ranks.values() for v in r],
    }
)

# Plot: reads only df and the constants above
table = df.pivot_table(index=PERIOD, columns=ENTITY, values=RANK, sort=False)
entities = df[ENTITY].drop_duplicates().tolist()
max_rank = int(df[RANK].max())
min_rank = int(df[RANK].min())

# pygal has no reversed axis: plot (max + min - rank) so rank 1 sits at the top, label the ticks with the real rank
flip = max_rank + min_rank

# Title font size shrinks only when the mandated title is longer than the canvas fits
title_str = "bump-basic · python · pygal · anyplot.ai"
title_font_size = max(44, round(66 * min(1.0, 67 / len(title_str))))

# Semantic colors first; the other entities take the unused palette entries in order
spare = iter(c for c in IMPRINT_PALETTE if c not in SEMANTIC.values())
team_colors = [SEMANTIC[e] if e in SEMANTIC else next(spare, IMPRINT_PALETTE[i % 8]) for i, e in enumerate(entities)]

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    guide_stroke_color=INK_MUTED,
    major_guide_stroke_color=INK_MUTED,
    colors=team_colors,
    title_font_size=title_font_size,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=14,
    opacity=1.0,
    opacity_hover=1.0,
)

chart = pygal.Line(
    width=3200,
    height=1800,
    style=custom_style,
    title=title_str,
    x_title=PERIOD,
    y_title=RANK,
    show_dots=True,
    dots_size=18,
    show_x_guides=False,
    show_y_guides=False,
    x_label_rotation=0,
    legend_at_bottom=True,
    legend_at_bottom_columns=len(entities),
    truncate_legend=-1,
    interpolate=None,
    range=(min_rank - 0.4, max_rank + 0.4),
    margin_right=160,
    value_formatter=lambda v: f"P{flip - round(v)}" if v == v else "",
    human_readable=True,
)

chart.x_labels = table.index.tolist()
chart.y_labels = [{"value": flip - r, "label": f"P{r}"} for r in range(min_rank, max_rank + 1)]

for entity in entities:
    chart.add(entity, (flip - table[entity]).tolist())

# Save
chart.render_to_png(f"plot-{THEME}.png")
chart.render_to_file(f"plot-{THEME}.html")
