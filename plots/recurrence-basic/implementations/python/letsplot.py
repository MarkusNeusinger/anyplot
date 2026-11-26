"""anyplot.ai
recurrence-basic: Recurrence Plot for Nonlinear Time Series
Library: letsplot 4.10.1 | Python 3.13.13
Quality: pending | Created: 2026-06-10
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *
from scipy.spatial.distance import cdist


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Imprint palette position 1

# Constants
EMBED_DIM = 2  # time-delay embedding dimension (Takens' theorem)
EMBED_DELAY = 5  # time-delay embedding delay, in steps
RECURRENCE_PERCENTILE = 15  # threshold epsilon = this percentile of the pairwise distances

# Columns: set these to your table's column names
TIME = "Time index"  # role: time
VALUE = "State variable x"  # role: value
THRESHOLD = "Recurrence threshold ε"  # role: threshold

# Data: replace this block with your own table, for example df = pd.read_csv("series.csv")
# Logistic map in the chaotic regime (r=3.8), transient discarded
np.random.seed(42)
n_total = 350
growth = 3.8
x_all = np.zeros(n_total)
x_all[0] = 0.5
for i in range(1, n_total):
    x_all[i] = growth * x_all[i - 1] * (1 - x_all[i - 1])
x_series = x_all[100:]  # 250 steps, transient removed
df = pd.DataFrame({TIME: np.arange(len(x_series)), VALUE: x_series})

# Plot: reads only df and the constants above
values = df[VALUE].to_numpy()

# Time-delay embedding: one state vector per embedded time step
n_states = len(values) - (EMBED_DIM - 1) * EMBED_DELAY
embedded = np.column_stack([values[k * EMBED_DELAY : k * EMBED_DELAY + n_states] for k in range(EMBED_DIM)])

# Pairwise Euclidean distances, threshold at a percentile of the off-diagonal distances
dist_matrix = cdist(embedded, embedded, metric="euclidean")
off_diag = dist_matrix[np.triu_indices(n_states, k=1)]
epsilon = np.percentile(off_diag, RECURRENCE_PERCENTILE)

# Binary recurrence: a pair (i, j) is recurrent when its distance is within epsilon
rows, cols = np.where(dist_matrix <= epsilon)
recurrence = pd.DataFrame({"i": rows, "j": cols})

title = "recurrence-basic · python · letsplot · anyplot.ai"

# Theme — color=PAGE_BG on panel_background hides the panel box, yielding an L-shaped frame
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_border=element_blank(),
    panel_grid_major=element_blank(),
    panel_grid_minor=element_blank(),
    axis_title=element_text(color=INK, size=12),
    axis_text=element_text(color=INK_SOFT, size=10),
    axis_line=element_line(color=INK_SOFT),
    plot_title=element_text(color=INK, size=16),
    legend_position="none",
)

# Recurrent pairs as tiles; the filled main diagonal (i = j) comes from the data itself
plot = (
    ggplot(recurrence, aes(x="i", y="j"))
    + geom_tile(fill=BRAND, alpha=0.9, tooltips=layer_tooltips().line("@i, @j").line(f"{THRESHOLD} = {epsilon:.3f}"))
    + labs(x=f"{TIME} i", y=f"{TIME} j", title=title)
    + anyplot_theme
    + coord_fixed(ratio=1.0)
)

# The fixed aspect leaves the canvas edges transparent: a one-panel grid paints the page color
plot = gggrid([plot]) + ggsize(600, 600) + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
