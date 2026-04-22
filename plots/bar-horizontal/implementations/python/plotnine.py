""" pyplots.ai
bar-horizontal: Horizontal Bar Chart
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 97/100 | Created: 2025-12-25
"""

import pandas as pd
from plotnine import aes, coord_flip, element_text, geom_bar, geom_text, ggplot, labs, theme, theme_minimal


# Data: Top 10 programming languages by popularity (survey results)
data = {
    "language": ["JavaScript", "Python", "Java", "TypeScript", "C#", "C++", "PHP", "Go", "Rust", "Swift"],
    "users_percent": [65.6, 49.3, 35.4, 34.8, 29.7, 23.0, 18.4, 14.3, 13.1, 6.6],
}

df = pd.DataFrame(data)

# Sort by value and convert to categorical for proper ordering
df = df.sort_values("users_percent", ascending=True)
df["language"] = pd.Categorical(df["language"], categories=df["language"], ordered=True)

# Plot
plot = (
    ggplot(df, aes(x="language", y="users_percent"))
    + geom_bar(stat="identity", fill="#306998", width=0.7)
    + geom_text(aes(label="users_percent"), format_string="{:.1f}%", ha="left", nudge_y=1.5, size=12, color="#333333")
    + coord_flip()
    + labs(x="Programming Language", y="Developer Usage (%)", title="bar-horizontal · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold"),
        axis_title_x=element_text(size=20),
        axis_title_y=element_text(size=20),
        axis_text_x=element_text(size=16),
        axis_text_y=element_text(size=16),
        panel_grid_major_x=element_text(color="#cccccc"),
        panel_grid_minor=element_text(color="#eeeeee"),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
