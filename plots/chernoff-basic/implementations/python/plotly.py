"""anyplot.ai
chernoff-basic: Chernoff Faces for Multivariate Data
Library: plotly 6.7.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-15
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

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
# Facial feature driven by each variable, in the order of VARIABLES
FEATURES = ["Face width", "Face height", "Eye size", "Smile"]

# Columns: set these to your table's column names
COFFEE = "Coffee"  # role: observation_id
ORIGIN = "Origin"  # role: extra
VARIABLES = [
    "Body (cupping score)",
    "Acidity (cupping score)",
    "Aroma (cupping score)",
    "Sweetness (cupping score)",
]  # role: variable_

# Data: replace this block with your own table, for example df = pd.read_csv("coffees.csv")
df = pd.DataFrame(
    {
        COFFEE: [
            "Yirgacheffe",
            "Sidamo",
            "Guji",
            "Harrar",
            "Limu",
            "Huila",
            "Nariño",
            "Cauca",
            "Tolima",
            "Antioquia",
            "Cerrado",
            "Mogiana",
            "Sul de Minas",
            "Bahia",
            "Espírito Santo",
        ],
        ORIGIN: ["Ethiopia"] * 5 + ["Colombia"] * 5 + ["Brazil"] * 5,
    }
    | dict(
        zip(
            VARIABLES,
            [
                [6.9, 7.3, 7.0, 8.1, 7.5, 7.6, 7.9, 7.4, 7.7, 7.2, 8.4, 8.0, 8.7, 8.2, 7.8],
                [8.9, 8.6, 8.4, 8.0, 8.2, 8.1, 8.3, 7.8, 7.6, 7.9, 6.6, 7.0, 6.9, 6.7, 7.2],
                [8.8, 8.5, 8.7, 8.9, 8.1, 7.7, 7.9, 8.0, 7.4, 7.6, 7.3, 7.1, 7.5, 6.9, 7.2],
                [7.8, 7.4, 7.9, 7.1, 8.0, 8.2, 7.7, 8.4, 7.9, 8.3, 8.8, 8.5, 8.9, 8.1, 8.6],
            ],
        )
    )
)

# Plot: reads only df and the constants above
groups = list(df[ORIGIN].unique())
df_rows = df[ORIGIN].map({g: i for i, g in enumerate(groups)}).to_numpy()
df_cols = df.groupby(ORIGIN, sort=False).cumcount().to_numpy()
n_rows = len(groups)
n_cols = int(np.nanmax(df_cols)) + 1

# Normalize every variable to 0-1 before mapping it to a feature
values = df[VARIABLES]
span = (values.max() - values.min()).replace(0, 1)
norm = ((values - values.min()) / span).fillna(0.5).to_numpy()

cell_w, cell_h, radius = 2.2, 2.6, 0.95


def outline(xs, ys, closed=True):
    return "M " + " L ".join(f"{x:.4f},{y:.4f}" for x, y in zip(xs, ys)) + (" Z" if closed else "")


def ellipse(cx, cy, rx, ry, n=48):
    t = np.linspace(0, 2 * np.pi, n)
    return cx + rx * np.cos(t), cy + ry * np.sin(t)


shapes = []
for k, (width_v, height_v, eye_v, smile_v) in enumerate(norm):
    cx = df_cols[k] * cell_w
    cy = (n_rows - 1 - df_rows[k]) * cell_h
    color = IMPRINT_PALETTE[df_rows[k] % len(IMPRINT_PALETTE)]

    face_w = radius * (0.55 + 0.6 * width_v)
    face_h = radius * (0.7 + 0.5 * height_v)
    eye_r = radius * (0.07 + 0.17 * eye_v)
    mouth_curve = 0.3 - 0.6 * smile_v

    shapes.append(
        dict(
            type="path",
            path=outline(*ellipse(cx, cy, face_w, face_h)),
            fillcolor=color,
            opacity=0.4,
            line=dict(color=INK_SOFT, width=1.5),
        )
    )

    eye_dx, eye_dy = face_w * 0.4, face_h * 0.22
    for side in (-1, 1):
        ex = cx + side * eye_dx
        ey = cy + eye_dy
        shapes.append(
            dict(
                type="path",
                path=outline(*ellipse(ex, ey, eye_r, eye_r * 0.8)),
                fillcolor=ELEVATED_BG,
                line=dict(color=INK_SOFT, width=1.5),
            )
        )
        shapes.append(
            dict(
                type="path",
                path=outline(*ellipse(ex, ey, eye_r * 0.5, eye_r * 0.5, 24)),
                fillcolor=INK,
                line=dict(color=INK, width=0.5),
            )
        )
        brow_y = cy + eye_dy + eye_r + face_h * 0.1
        shapes.append(
            dict(
                type="line",
                x0=ex - eye_r * 1.2,
                x1=ex + eye_r * 1.2,
                y0=brow_y,
                y1=brow_y,
                line=dict(color=INK, width=2),
            )
        )

    nose_h, nose_w = face_h * 0.15, face_w * 0.1
    shapes.append(
        dict(
            type="path",
            path=f"M {cx},{cy + nose_h / 2} L {cx - nose_w},{cy - nose_h / 2} L {cx + nose_w},{cy - nose_h / 2} Z",
            fillcolor=INK,
            opacity=0.5,
            line=dict(color=INK, width=0.5),
        )
    )

    mouth_w = face_w * 0.5
    mx = np.linspace(cx - mouth_w, cx + mouth_w, 24)
    my = cy - face_h * 0.4 + mouth_curve * (1 - ((mx - cx) / mouth_w) ** 2) * radius * 0.5
    shapes.append(dict(type="path", path=outline(mx, my, closed=False), line=dict(color=INK, width=2)))

fig = go.Figure()

# Legend entries: one marker per group, colored like its faces
for i, group in enumerate(groups):
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            marker=dict(
                size=12,
                color=IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)],
                opacity=0.6,
                line=dict(color=INK_SOFT, width=1),
            ),
            name=str(group),
        )
    )

# Observation labels below each face
for k, name in enumerate(df[COFFEE]):
    fig.add_annotation(
        x=df_cols[k] * cell_w,
        y=(n_rows - 1 - df_rows[k]) * cell_h - 1.3,
        text=str(name),
        showarrow=False,
        font=dict(size=10, color=INK_SOFT),
        yanchor="top",
    )

# Row labels (groups)
for i, group in enumerate(groups):
    fig.add_annotation(
        x=-1.4,
        y=(n_rows - 1 - i) * cell_h,
        text=f"<b>{group}</b>",
        showarrow=False,
        font=dict(size=12, color=INK),
        xanchor="right",
    )

# Key: which variable drives which facial feature
key_text = f"<b>Key</b><br>{'<br>'.join(f'{f}: {v.split(" (")[0]}' for f, v in zip(FEATURES, VARIABLES))}"
fig.add_annotation(
    x=(n_cols - 1) * cell_w + 1.5,
    y=(n_rows - 1) * cell_h / 2 - 0.6,
    text=key_text,
    showarrow=False,
    font=dict(size=10, color=INK_SOFT),
    align="left",
    xanchor="left",
    bgcolor=ELEVATED_BG,
    bordercolor=INK_SOFT,
    borderwidth=1,
    borderpad=6,
)

fig.update_layout(
    autosize=False,
    width=800,
    height=450,
    title=dict(text="chernoff-basic · python · plotly · anyplot.ai", font=dict(size=16, color=INK), x=0.5),
    shapes=shapes,
    xaxis=dict(
        range=[-3.2, (n_cols - 1) * cell_w + 4.6], showgrid=False, zeroline=False, showticklabels=False, fixedrange=True
    ),
    yaxis=dict(
        range=[-1.9, (n_rows - 1) * cell_h + 1.5],
        showgrid=False,
        zeroline=False,
        showticklabels=False,
        scaleanchor="x",
        scaleratio=1,
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(color=INK),
    legend=dict(
        title=dict(text=f"<b>{ORIGIN}</b>", font=dict(size=11, color=INK)),
        font=dict(size=10, color=INK_SOFT),
        x=1,
        y=0.98,
        xanchor="right",
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=1,
    ),
    margin=dict(l=20, r=20, t=50, b=20),
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
