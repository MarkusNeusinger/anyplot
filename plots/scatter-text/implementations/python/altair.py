""" anyplot.ai
scatter-text: Scatter Plot with Text Labels Instead of Points
Library: altair 6.1.0 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-17
"""

import os

import numpy as np
import pandas as pd
from altair import Chart, Color, Legend, Scale, Title, Tooltip, X, Y, condition, selection_point, value


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Okabe-Ito position 1

# Data: Programming languages positioned by popularity vs age
np.random.seed(42)

languages = [
    "Python",
    "JavaScript",
    "Java",
    "C++",
    "Ruby",
    "Go",
    "Rust",
    "Swift",
    "Kotlin",
    "TypeScript",
    "Scala",
    "R",
    "Julia",
    "Perl",
    "PHP",
    "C#",
    "Haskell",
    "Elixir",
    "Clojure",
    "Dart",
    "Lua",
    "MATLAB",
    "Fortran",
    "COBOL",
    "Lisp",
    "Erlang",
    "F#",
    "Groovy",
]

# Simulated: x = language age (years), y = relative popularity score
ages = np.array(
    [33, 29, 26, 41, 29, 15, 9, 10, 13, 8, 20, 31, 12, 37, 30, 24, 34, 13, 17, 18, 31, 40, 68, 65, 66, 38, 19, 21]
)
popularity = np.array(
    [98, 88, 82, 68, 42, 62, 52, 58, 48, 75, 32, 45, 28, 18, 55, 72, 12, 15, 9, 22, 25, 38, 8, 4, 6, 14, 35, 20]
)

df = pd.DataFrame({"age": ages, "popularity": popularity, "language": languages, "year_created": 2026 - ages})

# Selection for hover highlight
hover = selection_point(on="pointerover", nearest=True, empty=False)

chart = (
    Chart(df)
    .mark_text(fontSize=14, fontWeight="bold")
    .encode(
        x=X("age:Q", title="Language Age (Years Since Creation)", scale=Scale(domain=[-2, 75])),
        y=Y("popularity:Q", title="Relative Popularity Score", scale=Scale(domain=[-2, 105])),
        text="language:N",
        color=condition(
            hover, value(BRAND), Color("popularity:Q", scale=Scale(scheme="viridis"), legend=Legend(title="Popularity"))
        ),
        size=condition(hover, value(18), value(14)),
        tooltip=[
            Tooltip("language:N", title="Language"),
            Tooltip("age:Q", title="Age (years)"),
            Tooltip("popularity:Q", title="Popularity Score"),
            Tooltip("year_created:Q", title="Year Created"),
        ],
    )
    .add_params(hover)
    .properties(
        width=1600,
        height=900,
        background=PAGE_BG,
        title=Title(text="scatter-text · Python · altair · anyplot.ai", fontSize=28, anchor="middle"),
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT, strokeWidth=0)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        labelFontSize=18,
        titleColor=INK,
        titleFontSize=22,
    )
    .configure_title(color=INK)
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        titleFontSize=18,
        labelFontSize=16,
    )
)

# Save as PNG and HTML
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
