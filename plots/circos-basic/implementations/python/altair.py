""" anyplot.ai
circos-basic: Circos Plot
Library: altair 6.3.0 | Python 3.14.10
Quality: 77/100 | Updated: 2026-11-21
"""

import colorsys
import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per module in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
SOURCE = "Source module"  # role: source
TARGET = "Target module"  # role: target
VALUE = "Dependencies"  # role: value
SOURCE_SIZE = "Source module size"  # role: segment_size
TARGET_SIZE = "Target module size"  # role: extra
SOURCE_TRACK = "Activity"  # role: track_data
TARGET_TRACK = "Target activity"  # role: extra

# Data: replace with your own edge list (source, target, value) that also carries each end's
# segment size and inner-track value
np.random.seed(42)
sizes = dict(
    zip(
        ["Core", "API", "Database", "Auth", "Cache", "Queue", "Logger", "Config"],
        [25, 20, 18, 15, 12, 10, 8, 6],
        strict=True,
    )
)
tracks = dict(zip(sizes, np.random.uniform(0.3, 1.0, len(sizes)), strict=True))
df = pd.DataFrame(
    [
        ("Core", "API", 15),
        ("Core", "Database", 12),
        ("Core", "Logger", 8),
        ("API", "Auth", 10),
        ("API", "Cache", 8),
        ("Database", "Cache", 6),
        ("Database", "Logger", 5),
        ("Auth", "Logger", 4),
        ("Queue", "Logger", 7),
        ("Queue", "Database", 5),
        ("Config", "Core", 9),
        ("Config", "Logger", 3),
        ("Cache", "Logger", 4),
        ("API", "Queue", 6),
    ],
    columns=[SOURCE, TARGET, VALUE],
)
df[SOURCE_SIZE] = df[SOURCE].map(sizes)
df[TARGET_SIZE] = df[TARGET].map(sizes)
df[SOURCE_TRACK] = df[SOURCE].map(tracks)
df[TARGET_TRACK] = df[TARGET].map(tracks)

# Plot: geometry is derived from df
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
# One row per module (largest first), collected from both ends of every edge
ends = [(SOURCE, SOURCE_SIZE, SOURCE_TRACK), (TARGET, TARGET_SIZE, TARGET_TRACK)]
nodes = (
    pd.concat([df[list(cols)].set_axis(["segment", "size", "track"], axis=1) for cols in ends])
    .drop_duplicates("segment")
    .sort_values("size", ascending=False, kind="stable")
    .reset_index(drop=True)
)
names = list(nodes["segment"])
n_seg = len(names)
colors = {name: IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] for i, name in enumerate(names)}


def darker(hex_color):
    h, light, s = colorsys.rgb_to_hls(*(int(hex_color[i : i + 2], 16) / 255 for i in (1, 3, 5)))
    r, g, b = colorsys.hls_to_rgb(h, light * 0.6, s)
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"


# Inner view in pixels; the circle is drawn in this coordinate system
W, H = 440, 400
cx, cy = W / 2, H / 2
r_out, r_ring = 175, 158
r_track_out, r_track_in = 150, 122
r_ribbon = 118

gap = 0.05
share = nodes["size"] / nodes["size"].sum()
spans = share.to_numpy() * (2 * np.pi - gap * n_seg)
arcs = {}
angle = np.pi / 2
for name, span in zip(names, spans, strict=True):
    arcs[name] = (angle, angle - span)  # (start, end), clockwise from the top
    angle -= span + gap


def band(name, r_low, r_high, n=40):
    """Closed polygon of an annular sector for one segment."""
    start, end = arcs[name]
    th = np.linspace(end, start, n)
    xs = np.concatenate([cx + r_high * np.cos(th), cx + r_low * np.cos(th[::-1])])
    ys = np.concatenate([cy + r_high * np.sin(th), cy + r_low * np.sin(th[::-1])])
    return pd.DataFrame({"segment": name, "x": xs, "y": ys, "order": np.arange(2 * n)})


ring_df = pd.concat([band(name, r_ring, r_out) for name in names])
track_df = pd.concat(
    [
        band(name, r_track_in, r_track_in + (r_track_out - r_track_in) * val)
        for name, val in zip(names, nodes["track"] / nodes["track"].max(), strict=True)
    ]
)


def bezier(p0, p2, n=30):
    t = np.linspace(0, 1, n)[:, None]
    return (1 - t) ** 2 * np.array(p0) + 2 * (1 - t) * t * np.array([cx, cy]) + t**2 * np.array(p2)


