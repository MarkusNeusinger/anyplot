""" anyplot.ai
parliament-basic: Parliament Seat Chart
Library: pygal 3.1.3 | Python 3.13.15
Quality: 79/100 | Updated: 2026-10-07
"""

import os

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order (first series ALWAYS #009E73)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
PARTY = "Party"  # role: party
SEATS = "Seats"  # role: seats
COLOR = "Color"  # role: color

# Data: replace this block with your own table, for example df = pd.read_csv("chamber.csv")
# An invented chamber: made-up party names (a neutral noun plus a group word) and made-up seat
# counts, in data order (not a left-right spectrum); no real country, parliament or election
df = pd.DataFrame(
    {
        PARTY: [
            "Harborview Assembly",
            "Rivermouth Coalition",
            "Timberwright Union",
            "Stonebridge Front",
            "Lowland Alliance",
            "Millbrook Guild",
            "Ashford Collective",
        ],
        SEATS: [158, 122, 95, 70, 54, 38, 12],
        COLOR: ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"],
    }
)

# Plot: concentric arcs whose seat capacity grows with their radius; all seats are sorted by angle
# from the left end (180°) to the right end (0°), and the parties claim them in data order
parties = df.dropna(subset=[PARTY, SEATS]).reset_index(drop=True)
seat_counts = parties[SEATS].astype(int).clip(lower=0).tolist()
# one dot per seat; a chamber far beyond the spec's 700 seats gets one dot per block of seats instead
seats_per_dot = max(1, -(-sum(seat_counts) // 1000))
dot_counts = [round(seats / seats_per_dot) for seats in seat_counts]
total = sum(dot_counts)
n_rows = max(1, round(np.sqrt(total / 3)))  # rows about as far apart as neighbouring seats in a row
radii = np.linspace(0.32, 1.0, n_rows) if n_rows > 1 else np.array([1.0])
raw = total * radii / radii.sum()
capacity = np.floor(raw).astype(int)
for row in np.argsort(capacity - raw)[: total - capacity.sum()]:  # largest remainders take the leftover seats
    capacity[row] += 1
slots = sorted(
    (((j + 0.5) / cap * np.pi, radius) for radius, cap in zip(radii, capacity, strict=True) for j in range(cap)),
    key=lambda slot: (-slot[0], slot[1]),
)
starts = np.cumsum([0, *dot_counts])
# the table's own hex colours; a party without one takes the next Imprint colour nobody uses yet,
# and only past the palette's eight colours does one repeat
given = [
    color if isinstance(color, str) and color.startswith("#") else None
    for color in (parties[COLOR] if COLOR in parties else [None] * len(parties))
]
spare = iter([color for color in IMPRINT_PALETTE if color not in given])
colors = [color or next(spare, IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)]) for i, color in enumerate(given)]

# Equal scale on both axes keeps the half circle round: the plot area is about 2.2 times as wide as tall
y_range = (-0.06, 1.06)
x_half = (y_range[1] - y_range[0]) * 2.2 / 2
seat_pitch = 0.68 / max(n_rows - 1, 1) if n_rows > 1 else np.pi / max(total, 1)
dot_radius = max(4, round(0.4 * seat_pitch * 1400 / (y_range[1] - y_range[0])))  # in px on a ~1400 px tall plot
# pygal reserves floor(n / columns) legend rows at the bottom; a last, partly filled row needs its own room
legend_columns = 3
legend_room = 1.5 * 46 * (-(-len(parties) // legend_columns) - len(parties) // legend_columns)

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_SOFT,
    colors=tuple(colors),
    title_font_size=66,
    label_font_size=46,
    major_label_font_size=46,
    legend_font_size=46,
    value_font_size=36,
    opacity=1,
    opacity_hover=1,
)

chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title="parliament-basic · python · pygal · anyplot.ai",
    x_title=f"Each dot stands for {seats_per_dot:,} seats" if seats_per_dot > 1 else None,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=legend_columns,
    legend_box_size=46,
    truncate_legend=-1,
    show_dots=True,
    stroke=False,
    show_x_guides=False,
    show_y_guides=False,
    show_x_labels=False,
    show_y_labels=False,
    xrange=(-x_half, x_half),
    range=y_range,
    spacing=24,
    margin=40,
    margin_bottom=40 + legend_room,
)

for i, party in enumerate(parties[PARTY]):
    party_slots = slots[starts[i] : starts[i + 1]]
    points = [(radius * np.cos(angle), radius * np.sin(angle)) for angle, radius in party_slots]
    chart.add(f"{party} ({seat_counts[i]})", points, dots_size=dot_radius)

# Save
chart.render_to_file(f"plot-{THEME}.html")
chart.render_to_png(f"plot-{THEME}.png")
