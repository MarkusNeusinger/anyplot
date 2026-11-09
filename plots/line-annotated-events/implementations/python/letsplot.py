"""anyplot.ai
line-annotated-events: Annotated Line Plot with Event Markers
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 86/100 | Updated: 2026-11-09
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_line,
    geom_point,
    geom_text,
    geom_vline,
    ggplot,
    ggsave,
    ggsize,
    labs,
    layer_tooltips,
    scale_x_datetime,
    scale_y_continuous,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "#E4E2DB" if THEME == "light" else "#34342F"  # INK at ~12 % over PAGE_BG
BRAND = "#009E73"  # Imprint palette position 1 — the single data series

# Columns: set these to your table's column names
DATE = "Date"  # role: date
USERS = "Daily active users"  # role: value
EVENT_DATE = "Event date"  # role: event_date
EVENT_LABEL = "Event"  # role: event_label

# Data: replace this block with your own table, for example df = pd.read_csv("daily_users.csv")
np.random.seed(42)
dates = pd.date_range("2024-01-01", periods=365, freq="D")
trend = np.linspace(1000, 5000, 365)
seasonality = 300 * np.sin(np.arange(365) * 2 * np.pi / 30)
noise = np.random.normal(0, 150, 365)
daily_users = trend + seasonality + noise
launches = {45: "Dark Mode", 120: "Team Workspaces", 200: "Mobile App", 280: "API v2.0", 330: "Partners"}
step_sizes = {45: 400, 120: 600, 200: 800, 280: 500, 330: 300}
for day, step in step_sizes.items():
    daily_users[day:] += step
event_labels = [launches.get(day) for day in range(365)]
df = pd.DataFrame(
    {
        DATE: dates,
        USERS: daily_users,
        EVENT_DATE: [dates[day] if label else pd.NaT for day, label in enumerate(event_labels)],
        EVENT_LABEL: event_labels,
    }
)

# Plot: reads only df and the constants above
series = df.dropna(subset=[USERS])
events = df.dropna(subset=[EVENT_DATE, EVENT_LABEL]).sort_values(EVENT_DATE).reset_index(drop=True)
top = series[USERS].max()
low = min(series[USERS].min(), 0)
events["label_y"] = top * np.where(events.index % 2 == 0, 1.07, 1.15)
events["label_text"] = "  " + events[EVENT_LABEL].astype(str)

title = "line-annotated-events · python · letsplot · anyplot.ai"

plot = (
    ggplot()
    + geom_vline(
        aes(xintercept=EVENT_DATE),
        data=events,
        color=INK_MUTED,
        linetype="dashed",
        size=0.6,
        tooltips=layer_tooltips()
        .title("@{" + EVENT_LABEL + "}")
        .line("@{" + EVENT_DATE + "}")
        .format(EVENT_DATE, "%b %d"),
    )
    + geom_line(
        aes(x=DATE, y=USERS),
        data=series,
        color=BRAND,
        size=1.3,
        tooltips=layer_tooltips()
        .line("@{" + DATE + "}")
        .line(USERS + ": @{" + USERS + "}")
        .format(DATE, "%b %d")
        .format(USERS, ",.0f"),
    )
    + geom_point(aes(x=EVENT_DATE, y=USERS), data=events, shape=21, size=3.5, fill=PAGE_BG, color=INK, stroke=1.1)
    + geom_point(aes(x=EVENT_DATE, y="label_y"), data=events, shape=18, size=4.5, color=INK_SOFT)
    + geom_text(
        aes(x=EVENT_DATE, y="label_y", label="label_text"), data=events, color=INK, size=5, hjust=0, fontface="bold"
    )
    + labs(x=DATE, y=USERS, title=title)
    + scale_x_datetime(format="%b")
    + scale_y_continuous(limits=[low, top * 1.22], format=",.0f")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major_x=element_blank(),
        panel_grid_major_y=element_line(color=GRID, size=0.4),
        panel_grid_minor=element_blank(),
        axis_line_x=element_line(color=INK_SOFT),
        axis_ticks=element_blank(),
        plot_title=element_text(size=16, color=INK, face="bold"),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
    )
    + ggsize(800, 450)
)

# Save
ggsave(plot, f"plot-{THEME}.png", scale=4, path=".")
ggsave(plot, f"plot-{THEME}.html", path=".")
