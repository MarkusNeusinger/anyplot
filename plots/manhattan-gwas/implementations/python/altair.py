"""anyplot.ai
manhattan-gwas: Manhattan Plot for GWAS
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-15
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
GENOME_WIDE = 5e-8  # conventional genome-wide significance level
SUGGESTIVE = 1e-5  # conventional suggestive significance level

# Columns: set these to your table's column names
CHROMOSOME = "Chromosome"  # role: chromosome
POSITION = "Position (bp)"  # role: position
P_VALUE = "P-value"  # role: p_value

# Data: replace this block with your own table, for example df = pd.read_csv("gwas.csv")
np.random.seed(42)
chrom_mb = {  # approximate human chromosome sizes in Mb
    "1": 249,
    "2": 243,
    "3": 198,
    "4": 191,
    "5": 182,
    "6": 171,
    "7": 159,
    "8": 145,
    "9": 138,
    "10": 134,
    "11": 135,
    "12": 133,
    "13": 114,
    "14": 107,
    "15": 102,
    "16": 90,
    "17": 83,
    "18": 80,
    "19": 59,
    "20": 64,
    "21": 47,
    "22": 51,
}
frames = []
for chrom, mb in chrom_mb.items():
    n_snps = mb * 20  # about 20 variants per Mb
    positions = np.sort(np.random.randint(1, mb * 1_000_000, n_snps))
    pvalues = np.random.uniform(0.001, 1.0, n_snps)
    if chrom in ("2", "6", "8", "15"):  # associated loci
        hits = np.random.choice(n_snps, np.random.randint(5, 15), replace=False)
        pvalues[hits] = 10 ** np.random.uniform(-10, -7, len(hits))
    if chrom in ("3", "11", "19"):  # suggestive signals
        hits = np.random.choice(n_snps, np.random.randint(3, 8), replace=False)
        pvalues[hits] = 10 ** np.random.uniform(-6, -5, len(hits))
    frames.append(pd.DataFrame({CHROMOSOME: chrom, POSITION: positions, P_VALUE: pvalues}))
df = pd.concat(frames, ignore_index=True)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
CUM_POS = "Cumulative position (bp)"
NEG_LOG_P = "-log₁₀(p-value)"
ALTERNATE = "Alternating color"
SIGNIFICANT = "Genome-wide significant"

# Chromosomes laid end to end, in the data's order
extent = df.groupby(CHROMOSOME, sort=False)[POSITION].max()
offset = extent.cumsum() - extent
df[CUM_POS] = df[POSITION] + df[CHROMOSOME].map(offset)
df[NEG_LOG_P] = -np.log10(df[P_VALUE])
df[ALTERNATE] = df[CHROMOSOME].map({c: i % 2 for i, c in enumerate(extent.index)})
gw_line_y = -np.log10(GENOME_WIDE)
sug_line_y = -np.log10(SUGGESTIVE)
df[SIGNIFICANT] = df[NEG_LOG_P] > gw_line_y

genome_end = float(extent.sum())
x_scale = alt.Scale(domain=[0, genome_end], nice=False)
y_low = min(0.0, float(df[NEG_LOG_P].min()))
y_high = float(df[NEG_LOG_P].max())
y_top = y_high + 0.05 * (y_high - y_low)
labels = pd.DataFrame({CHROMOSOME: extent.index, CUM_POS: offset.to_numpy() + extent.to_numpy() / 2})

points = (
    alt.Chart(df)
    .mark_circle(opacity=0.65)
    .encode(
        x=alt.X(
            CUM_POS.translate(ESCAPE),
            type="quantitative",
            title=None,
            scale=x_scale,
            axis=alt.Axis(labels=False, ticks=False, grid=False),
        ),
        y=alt.Y(
            NEG_LOG_P.translate(ESCAPE),
            type="quantitative",
            title=NEG_LOG_P,
            scale=alt.Scale(domain=[y_low, y_top], nice=False),
        ),
        color=alt.Color(
            ALTERNATE.translate(ESCAPE),
            type="nominal",
            scale=alt.Scale(domain=[0, 1], range=[IMPRINT_PALETTE[0], IMPRINT_PALETTE[2]]),
            legend=None,
        ),
        size=alt.condition(
            alt.datum[SIGNIFICANT] == True,  # noqa: E712 - Vega-Lite expression, not a Python comparison
            alt.value(34),
            alt.value(7),
        ),
        tooltip=[
            alt.Tooltip(CHROMOSOME.translate(ESCAPE), type="nominal", title=CHROMOSOME),
            alt.Tooltip(POSITION.translate(ESCAPE), type="quantitative", title=POSITION, format=","),
            alt.Tooltip(P_VALUE.translate(ESCAPE), type="quantitative", title=P_VALUE, format=".2e"),
        ],
    )
)

rules = pd.DataFrame({"y": [gw_line_y, sug_line_y], "label": ["genome-wide 5×10⁻⁸", "suggestive 1×10⁻⁵"]})
gw_line = (
    alt.Chart(rules.iloc[[0]])
    .mark_rule(strokeDash=[10, 5], color=INK, strokeWidth=1.4)
    .encode(y=alt.Y("y:Q", scale=alt.Scale(domain=[y_low, y_top], nice=False)))
)
sug_line = (
    alt.Chart(rules.iloc[[1]])
    .mark_rule(strokeDash=[3, 4], color=INK_MUTED, strokeWidth=1.0)
    .encode(y=alt.Y("y:Q", scale=alt.Scale(domain=[y_low, y_top], nice=False)))
)
rule_text = (
    alt.Chart(rules)
    .mark_text(align="left", baseline="bottom", dx=4, dy=-2, fontSize=9, color=INK_SOFT)
    .encode(x=alt.value(0), y=alt.Y("y:Q", scale=alt.Scale(domain=[y_low, y_top], nice=False)), text="label:N")
)

main = alt.layer(points, gw_line, sug_line, rule_text).properties(width=620, height=300)

chrom_text = (
    alt.Chart(labels)
    .mark_text(fontSize=9, baseline="top", color=INK_SOFT)
    .encode(
        x=alt.X(CUM_POS.translate(ESCAPE), type="quantitative", scale=x_scale, axis=None),
        text=alt.Text(CHROMOSOME.translate(ESCAPE), type="nominal"),
    )
    .properties(width=620, height=14)
)

chart = (
    alt.vconcat(main, chrom_text, spacing=2)
    .properties(
        title=alt.Title(
            "manhattan-gwas · python · altair · anyplot.ai",
            subtitle="Simulated GWAS: variants ordered by chromosome, 22 autosomes",
            anchor="middle",
        ),
        background=PAGE_BG,
        padding={"left": 8, "right": 8, "top": 6, "bottom": 6},
    )
    .configure_view(fill=PAGE_BG, stroke=None)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=10,
        titleFontSize=12,
    )
    .configure_title(fontSize=16, color=INK, subtitleFontSize=11, subtitleColor=INK_SOFT)
)

# Save, then pad (never crop) to the 3200 x 1800 target
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

TW, TH = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
w, h = img.size
if w > TW or h > TH:
    raise SystemExit(f"altair produced {w}x{h}, exceeds target {TW}x{TH}; shrink width/height")
if (w, h) != (TW, TH):
    canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    canvas.paste(img, ((TW - w) // 2, (TH - h) // 2))
    canvas.save(f"plot-{THEME}.png")
