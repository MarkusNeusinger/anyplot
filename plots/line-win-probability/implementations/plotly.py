""" pyplots.ai
line-win-probability: Win Probability Chart
Library: plotly 6.6.0 | Python 3.14.3
Quality: 86/100 | Created: 2026-03-20
"""

import numpy as np
import plotly.graph_objects as go


# Data - simulated NFL game: Eagles vs Cowboys
np.random.seed(42)

play_count = 120
plays = np.arange(play_count)

# Build win probability through game events
win_prob = np.zeros(play_count)
win_prob[0] = 0.50

# Quarter boundaries
q1_end, q2_end, q3_end = 30, 60, 90

# Key scoring events (play_index, prob_shift, label)
events = [
    (10, 0.15, "Eagles TD\n7-0"),
    (25, -0.10, "Cowboys FG\n7-3"),
    (40, 0.16, "Eagles TD\n14-3"),
    (55, -0.18, "Cowboys TD\n14-10"),
    (68, 0.12, "Eagles FG\n17-10"),
    (80, -0.22, "Cowboys TD\n17-17"),
    (98, 0.20, "Eagles TD\n24-17"),
    (112, 0.10, "Eagles FG\n27-17"),
]

event_plays = {e[0]: e[1] for e in events}

for i in range(1, play_count):
    if i in event_plays:
        drift = event_plays[i]
    else:
        drift = np.random.normal(0, 0.012)
    win_prob[i] = np.clip(win_prob[i - 1] + drift, 0.03, 0.97)

# Final plays ramp to victory
win_prob[-1] = 1.0
win_prob[-2] = 0.96
win_prob[-3] = 0.92

# Convert to percentage
win_pct = win_prob * 100

# Team colors
home_color = "#004C54"  # Eagles dark teal
away_color = "#041E42"  # Cowboys navy

# Plot
fig = go.Figure()

# Fill above 50% (home team)
win_above = np.clip(win_pct, 50, 100)
fig.add_trace(go.Scatter(x=plays, y=win_above, mode="lines", line={"width": 0}, showlegend=False, hoverinfo="skip"))
fig.add_trace(
    go.Scatter(
        x=plays,
        y=np.full(play_count, 50),
        mode="lines",
        line={"width": 0},
        fill="tonexty",
        fillcolor="rgba(0,76,84,0.25)",
        showlegend=False,
        hoverinfo="skip",
    )
)

# Fill below 50% (away team)
win_below = np.clip(win_pct, 0, 50)
fig.add_trace(go.Scatter(x=plays, y=win_below, mode="lines", line={"width": 0}, showlegend=False, hoverinfo="skip"))
fig.add_trace(
    go.Scatter(
        x=plays,
        y=np.full(play_count, 50),
        mode="lines",
        line={"width": 0},
        fill="tonexty",
        fillcolor="rgba(4,30,66,0.25)",
        showlegend=False,
        hoverinfo="skip",
    )
)

# Main win probability line
fig.add_trace(
    go.Scatter(
        x=plays,
        y=win_pct,
        mode="lines",
        line={"width": 3.5, "color": "#306998"},
        name="Win Probability",
        hovertemplate="Play %{x}<br>Win Prob: %{y:.1f}%<extra></extra>",
    )
)

# 50% reference line
fig.add_hline(y=50, line_dash="dash", line_color="rgba(0,0,0,0.35)", line_width=2)

# Quarter dividers
for q_play, q_label in [(q1_end, "Q2"), (q2_end, "Q3"), (q3_end, "Q4")]:
    fig.add_vline(x=q_play, line_dash="dot", line_color="rgba(0,0,0,0.2)", line_width=1.5)
    fig.add_annotation(
        x=q_play, y=100, text=f"<b>{q_label}</b>", showarrow=False, font={"size": 16, "color": "#888"}, yshift=12
    )

# Q1 label
fig.add_annotation(x=0, y=100, text="<b>Q1</b>", showarrow=False, font={"size": 16, "color": "#888"}, yshift=12)

# Annotate scoring events
for play_idx, _, label in events:
    label_clean = label.replace("\n", "<br>")
    is_home = "Eagles" in label
    marker_color = home_color if is_home else away_color
    y_val = win_pct[play_idx]

    fig.add_trace(
        go.Scatter(
            x=[play_idx],
            y=[y_val],
            mode="markers",
            marker={"size": 14, "color": marker_color, "line": {"color": "white", "width": 2}},
            showlegend=False,
            hovertemplate=f"{label_clean}<br>Play {play_idx}<br>Win Prob: {y_val:.1f}%<extra></extra>",
        )
    )

    ay_offset = -55 if y_val > 55 else 55
    ax_offset = 0
    # Stagger annotations to reduce overlap
    if play_idx in (68, 112):
        ax_offset = 40
    elif play_idx in (80,):
        ax_offset = -40

    fig.add_annotation(
        x=play_idx,
        y=y_val,
        text=f"<b>{label_clean}</b>",
        showarrow=True,
        arrowhead=0,
        arrowwidth=1.5,
        arrowcolor=marker_color,
        ax=ax_offset,
        ay=ay_offset,
        font={"size": 13, "color": marker_color},
        bgcolor="rgba(255,255,255,0.92)",
        bordercolor=marker_color,
        borderwidth=1,
        borderpad=4,
    )

# Team legend annotations
fig.add_annotation(
    x=0.01,
    y=0.98,
    xref="paper",
    yref="paper",
    text="<b>▲ PHI Eagles</b>",
    showarrow=False,
    font={"size": 18, "color": home_color},
    bgcolor="rgba(255,255,255,0.85)",
    borderpad=6,
)

fig.add_annotation(
    x=0.01,
    y=0.02,
    xref="paper",
    yref="paper",
    text="<b>▼ DAL Cowboys</b>",
    showarrow=False,
    font={"size": 18, "color": away_color},
    bgcolor="rgba(255,255,255,0.85)",
    borderpad=6,
)

# Final score subtitle
fig.add_annotation(
    x=0.5,
    y=1.08,
    xref="paper",
    yref="paper",
    text="Final Score: Eagles 27 – Cowboys 17",
    showarrow=False,
    font={"size": 20, "color": "#555"},
)

# Style
fig.update_layout(
    title={
        "text": "line-win-probability · plotly · pyplots.ai",
        "font": {"size": 28, "color": "#2a2a2a"},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.97,
    },
    template="plotly_white",
    plot_bgcolor="rgba(248,249,252,1)",
    paper_bgcolor="white",
    xaxis={
        "title": {"text": "Play Number", "font": {"size": 22, "color": "#444"}},
        "tickfont": {"size": 18, "color": "#666"},
        "showline": True,
        "linewidth": 1,
        "linecolor": "rgba(0,0,0,0.18)",
        "range": [-2, play_count + 2],
    },
    yaxis={
        "title": {"text": "Win Probability (%)", "font": {"size": 22, "color": "#444"}},
        "tickfont": {"size": 18, "color": "#666"},
        "tickvals": [0, 25, 50, 75, 100],
        "ticktext": ["0%", "25%", "50%", "75%", "100%"],
        "range": [0, 100],
        "showline": True,
        "linewidth": 1,
        "linecolor": "rgba(0,0,0,0.18)",
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": "rgba(0,0,0,0.06)",
    },
    showlegend=False,
    margin={"l": 80, "r": 40, "t": 130, "b": 70},
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
