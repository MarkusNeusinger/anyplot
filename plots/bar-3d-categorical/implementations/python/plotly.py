""" anyplot.ai
bar-3d-categorical: 3D Bar Chart for Categorical Comparison
Library: plotly 6.7.0 | Python 3.13.13
Quality: 82/100 | Created: 2026-05-15
"""

import os

import numpy as np
import plotly.graph_objects as go


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID_COLOR = "#D0CEC7" if THEME == "light" else "#2D2D2A"

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data
np.random.seed(42)
products = ["Electronics", "Clothing", "Food", "Sports"]
regions = ["North", "South", "East", "West", "Central"]
n_prod, n_reg = len(products), len(regions)

base = np.array([85, 60, 45, 55])
sales = base[:, None] + np.random.randint(-18, 22, size=(n_prod, n_reg))
z_max = int(sales.max()) + 10

DW = 0.42

# Plot
fig = go.Figure()

for p_idx, prod in enumerate(products):
    xs, ys, zs = [], [], []
    ii, jj, kk = [], [], []

    for r_idx in range(n_reg):
        xi, yi, h = p_idx, r_idx, float(sales[p_idx, r_idx])
        x0, x1 = xi - DW / 2, xi + DW / 2
        y0, y1 = yi - DW / 2, yi + DW / 2
        vx = [x0, x1, x1, x0, x0, x1, x1, x0]
        vy = [y0, y0, y1, y1, y0, y0, y1, y1]
        vz = [0, 0, 0, 0, h, h, h, h]
        fi = [0, 0, 4, 4, 0, 0, 2, 2, 0, 0, 1, 1]
        fj = [1, 2, 5, 6, 1, 5, 3, 7, 3, 7, 2, 6]
        fk = [2, 3, 6, 7, 5, 4, 7, 6, 7, 4, 6, 5]
        n = len(xs)
        xs.extend(vx)
        ys.extend(vy)
        zs.extend(vz)
        ii.extend(v + n for v in fi)
        jj.extend(v + n for v in fj)
        kk.extend(v + n for v in fk)

    fig.add_trace(
        go.Mesh3d(
            x=xs,
            y=ys,
            z=zs,
            i=ii,
            j=jj,
            k=kk,
            color=IMPRINT[p_idx],
            opacity=1.0,
            name=prod,
            showlegend=True,
            flatshading=True,
            lighting={"ambient": 0.7, "diffuse": 0.7, "specular": 0.05, "roughness": 0.8},
            lightposition={"x": 3, "y": -3, "z": 8},
        )
    )

# Value labels on top of each bar
lx, ly, lz, lt = [], [], [], []
for p_idx in range(n_prod):
    for r_idx in range(n_reg):
        lx.append(p_idx)
        ly.append(r_idx)
        lz.append(float(sales[p_idx, r_idx]) + 2)
        lt.append(str(int(sales[p_idx, r_idx])))

fig.add_trace(
    go.Scatter3d(
        x=lx, y=ly, z=lz, mode="text", text=lt, textfont={"size": 14, "color": INK}, showlegend=False, hoverinfo="skip"
    )
)

# Style
fig.update_layout(
    title={
        "text": "bar-3d-categorical · plotly · anyplot.ai",
        "font": {"size": 28, "color": INK},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.98,
        "yanchor": "top",
    },
    scene={
        "xaxis": {
            "ticktext": products,
            "tickvals": list(range(n_prod)),
            "title": {"text": "Product Category", "font": {"size": 22, "color": INK}},
            "tickfont": {"size": 18, "color": INK_SOFT},
            "gridcolor": GRID_COLOR,
            "backgroundcolor": PAGE_BG,
            "showbackground": True,
            "linecolor": INK_SOFT,
            "showgrid": True,
        },
        "yaxis": {
            "ticktext": regions,
            "tickvals": list(range(n_reg)),
            "title": {"text": "Sales Region", "font": {"size": 22, "color": INK}},
            "tickfont": {"size": 18, "color": INK_SOFT},
            "gridcolor": GRID_COLOR,
            "backgroundcolor": PAGE_BG,
            "showbackground": True,
            "linecolor": INK_SOFT,
            "showgrid": True,
        },
        "zaxis": {
            "title": {"text": "Sales ($K)", "font": {"size": 22, "color": INK}},
            "tickfont": {"size": 18, "color": INK_SOFT},
            "gridcolor": GRID_COLOR,
            "backgroundcolor": PAGE_BG,
            "showbackground": True,
            "linecolor": INK_SOFT,
            "showgrid": True,
            "range": [0, z_max],
        },
        "camera": {"eye": {"x": 1.5, "y": -2.2, "z": 1.2}, "up": {"x": 0, "y": 0, "z": 1}},
    },
    paper_bgcolor=PAGE_BG,
    legend={
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
        "font": {"color": INK_SOFT, "size": 16},
        "title": {"text": "Product", "font": {"color": INK, "size": 17}},
        "x": 0.02,
        "y": 0.95,
    },
    margin={"l": 0, "r": 20, "t": 60, "b": 0},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
