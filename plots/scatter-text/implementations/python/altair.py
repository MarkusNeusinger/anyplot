"""anyplot.ai
scatter-text: Scatter Plot with Text Labels Instead of Points
Library: altair 6.1.0 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-17
"""

import os

import altair as alt
import pandas as pd
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: continuous data uses the two-stop imprint_seq ramp (green to blue)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
IMPRINT_SEQ = [IMPRINT_PALETTE[0], IMPRINT_PALETTE[2]]

# Columns: set these to your table's column names
LANGUAGE = "Language"  # role: label
AGE = "Language age (years since creation)"  # role: x
POPULARITY = "Relative popularity score"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("languages.csv")
df = pd.DataFrame(
    {
        LANGUAGE: [
            "Python", "JavaScript", "Java", "C++", "Ruby", "Go", "Rust", "Swift", "Kotlin", "TypeScript",
            "Scala", "R", "Julia", "Perl", "PHP", "C#", "Haskell", "Elixir", "Clojure", "Dart",
            "Lua", "MATLAB", "Fortran", "COBOL", "Lisp", "Erlang", "F#", "Groovy",
        ],
        AGE: [33, 29, 26, 41, 29, 15, 9, 10, 13, 8, 20, 31, 12, 37, 30, 24, 34, 13, 17, 18, 31, 40, 68, 65, 66, 38, 19, 21],
        POPULARITY: [98, 88, 82, 68, 42, 62, 52, 58, 48, 75, 32, 45, 28, 18, 55, 72, 12, 15, 9, 22, 25, 38, 8, 4, 6, 14, 35, 20],
    }
)  # fmt: skip

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
YEAR_CREATED = "Year created"
plot_df = df.copy()
plot_df[YEAR_CREATED] = pd.Timestamp.now().year - plot_df[AGE]

hover = alt.selection_point(on="pointerover", nearest=True, empty=False)

chart = (
    alt.Chart(plot_df)
    .mark_text(fontWeight="bold", align="center", baseline="middle")
    .encode(
        x=alt.X(
            AGE.translate(ESCAPE),
            type="quantitative",
            title=AGE,
            scale=alt.Scale(domain=[0, plot_df[AGE].max() * 1.08]),
        ),
        y=alt.Y(
            POPULARITY.translate(ESCAPE),
            type="quantitative",
            title=POPULARITY,
            scale=alt.Scale(domain=[0, plot_df[POPULARITY].max() * 1.06]),
        ),
        text=alt.Text(LANGUAGE.translate(ESCAPE), type="nominal"),
        color=alt.Color(
            POPULARITY.translate(ESCAPE),
            type="quantitative",
            title="Popularity",
            scale=alt.Scale(range=IMPRINT_SEQ),
            legend=alt.Legend(gradientLength=150, gradientThickness=12),
        ),
        size=alt.condition(hover, alt.value(14), alt.value(10)),
        tooltip=[
            alt.Tooltip(LANGUAGE.translate(ESCAPE), type="nominal", title=LANGUAGE),
            alt.Tooltip(AGE.translate(ESCAPE), type="quantitative", title=AGE),
            alt.Tooltip(POPULARITY.translate(ESCAPE), type="quantitative", title=POPULARITY),
            alt.Tooltip(YEAR_CREATED.translate(ESCAPE), type="quantitative", title=YEAR_CREATED, format="d"),
        ],
    )
    .add_params(hover)
    .properties(
        width=620,
        height=320,
        background=PAGE_BG,
        title=alt.Title(text="scatter-text · python · altair · anyplot.ai", fontSize=16, anchor="middle"),
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT, strokeWidth=0)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        labelFontSize=10,
        titleColor=INK,
        titleFontSize=12,
    )
    .configure_title(color=INK)
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        titleFontSize=11,
        labelFontSize=10,
        padding=6,
    )
)

# Save as PNG and HTML
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Pad (never crop) to the canonical 3200 x 1800 canvas
TARGET_W, TARGET_H = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TARGET_W or img.height > TARGET_H:
    raise SystemExit(f"altair produced {img.width}x{img.height}, exceeds {TARGET_W}x{TARGET_H}")
if img.size != (TARGET_W, TARGET_H):
    canvas = Image.new("RGB", (TARGET_W, TARGET_H), PAGE_BG)
    canvas.paste(img, ((TARGET_W - img.width) // 2, (TARGET_H - img.height) // 2))
    canvas.save(f"plot-{THEME}.png")
