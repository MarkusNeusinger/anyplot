#' anyplot.ai
#' bubble-basic: Basic Bubble Chart
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 90/100 | Created: 2026-05-28

library(ggplot2)
library(dplyr)
library(scales)
library(ragg)
library(gapminder)

set.seed(42)

# Theme tokens
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
GRID        <- if (THEME == "light") "#D3D1CA" else "#3A3A37"

continent_colors <- c(
    Africa   = "#009E73",
    Americas = "#C475FD",
    Asia     = "#4467A3",
    Europe   = "#BD8233",
    Oceania  = "#AE3030"
)

# Data — gapminder 2007: GDP per capita vs life expectancy, bubble = population
gm_2007 <- gapminder::gapminder |>
    dplyr::filter(year == 2007)

# Plot
p <- ggplot(gm_2007, aes(
    x    = gdpPercap,
    y    = lifeExp,
    size = pop,
    fill = continent
)) +
    geom_point(
        shape  = 21,
        color  = PAGE_BG,
        alpha  = 0.65,
        stroke = 0.4
    ) +
    scale_x_log10(
        labels = label_dollar(accuracy = 1),
        breaks = c(500, 1000, 5000, 10000, 50000)
    ) +
    scale_size_area(
        max_size = 22,
        breaks   = c(5e7, 2e8, 5e8, 1e9),
        labels   = c("50M", "200M", "500M", "1B"),
        name     = "Population"
    ) +
    scale_fill_manual(
        values = continent_colors,
        name   = "Continent"
    ) +
    labs(
        title = "bubble-basic · r · ggplot2 · anyplot.ai",
        x     = "GDP per Capita (log scale)",
        y     = "Life Expectancy (years)"
    ) +
    guides(
        fill = guide_legend(override.aes = list(size = 4, alpha = 0.9)),
        size = guide_legend(title = "Population")
    ) +
    theme_minimal(base_size = 8) +
    theme(
        plot.background   = element_rect(fill = PAGE_BG,     color = PAGE_BG),
        panel.background  = element_rect(fill = PAGE_BG,     color = NA),
        panel.grid.major  = element_line(color = GRID,       linewidth = 0.4),
        panel.grid.minor  = element_line(color = GRID,       linewidth = 0.2),
        axis.title        = element_text(color = INK,        size = 10),
        axis.text         = element_text(color = INK_SOFT,   size = 8),
        plot.title        = element_text(color = INK,        size = 12),
        legend.background = element_rect(fill = ELEVATED_BG, color = INK_SOFT,
                                         linewidth = 0.3),
        legend.text       = element_text(color = INK_SOFT,   size = 8),
        legend.title      = element_text(color = INK,        size = 10),
        legend.key        = element_rect(fill = NA,          color = NA),
        legend.margin     = margin(6, 8, 6, 8),
        plot.margin       = margin(12, 12, 10, 10)
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
