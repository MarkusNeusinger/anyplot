""" anyplot.ai
gantt-basic: Basic Gantt Chart
Library: altair 6.3.0 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-22
"""

import os
import sys


sys.modules.pop("altair", None)
sys.path = [p for p in sys.path if p not in ("", ".", os.getcwd())]

import altair as alt  # noqa: E402
import pandas as pd  # noqa: E402
from PIL import Image  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per category in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
TASK = "Task"  # role: task
PHASE = "Phase"  # role: category
START = "Start"  # role: start
END = "End"  # role: end

# Data: replace this block with your own table, for example df = pd.read_csv("schedule.csv")
df = pd.DataFrame(
    {
        TASK: [
            "Project Planning",
            "Requirements Analysis",
            "System Architecture",
            "UI/UX Design",
            "Database Design",
            "Backend Development",
            "Frontend Development",
            "API Development",
            "Unit Testing",
            "Integration Testing",
            "UAT & Bug Fixes",
            "Documentation",
            "Deployment Prep",
        ],
        PHASE: ["Planning"] * 2 + ["Design"] * 3 + ["Development"] * 3 + ["Testing"] * 3 + ["Deployment"] * 2,
        START: pd.to_datetime(
            [
                "2024-01-02",
                "2024-01-05",
                "2024-01-22",
                "2024-01-29",
                "2024-02-05",
                "2024-02-19",
                "2024-02-26",
                "2024-03-11",
                "2024-03-25",
                "2024-04-08",
                "2024-04-22",
                "2024-04-15",
                "2024-05-01",
            ]
        ),
        END: pd.to_datetime(
            [
                "2024-01-18",
                "2024-01-25",
                "2024-02-12",
                "2024-02-16",
                "2024-02-22",
                "2024-04-08",
                "2024-04-15",
                "2024-03-29",
                "2024-04-22",
                "2024-04-29",
                "2024-05-10",
                "2024-05-03",
                "2024-05-13",
            ]
        ),
    }
)

# Plot
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
task_order = df.sort_values(START, kind="stable")[TASK].tolist()
phases = df[PHASE].drop_duplicates().tolist()
span_days = (df[END].max() - df[START].min()).days

chart = (
    alt.Chart(df)
    .mark_bar(size=15, cornerRadius=2)
    .encode(
        x=alt.X(
            START.translate(ESCAPE),
            type="temporal",
            title="Project timeline",
            axis=alt.Axis(
                format="%b %d",
                labelFontSize=10,
                titleFontSize=12,
                labelAngle=-45,
                tickCount=max(4, span_days // 7),
                domainColor=INK_SOFT,
                tickColor=INK_SOFT,
            ),
        ),
        x2=alt.X2(END.translate(ESCAPE)),
        y=alt.Y(
            TASK.translate(ESCAPE),
            type="nominal",
            title=TASK,
            sort=task_order,
            axis=alt.Axis(labelFontSize=10, titleFontSize=12, labelLimit=250, domainColor=INK_SOFT, tickColor=INK_SOFT),
        ),
        color=alt.Color(
            PHASE.translate(ESCAPE),
            type="nominal",
            title=PHASE,
            sort=None,
            scale=alt.Scale(domain=phases, range=IMPRINT_PALETTE),
            legend=alt.Legend(titleFontSize=12, labelFontSize=10, orient="right", symbolSize=120),
        ),
        tooltip=[
            alt.Tooltip(TASK.translate(ESCAPE), type="nominal", title=TASK),
            alt.Tooltip(PHASE.translate(ESCAPE), type="nominal", title=PHASE),
            alt.Tooltip(START.translate(ESCAPE), type="temporal", title=START, format="%B %d, %Y"),
            alt.Tooltip(END.translate(ESCAPE), type="temporal", title=END, format="%B %d, %Y"),
        ],
    )
    .properties(
        width=550,
        height=350,
        title=alt.Title(text="gantt-basic · python · altair · anyplot.ai", fontSize=16, anchor="middle", offset=12),
        background=PAGE_BG,
    )
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .configure_axis(gridColor=INK_SOFT, gridOpacity=0.12, labelColor=INK_SOFT, titleColor=INK)
    .configure_title(color=INK)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK, padding=8)
)

chart.save(f"plot-{THEME}.png", scale_factor=4.0)

# Pad (never crop) to the 3200 x 1800 target canvas
TARGET_W, TARGET_H = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TARGET_W or img.height > TARGET_H:
    # Other data can widen labels or legend; scale the whole render down so nothing is clipped
    fit = min(TARGET_W / img.width, TARGET_H / img.height)
    img = img.resize((int(img.width * fit), int(img.height * fit)), Image.Resampling.LANCZOS)
canvas = Image.new("RGB", (TARGET_W, TARGET_H), PAGE_BG)
canvas.paste(img, ((TARGET_W - img.width) // 2, (TARGET_H - img.height) // 2))
canvas.save(f"plot-{THEME}.png")

chart.interactive().save(f"plot-{THEME}.html")
