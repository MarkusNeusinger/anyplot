"""anyplot.ai
bar-stacked: Stacked Bar Chart
Library: pygal 3.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-09
"""

import os
import sys


script_dir = os.path.dirname(os.path.abspath(__file__))
for path in ("", ".", script_dir):
    if path in sys.path:
        sys.path.remove(path)

import pandas as pd  # noqa: E402
import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, one per component in order
IMPRINT_PALETTE = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Columns: set these to your table's column names
SPRINT = "Sprint"  # role: category
TASK_TYPE = "Task type"  # role: component
HOURS = "Team hours"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("hours.csv")
# Team hours per task type across six sprints, largest component first
_sprints = ["Sprint 1", "Sprint 2", "Sprint 3", "Sprint 4", "Sprint 5", "Sprint 6"]
_hours = {
    "Development": [212, 236, 198, 244, 228, 205],
    "Code review": [64, 71, 82, 69, 77, 88],
    "Testing": [48, 55, 91, 63, 84, 97],
    "Meetings": [42, 38, 45, 36, 40, 33],
}
df = pd.DataFrame(
    {
        SPRINT: [s for task in _hours for s in _sprints],
        TASK_TYPE: [task for task, values in _hours.items() for _ in values],
        HOURS: [v for values in _hours.values() for v in values],
    }
)

# Plot: reads only df and the constants above
table = df.pivot_table(index=SPRINT, columns=TASK_TYPE, values=HOURS, sort=False)
table = table.reindex(columns=df[TASK_TYPE].dropna().unique())

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT_PALETTE,
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    value_colors=("#FFFFFF",) * len(table.columns),
    stroke_width=2.5,
)

chart = pygal.StackedBar(
    width=3200,
    height=1800,
    style=custom_style,
    title="bar-stacked · python · pygal · anyplot.ai",
    x_title=SPRINT,
    y_title=HOURS,
    show_y_guides=True,
    show_x_guides=False,
    legend_at_bottom=True,
    legend_box_size=36,
    spacing=40,
    margin=50,
    print_values=True,
    print_values_position="center",
    value_formatter=lambda x: f"{x:.0f}",
    truncate_legend=-1,
)

chart.x_labels = table.index.tolist()
for task in table.columns:
    chart.add(str(task), table[task].tolist())

os.chdir(script_dir)
chart.render_to_png(f"plot-{THEME}.png")
chart.render_to_file(f"plot-{THEME}.html")
