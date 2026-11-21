"""anyplot.ai
bar-3d-categorical: 3D Bar Chart for Categorical Comparison
Library: pygal 3.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-11-21
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

# Imprint palette: all eight positions, one per treatment in order
IMPRINT_PALETTE = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Columns: set these to your table's column names
VARIETY = "Crop variety"  # role: x_category
TREATMENT = "Treatment"  # role: y_category
YIELD = "Yield (kg / hectare)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("yields.csv")
varieties = ["Aster", "Borealis", "Crocus", "Delphi", "Ember"]
yields = {
    "Control": [2850, 3120, 2640, 3380, 2970],
    "Nitrogen+": [3540, 3820, 3290, 4050, 3650],
    "Phosphorus+": [3180, 3460, 2980, 3720, 3310],
    "NPK Blend": [3920, 4210, 3680, 4480, 4020],
}
df = pd.DataFrame(
    {
        VARIETY: varieties * len(yields),
        TREATMENT: [t for t in yields for _ in varieties],
        YIELD: [v for values in yields.values() for v in values],
    }
)

# Plot: reads only df and the constants above
table = df.pivot_table(index=VARIETY, columns=TREATMENT, values=YIELD, sort=False)

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT_PALETTE,
    title_font_size=56,
    label_font_size=48,
    major_label_font_size=40,
    legend_font_size=40,
    value_font_size=30,
    value_colors=(INK,),
    stroke_width=2.5,
)

chart = pygal.Bar(
    style=custom_style,
    width=3200,
    height=1800,
    title="Crop Yield by Variety & Treatment · bar-3d-categorical · python · pygal · anyplot.ai",
    x_title=VARIETY,
    y_title=YIELD,
    show_legend=True,
    legend_at_bottom=False,
    show_y_guides=True,
    show_x_guides=False,
    print_values=True,
    print_values_position="top",
    value_formatter=lambda v: f"{v:,.0f}",
    range=(0, float(table.max().max()) * 1.12),
    margin=60,
)

chart.x_labels = table.index.tolist()
for treatment in table.columns:
    chart.add(str(treatment), table[treatment].tolist())

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
