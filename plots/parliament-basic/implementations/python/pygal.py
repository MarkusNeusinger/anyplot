"""anyplot.ai
parliament-basic: Parliament Seat Chart
Library: pygal 3.1.3 | Python 3.13.12
Quality: pending | Created: 2026-10-07
"""

import math
import os

# Import pygal using absolute path to avoid shadowing by this file's own name
import sys


_saved_path = sys.path[:]
sys.path = [p for p in sys.path if p not in ("", ".") and "parliament-basic" not in p]
try:
    import pygal
    from pygal.style import Style
finally:
    sys.path = _saved_path

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette, canonical order (first series ALWAYS #009E73)
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]

# Invented chamber: made-up party names (a neutral noun + a group word), made-up
# seat counts, colors assigned in Imprint canonical order (data order, not a
# left-right political spectrum). No real country, parliament, election, or
# politician is represented.
parties_data = [
    {"name": "Harborview Assembly", "seats": 158, "color": IMPRINT[0]},
    {"name": "Rivermouth Coalition", "seats": 122, "color": IMPRINT[1]},
    {"name": "Timberwright Union", "seats": 95, "color": IMPRINT[2]},
    {"name": "Stonebridge Front", "seats": 70, "color": IMPRINT[3]},
    {"name": "Lowland Alliance", "seats": 54, "color": IMPRINT[4]},
    {"name": "Millbrook Guild", "seats": 38, "color": IMPRINT[5]},
    {"name": "Ashford Collective", "seats": 12, "color": IMPRINT[6]},
]

NUM_ROWS = 10
RADIUS_START = 27
RADIUS_STEP = 7


def parliament_layout(parties, num_rows=NUM_ROWS):
    """Generate semicircular parliament seat positions in concentric arcs.

    Each row's seat capacity is proportional to its radius (longer arcs hold
    more seats), and every seat slot across all rows is sorted by angle
    before parties claim their share in order — so each party forms one
    contiguous wedge running from the inner arc to the outer arc, rather
    than being confined to a single row.
    """
    total_seats = sum(p["seats"] for p in parties)
    radii = [RADIUS_START + row * RADIUS_STEP for row in range(num_rows)]
    total_radius = sum(radii)

    raw_capacities = [total_seats * radius / total_radius for radius in radii]
    capacities = [int(c) for c in raw_capacities]
    remainder = total_seats - sum(capacities)
    by_fraction = sorted(range(num_rows), key=lambda i: raw_capacities[i] - capacities[i], reverse=True)
    for row in by_fraction[:remainder]:
        capacities[row] += 1

    slots = []
    for radius, capacity in zip(radii, capacities, strict=True):
        for j in range(capacity):
            angle = (j + 0.5) / capacity * math.pi
            slots.append((angle, radius))
    slots.sort(key=lambda slot: slot[0])

    seats_list = []
    slot_idx = 0
    for party_idx, party in enumerate(parties):
        for _ in range(party["seats"]):
            angle, radius = slots[slot_idx]
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            seats_list.append({"x": x, "y": y, "party_idx": party_idx})
            slot_idx += 1

    return seats_list


seats = parliament_layout(parties_data)
max_radius = RADIUS_START + (NUM_ROWS - 1) * RADIUS_STEP

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=tuple(IMPRINT),
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=2.5,
)

chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title="parliament-basic · python · pygal · anyplot.ai",
    show_legend=True,
    legend_at_bottom=True,
    show_dots=True,
    dots_size=5,
    stroke=False,
    show_x_guides=False,
    show_y_guides=False,
    show_x_labels=False,
    show_y_labels=False,
    xrange=(-max_radius * 1.1, max_radius * 1.1),
    range=(-max_radius * 0.08, max_radius * 1.1),
)

# Add data by party (each party is a separate series with individual points,
# so the legend lists every party name with its seat count)
for party_idx, party in enumerate(parties_data):
    party_seats = [s for s in seats if s["party_idx"] == party_idx]
    data = [(s["x"], s["y"]) for s in party_seats]
    chart.add(f"{party['name']} ({party['seats']})", data)

# Save outputs
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
