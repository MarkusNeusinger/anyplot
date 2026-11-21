"""anyplot.ai
box-horizontal: Horizontal Box Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-12
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: all eight positions, one per category in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
COURIER = "Courier"  # role: categories
DELIVERY_TIME = "Delivery time (minutes)"  # role: values

# Data: replace this block with your own table, for example df = pd.read_csv("deliveries.csv")
rng = np.random.default_rng(7)
couriers = {
    # name: (median minutes, spread, share of late deliveries)
    "Bike Messenger": (24, 6, 0.04),
    "Electric Scooter": (31, 8, 0.06),
    "Motorbike Express": (19, 4, 0.05),
    "Van Fleet": (46, 12, 0.08),
    "Drone Service": (14, 3, 0.02),
    "Parcel Locker Pickup": (58, 18, 0.10),
}
frames = []
for name, (typical, spread, late_share) in couriers.items():
    times = rng.lognormal(np.log(typical), spread / typical, 90)
    late = rng.random(90) < late_share
    times[late] *= rng.uniform(1.8, 2.6, late.sum())
    frames.append(pd.DataFrame({COURIER: name, DELIVERY_TIME: times.round(1)}))
df = pd.concat(frames, ignore_index=True)

# Plot: reads only df and the constants above
order = df.groupby(COURIER)[DELIVERY_TIME].median().sort_values(ascending=False).index

fig = go.Figure()
for i, courier in enumerate(order):
    fig.add_trace(
        go.Box(
            x=df.loc[df[COURIER] == courier, DELIVERY_TIME],
            name=courier,
            orientation="h",
            marker=dict(color=IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)], size=6),
            line=dict(color=INK_SOFT, width=1.5),
            fillcolor=IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)],
            boxpoints="outliers",
            hovertemplate="<b>%{y}</b><br>%{x:.1f} min<extra></extra>",
        )
    )

fig.update_layout(
    autosize=False,
    margin=dict(l=130, r=40, t=70, b=60),
    title=dict(text="box-horizontal · python · plotly · anyplot.ai", font=dict(size=16, color=INK), x=0.5),
    xaxis=dict(
        title=dict(text=DELIVERY_TIME, font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        gridcolor=GRID,
        linecolor=INK_SOFT,
        zeroline=False,
    ),
    yaxis=dict(tickfont=dict(size=10, color=INK_SOFT), linecolor=INK_SOFT, automargin=True),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(color=INK),
    showlegend=False,
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
