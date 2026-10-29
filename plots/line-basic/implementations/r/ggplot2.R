#' anyplot.ai
#' line-basic: Basic Line Plot
#' Library: ggplot2 4.0.3 | R 4.6.1
#' Quality: 82/100 | Updated: 2026-10-29

library(ggplot2)
library(ragg)

# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME    <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG  <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK      <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Columns: set these to your table's column names
DAY         <- "Day of Season"     # role: x
TEMPERATURE <- "Temperature (°C)"  # role: y

# Data: replace this block with your own table, for example df <- read.csv("temperature.csv", check.names = FALSE)
set.seed(42)
n_days <- 90
day_of_season <- 1:n_days
seasonal_curve <- 24 + 6 * sin(pi * day_of_season / n_days)
df <- tibble::tibble(
  !!DAY         := day_of_season,
  !!TEMPERATURE := seasonal_curve + rnorm(n_days, mean = 0, sd = 0.7)
)

# Plot: reads only df and the constants above
p <- ggplot(df, aes(x = .data[[DAY]], y = .data[[TEMPERATURE]])) +
  geom_line(color = IMPRINT_PALETTE[1], linewidth = 1.5) +
  labs(
    title = "line-basic · r · ggplot2 · anyplot.ai",
    x = DAY,
    y = TEMPERATURE
  ) +
  scale_x_continuous(expand = expansion(mult = c(0.01, 0.02))) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.x = element_blank(),
    panel.grid.minor.x = element_blank(),
    panel.grid.minor.y = element_blank(),
    panel.grid.major.y = element_line(color = INK, linewidth = 0.2),
    axis.title         = element_text(color = INK, size = 10),
    axis.text          = element_text(color = INK_SOFT, size = 8),
    axis.ticks         = element_blank(),
    plot.title         = element_text(color = INK, size = 12, face = "bold"),
    plot.margin        = margin(12, 16, 8, 8)
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
