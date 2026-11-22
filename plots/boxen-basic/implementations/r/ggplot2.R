#' anyplot.ai
#' boxen-basic: Basic Boxen Plot (Letter-Value Plot)
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: pending | Created: 2026-05-17

library(ggplot2)
library(dplyr)
library(ragg)
library(tibble)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

# Imprint palette: quantile levels step from position 1 (green) to position 3 (blue)
IMPRINT_SEQ <- colorRampPalette(c("#009E73", "#4467A3"))

# --- Columns ----------------------------------------------------------------
ENDPOINT <- "Server endpoint"   # role: category
RESPONSE <- "Response time (ms)" # role: value

# --- Data -------------------------------------------------------------------
# Simulated response times for three server endpoints
set.seed(42)

df <- tibble(
  !!ENDPOINT := rep(c("API Search", "API Users", "API Reports"), each = 3000),
  !!RESPONSE := c(
    c(rnorm(2700, mean = 50, sd = 15), rnorm(300, mean = 200, sd = 50)),
    rnorm(3000, mean = 80, sd = 12),
    c(rnorm(2500, mean = 120, sd = 25), rnorm(500, mean = 400, sd = 80))
  )
) %>%
  mutate(!!RESPONSE := pmax(.data[[RESPONSE]], 10))

# --- Letter values ----------------------------------------------------------
# Each level spans a pair of tail probabilities; deeper levels are drawn narrower
LEVELS <- tibble(
  level  = c("Sixteenths (6.25-93.75%)", "Eighths (12.5-87.5%)", "Quartiles (25-75%)"),
  p_low  = c(0.0625, 0.125, 0.25),
  width  = c(0.3, 0.5, 0.7)
) %>%
  mutate(level = factor(level, levels = rev(level)), p_high = 1 - p_low)

endpoints <- unique(df[[ENDPOINT]])

summaries <- df %>%
  group_by(.data[[ENDPOINT]]) %>%
  summarize(
    median = median(.data[[RESPONSE]]),
    lo_min = quantile(.data[[RESPONSE]], min(LEVELS$p_low)),
    hi_max = quantile(.data[[RESPONSE]], max(LEVELS$p_high)),
    .groups = "drop"
  ) %>%
  mutate(x = match(.data[[ENDPOINT]], endpoints))

boxes <- df %>%
  group_by(.data[[ENDPOINT]]) %>%
  reframe(
    level  = LEVELS$level,
    x_half = LEVELS$width / 2,
    y_low  = quantile(.data[[RESPONSE]], LEVELS$p_low),
    y_high = quantile(.data[[RESPONSE]], LEVELS$p_high)
  ) %>%
  mutate(x = match(.data[[ENDPOINT]], endpoints))

# Observations beyond the deepest letter value
outliers <- df %>%
  left_join(summaries, by = ENDPOINT) %>%
  filter(.data[[RESPONSE]] < lo_min | .data[[RESPONSE]] > hi_max) %>%
  mutate(x = match(.data[[ENDPOINT]], endpoints))

# --- Plot -------------------------------------------------------------------
p <- ggplot() +
  geom_point(
    data = outliers,
    aes(x = x, y = .data[[RESPONSE]]),
    shape = 21, size = 1.3, stroke = 0.4,
    color = INK_SOFT, fill = NA, alpha = 0.6
  ) +
  geom_rect(
    data = boxes,
    aes(xmin = x - x_half, xmax = x + x_half, ymin = y_low, ymax = y_high, fill = level),
    color = PAGE_BG, linewidth = 0.4
  ) +
  geom_segment(
    data = summaries,
    aes(x = x - 0.35, xend = x + 0.35, y = median, yend = median),
    color = INK, linewidth = 0.9
  ) +
  scale_fill_manual(
    name   = "Quantile level",
    values = setNames(IMPRINT_SEQ(nrow(LEVELS)), rev(levels(LEVELS$level))),
    breaks = rev(levels(LEVELS$level))
  ) +
  scale_x_continuous(
    breaks = seq_along(endpoints),
    labels = endpoints,
    limits = c(0.4, length(endpoints) + 0.6)
  ) +
  scale_y_continuous(expand = expansion(mult = c(0.03, 0.05))) +
  labs(
    title = "boxen-basic · r · ggplot2 · anyplot.ai",
    x = ENDPOINT,
    y = RESPONSE
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background    = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background   = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.x = element_blank(),
    panel.grid.minor   = element_blank(),
    panel.grid.major.y = element_line(color = INK_SOFT, linewidth = 0.15),
    axis.line          = element_line(color = INK_SOFT, linewidth = 0.3),
    axis.title         = element_text(color = INK, size = 10),
    axis.text          = element_text(color = INK_SOFT, size = 8),
    plot.title         = element_text(color = INK, size = 12, face = "bold"),
    legend.position    = "right",
    legend.background  = element_rect(fill = ELEVATED_BG, color = INK_SOFT, linewidth = 0.3),
    legend.text        = element_text(color = INK_SOFT, size = 8),
    legend.title       = element_text(color = INK, size = 10),
    legend.key         = element_blank(),
    plot.margin        = margin(10, 10, 10, 10, "pt")
  )

# --- Save -------------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 8,
  height   = 4.5,
  units    = "in",
  dpi      = 400
)
