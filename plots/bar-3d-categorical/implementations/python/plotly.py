"""anyplot.ai
bar-3d-categorical: 3D Bar Chart for Categorical Comparison
Library: plotly 6.7.0 | Python 3.13.13
Quality: 82/100 | Created: 2026-05-15
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID_COLOR = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
PRODUCT = "Product Category"  # role: x_category
REGION = "Sales Region"  # role: y_category
SALES = "Sales ($K)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("sales.csv")
np.random.seed(42)
_products = ["Electronics", "Clothing", "Food", "Sports"]
_regions = ["North", "South", "East", "West", "Central"]
_base = np.array([85, 60, 45, 55])
_sales = _base[:, None] + np.random.randint(-18, 22, size=(len(_products), len(_regions)))
df = pd.DataFrame(
    {
        PRODUCT: np.repeat(_products, len(_regions)),
        REGION: _regions * len(_products),
        SALES: _sales.ravel().astype(float),
    }
)

# Plot
products = list(df[PRODUCT].unique())
regions = list(df[REGION].unique())
z_max = np.nanmax(df[SALES]) + 10
half = 0.21  # half bar width, leaves a gap between neighbouring bars

# Cube faces as triangles over 8 corner vertices
FACE_I = [0, 0, 4, 4, 0, 0, 2, 2, 0, 0, 1, 1]
FACE_J = [1, 2, 5, 6, 1, 5, 3, 7, 3, 7, 2, 6]
FACE_K = [2, 3, 6, 7, 5, 4, 7, 6, 7, 4, 6, 5]

fig = go.Figure()
label_x, label_y, label_z, label_t = [], [], [], []

for p_idx, prod in enumerate(products):
    xs, ys, zs = [], [], []
    ii, jj, kk = [], [], []
    for _, row in df[df[PRODUCT] == prod].dropna(subset=[SALES]).iterrows():
        xi, yi, h = p_idx, regions.index(row[REGION]), row[SALES]
        n = len(xs)
        xs.extend([xi - half, xi + half, xi + half, xi - half] * 2)
        ys.extend([yi - half, yi - half, yi + half, yi + half] * 2)
        zs.extend([0] * 4 + [h] * 4)
        ii.extend(v + n for v in FACE_I)
        jj.extend(v + n for v in FACE_J)
        kk.extend(v + n for v in FACE_K)
        label_x.append(xi)
        label_y.append(yi)
        label_z.append(h + 2)
        label_t.append(f"{h:g}")

    fig.add_trace(
        go.Mesh3d(
            x=xs,
            y=ys,
            z=zs,
            i=ii,
            j=jj,
            k=kk,
            color=IMPRINT_PALETTE[p_idx % len(IMPRINT_PALETTE)],
            opacity=1.0,
            name=prod,
            showlegend=True,
            flatshading=True,
            lighting={"ambient": 0.7, "diffuse": 0.7, "specular": 0.05, "roughness": 0.8},
            lightposition={"x": 3, "y": -3, "z": 8},
        )
    )

# Value labels on top of each bar
fig.add_trace(
    go.Scatter3d(
        x=label_x,
        y=label_y,
        z=label_z,
        mode="text",
        text=label_t,
        textfont={"size": 10, "color": INK},
        showlegend=False,
        hoverinfo="skip",
    )
)


def axis_style(title):
    return {
        "title": {"text": title, "font": {"size": 14, "color": INK}},
        "tickfont": {"size": 11, "color": INK_SOFT},
        "gridcolor": GRID_COLOR,
        "backgroundcolor": PAGE_BG,
        "showbackground": True,
        "linecolor": INK_SOFT,
        "showgrid": True,
    }


# Style
fig.update_layout(
    autosize=False,
    title={
        "text": "bar-3d-categorical · python · plotly · anyplot.ai",
        "font": {"size": 20, "color": INK},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.98,
        "yanchor": "top",
    },
    scene={
        "xaxis": {**axis_style(PRODUCT), "ticktext": products, "tickvals": list(range(len(products)))},
        "yaxis": {**axis_style(REGION), "ticktext": regions, "tickvals": list(range(len(regions)))},
        "zaxis": {**axis_style(SALES), "range": [0, z_max]},
        "camera": {"eye": {"x": 1.5, "y": -2.2, "z": 1.2}, "up": {"x": 0, "y": 0, "z": 1}},
    },
    paper_bgcolor=PAGE_BG,
    legend={
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
        "font": {"color": INK_SOFT, "size": 12},
        "title": {"text": "Product", "font": {"color": INK, "size": 13}},
        "x": 0.02,
        "y": 0.92,
    },
    margin={"l": 0, "r": 20, "t": 50, "b": 0},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
