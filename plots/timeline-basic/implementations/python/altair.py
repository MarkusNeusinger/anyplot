"""anyplot.ai
timeline-basic: Event Timeline
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-11
"""

import os

import altair as alt
import pandas as pd
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per category in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
DATE = "Date"  # role: date
EVENT = "Event"  # role: event
CATEGORY = "Phase"  # role: category

# Data: replace this block with your own table, for example df = pd.read_csv("milestones.csv")
df = pd.DataFrame(
    {
        DATE: pd.to_datetime(
            [
                "2024-01-15",
                "2024-02-20",
                "2024-03-10",
                "2024-04-05",
                "2024-05-01",
                "2024-06-15",
                "2024-07-20",
                "2024-08-30",
                "2024-09-15",
                "2024-10-25",
                "2024-11-10",
                "2024-12-01",
            ]
        ),
        EVENT: [
            "Project Kickoff",
            "Requirements Complete",
            "Design Review",
            "Development Start",
            "Alpha Release",
            "Beta Testing",
            "Security Audit",
            "Performance Testing",
            "User Acceptance",
            "Release Candidate",
            "Documentation",
            "Production Launch",
        ],
        CATEGORY: [
            "Planning",
            "Planning",
            "Planning",
            "Development",
            "Development",
            "Testing",
            "Testing",
            "Testing",
            "Testing",
            "Release",
            "Release",
            "Release",
        ],
    }
)

# Plot: reads only df and the constants above
# Labels alternate above and below the axis; the offset is layout, only the date is data
side = pd.Series([1 if i % 2 == 0 else -1 for i in range(len(df))], index=df.index)
tier = pd.Series([(i // 2) % 2 for i in range(len(df))], index=df.index)  # two label heights per side
events = pd.DataFrame(
    {
        "date": df[DATE],
        "event": df[EVENT],
        "category": df[CATEGORY],
        "marker_y": side * (1.2 + 1.0 * tier),
        "label_y": side * (2.0 + 1.0 * tier),
        "axis_y": 0,
    }
)

categories = list(dict.fromkeys(df[CATEGORY].dropna().astype(str)))
color = alt.Color(
    "category:N",
    title=CATEGORY,
    sort=None,
    scale=alt.Scale(domain=categories, range=IMPRINT_PALETTE),
    legend=alt.Legend(orient="top", direction="horizontal", labelFontSize=11, titleFontSize=12, symbolSize=180),
)
y_scale = alt.Scale(domain=[-3.6, 3.6])
x_scale = alt.Scale(
    domain=[(df[DATE].min() - pd.Timedelta(days=45)).isoformat(), (df[DATE].max() + pd.Timedelta(days=45)).isoformat()]
)

axis_line = alt.Chart(events).mark_rule(color=INK_SOFT, strokeWidth=2).encode(y=alt.Y("axis_y:Q", scale=y_scale))

connectors = (
    alt.Chart(events)
    .mark_rule(strokeWidth=1.6, opacity=1)
    .encode(x=alt.X("date:T", scale=x_scale), y=alt.Y("axis_y:Q", scale=y_scale), y2="marker_y:Q", color=color)
)

points = (
    alt.Chart(events)
    .mark_circle(size=130, stroke=PAGE_BG, strokeWidth=1.5, opacity=1)
    .encode(
        x=alt.X(
            "date:T",
            scale=x_scale,
            title=DATE,
            axis=alt.Axis(format="%b %Y", labelAngle=-45, grid=False, labelColor=INK_SOFT, titleColor=INK),
        ),
        y=alt.Y("marker_y:Q", scale=y_scale),
        color=color,
        tooltip=[
            alt.Tooltip("date:T", title=DATE, format="%B %d, %Y"),
            alt.Tooltip("event:N", title=EVENT),
            alt.Tooltip("category:N", title=CATEGORY),
        ],
    )
)

labels = (
    alt.Chart(events)
    .mark_text(align="center", fontSize=10, fontWeight="bold", color=INK)
    .encode(x=alt.X("date:T", scale=x_scale), y=alt.Y("label_y:Q", scale=y_scale), text="event:N")
)

chart = (
    alt.layer(axis_line, connectors, points, labels)
    .properties(
        width=730,
        height=295,
        background=PAGE_BG,
        title=alt.Title("timeline-basic · python · altair · anyplot.ai", fontSize=16, anchor="middle", color=INK),
    )
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .configure_axis(domainColor=INK_SOFT, tickColor=INK_SOFT, labelFontSize=10, titleFontSize=12)
    .configure_axisY(disable=True)
    .configure_legend(labelColor=INK_SOFT, titleColor=INK)
    .interactive()
)

# Save outputs
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Pad (never crop) to the canonical landscape canvas
TW, TH = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
w, h = img.size
if w > TW or h > TH:
    raise SystemExit(f"altair vl-convert produced {w}x{h}, exceeds target {TW}x{TH}")
if (w, h) != (TW, TH):
    canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    canvas.paste(img, ((TW - w) // 2, (TH - h) // 2))
    canvas.save(f"plot-{THEME}.png")
