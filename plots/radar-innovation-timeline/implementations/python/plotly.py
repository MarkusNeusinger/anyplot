""" anyplot.ai
radar-innovation-timeline: Innovation Radar with Time-Horizon Rings
Library: plotly 6.7.0 | Python 3.13.13
Quality: 75/100 | Updated: 2026-05-29
"""

import sys


sys.path = sys.path[1:]  # prevent this file from shadowing the installed plotly package

import os

import numpy as np
import plotly.graph_objects as go


# Theme tokens (Imprint palette — see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

np.random.seed(42)

# Data — technology innovations across sectors and time horizons
sectors = ["AI & ML", "Cloud & Infra", "Sustainability", "Biotech"]
rings = ["Adopt", "Trial", "Assess", "Hold"]
ring_radii = {"Adopt": 1.3, "Trial": 2.3, "Assess": 3.3, "Hold": 4.3}
ring_marker_sizes = {"Adopt": 18, "Trial": 14, "Assess": 11, "Hold": 9}
ring_boundaries = [1.8, 2.8, 3.8, 4.8]

innovations = [
    # AI & ML
    {"name": "LLM Agents", "sector": "AI & ML", "ring": "Adopt", "textpos": "top center"},
    {"name": "RAG Pipelines", "sector": "AI & ML", "ring": "Adopt", "textpos": "bottom left"},
    {"name": "Multimodal Models", "sector": "AI & ML", "ring": "Trial", "textpos": "top left"},
    {"name": "AI Code Review", "sector": "AI & ML", "ring": "Trial", "textpos": "bottom right"},
    {"name": "Neuromorphic Chips", "sector": "AI & ML", "ring": "Assess", "textpos": "top center"},
    {"name": "Autonomous Research", "sector": "AI & ML", "ring": "Hold", "textpos": "bottom center"},
    {"name": "Quantum ML", "sector": "AI & ML", "ring": "Hold", "textpos": "top center"},
    # Cloud & Infra
    {"name": "Platform Engineering", "sector": "Cloud & Infra", "ring": "Adopt", "textpos": "bottom right"},
    {"name": "FinOps", "sector": "Cloud & Infra", "ring": "Adopt", "textpos": "top right"},
    {"name": "WebAssembly", "sector": "Cloud & Infra", "ring": "Trial", "textpos": "top center"},
    {"name": "Edge Computing", "sector": "Cloud & Infra", "ring": "Trial", "textpos": "bottom center"},
    {"name": "Confidential Computing", "sector": "Cloud & Infra", "ring": "Assess", "textpos": "top right"},
    {"name": "Serverless GPUs", "sector": "Cloud & Infra", "ring": "Assess", "textpos": "bottom right"},
    {"name": "Decentralized Cloud", "sector": "Cloud & Infra", "ring": "Hold", "textpos": "top center"},
    # Sustainability
    {"name": "Carbon Tracking APIs", "sector": "Sustainability", "ring": "Adopt", "textpos": "top left"},
    {"name": "Green Software", "sector": "Sustainability", "ring": "Trial", "textpos": "bottom right"},
    {"name": "Digital Product Passports", "sector": "Sustainability", "ring": "Trial", "textpos": "top left"},
    {"name": "Circular Economy Platforms", "sector": "Sustainability", "ring": "Assess", "textpos": "bottom right"},
    {"name": "Climate AI", "sector": "Sustainability", "ring": "Assess", "textpos": "top left"},
    {"name": "Fusion Energy Tech", "sector": "Sustainability", "ring": "Hold", "textpos": "top center"},
    # Biotech — text positions flipped inward (rightward) to prevent left-edge clipping
    {"name": "mRNA Therapeutics", "sector": "Biotech", "ring": "Adopt", "textpos": "top center"},
    {"name": "CRISPR Diagnostics", "sector": "Biotech", "ring": "Trial", "textpos": "bottom right"},
    {"name": "Digital Twins (Health)", "sector": "Biotech", "ring": "Assess", "textpos": "bottom right"},
    {"name": "Synthetic Biology", "sector": "Biotech", "ring": "Assess", "textpos": "top right"},
    {"name": "Brain-Computer Interfaces", "sector": "Biotech", "ring": "Hold", "textpos": "bottom center"},
    {"name": "Longevity Engineering", "sector": "Biotech", "ring": "Hold", "textpos": "top right"},
]

# Sector colors using Imprint palette canonical order
sector_colors = {
    "AI & ML": IMPRINT_PALETTE[0],  # #009E73 brand green
    "Cloud & Infra": IMPRINT_PALETTE[1],  # #C475FD lavender
    "Sustainability": IMPRINT_PALETTE[2],  # #4467A3 blue
    "Biotech": IMPRINT_PALETTE[3],  # #BD8233 ochre
}

