"""anyplot.ai
map-animated-temporal: Animated Map over Time
Library: plotly | Python 3.13
Quality: pending | Updated: 2026-05-27
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"
LAND_COLOR = "#E0DDD5" if THEME == "light" else "#252520"
OCEAN_COLOR = "#C5D5E5" if THEME == "light" else "#1E2832"
BORDER_COLOR = "#888888" if THEME == "light" else "#555555"

# Continuous colorscale (imprint_seq — sequential, single-polarity)
imprint_seq = [[0.0, "#009E73"], [1.0, "#4467A3"]]

# Data: Simulated earthquake aftershock sequence (off Japan coast)
np.random.seed(42)
n_days = 15
epicenter_lat, epicenter_lon = 38.3, 142.4

days_data = {}
for day in range(n_days):
    n_points = 30 + np.random.randint(-10, 15)
    spread = 0.5 + day * 0.3
    intensity_decay = 1.0 - day * 0.05
    lats, lons, mags = [], [], []
    for _ in range(n_points):
        angle = np.random.uniform(0, 2 * np.pi)
        distance = np.abs(np.random.normal(0, spread))
        lats.append(epicenter_lat + distance * np.cos(angle))
        lons.append(epicenter_lon + distance * np.sin(angle))
        mags.append(min(7.5, max(2.0, np.random.exponential(2.5) * intensity_decay)))
    days_data[day] = {"lat": lats, "lon": lons, "mag": mags}

# Plot: base figure initialised with Day 1 data
cd0 = days_data[0]
fig = go.Figure()

fig.add_trace(
    go.Scattergeo(  # trail layer — ghost points from previous 2 days
        lat=[],
        lon=[],
        mode="markers",
        marker=dict(size=4, color="#009E73", opacity=0.2),
        showlegend=False,
        hoverinfo="skip",
    )
)
fig.add_trace(
    go.Scattergeo(  # current-day layer
        lat=cd0["lat"],
        lon=cd0["lon"],
        mode="markers",
        marker=dict(
            size=[max(4, m * 3.5) for m in cd0["mag"]],
            color=cd0["mag"],
            coloraxis="coloraxis",
            opacity=0.75,
            line=dict(width=0.5, color=INK_SOFT),
        ),
        hovertemplate="Lat: %{lat:.2f}<br>Lon: %{lon:.2f}<extra></extra>",
        showlegend=False,
    )
)

# Build animation frames with trailing ghost points
frames = []
for day in range(n_days):
    trail_lats, trail_lons = [], []
    for d in range(max(0, day - 2), day):
        trail_lats.extend(days_data[d]["lat"])
        trail_lons.extend(days_data[d]["lon"])

    cd = days_data[day]
    frames.append(
        go.Frame(
            data=[
                go.Scattergeo(
                    lat=trail_lats,
                    lon=trail_lons,
                    mode="markers",
                    marker=dict(size=4, color="#009E73", opacity=0.2),
                    hoverinfo="skip",
                ),
                go.Scattergeo(
                    lat=cd["lat"],
                    lon=cd["lon"],
                    mode="markers",
                    marker=dict(
                        size=[max(4, m * 3.5) for m in cd["mag"]],
                        color=cd["mag"],
                        coloraxis="coloraxis",
                        opacity=0.75,
                        line=dict(width=0.5, color=INK_SOFT),
                    ),
                    hovertemplate="Lat: %{lat:.2f}<br>Lon: %{lon:.2f}<extra></extra>",
                ),
            ],
            name=f"Day {day + 1:02d}",
        )
    )

fig.frames = frames

# Title with adaptive fontsize (longer title shrinks proportionally)
title_text = "Earthquake Aftershock Sequence · map-animated-temporal · python · plotly · anyplot.ai"
n = len(title_text)
title_fontsize = max(11, round(16 * min(1.0, 67 / n)))

slider_steps = [
    dict(
        args=[
            [f"Day {i + 1:02d}"],
            {"frame": {"duration": 300, "redraw": True}, "mode": "immediate", "transition": {"duration": 300}},
        ],
        label=f"Day {i + 1}",
        method="animate",
    )
    for i in range(n_days)
]

# Style
fig.update_layout(
    autosize=False,
    paper_bgcolor=PAGE_BG,
    font=dict(color=INK),
    title=dict(text=title_text, font=dict(size=title_fontsize, color=INK), x=0.5, xanchor="center"),
    geo=dict(
        scope="asia",
        center=dict(lat=epicenter_lat, lon=epicenter_lon),
        projection_scale=4,
        showland=True,
        landcolor=LAND_COLOR,
        showocean=True,
        oceancolor=OCEAN_COLOR,
        showcountries=True,
        countrycolor=BORDER_COLOR,
        countrywidth=1,
        showcoastlines=True,
        coastlinecolor=BORDER_COLOR,
        coastlinewidth=1.5,
        showlakes=True,
        lakecolor=OCEAN_COLOR,
        lataxis=dict(showgrid=True, gridcolor=GRID),
        lonaxis=dict(showgrid=True, gridcolor=GRID),
        bgcolor=PAGE_BG,
    ),
    coloraxis=dict(
        colorscale=imprint_seq,
        cmin=2,
        cmax=7.5,
        colorbar=dict(
            title=dict(text="Magnitude", font=dict(size=12, color=INK)),
            tickfont=dict(size=10, color=INK_SOFT),
            bgcolor=ELEVATED_BG,
            bordercolor=INK_SOFT,
            borderwidth=1,
            len=0.6,
            thickness=15,
        ),
    ),
    margin=dict(l=20, r=20, t=70, b=120),
    updatemenus=[
        dict(
            type="buttons",
            showactive=True,
            y=0.08,
            x=0.05,
            xanchor="left",
            buttons=[
                dict(
                    label="▶ Play",
                    method="animate",
                    args=[
                        None,
                        {
                            "frame": {"duration": 800, "redraw": True},
                            "fromcurrent": True,
                            "transition": {"duration": 300, "easing": "cubic-in-out"},
                        },
                    ],
                ),
                dict(
                    label="⏸ Pause",
                    method="animate",
                    args=[
                        [None],
                        {"frame": {"duration": 0, "redraw": False}, "mode": "immediate", "transition": {"duration": 0}},
                    ],
                ),
            ],
            font=dict(size=12, color=INK),
            bgcolor=ELEVATED_BG,
            bordercolor=INK_SOFT,
        )
    ],
    sliders=[
        dict(
            active=0,
            yanchor="top",
            xanchor="left",
            currentvalue=dict(font=dict(size=12, color=INK), prefix="Time: ", visible=True, xanchor="center"),
            transition=dict(duration=300, easing="cubic-in-out"),
            pad=dict(b=10, t=50),
            len=0.9,
            x=0.05,
            y=0,
            steps=slider_steps,
            font=dict(color=INK_SOFT),
            bgcolor=ELEVATED_BG,
            bordercolor=INK_SOFT,
        )
    ],
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn", full_html=True)
