""" anyplot.ai
dot-matrix-proportional: Dot Matrix Chart for Proportional Counts
Library: altair 6.1.0 | Python 3.13.13
Quality: 89/100 | Created: 2026-05-08
"""

import importlib
import os
import sys


# Remove the script's own directory from sys.path so "import altair" resolves
# the library, not this file (which shares the library's name).
_this_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if not (p and os.path.abspath(p) == _this_dir)]

alt = importlib.import_module("altair")
pd = importlib.import_module("pandas")

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

COLORS = ["#009E73", "#C475FD", "#4467A3"]

# Data: conference session survey — 100 attendees, 10×10 grid
# Categories ordered alphabetically to match Altair's nominal-sort color assignment.
categories = ["Agree", "Neutral", "Oppose"]
counts = [58, 27, 15]
total = 100
grid_cols = 10
grid_rows = 10

# Build dot grid: fill left-to-right, top-to-bottom
dots = []
for cat, cnt in zip(categories, counts, strict=True):
    dots.extend([cat] * cnt)

records = []
for idx, cat in enumerate(dots):
    records.append({"col": idx % grid_cols, "row": idx // grid_cols, "category": cat})

df = pd.DataFrame(records)

cat_counts = dict(zip(categories, counts, strict=True))

# Vega expression to append count to each legend label
label_expr = " : ".join(f"datum.label === '{c}' ? '{c} — {n}'" for c, n in cat_counts.items()) + " : datum.label"

chart = (
    alt.Chart(df)
    .mark_circle(size=5500, opacity=1.0)
    .encode(
        x=alt.X("col:O", axis=None),
        y=alt.Y("row:O", sort="ascending", axis=None),
        color=alt.Color(
            "category:N",
            scale=alt.Scale(domain=categories, range=COLORS),
            legend=alt.Legend(
                title="Response",
                titleFontSize=20,
                labelFontSize=18,
                symbolSize=200,
                symbolType="circle",
                labelExpr=label_expr,
                titleLimit=300,
                labelLimit=300,
            ),
        ),
        tooltip=[alt.Tooltip("category:N", title="Response")],
    )
    .properties(
        width=1200,
        height=1200,
        background=PAGE_BG,
        title=alt.TitleParams(
            text="dot-matrix-proportional · altair · anyplot.ai",
            subtitle="Conference session survey — Would you recommend this talk?",
            fontSize=28,
            subtitleFontSize=20,
            color=INK,
            subtitleColor=INK_SOFT,
            anchor="start",
            offset=20,
        ),
    )
    .configure_view(fill=PAGE_BG, stroke=None)
    .configure_legend(
        fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK, padding=12, cornerRadius=4
    )
    .configure_title(color=INK)
)

chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