sector_symbols = {"AI & ML": "circle", "Cloud & Infra": "diamond", "Sustainability": "square", "Biotech": "triangle-up"}

# 270° layout, 4 equal sectors
sector_span = 270 / len(sectors)
sector_starts = {s: i * sector_span for i, s in enumerate(sectors)}

# Compute item positions within each sector ring
items_by_sector = {s: [] for s in sectors}

for sector in sectors:
    start_angle = sector_starts[sector]
    sector_items = [inn for inn in innovations if inn["sector"] == sector]

    for ring in rings:
        ring_items = [it for it in sector_items if it["ring"] == ring]
        if not ring_items:
            continue
        n = len(ring_items)
        # Wider padding reduces crowding in dense inner rings
        padding = sector_span * 0.22
        usable_span = sector_span - 2 * padding
        for idx, item in enumerate(ring_items):
            if n == 1:
                angle = start_angle + sector_span / 2
            else:
                angle = start_angle + padding + usable_span * idx / (n - 1)
            base_r = ring_radii[ring]
            # Tighter jitter for Adopt ring to reduce crowding near center
            jitter_range = 0.10 if ring == "Adopt" else 0.15
            jitter = np.random.uniform(-jitter_range, jitter_range)
            items_by_sector[sector].append(
                {"name": item["name"], "ring": ring, "angle": angle, "r": base_r + jitter, "textpos": item["textpos"]}
            )

# Ring fill colors — theme-adaptive, Imprint green tinted bands
if THEME == "light":
    ring_fill_colors = ["rgba(0,158,115,0.10)", "rgba(0,158,115,0.06)", "rgba(0,158,115,0.04)", "rgba(0,158,115,0.02)"]
else:
    ring_fill_colors = ["rgba(0,158,115,0.18)", "rgba(0,158,115,0.10)", "rgba(0,158,115,0.06)", "rgba(0,158,115,0.03)"]

ring_line_color = "rgba(26,26,23,0.12)" if THEME == "light" else "rgba(240,239,232,0.12)"
sector_line_color = "rgba(26,26,23,0.18)" if THEME == "light" else "rgba(240,239,232,0.18)"

# Plot
fig = go.Figure()

# Ring background fills — non-overlapping bands from center outward
theta_fill = np.linspace(0, 270, 200).tolist()
ring_bands = [(0, ring_boundaries[0])] + list(zip(ring_boundaries[:-1], ring_boundaries[1:], strict=False))
for i, (r_inner, r_outer) in enumerate(ring_bands):
    fig.add_trace(
        go.Scatterpolar(
            r=[r_outer] * len(theta_fill) + [r_inner] * len(theta_fill),
            theta=theta_fill + theta_fill[::-1],
            fill="toself",
            fillcolor=ring_fill_colors[i],
            line={"width": 0},
            showlegend=False,
            hoverinfo="skip",
        )
    )

# Ring boundary lines
for radius in ring_boundaries:
    theta_circle = np.linspace(0, 270, 200)
    fig.add_trace(
        go.Scatterpolar(
            r=np.full_like(theta_circle, radius).tolist(),
            theta=theta_circle.tolist(),
            mode="lines",
            line={"color": ring_line_color, "width": 1.2},
            showlegend=False,
            hoverinfo="skip",
        )
    )

# Sector divider lines
for angle in [sector_starts[s] for s in sectors] + [270]:
    fig.add_trace(
        go.Scatterpolar(
            r=[0, 5.2],
            theta=[angle, angle],
            mode="lines",
            line={"color": sector_line_color, "width": 1, "dash": "dot"},
            showlegend=False,
            hoverinfo="skip",
        )
    )

# Innovation items per sector — marker size encodes time horizon priority
for sector in sectors:
    items = items_by_sector[sector]
    color = sector_colors[sector]
    fig.add_trace(
        go.Scatterpolar(
            r=[it["r"] for it in items],
            theta=[it["angle"] for it in items],
            mode="markers+text",
            marker={
                "size": [ring_marker_sizes[it["ring"]] for it in items],
                "color": color,
                "symbol": sector_symbols[sector],
                "line": {"color": PAGE_BG, "width": 2},
                "opacity": [1.0 if it["ring"] == "Adopt" else 0.82 for it in items],
            },
            text=[f"<b>{it['name']}</b>" if it["ring"] == "Adopt" else it["name"] for it in items],
            textposition=[it["textpos"] for it in items],
            textfont={"size": 13, "color": color},
            name=sector,
            legendgroup=sector,
            hovertemplate="%{text}<br>Ring: %{customdata}<extra>" + sector + "</extra>",
            customdata=[it["ring"] for it in items],
        )
    )

