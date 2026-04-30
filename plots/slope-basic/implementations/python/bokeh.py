""" anyplot.ai
slope-basic: Basic Slope Chart (Slopegraph)
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 84/100 | Updated: 2026-04-30
"""

import os

from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource, HoverTool, Label
from bokeh.plotting import figure
from bokeh.resources import CDN


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

INCREASE_COLOR = "#009E73"  # Okabe-Ito position 1 (brand green)
DECREASE_COLOR = "#D55E00"  # Okabe-Ito position 2 (vermillion)

products = [
    "Product A",
    "Product B",
    "Product C",
    "Product D",
    "Product E",
    "Product F",
    "Product G",
    "Product H",
    "Product I",
    "Product J",
]
q1_sales = [85, 72, 91, 45, 68, 53, 78, 62, 40, 88]
q4_sales = [92, 65, 88, 71, 74, 48, 95, 58, 67, 82]

colors = [INCREASE_COLOR if end > start else DECREASE_COLOR for start, end in zip(q1_sales, q4_sales, strict=True)]


def spread_labels(ys, min_gap=4.5):
    """Shift label y-positions apart so dense clusters don't overlap."""
    n = len(ys)
    order = sorted(range(n), key=lambda i: ys[i])
    adjusted = [float(ys[i]) for i in order]
    for _ in range(30):
        changed = False
        for i in range(1, n):
            if adjusted[i] - adjusted[i - 1] < min_gap:
                mid = (adjusted[i] + adjusted[i - 1]) / 2
                adjusted[i - 1] = mid - min_gap / 2
                adjusted[i] = mid + min_gap / 2
                changed = True
        if not changed:
            break
    result = [0.0] * n
    for new_i, orig_i in enumerate(order):
        result[orig_i] = adjusted[new_i]
    return result


left_y = spread_labels(q1_sales)
right_y = spread_labels(q4_sales)

p = figure(
    width=4800,
    height=2700,
    title="slope-basic · bokeh · anyplot.ai",
    x_range=(-0.5, 1.5),
    y_range=(25, 112),
    toolbar_location=None,
)

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

p.title.text_font_size = "32pt"
p.title.align = "center"
p.title.text_color = INK

p.xaxis.visible = False
p.yaxis.axis_label = "Sales (thousands)"
p.yaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_color = INK
p.yaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = INK_SOFT
p.ygrid.grid_line_alpha = 0.10

# Time point labels
for x_pos, label in [(0, "Q1"), (1, "Q4")]:
    p.add_layout(
        Label(
            x=x_pos, y=27, text=label, text_font_size="28pt", text_align="center", text_baseline="top", text_color=INK
        )
    )

# Direction legend in upper-center (above data range)
for y_pos, legend_text, color in [(109, "— Increase", INCREASE_COLOR), (103, "— Decrease", DECREASE_COLOR)]:
    p.add_layout(
        Label(
            x=0.5,
            y=y_pos,
            text=legend_text,
            text_font_size="20pt",
            text_align="center",
            text_baseline="middle",
            text_color=color,
        )
    )

# ColumnDataSource for scatter enables HoverTool
scatter_data: dict[str, list] = {"x": [], "y": [], "color": [], "product": [], "period": [], "value": []}
for product, start, end, color in zip(products, q1_sales, q4_sales, colors, strict=True):
    scatter_data["x"].extend([0, 1])
    scatter_data["y"].extend([start, end])
    scatter_data["color"].extend([color, color])
    scatter_data["product"].extend([product, product])
    scatter_data["period"].extend(["Q1", "Q4"])
    scatter_data["value"].extend([start, end])

source = ColumnDataSource(data=scatter_data)

# Draw slope lines and endpoint labels
for i, (product, start, end, color) in enumerate(zip(products, q1_sales, q4_sales, colors, strict=True)):
    p.line(x=[0, 1], y=[start, end], line_width=4, line_color=color, line_alpha=0.8)
    p.add_layout(
        Label(
            x=-0.05,
            y=left_y[i],
            text=f"{product}: {start}",
            text_font_size="18pt",
            text_align="right",
            text_baseline="middle",
            text_color=color,
        )
    )
    p.add_layout(
        Label(
            x=1.05,
            y=right_y[i],
            text=f"{end}: {product}",
            text_font_size="18pt",
            text_align="left",
            text_baseline="middle",
            text_color=color,
        )
    )

dots = p.scatter(x="x", y="y", size=18, color="color", source=source, alpha=0.9)
p.add_tools(
    HoverTool(
        renderers=[dots], tooltips=[("Product", "@product"), ("Period", "@period"), ("Sales", "@value{0} thousand")]
    )
)

export_png(p, filename=f"plot-{THEME}.png")
save(p, filename=f"plot-{THEME}.html", resources=CDN, title="slope-basic · bokeh · anyplot.ai")
