"""anyplot.ai
choropleth-basic: Choropleth Map with Regional Coloring
Library: pygal 3.1.3 | Python 3.13
Quality: pending | Updated: 2026-11-21
"""

import os
import re

import cairosvg
from pygal.style import Style
from pygal_maps_world.maps import World


THEME = os.getenv("ANYPLOT_THEME", "light")

# Theme tokens
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
NO_DATA = "#B9B8B0" if THEME == "light" else "#55544E"

# Imprint palette: all eight positions, in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]


def lerp_hex(c0, c1, t):
    """Linear blend between two hex colors."""
    a = [int(c0[i : i + 2], 16) for i in (1, 3, 5)]
    b = [int(c1[i : i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(a, b, strict=True))


# Constants
BIN_EDGES = [0, 20, 40, 60, 80]  # lower bounds of the class bins (share of electricity, %)

# Columns
REGION = "Country code"  # role: region_id
VALUE = "Renewable share of electricity (%)"  # role: value

# Data: replace this block with your own table, for example
# df = pd.read_csv("renewables.csv") with ISO 3166-1 alpha-2 codes in lowercase
shares = {
    "no": 98,
    "is": 100,
    "br": 89,
    "ca": 68,
    "se": 68,
    "at": 78,
    "nz": 84,
    "pt": 61,
    "dk": 80,
    "es": 50,
    "de": 52,
    "fr": 26,
    "gb": 45,
    "it": 41,
    "fi": 50,
    "ie": 40,
    "gr": 44,
    "pl": 22,
    "us": 23,
    "cn": 32,
    "in": 21,
    "jp": 22,
    "au": 36,
    "cl": 54,
    "co": 71,
    "ar": 34,
    "mx": 25,
    "pe": 58,
    "ve": 62,
    "ke": 90,
    "et": 98,
    "za": 11,
    "eg": 12,
    "ma": 21,
    "ng": 20,
    "id": 20,
    "vn": 38,
    "th": 17,
    "kr": 9,
    "ru": 19,
    "tr": 44,
    "ua": 12,
    "py": 100,
    "cd": 99,
    "sa": 1,
    "ir": 6,
    "dz": 1,
    "ly": 1,
}
df = {REGION: list(shares), VALUE: list(shares.values())}

# Plot: reads only df and the constants above
n_bins = len(BIN_EDGES)
bin_colors = [lerp_hex("#009E73", "#4467A3", i / (n_bins - 1)) for i in range(n_bins)]
upper = [*BIN_EDGES[1:], max(df[VALUE]) + 1]

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=tuple(bin_colors),
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=48,
    value_font_size=36,
    tooltip_font_size=36,
    opacity=1,
    opacity_hover=0.85,
    no_data_font_size=36,
    # thin, quiet outlines in the page color so neighbours of similar shade stay apart
    custom_css=f"""
    g.country path {{ stroke: {PAGE_BG}; stroke-width: 1.2; stroke-opacity: 1; }}
    g.country:not(.series) path {{ fill: {NO_DATA}; }}
    g.country.series {{ fill-opacity: 1 !important; }}
    g.country.series path {{ fill-opacity: 1 !important; }}
    """,
)

worldmap = World(
    style=custom_style,
    width=3200,
    height=1800,
    title="choropleth-basic · python · pygal · anyplot.ai",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=n_bins,
    legend_box_size=44,
    print_values=False,
    show_x_labels=False,
)

for lo, hi in zip(BIN_EDGES, upper, strict=True):
    members = {code: v for code, v in zip(df[REGION], df[VALUE], strict=True) if lo <= v < hi}
    last = hi == upper[-1]
    label = f"≥ {lo} %" if last else f"{lo}–{hi} %"
    worldmap.add(label, members)

# Save: pygal shades each country by an inline fill-opacity and leaves no-data countries unfilled;
# a flat fill per class keeps the swatches exact and no-data distinct from every bin
svg = worldmap.render(is_unicode=True)
svg = re.sub(r' style="fill-opacity: [0-9.]+"', "", svg)
svg = re.sub(r'class="(\w+ country map-element)"', rf'class="\1" style="fill: {NO_DATA}"', svg)
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(svg)
cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=f"plot-{THEME}.png")