def on_circle(a):
    return np.array([cx + r_ribbon * np.cos(a), cy + r_ribbon * np.sin(a)])


vmax = df[VALUE].max()
ribbon_parts = []
for k, row in enumerate(df.dropna(subset=[VALUE]).itertuples(index=False)):
    src, tgt, val = row[0], row[1], row[2]
    m1, m2 = np.mean(arcs[src]), np.mean(arcs[tgt])
    half = max(0.04, val / vmax * 0.12)  # half-width in radians, proportional to the value
    a1, b1, a2, b2 = m1 - half, m1 + half, m2 - half, m2 + half
    pts = np.vstack(
        [
            [on_circle(a) for a in np.linspace(a1, b1, 8)],
            bezier(on_circle(b1), on_circle(a2)),
            [on_circle(a) for a in np.linspace(a2, b2, 8)],
            bezier(on_circle(b2), on_circle(a1)),
        ]
    )
    ribbon_parts.append(
        pd.DataFrame(
            {
                "ribbon": f"{k}",
                "source": src,
                "target": tgt,
                "value": val,
                "x": pts[:, 0],
                "y": pts[:, 1],
                "order": np.arange(len(pts)),
            }
        )
    )
ribbons_df = pd.concat(ribbon_parts)

label_df = pd.DataFrame(
    [
        {
            "segment": name,
            "x": cx + (r_out + 20) * np.cos(np.mean(arcs[name])),
            "y": cy + (r_out + 20) * np.sin(np.mean(arcs[name])),
        }
        for name in names
    ]
)
caption_df = pd.DataFrame({"x": [cx], "y": [cy], "text": [f"Inner ring: {SOURCE_TRACK.lower()} per module"]})

x_enc = alt.X("x:Q", scale=alt.Scale(domain=[0, W]), axis=None)
y_enc = alt.Y("y:Q", scale=alt.Scale(domain=[0, H]), axis=None)


def seg_color(palette, legend=None):
    return alt.Color(
        "segment:N", scale=alt.Scale(domain=names, range=palette), legend=legend, title="Modules", sort=None
    )


ring_chart = (
    alt.Chart(ring_df)
    .mark_line(filled=True, strokeWidth=0.6, stroke=INK_SOFT)
    .encode(x=x_enc, y=y_enc, color=seg_color([colors[n] for n in names]), detail="segment:N", order="order:Q")
)
track_chart = (
    alt.Chart(track_df)
    .mark_line(filled=True, strokeWidth=0.8, stroke=INK_SOFT, opacity=0.9)
    .encode(x=x_enc, y=y_enc, color=seg_color([darker(colors[n]) for n in names]), detail="segment:N", order="order:Q")
)
ribbon_chart = (
    alt.Chart(ribbons_df)
    .mark_line(filled=True, opacity=0.5, strokeWidth=0)
    .encode(
        x=x_enc,
        y=y_enc,
        color=alt.Color("source:N", scale=alt.Scale(domain=names, range=[colors[n] for n in names]), legend=None),
        detail="ribbon:N",
        order="order:Q",
        tooltip=[
            alt.Tooltip("source:N", title=SOURCE),
            alt.Tooltip("target:N", title=TARGET),
            alt.Tooltip("value:Q", title=VALUE),
        ],
    )
)
label_chart = (
    alt.Chart(label_df).mark_text(fontSize=12, fontWeight="bold", color=INK).encode(x=x_enc, y=y_enc, text="segment:N")
)
caption_chart = (
    alt.Chart(caption_df)
    .mark_text(fontSize=9, color=INK_SOFT, baseline="middle")
    .encode(x=x_enc, y=y_enc, text="text:N")
)

TITLE = "circos-basic · python · altair · anyplot.ai"
chart = (
    alt.layer(ribbon_chart, track_chart, ring_chart, label_chart, caption_chart)
    .resolve_scale(color="independent")
    .properties(width=W, height=H, title=alt.Title(text=TITLE, fontSize=16, anchor="middle"), background=PAGE_BG)
    .configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_title(color=INK)
)

chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Pad (never crop) to the 2400 x 2400 square canvas
TW, TH = 2400, 2400
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TW or img.height > TH:
    raise SystemExit(f"altair rendered {img.width}x{img.height}, larger than {TW}x{TH}; shrink W and H")
canvas = Image.new("RGB", (TW, TH), PAGE_BG)
canvas.paste(img, ((TW - img.width) // 2, (TH - img.height) // 2))
canvas.save(f"plot-{THEME}.png")
