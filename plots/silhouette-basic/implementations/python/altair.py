""" anyplot.ai
silhouette-basic: Silhouette Plot
Library: altair 6.3.0 | Python 3.14.10
Quality: 86/100 | Updated: 2026-11-09
"""

import os

import altair as alt
import pandas as pd
from PIL import Image
from sklearn.cluster import KMeans
from sklearn.datasets import load_iris
from sklearn.metrics import silhouette_samples


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per cluster in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
SAMPLE = "Sample"  # role: samples
CLUSTER = "Cluster"  # role: cluster_labels
SILHOUETTE = "Silhouette coefficient"  # role: silhouette_values

# Data: replace this block with your own table, for example df = pd.read_csv("clusters.csv")
features = load_iris().data
labels = KMeans(n_clusters=3, random_state=42, n_init=10).fit_predict(features)
df = pd.DataFrame(
    {
        SAMPLE: [f"Iris {i + 1}" for i in range(len(features))],
        CLUSTER: labels,
        SILHOUETTE: silhouette_samples(features, labels),
    }
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
silhouette_avg = df[SILHOUETTE].mean()
gap = max(2, round(len(df) * 0.03))

# Sort within each cluster and stack the clusters bottom-up with a gap between blocks
ordered = df.dropna(subset=[SILHOUETTE]).sort_values([CLUSTER, SILHOUETTE]).reset_index(drop=True)
cluster_names = [f"Cluster {c}" for c in ordered[CLUSTER].unique()]
ordered["cluster_name"] = ordered[CLUSTER].map(lambda c: f"Cluster {c}")
ordered["block"] = ordered.groupby(CLUSTER, sort=False).ngroup()
ordered["y"] = ordered.index + ordered["block"] * gap
ordered["y2"] = ordered["y"] + 1.15  # slight overlap hides anti-aliasing seams between neighbouring bars

summary = ordered.groupby("cluster_name", sort=False).agg(
    y_mid=("y", "mean"), x_tip=(SILHOUETTE, "max"), avg=(SILHOUETTE, "mean")
)
summary = summary.reset_index()
summary["label"] = summary["cluster_name"] + summary["avg"].map(lambda v: f" · avg {v:.2f}")

x_low = min(0.0, ordered[SILHOUETTE].min())
x_max = ordered[SILHOUETTE].max()
x_high = max(1.0, x_max + 0.2 * (x_max - x_low))  # room right of the longest bar for its cluster label
x_scale = alt.Scale(domain=[x_low - 0.05 * (x_high - x_low), x_high])

bars = (
    alt.Chart(ordered)
    .mark_rect()
    .encode(
        x=alt.X(SILHOUETTE.translate(ESCAPE), type="quantitative", title=SILHOUETTE, scale=x_scale),
        x2=alt.datum(0),
        y=alt.Y("y", type="quantitative", axis=None),
        y2="y2",
        color=alt.Color(
            "cluster_name",
            type="nominal",
            title=CLUSTER,
            sort=cluster_names,
            scale=alt.Scale(domain=cluster_names, range=IMPRINT_PALETTE),
        ),
        tooltip=[
            alt.Tooltip(SAMPLE.translate(ESCAPE), type="nominal", title=SAMPLE),
            alt.Tooltip("cluster_name", type="nominal", title=CLUSTER),
            alt.Tooltip(SILHOUETTE.translate(ESCAPE), type="quantitative", title=SILHOUETTE, format=".3f"),
        ],
    )
)

avg_line = (
    alt.Chart(pd.DataFrame({"avg": [silhouette_avg]}))
    .mark_rule(color=INK, strokeWidth=2, strokeDash=[8, 5])
    .encode(x=alt.X("avg", type="quantitative"), tooltip=[alt.Tooltip("avg", title="Average", format=".3f")])
)

avg_label = (
    alt.Chart(pd.DataFrame({"avg": [silhouette_avg], "label": [f"Overall avg {silhouette_avg:.2f}"]}))
    .mark_text(align="left", baseline="bottom", dx=6, dy=-4, fontSize=11, color=INK, y="height")
    .encode(x=alt.X("avg", type="quantitative"), text="label")
)

cluster_labels = (
    alt.Chart(summary)
    .mark_text(align="left", baseline="middle", dx=10, fontSize=11, fontWeight="bold")
    .encode(
        x=alt.X("x_tip", type="quantitative"),
        y=alt.Y("y_mid", type="quantitative"),
        text="label",
        color=alt.Color("cluster_name", type="nominal", legend=None),
    )
)

title = "silhouette-basic · python · altair · anyplot.ai"
chart = (
    alt.layer(bars, avg_line, avg_label, cluster_labels)
    .properties(
        width=660,
        height=340,
        background=PAGE_BG,
        padding={"left": 10, "right": 10, "top": 10, "bottom": 10},
        title=alt.Title(title, fontSize=16, anchor="start"),
    )
    .configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.15,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=10,
        titleFontSize=12,
    )
    .configure_axisY(grid=False)
    .configure_title(color=INK)
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=10,
        titleFontSize=10,
        padding=8,
    )
)

chart.save(f"plot-{THEME}.png", scale_factor=4.0)

TW, TH = 3200, 1800
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
_w, _h = _img.size
if _w > TW or _h > TH:
    raise SystemExit(
        f"altair vl-convert produced {_w}×{_h}, exceeds target {TW}×{TH}. "
        f"Shrink chart .properties(width=, height=) values and re-render."
    )
if _w < TW or _h < TH:
    _canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _w) // 2, (TH - _h) // 2))
    _canvas.save(f"plot-{THEME}.png")

chart.save(f"plot-{THEME}.html")
