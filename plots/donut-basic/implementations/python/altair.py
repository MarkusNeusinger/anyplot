""" anyplot.ai
donut-basic: Basic Donut Chart
Library: altair 6.1.0 | Python 3.14.4
Quality: 91/100 | Updated: 2026-04-24
"""

import importlib
import os
import sys


# Drop script directory from sys.path so the `altair` package resolves, not this file
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]
alt = importlib.import_module("altair")
pd = importlib.import_module("pandas")

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030"]

data = pd.DataFrame(
    {"category": ["Engineering", "Marketing", "Operations", "Sales", "Support"], "value": [480, 210, 155, 125, 55]}
)

total = int(data["value"].sum())
data["percentage"] = (data["value"] / total * 100).round(1)
data["label"] = data["percentage"].astype(str) + "%"

arc = (
    alt.Chart(data)
    .mark_arc(innerRadius=260, outerRadius=520, stroke=PAGE_BG, strokeWidth=4)
    .encode(
        theta=alt.Theta(field="value", type="quantitative", stack=True),
        color=alt.Color(
            field="category",
            type="nominal",
            scale=alt.Scale(domain=list(data["category"]), range=IMPRINT),
            legend=alt.Legend(
                title="Department", titleFontSize=22, labelFontSize=18, orient="right", symbolSize=400, padding=16
            ),
        ),
        order=alt.Order(field="value", sort="descending"),
        tooltip=[
            alt.Tooltip("category:N", title="Department"),
            alt.Tooltip("value:Q", title="Budget ($K)"),
            alt.Tooltip("percentage:Q", title="Share (%)", format=".1f"),
        ],
    )
)

labels = (
    alt.Chart(data)
    .mark_text(radius=390, fontSize=22, fontWeight="bold", color="#FFFFFF")
    .encode(
        theta=alt.Theta(field="value", type="quantitative", stack=True),
        order=alt.Order(field="value", sort="descending"),
        text=alt.Text("label:N"),
    )
)

center = (
    alt.Chart(pd.DataFrame({"line": ["Total budget", f"${total:,}K"], "y": [0.08, -0.08]}))
    .mark_text(fontSize=36, fontWeight="bold", color=INK, align="center")
    .encode(y=alt.Y("y:Q", axis=None, scale=alt.Scale(domain=[-1, 1])), text="line:N")
)

final_chart = (
    alt.layer(arc, labels, center)
    .properties(
        width=1200,
        height=1200,
        background=PAGE_BG,
        title=alt.Title(text="donut-basic · altair · anyplot.ai", fontSize=28, anchor="middle", color=INK, offset=20),
        padding={"left": 40, "right": 40, "top": 20, "bottom": 20},
    )
    .configure_view(fill=PAGE_BG, stroke=None)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK, cornerRadius=6)
)

final_chart.save(f"plot-{THEME}.png", scale_factor=3.0)
final_chart.save(f"plot-{THEME}.html")
