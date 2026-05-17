#' anyplot.ai
#' boxen-basic: Basic Boxen Plot (Letter-Value Plot)
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 38/100 | Created: 2026-05-17

library(ggplot2)
library(dplyr)
library(ragg)
library(tibble)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
OKABE_ITO   <- c("#009E73", "#D55E00", "#0072B2", "#CC79A7",
                 "#E69F00", "#56B4E9", "#F0E442")

# --- Data -------------------------------------------------------------------
# Simulate response time distributions across three server endpoints
# with different characteristics
set.seed(42)

df <- tibble(
  endpoint = c(
    rep("API Search", 3000),
    rep("API Users", 3000),
    rep("API Reports", 3000)
  ),
  response_time_ms = c(
    # API Search: mostly fast, some slower responses, right skew
    c(rnorm(2700, mean = 50, sd = 15), rnorm(300, mean = 200, sd = 50)),
    # API Users: consistent, tight distribution
    rnorm(3000, mean = 80, sd = 12),
    # API Reports: slower on average, more variable
    c(rnorm(2500, mean = 120, sd = 25), rnorm(500, mean = 400, sd = 80))
  )
) %>%
  mutate(response_time_ms = pmax(response_time_ms, 10))  # No negative values

# --- Plot -------------------------------------------------------------------
p <- ggplot(df, aes(x = endpoint, y = response_time_ms, fill = endpoint)) +
  geom_boxplot(
    outlier.size = 3,
    outlier.alpha = 0.6,
    outlier.color = INK_SOFT,
    linewidth = 1,
    alpha = 0.85
  ) +
  scale_fill_manual(values = OKABE_ITO[1:3]) +
  scale_y_continuous(expand = expansion(mult = c(0.05, 0.1))) +
  labs(
    title = "boxen-basic · ggplot2 · anyplot.ai",
    x = "Server Endpoint",
    y = "Response Time (ms)",
    fill = "Endpoint"
  ) +
  theme_minimal(base_size = 14) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.x = element_blank(),
    panel.grid.minor.y = element_blank(),
    panel.grid.major.y = element_line(color = INK_SOFT, linewidth = 0.3),
    panel.border      = element_blank(),
    axis.line.x       = element_line(color = INK_SOFT, linewidth = 0.3),
    axis.line.y       = element_line(color = INK_SOFT, linewidth = 0.3),
    axis.title        = element_text(color = INK, size = 20),
    axis.text         = element_text(color = INK_SOFT, size = 16),
    plot.title        = element_text(color = INK, size = 24, face = "bold"),
    legend.position   = "right",
    legend.background = element_rect(fill = ELEVATED_BG, color = INK_SOFT, linewidth = 0.5),
    legend.text       = element_text(color = INK_SOFT, size = 16),
    legend.title      = element_text(color = INK, size = 18),
    plot.margin       = margin(20, 20, 20, 20, "pt")
  )

# --- Save -------------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 16,
  height   = 9,
  units    = "in",
  dpi      = 300
)
