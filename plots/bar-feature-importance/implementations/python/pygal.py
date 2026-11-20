"""anyplot.ai
bar-feature-importance: Feature Importance Bar Chart
Library: pygal 3.1.0 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-10
"""

import os
import sys


# Avoid shadowing the pygal package by temporarily removing this directory from path during import
_original_path = sys.path.copy()
sys.path = [
    p
    for p in sys.path
    if not p.endswith(("implementations/python", "plots/bar-feature-importance/implementations/python"))
]

try:
    import pandas as pd
    import pygal
    from pygal.style import Style
finally:
    sys.path = _original_path

# Theme tokens from prompts/default-style-guide.md
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants: Imprint sequential ramp, weakest bar to strongest bar
SEQ_LOW = "#4467A3"
SEQ_HIGH = "#009E73"

# Columns: set these to your table's column names
FEATURE = "Feature"  # role: feature
IMPORTANCE = "Importance Score"  # role: importance

# Data: replace this block with your own table, for example df = pd.read_csv("importances.csv")
# Feature importances from a customer churn prediction model
df = pd.DataFrame(
    {
        FEATURE: [
            "ContractLength",
            "MonthlyCharges",
            "TotalCharges",
            "InternetServiceType",
            "TenureMonths",
            "OnlineSecurity",
            "TechSupport",
            "AutomaticPayment",
            "DeviceProtection",
            "StreamingService",
            "PhoneService",
        ],
        IMPORTANCE: [0.287, 0.231, 0.154, 0.112, 0.087, 0.062, 0.038, 0.019, 0.008, 0.003, 0.001],
    }
)


# Plot: reads only df and the constants above
def lerp_hex(c0, c1, t):
    """Linear RGB interpolation between two hex colors."""
    a = [int(c0[i : i + 2], 16) for i in (1, 3, 5)]
    b = [int(c1[i : i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(a, b, strict=True))


# pygal draws the first label at the bottom, so ascending order puts the highest bar on top
table = df.sort_values(IMPORTANCE, ascending=True, kind="stable")
low, high = table[IMPORTANCE].min(), table[IMPORTANCE].max()
span = (high - low) or 1.0
bar_data = [
    {
        "value": None if pd.isna(v) else float(v),
        "color": lerp_hex(SEQ_LOW, SEQ_HIGH, 0.0 if pd.isna(v) else (v - low) / span),
    }
    for v in table[IMPORTANCE]
]

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=tuple(IMPRINT_PALETTE),
    value_colors=(INK,),
    value_label_colors=(INK,),
    font_family="sans-serif",
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=40,
    stroke_width=2.5,
)

chart = pygal.HorizontalBar(
    width=3200,
    height=1800,
    style=custom_style,
    title="bar-feature-importance · python · pygal · anyplot.ai",
    x_title=IMPORTANCE,
    show_legend=False,
    show_y_guides=False,
    show_x_guides=True,
    print_values=True,
    print_values_position="top",
    value_formatter=lambda x: f"{x:.3f}",
    range=(0, high * 1.15),
    margin=50,
    spacing=10,
    truncate_label=-1,
)
chart.x_labels = table[FEATURE].tolist()
chart.add(IMPORTANCE, bar_data)

# Save outputs for both themes
chart.render_to_file(f"plot-{THEME}.html")
chart.render_to_png(f"plot-{THEME}.png")
