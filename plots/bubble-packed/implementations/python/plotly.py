"""anyplot.ai
bubble-packed: Basic Packed Bubble Chart
Library: plotly 6.7.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-29
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go


THEME = os.getenv("ANYPLOT_THEME", "light")

# Theme-adaptive chrome tokens
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette — canonical order; first series always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
SERVICE = "Service"  # role: label
SPEND = "Monthly spend (thousand USD)"  # role: value
CATEGORY = "Category"  # role: group

# Data: replace this block with your own table, for example df = pd.read_csv("cloud_spend.csv")
df = pd.DataFrame(
    [
        ("Virtual machines", 412, "Compute"),
        ("GPU training", 340, "Compute"),
        ("Kubernetes", 268, "Compute"),
        ("Serverless", 96, "Compute"),
        ("Object storage", 188, "Storage"),
        ("Block volumes", 124, "Storage"),
        ("Backups", 62, "Storage"),
        ("Archive", 31, "Storage"),
        ("Data warehouse", 305, "Data & Analytics"),
        ("Managed SQL", 176, "Data & Analytics"),
        ("Streaming", 142, "Data & Analytics"),
        ("ETL pipelines", 88, "Data & Analytics"),
        ("Egress", 158, "Networking"),
        ("CDN", 74, "Networking"),
        ("Load balancers", 46, "Networking"),
        ("Monitoring", 112, "Security & Ops"),
        ("Identity", 38, "Security & Ops"),
        ("Key management", 22, "Security & Ops"),
    ],
    columns=[SERVICE, SPEND, CATEGORY],
)

# Plot: reads only df and the constants above
labels = df[SERVICE].tolist()
values = df[SPEND].to_numpy(dtype=float)
group_names = list(dict.fromkeys(df[CATEGORY]))
group_colors = {g: IMPRINT_PALETTE[k] for k, g in enumerate(group_names)}
group_idx = df[CATEGORY].map({g: k for k, g in enumerate(group_names)}).to_numpy(dtype=int)
n = len(df)

# Area proportional to value: radius scales with the square root
radii = np.sqrt(values / values.max()) * 100

# Circle packing: pairwise overlap push, a pull toward the group centre and one toward the middle
angles = np.arange(n) * 2.39996
pos = np.sqrt(np.arange(n) + 1)[:, None] * 40 * np.column_stack([np.cos(angles), np.sin(angles)])
gap = 3
min_dist = radii[:, None] + radii[None, :] + gap
same_group = group_idx[:, None] == group_idx[None, :]

for step in range(2500):
    delta = pos[:, None, :] - pos[None, :, :]
    dist = np.hypot(delta[..., 0], delta[..., 1]) + np.eye(n)
    overlap = np.clip(min_dist - dist, 0, None)
    np.fill_diagonal(overlap, 0)
    push = (delta / dist[..., None] * overlap[..., None]).sum(axis=1) * 0.5
    if step < 2000:
        centres = (same_group[..., None] * pos[None, :, :]).sum(axis=1) / same_group.sum(axis=1)[:, None]
        push += (centres - pos) * 0.03 - pos * 0.01
    pos += push

pos -= pos.mean(axis=0)

# Axis ranges: a square window around the packed cluster (equal scale on both axes)
pad = 12
x_lo, y_lo = (pos - radii[:, None]).min(axis=0) - pad
x_hi, y_hi = (pos + radii[:, None]).max(axis=0) + pad

# Canvas: width=600, height=600, scale=4 → 2400×2400 (square: a packed cluster has no preferred axis)
fig_w, fig_h = 600, 600
m_l, m_r, m_t, m_b = 20, 20, 50, 60
plot_w, plot_h = fig_w - m_l - m_r, fig_h - m_t - m_b
px_per_unit = min(plot_w / (x_hi - x_lo), plot_h / (y_hi - y_lo))
marker_diameters = 2 * radii * px_per_unit

# Label colour: whichever of the two ink tones has the higher WCAG contrast on the fill
LIGHT_TEXT, DARK_TEXT = "#F0EFE8", "#1A1A17"


def luminance(hex_color):
    channels = np.array([int(hex_color[k : k + 2], 16) / 255 for k in (1, 3, 5)])
    linear = np.where(channels <= 0.03928, channels / 12.92, ((channels + 0.055) / 1.055) ** 2.4)
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def label_color(fill):
    lum = luminance(fill)
    return max(
        (LIGHT_TEXT, DARK_TEXT), key=lambda ink: (max(lum, luminance(ink)) + 0.05) / (min(lum, luminance(ink)) + 0.05)
    )


spend_text = [f"${v / 1000:.1f}M" if v >= 1000 else f"${v:.0f}K" for v in values]
shares = values / values.sum() * 100

fig = go.Figure()
for group_name in group_names:
    idx = np.flatnonzero(group_idx == group_names.index(group_name))
    fig.add_trace(
        go.Scatter(
            x=pos[idx, 0],
            y=pos[idx, 1],
            mode="markers",
            name=group_name,
            marker={
                "size": marker_diameters[idx],
                "sizemode": "diameter",
                "color": group_colors[group_name],
                "opacity": 0.92,
                "line": {"color": PAGE_BG, "width": 2},
            },
            text=[labels[i] for i in idx],
            customdata=np.column_stack([[spend_text[i] for i in idx], shares[idx].round(1)]),
            hovertemplate="<b>%{text}</b> (%{fullData.name})<br>Spend: %{customdata[0]}/month<br>Share: %{customdata[1]}%<extra></extra>",
        )
    )

# Labels inside circles, only where the circle can hold them
for i in range(n):
    d = marker_diameters[i]
    font_size = max(8, min(12, round(d * 0.13)))
    if d < 0.6 * font_size * len(labels[i]):
        continue
    text = f"<b>{labels[i]}</b>" + (f"<br>{spend_text[i]}" if d > 75 else "")
    fig.add_annotation(
        x=pos[i, 0],
        y=pos[i, 1],
        text=text,
        showarrow=False,
        font={"size": font_size, "color": label_color(group_colors[df[CATEGORY].iloc[i]]), "family": "Arial"},
    )

title_text = "Cloud Spend by Service · bubble-packed · python · plotly · anyplot.ai"
title_fontsize = round(14 * 67 / len(title_text)) if len(title_text) > 67 else 14

fig.update_layout(
    autosize=False,
    title={"text": title_text, "font": {"size": title_fontsize, "color": INK}, "x": 0.5, "xanchor": "center"},
    xaxis={"visible": False, "range": [x_lo, x_hi]},
    yaxis={"visible": False, "range": [y_lo, y_hi], "scaleanchor": "x", "scaleratio": 1},
    template="plotly_white",
    legend={
        "title": {"text": CATEGORY, "font": {"size": 11, "color": INK_SOFT}},
        "font": {"size": 11, "family": "Arial", "color": INK_SOFT},
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
        "orientation": "h",
        "yanchor": "top",
        "y": -0.01,
        "xanchor": "center",
        "x": 0.5,
        "itemsizing": "constant",
    },
    margin={"l": m_l, "r": m_r, "t": m_t, "b": m_b},
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
)

fig.write_image(f"plot-{THEME}.png", width=fig_w, height=fig_h, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn", full_html=True)
