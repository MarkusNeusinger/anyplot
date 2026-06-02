#' anyplot.ai
#' heatmap-stripes-climate: Climate Warming Stripes
#' Library: ggplot2 | R 4.x
#' Quality: pending | Created: 2026-06-02

library(ggplot2)
library(ragg)

set.seed(42)

# Theme tokens
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"

# Data - synthetic global temperature anomalies 1880-2024 (relative to 1961-1990 baseline)
years   <- 1880:2024
n       <- length(years)
trend   <- (years - 1880) / (2024 - 1880) * 1.2
noise   <- rnorm(n, 0, 0.12)
dip     <- ifelse(years >= 1945 & years <= 1975, -0.12, 0)
anomaly <- trend + noise + dip
anomaly <- anomaly - mean(anomaly[years >= 1961 & years <= 1990])

df <- data.frame(year = years, anomaly = anomaly)

# Imprint diverging colormap: Imprint blue (cold) -> page neutral -> Imprint red (warm)
MID_COLOR <- if (THEME == "light") "#FAF8F1" else "#1A1A17"

# Title: 50 chars — below the 67-char baseline, no font-size scaling needed
title_text <- "heatmap-stripes-climate · r · ggplot2 · anyplot.ai"

# Warming stripes: one full-height bar per year, no axes, no labels, no grid
p <- ggplot(df, aes(x = year, y = 1, fill = anomaly)) +
    geom_tile(width = 1, height = 2) +
    scale_fill_gradient2(
        low      = "#4467A3",  # Imprint blue  — cold anomaly
        mid      = MID_COLOR,
        high     = "#AE3030",  # Imprint red   — warm anomaly
        midpoint = 0,
        guide    = "none"
    ) +
    scale_x_continuous(expand = c(0, 0)) +
    scale_y_continuous(limits = c(0, 2), expand = c(0, 0)) +
    labs(title = title_text) +
    theme_void() +
    theme(
        plot.background = element_rect(fill = PAGE_BG, color = NA),
        plot.title      = element_text(
            color  = INK,
            size   = 12,
            hjust  = 0.5,
            margin = margin(b = 8)
        ),
        plot.margin = margin(t = 20, r = 20, b = 20, l = 20)
    )

# Save
ggsave(
    filename = sprintf("plot-%s.png", THEME),
    plot     = p,
    device   = ragg::agg_png,
    width    = 8,
    height   = 4.5,
    units    = "in",
    dpi      = 400
)
