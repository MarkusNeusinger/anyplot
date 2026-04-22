""" pyplots.ai
line-annotated-events: Annotated Line Plot with Event Markers
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403


LetsPlot.setup_html()

# Data - Daily product metrics with feature launch events
np.random.seed(42)
dates = pd.date_range("2024-01-01", periods=365, freq="D")

# Create realistic user growth pattern with trend and seasonality
trend = np.linspace(1000, 5000, 365)
seasonality = 300 * np.sin(np.arange(365) * 2 * np.pi / 30)
noise = np.random.normal(0, 150, 365)
daily_users = trend + seasonality + noise

# Create jumps at event dates to show impact
daily_users[45:] += 400  # After Feature A launch
daily_users[120:] += 600  # After Feature B launch
daily_users[200:] += 800  # After Mobile App launch
daily_users[280:] += 500  # After API release
daily_users[330:] += 300  # After Integration launch

df = pd.DataFrame({"date": dates, "users": daily_users})

# Convert date to numeric for plotting
df["date_num"] = (df["date"] - df["date"].min()).dt.days

# Event data - Feature launches throughout the year
events = pd.DataFrame(
    {
        "event_date": pd.to_datetime(["2024-02-15", "2024-05-01", "2024-07-20", "2024-10-07", "2024-11-20"]),
        "event_label": ["Feature A", "Feature B", "Mobile App", "API v2.0", "Partners"],
        "y_offset": [4800, 5200, 5600, 6000, 6400],  # Alternating heights to avoid overlap
    }
)
events["event_num"] = (events["event_date"] - df["date"].min()).dt.days

# Create the plot
plot = (
    ggplot()
    # Main line - daily active users
    + geom_line(aes(x="date_num", y="users"), data=df, color="#306998", size=1.5, alpha=0.9)
    # Vertical lines for events
    + geom_vline(aes(xintercept="event_num"), data=events, color="#DC2626", linetype="dashed", size=1.0, alpha=0.7)
    # Event markers at the line
    + geom_point(aes(x="event_num", y="y_offset"), data=events, color="#DC2626", size=5, shape=18)
    # Event labels
    + geom_text(
        aes(x="event_num", y="y_offset", label="event_label"),
        data=events,
        color="#333333",
        size=14,
        hjust=0,
        nudge_x=5,
        fontface="bold",
    )
    # Labels and title
    + labs(x="Day of Year 2024", y="Daily Active Users", title="line-annotated-events · letsplot · pyplots.ai")
    # Styling
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        panel_grid_major=element_line(color="#CCCCCC", size=0.5),
        panel_grid_minor=element_blank(),
    )
    # Set axis limits to show all data and labels
    + scale_x_continuous(
        breaks=[0, 60, 120, 180, 240, 300, 360], labels=["Jan", "Mar", "May", "Jul", "Sep", "Nov", "Jan"]
    )
    + scale_y_continuous(limits=[0, 7500])
    # Figure size (scaled 3x on export = 4800 × 2700 px)
    + ggsize(1600, 900)
)

# Save as PNG and HTML
ggsave(plot, "plot.png", scale=3)
ggsave(plot, "plot.html")
