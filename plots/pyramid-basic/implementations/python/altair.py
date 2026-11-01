"""anyplot.ai
pyramid-basic: Basic Pyramid Chart
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-04-29
"""

import importlib
import os
import sys


# Drop script directory from sys.path so the `altair` package resolves, not this file
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]
alt = importlib.import_module("altair")
np = importlib.import_module("numpy")
pd = importlib.import_module("pandas")
Image = importlib.import_module("PIL.Image")

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
AGE_GROUP = "Age group"  # role: category
MALE = "Male"  # role: value_left
FEMALE = "Female"  # role: value_right
SIDE = "Gender"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("population.csv")
df = pd.DataFrame(
    {
        AGE_GROUP: ["0-9", "10-19", "20-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80+"],
        MALE: [4.8, 5.2, 6.1, 7.3, 8.5, 7.8, 5.9, 3.2, 1.2],
        FEMALE: [4.5, 5.0, 6.3, 7.5, 8.7, 8.2, 6.8, 4.8, 2.5],
    }
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
VALUE = "Population (millions)"
SIGNED = "Signed value"

sides = [MALE, FEMALE]
long = df.melt(id_vars=AGE_GROUP, value_vars=sides, var_name=SIDE, value_name=VALUE)
long[SIGNED] = np.where(long[SIDE] == MALE, -long[VALUE], long[VALUE])
limit = float(np.ceil(long[VALUE].max() / 2) * 2 + 2)

# Interactive highlight — click legend to isolate a side
selection = alt.selection_point(fields=[SIDE], bind="legend")

chart = (
    alt.Chart(long)
    .mark_bar(cornerRadiusEnd=2)
    .encode(
        y=alt.Y(
            AGE_GROUP.translate(ESCAPE),
            type="ordinal",
            title=AGE_GROUP,
            sort="descending",
            axis=alt.Axis(titleFontSize=12, labelFontSize=10),
        ),
        x=alt.X(
            SIGNED.translate(ESCAPE),
            type="quantitative",
            title=VALUE,
            axis=alt.Axis(titleFontSize=12, labelFontSize=10, labelExpr="abs(datum.value)", tickMinStep=2),
            scale=alt.Scale(domain=[-limit, limit], nice=False),
        ),
        color=alt.Color(
            SIDE.translate(ESCAPE),
            type="nominal",
            title=SIDE,
            sort=None,
            scale=alt.Scale(domain=sides, range=IMPRINT_PALETTE[: len(sides)]),
            legend=alt.Legend(titleFontSize=10, labelFontSize=10, orient="bottom"),
        ),
        opacity=alt.condition(selection, alt.value(0.9), alt.value(0.25)),
        tooltip=[
            alt.Tooltip(SIDE.translate(ESCAPE), type="nominal", title=SIDE),
            alt.Tooltip(AGE_GROUP.translate(ESCAPE), type="ordinal", title=AGE_GROUP),
            alt.Tooltip(VALUE.translate(ESCAPE), type="quantitative", title=VALUE, format=".1f"),
        ],
    )
    .add_params(selection)
    .properties(
        width=620,
        height=320,
        background=PAGE_BG,
        title=alt.Title(text="pyramid-basic · altair · anyplot.ai", fontSize=16, anchor="middle"),
    )
    .configure_view(fill=PAGE_BG, stroke=None)
    .configure_axis(
        domainColor=INK_SOFT, tickColor=INK_SOFT, gridColor=INK, gridOpacity=0.10, labelColor=INK_SOFT, titleColor=INK
    )
    .configure_title(color=INK)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK, padding=6)
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Pad (never crop) to the canonical 3200 x 1800 canvas
TARGET_W, TARGET_H = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
w, h = img.size
if w > TARGET_W or h > TARGET_H:
    raise SystemExit(f"altair produced {w}x{h}, exceeds {TARGET_W}x{TARGET_H}; shrink width/height")
if (w, h) != (TARGET_W, TARGET_H):
    canvas = Image.new("RGB", (TARGET_W, TARGET_H), PAGE_BG)
    canvas.paste(img, ((TARGET_W - w) // 2, (TARGET_H - h) // 2))
    canvas.save(f"plot-{THEME}.png")
