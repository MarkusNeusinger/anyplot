""" anyplot.ai
bump-basic: Basic Bump Chart
Library: altair 6.3.0 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-27
"""

import os
import sys


# Prevent self-import: this file is named altair.py; remove the script directory
# from sys.path so `import altair` finds the installed package, not this file.
_this_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if not p or os.path.abspath(p) != _this_dir]

import altair as alt
import pandas as pd
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette, canonical order — first series is always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
TEAM = "Team"  # role: entity
WEEK = "Match week"  # role: period
POSITION = "League position"  # role: rank

# Data: replace this block with your own table, for example df = pd.read_csv("standings.csv")
_teams = ["Arsenal", "Chelsea", "Liverpool", "Man City", "Man United", "Tottenham"]
_weeks = ["Week 1", "Week 2", "Week 3", "Week 4", "Week 5", "Week 6"]
_ranks = {
    "Arsenal": [3, 2, 1, 1, 2, 1],
    "Chelsea": [4, 4, 3, 4, 3, 3],
    "Liverpool": [1, 1, 2, 3, 1, 2],
    "Man City": [5, 5, 4, 2, 4, 4],
    "Man United": [2, 3, 5, 5, 5, 5],
    "Tottenham": [6, 6, 6, 6, 6, 6],
}
df = pd.DataFrame(
    {
        TEAM: [t for t in _teams for _ in _weeks],
        WEEK: _weeks * len(_teams),
        POSITION: [r for t in _teams for r in _ranks[t]],
    }
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
team_field = TEAM.translate(ESCAPE)
week_field = WEEK.translate(ESCAPE)
pos_field = POSITION.translate(ESCAPE)

teams = list(df[TEAM].unique())
periods = list(df[WEEK].unique())
rank_ticks = sorted(df[POSITION].dropna().unique().tolist())
rank_domain = [min(rank_ticks) - 0.5, max(rank_ticks) + 0.5]

x_enc = alt.X(
    week_field, type="ordinal", title=WEEK, sort=periods, scale=alt.Scale(padding=0.7), axis=alt.Axis(labelAngle=0)
)
y_enc = alt.Y(
    pos_field,
    type="quantitative",
    title=POSITION,
    scale=alt.Scale(domain=rank_domain, reverse=True, nice=False),
    axis=alt.Axis(values=rank_ticks, format="d"),
)
color_enc = alt.Color(
    team_field,
    type="nominal",
    title=TEAM,
    sort=teams,
    scale=alt.Scale(domain=teams, range=IMPRINT_PALETTE),
    legend=None,
)

lines = alt.Chart(df).mark_line(strokeWidth=4).encode(x=x_enc, y=y_enc, color=color_enc)
points = alt.Chart(df).mark_point(filled=True, size=260, opacity=1).encode(x=x_enc, y=y_enc, color=color_enc)

# Direct labels at the last period replace a legend
last = df[df[WEEK] == periods[-1]]
labels = (
    alt.Chart(last)
    .mark_text(align="left", dx=14, fontSize=14, fontWeight="bold")
    .encode(x=x_enc, y=y_enc, text=alt.Text(team_field, type="nominal"), color=color_enc)
)

title = "bump-basic · python · altair · anyplot.ai"
chart = (
    alt.layer(lines, points, labels)
    .properties(
        width=800,
        height=450,
        padding={"left": 10, "top": 10, "bottom": 10, "right": 30},
        autosize=alt.AutoSizeParams(type="fit", contains="padding"),
        background=PAGE_BG,
        title=alt.Title(title, fontSize=18),
    )
    .configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.15,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=13,
        titleFontSize=15,
    )
    .configure_title(color=INK)
)

chart.save(f"plot-{THEME}.png", scale_factor=4.0)

# Pad-only to exact 3200×1800 target (never crop)
TW, TH = 3200, 1800
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (TW, TH):
    _scale = min(1.0, TW / _img.width, TH / _img.height)
    _img = _img.resize((round(_img.width * _scale), round(_img.height * _scale)), Image.LANCZOS)
    _canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _img.width) // 2, (TH - _img.height) // 2))
    _canvas.save(f"plot-{THEME}.png")

chart.save(f"plot-{THEME}.html")
