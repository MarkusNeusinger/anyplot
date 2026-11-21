"""anyplot.ai
line-3d-trajectory: 3D Line Plot for Trajectory Visualization
Library: plotly 6.7.0 | Python 3.13.13
Quality: 96/100 | Updated: 2026-05-16
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: all eight positions, one per trajectory in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
TRAJECTORY = "Trajectory"  # role: color
X = "X position"  # role: x
Y = "Y position"  # role: y
Z = "Z position"  # role: z

# Data: replace this block with your own table, for example df = pd.read_csv("paths.csv")
# Three helical trajectories, rows in path order within each trajectory
t1 = np.linspace(0, 8 * np.pi, 500)
t2 = np.linspace(0, 6 * np.pi, 400)
t3 = np.linspace(0, 4 * np.pi, 400)
amplitude = 2 + 3 * (t3 / (4 * np.pi))
df = pd.DataFrame(
    {
        TRAJECTORY: ["Standard Helix"] * len(t1) + ["Compressed Helix"] * len(t2) + ["Expanding Helix"] * len(t3),
        X: np.concatenate([5 * np.cos(t1), 3.5 * np.cos(2 * t2), amplitude * np.cos(t3)]),
        Y: np.concatenate([5 * np.sin(t1), 3.5 * np.sin(2 * t2), amplitude * np.sin(t3)]),
        Z: np.concatenate([3 * t1 / (8 * np.pi), 5 * t2 / (6 * np.pi), 6 * t3 / (4 * np.pi)]),
    }
)

# Plot: reads only df and the constants above
title = "Multiple Helical Trajectories · line-3d-trajectory · python · plotly · anyplot.ai"
title_size = round(16 * 67 / len(title)) if len(title) > 67 else 16

fig = go.Figure()
for i, (name, rows) in enumerate(df.groupby(TRAJECTORY, sort=False)):
    fig.add_trace(
        go.Scatter3d(
            x=rows[X],
            y=rows[Y],
            z=rows[Z],
            mode="lines",
            name=str(name),
            line={"color": IMPRINT_PALETTE[i], "width": 4},
            hovertemplate=f"{name}<br>{X}: %{{x:.2f}}<br>{Y}: %{{y:.2f}}<br>{Z}: %{{z:.2f}}<extra></extra>",
        )
    )


def axis(label):
    return {
        "title": {"text": label, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "showbackground": True,
        "backgroundcolor": PAGE_BG,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    }


fig.update_layout(
    autosize=False,
    title={"text": title, "font": {"size": title_size, "color": INK}, "x": 0.5, "xanchor": "center"},
    scene={
        "xaxis": axis(X),
        "yaxis": axis(Y),
        "zaxis": axis(Z),
        "camera": {"eye": {"x": 1.5, "y": 1.5, "z": 1.2}},
        "aspectmode": "data",
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    legend={
        "x": 0.02,
        "y": 0.95,
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
        "font": {"size": 10, "color": INK},
        "title": {"text": TRAJECTORY, "font": {"size": 10, "color": INK}},
    },
    margin={"l": 20, "r": 20, "t": 60, "b": 20},
    hovermode="closest",
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
