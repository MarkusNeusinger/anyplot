"""pyplots.ai
pictogram-basic: Pictogram Chart (Isotype Visualization)
Library: plotly 6.6.0 | Python 3.14.3
Quality: 86/100 | Created: 2026-03-10
"""

import plotly.graph_objects as go


# Data — fruit production (thousands of tonnes)
# Includes exact-multiple (Apples=35, Mangoes=10) and partial (Oranges, Bananas, Grapes)
categories = ["Apples", "Oranges", "Bananas", "Grapes", "Mangoes"]
values = [35, 22, 18, 12, 10]
icons_per_unit = 5
colors = ["#306998", "#E8833A", "#2AA198", "#7B4F9D", "#4CAF50"]
row_bands = [
    "rgba(48,105,152,0.06)",
    "rgba(232,131,58,0.06)",
    "rgba(42,161,152,0.06)",
    "rgba(123,79,157,0.06)",
    "rgba(76,175,80,0.06)",
]

# Build pictogram grid
fig = go.Figure()

max_icons = max(v // icons_per_unit + (1 if v % icons_per_unit else 0) for v in values)
spacing = 0.55
row_height = 0.85
y_positions = [i * row_height for i in range(len(categories))]
band_half = row_height / 2

# Add subtle row background bands
for _row, (y_pos, band_color) in enumerate(zip(y_positions, row_bands, strict=True)):
    fig.add_shape(
        type="rect",
        xref="paper",
        x0=0,
        x1=1,
        y0=y_pos - band_half,
        y1=y_pos + band_half,
        fillcolor=band_color,
        line={"width": 0},
        layer="below",
    )

for row, (cat, val, color) in enumerate(zip(categories, values, colors, strict=True)):
    full_icons = val // icons_per_unit
    remainder = val % icons_per_unit
    y_pos = y_positions[row]
    is_leader = row == 0

    icon_size = 38 if is_leader else 34

    # Full icons
    if full_icons > 0:
        x_full = [i * spacing for i in range(full_icons)]
        fig.add_trace(
            go.Scatter(
                x=x_full,
                y=[y_pos] * full_icons,
                mode="markers",
                marker={"symbol": "square", "size": icon_size, "color": color, "line": {"color": "white", "width": 2}},
                customdata=[[cat, val, icons_per_unit]] * full_icons,
                hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}k tonnes<br>Each ▪ = %{customdata[2]}k<extra></extra>",
                showlegend=False,
            )
        )

    # Partial icon for remainder
    if remainder > 0:
        fraction = remainder / icons_per_unit
        fig.add_trace(
            go.Scatter(
                x=[full_icons * spacing],
                y=[y_pos],
                mode="markers",
                marker={
                    "symbol": "square",
                    "size": icon_size,
                    "color": color,
                    "opacity": max(0.3, fraction),
                    "line": {"color": "white", "width": 2},
                },
                customdata=[[cat, val, remainder]],
                hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}k tonnes<br>Partial: %{customdata[2]}k<extra></extra>",
                showlegend=False,
            )
        )

    # Value label at end of row
    total_icons = full_icons + (1 if remainder > 0 else 0)
    label_color = "#222222" if is_leader else "#555555"
    label_size = 22 if is_leader else 19
    fig.add_annotation(
        x=total_icons * spacing + 0.15,
        y=y_pos,
        text=f"<b>{val}k</b>" if is_leader else f"{val}k",
        showarrow=False,
        font={"size": label_size, "color": label_color, "family": "Arial"},
        xanchor="left",
    )

    # Thin baseline connector for visual alignment
    if total_icons > 0:
        fig.add_shape(
            type="line",
            x0=0,
            x1=(total_icons - 1) * spacing,
            y0=y_pos + icon_size * 0.0085,
            y1=y_pos + icon_size * 0.0085,
            line={"color": color, "width": 0.5, "dash": "dot"},
            opacity=0.25,
            layer="below",
        )

# Legend annotation at bottom
fig.add_annotation(
    xref="paper",
    yref="paper",
    x=0.0,
    y=-0.08,
    text="<b>▪</b> = 5k tonnes  |  Faded ▪ = partial unit",
    showarrow=False,
    font={"size": 18, "color": "#777777", "family": "Arial"},
    xanchor="left",
)

# Subtitle for storytelling context
fig.add_annotation(
    xref="paper",
    yref="paper",
    x=0.5,
    y=1.06,
    text="Apples lead with 35k tonnes — nearly double the next category",
    showarrow=False,
    font={"size": 19, "color": "#555555", "family": "Arial"},
    xanchor="center",
)

# Dropdown to toggle between absolute values and normalized view
fig.update_layout(
    updatemenus=[
        {
            "buttons": [
                {"label": "Absolute", "method": "update", "args": [{"visible": [True] * len(fig.data)}]},
                {
                    "label": "Top 3 Only",
                    "method": "update",
                    "args": [{"visible": [True if tr.y and tr.y[0] in y_positions[:3] else False for tr in fig.data]}],
                },
            ],
            "direction": "down",
            "showactive": True,
            "x": 1.0,
            "xanchor": "right",
            "y": 1.12,
            "yanchor": "top",
            "bgcolor": "rgba(48,105,152,0.08)",
            "bordercolor": "#306998",
            "font": {"size": 14, "color": "#306998"},
        }
    ]
)

# Layout
fig.update_layout(
    title={
        "text": "Fruit Production · pictogram-basic · plotly · pyplots.ai",
        "font": {"size": 28, "color": "#222222", "family": "Arial Black, Arial"},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.95,
    },
    xaxis={
        "showgrid": False,
        "zeroline": False,
        "showticklabels": False,
        "showline": False,
        "range": [-0.5, max_icons * spacing + 1.0],
    },
    yaxis={
        "tickvals": y_positions,
        "ticktext": [f"<b>{c}</b>" if i == 0 else c for i, c in enumerate(categories)],
        "tickfont": {"size": 22, "color": "#333333", "family": "Arial"},
        "showgrid": False,
        "zeroline": False,
        "showline": False,
        "range": [max(y_positions) + band_half + 0.1, min(y_positions) - band_half - 0.1],
    },
    template="plotly_white",
    margin={"t": 120, "b": 80, "l": 150, "r": 50},
    plot_bgcolor="white",
    paper_bgcolor="white",
    hoverlabel={"bgcolor": "white", "font_size": 16, "font_family": "Arial"},
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html")