# Ring labels — staggered just outside the 270° arc
ring_label_data = [
    ("Adopt (Now)", ring_radii["Adopt"], 280),
    ("Trial (0–1 yr)", ring_radii["Trial"], 283),
    ("Assess (1–3 yr)", ring_radii["Assess"], 286),
    ("Hold (3+ yr)", ring_radii["Hold"], 289),
]
for label, radius, angle in ring_label_data:
    fig.add_trace(
        go.Scatterpolar(
            r=[radius],
            theta=[angle],
            mode="text",
            text=[f"<b>{label}</b>"],
            textfont={"size": 12, "color": INK_SOFT},
            textposition="middle right",
            showlegend=False,
            hoverinfo="skip",
        )
    )

# Sector header labels — computed in paper coordinates to avoid polar-domain clipping
# Polar domain: x=[0.04, 0.64], y=[0.03, 0.93]; circle radius = min(x_half, y_half) = 0.30
POLAR_CX = 0.34  # (0.04 + 0.64) / 2
POLAR_CY = 0.48  # (0.03 + 0.93) / 2
POLAR_R = 0.30  # min((0.64-0.04)/2, (0.93-0.03)/2) = min(0.30, 0.45)
R_MAX = 6.2
HEADER_R = 5.5  # just beyond outermost boundary (4.8), within radial range

sector_header_annotations = []
for sector in sectors:
    mid_deg = sector_starts[sector] + sector_span / 2
    mid_rad = np.radians(mid_deg)
    frac = HEADER_R / R_MAX
    px = float(POLAR_CX + frac * POLAR_R * np.sin(mid_rad))
    py = float(POLAR_CY + frac * POLAR_R * np.cos(mid_rad))
    sector_header_annotations.append(
        {
            "text": f"<b>{sector}</b>",
            "x": px,
            "y": py,
            "xref": "paper",
            "yref": "paper",
            "xanchor": "center",
            "yanchor": "middle",
            "showarrow": False,
            "font": {"size": 17, "color": sector_colors[sector]},
        }
    )

# Title — n=56 chars < 67 baseline so default fontsize applies
title_text = "radar-innovation-timeline · python · plotly · anyplot.ai"
n_chars = len(title_text)
title_fontsize = max(11, round(16 * 67 / n_chars)) if n_chars > 67 else 16

fig.update_layout(
    autosize=False,
    title={
        "text": (
            title_text + "<br><sup style='color:" + INK_MUTED + "; font-weight:normal'>"
            "Technology adoption radar — inner rings = near-term, outer = longer horizon"
            "</sup>"
        ),
        "font": {"size": title_fontsize, "color": INK},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.98,
    },
    polar={
        "radialaxis": {"visible": False, "range": [0, 6.2]},
        "angularaxis": {"visible": False, "direction": "clockwise", "rotation": 90},
        "bgcolor": PAGE_BG,
        "domain": {"x": [0.04, 0.64], "y": [0.03, 0.93]},
    },
    legend={
        "font": {"size": 12, "color": INK_SOFT},
        "x": 0.66,
        "y": 0.60,
        "xanchor": "left",
        "yanchor": "middle",
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
        "title": {"text": "<b>Sectors</b>", "font": {"size": 14, "color": INK}},
    },
    paper_bgcolor=PAGE_BG,
    margin={"l": 30, "r": 30, "t": 80, "b": 40},
    annotations=sector_header_annotations
    + [
        {
            "text": (
                "<b>Time Horizons</b><br>"
                "● <b>Adopt</b> — ready now<br>"
                "● <b>Trial</b> — evaluating 0–1 yr<br>"
                "● <b>Assess</b> — exploring 1–3 yr<br>"
                "● <b>Hold</b> — future watch 3+ yr"
            ),
            "x": 0.66,
            "y": 0.38,
            "xref": "paper",
            "yref": "paper",
            "xanchor": "left",
            "yanchor": "top",
            "showarrow": False,
            "font": {"size": 12, "color": INK_SOFT},
            "bgcolor": ELEVATED_BG,
            "bordercolor": INK_SOFT,
            "borderwidth": 1,
            "borderpad": 8,
        }
    ],
)

# Save — square canvas (2400×2400) suits this symmetric radar chart
fig.write_image(f"plot-{THEME}.png", width=600, height=600, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
