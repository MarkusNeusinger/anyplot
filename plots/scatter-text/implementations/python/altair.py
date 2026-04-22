""" pyplots.ai
scatter-text: Scatter Plot with Text Labels Instead of Points
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-09
"""

import altair as alt
import numpy as np
import pandas as pd


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
# Data spread more evenly to avoid overlap
ages = np.array(
    [33, 29, 26, 41, 29, 15, 9, 10, 13, 8, 20, 31, 12, 37, 30, 24, 34, 13, 17, 18, 31, 40, 68, 65, 66, 38, 19, 21]
)
popularity = np.array(
    [98, 88, 82, 68, 42, 62, 52, 58, 48, 75, 32, 45, 28, 18, 55, 72, 12, 15, 9, 22, 25, 38, 8, 4, 6, 14, 35, 20]
)

df = pd.DataFrame({"age": ages, "popularity": popularity, "language": languages, "year_created": 2026 - ages})

# Create interactive scatter text plot using mark_text
# Selection for hover highlight - Altair's distinctive interactivity feature
hover = alt.selection_point(on="pointerover", nearest=True, empty=False)

chart = (
    alt.Chart(df)
    .mark_text(fontSize=14, fontWeight="bold")
    .encode(
        x=alt.X("age:Q", title="Language Age (Years Since Creation)", scale=alt.Scale(domain=[-2, 75])),
        y=alt.Y("popularity:Q", title="Relative Popularity Score", scale=alt.Scale(domain=[-2, 105])),
        text="language:N",
        color=alt.condition(
            hover,
            alt.value("#FF6B35"),
            alt.Color("popularity:Q", scale=alt.Scale(scheme="viridis"), legend=alt.Legend(title="Popularity")),
        ),
        size=alt.condition(hover, alt.value(18), alt.value(14)),
        tooltip=[
            alt.Tooltip("language:N", title="Language"),
            alt.Tooltip("age:Q", title="Age (years)"),
            alt.Tooltip("popularity:Q", title="Popularity Score"),
            alt.Tooltip("year_created:Q", title="Year Created"),
        ],
    )
    .add_params(hover)
    .properties(
        width=1600, height=900, title=alt.Title(text="scatter-text · altair · pyplots.ai", fontSize=28, anchor="middle")
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, gridOpacity=0.3)
    .configure_view(strokeWidth=0)
    .configure_legend(titleFontSize=18, labelFontSize=16)
)

# Save as PNG and HTML (HTML preserves interactivity)
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
