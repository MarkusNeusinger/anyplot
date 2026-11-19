"""anyplot.ai
dot-matrix-proportional: Dot Matrix Chart for Proportional Counts
Library: altair 6.1.0 | Python 3.13.13
Quality: 89/100 | Updated: 2026-11-19
"""

import importlib
import math
import os
import sys


# Remove the script's own directory from sys.path so "import altair" resolves
# the library, not this file (which shares the library's name).
_this_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if not (p and os.path.abspath(p) == _this_dir)]

alt = importlib.import_module("altair")
pd = importlib.import_module("pandas")
Image = importlib.import_module("PIL.Image")

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

NEUTRAL = "#8C8B84"  # remainder dots that belong to no listed category

# Imprint palette: all eight positions, one per category in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set this to your table's column name
RESPONSE = "Response"  # role: category
COUNT = "Attendees"  # role: count
TOTAL = "Total attendees"  # role: total

# Data: replace this block with your own table, one row per category in fill order,
# for example df = pd.read_csv("survey.csv")
# Conference session survey: 100 attendees answering "Would you recommend this talk?"
df = pd.DataFrame({RESPONSE: ["Agree", "Neutral", "Oppose"], COUNT: [58, 27, 15]})
df[TOTAL] = df[COUNT].sum()

# Plot: reads only df and the constants above
counts = pd.to_numeric(df[COUNT], errors="coerce").fillna(0).astype(int)
listed = list(zip(df[RESPONSE].astype(str), counts, strict=True))
legend_label = {r: f"{r} — {n}" for r, n in listed}

# One row per unit, filled left to right, top to bottom
units = [r for r, n in listed for _ in range(n)]
# Units of the total that belong to no listed category stay in the grid as a neutral remainder
total = max(int(pd.to_numeric(df[TOTAL], errors="coerce").max()), len(units))
if total > len(units):
    legend_label["Other"] = f"Other — {total - len(units)}"
    units += ["Other"] * (total - len(units))
grid_cols = math.ceil(math.sqrt(total))
dots = pd.DataFrame(
    {"unit": units, "col": [i % grid_cols for i in range(total)], "row": [i // grid_cols for i in range(total)]}
)
dots["label"] = dots["unit"].map(legend_label)

title = "dot-matrix-proportional · python · altair · anyplot.ai"
ratio = 67 / len(title) if len(title) > 67 else 1.0

chart = (
    alt.Chart(dots)
    .mark_circle(size=1000, opacity=1.0)
    .encode(
        x=alt.X("col", type="ordinal", axis=None),
        y=alt.Y("row", type="ordinal", axis=None, sort="ascending"),
        color=alt.Color(
            "label",
            type="nominal",
            title=RESPONSE,
            sort=None,
            scale=alt.Scale(
                domain=list(legend_label.values()),
                range=[NEUTRAL if k == "Other" else IMPRINT_PALETTE[i] for i, k in enumerate(legend_label)],
            ),
            legend=alt.Legend(
                orient="bottom",
                direction="horizontal",
                titleFontSize=20,
                labelFontSize=18,
                symbolSize=500,
                symbolType="circle",
                columnPadding=30,
                columns=2,
                titleLimit=300,
                labelLimit=200,
            ),
        ),
        tooltip=[alt.Tooltip("label", type="nominal", title=RESPONSE)],
    )
    .properties(
        width=400,
        height=400,
        background=PAGE_BG,
        title=alt.TitleParams(
            text=title,
            subtitle="Would you recommend this talk? 1 dot = 1 attendee",
            fontSize=round(22 * ratio),
            subtitleFontSize=16,
            color=INK,
            subtitleColor=INK_SOFT,
            anchor="start",
            offset=16,
        ),
    )
    .configure_view(fill=PAGE_BG, stroke=None)
    .configure_legend(
        fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK, padding=12, cornerRadius=4
    )
    .configure_title(color=INK)
)

chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Pad (never crop) to the canonical square canvas
TARGET = 2400
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TARGET or img.height > TARGET:
    raise SystemExit(f"altair produced {img.width}x{img.height}, exceeds {TARGET}x{TARGET}; shrink width/height")
canvas = Image.new("RGB", (TARGET, TARGET), PAGE_BG)
canvas.paste(img, ((TARGET - img.width) // 2, (TARGET - img.height) // 2))
canvas.save(f"plot-{THEME}.png")
