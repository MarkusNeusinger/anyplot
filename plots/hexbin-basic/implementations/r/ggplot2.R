#' anyplot.ai
#' hexbin-basic: Basic Hexbin Plot
#' Library: ggplot2 | R 4.x
#' Quality: pending | Created: 2026-05-29

library(ggplot2)
library(ragg)

set.seed(42)

# Theme tokens (Imprint palette, theme-adaptive chrome)
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
GRID_COLOR  <- if (THEME == "light") "#1A1A1726" else "#F0EFE826"

# Data — simulated GPS mobility data: three urban activity clusters
x <- c(
    rnorm(5000, mean =  0.4, sd = 1.1),   # downtown core
    rnorm(3000, mean = -2.6, sd = 0.6),   # transit hub
    rnorm(2000, mean =  3.0, sd = 0.8)    # university campus
)
y <- c(
    rnorm(5000, mean =  0.2, sd = 0.9),   # downtown core
    rnorm(3000, mean =  2.3, sd = 0.5),   # transit hub
    rnorm(2000, mean = -1.6, sd = 0.8)    # university campus
)

df <- data.frame(
    easting  = x,
    northing = y
)

plot_title <- "hexbin-basic · r · ggplot2 · anyplot.ai"
n_chars    <- nchar(plot_title)
title_fs   <- if (n_chars > 67) round(12 * 67 / n_chars) else 12

# Plot
p <- ggplot(df, aes(x = easting, y = northing)) +
    geom_hex(bins = 35, color = NA) +
    scale_fill_gradient(
        low   = "#009E73",
        high  = "#4467A3",
        name  = "Count",
        guide = guide_colorbar(
            barwidth  = unit(0.4, "cm"),
            barheight = unit(3.0, "cm"),
            ticks     = FALSE
        )
    ) +
    labs(
        title = plot_title,
        x     = "Easting (km from city center)",
        y     = "Northing (km from city center)"
    ) +
    theme_minimal(base_size = 8) +
    theme(
        plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
        panel.background  = element_rect(fill = PAGE_BG, color = NA),
        panel.border      = element_blank(),
        panel.grid.major  = element_line(color = GRID_COLOR, linewidth = 0.4),
        panel.grid.minor  = element_blank(),
        axis.title        = element_text(color = INK, size = 10),
        axis.text         = element_text(color = INK_SOFT, size = 8),
        axis.line         = element_line(color = INK_SOFT, linewidth = 0.4),
        axis.ticks        = element_blank(),
        plot.title        = element_text(
            color  = INK,
            size   = title_fs,
            face   = "bold",
            margin = margin(b = 8)
        ),
        legend.background = element_rect(fill = ELEVATED_BG, color = NA),
        legend.text       = element_text(color = INK_SOFT, size = 8),
        legend.title      = element_text(color = INK, size = 10),
        plot.margin       = margin(12, 15, 12, 12, "pt")
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
