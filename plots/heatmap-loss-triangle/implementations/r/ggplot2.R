#' anyplot.ai
#' heatmap-loss-triangle: Actuarial Loss Development Triangle
#' Library: ggplot2 | R 4.x
#' Quality: pending | Created: 2026-06-03

library(ggplot2)
library(dplyr)
library(scales)
library(ragg)

set.seed(42)

# Theme tokens (Imprint palette, theme-adaptive chrome)
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
INK_MUTED   <- if (THEME == "light") "#6B6A63" else "#A8A79F"

# Data: actuarial loss development triangle (chain-ladder method)
accident_years <- 2015:2024
dev_periods    <- 1:10

# Cumulative percent of ultimate paid by development period
pct_paid <- c(0.40, 0.65, 0.80, 0.88, 0.93, 0.96, 0.98, 0.990, 0.995, 1.000)

# Ultimate claims per accident year (in $M)
ultimates <- c(42.5, 38.2, 51.3, 47.8, 55.1, 49.6, 61.2, 57.4, 63.8, 68.5)

# Age-to-age development factors
ata_factors <- pct_paid[2:10] / pct_paid[1:9]
ata_str     <- paste(
  "Age-to-Age Factors:",
  paste(sprintf("%.3f", ata_factors), collapse = " → ")
)

# Build full 10 x 10 triangle grid
df <- expand.grid(
  accident_year = accident_years,
  dev_period    = dev_periods,
  stringsAsFactors = FALSE
) %>%
  mutate(
    ay_idx     = accident_year - 2014L,
    is_actual  = dev_period <= (11L - ay_idx),
    cumulative = ultimates[ay_idx] * pct_paid[dev_period],
    cumulative = ifelse(
      is_actual,
      round(cumulative * runif(n(), 0.97, 1.03), 1),
      round(cumulative, 1)
    ),
    label   = sprintf("$%.1fM", cumulative),
    dev_fac = factor(dev_period, levels = 1:10),
    acc_fac = factor(accident_year, levels = 2015:2024)
  )

df_proj    <- filter(df, !is_actual)
year_order <- rev(levels(df$acc_fac))  # oldest (2015) at top

# Plot
p <- ggplot(df, aes(x = dev_fac, y = acc_fac)) +
  # All cells: colored by cumulative claims (Imprint sequential: green -> blue)
  geom_tile(aes(fill = cumulative), color = INK_SOFT, linewidth = 0.15) +
  # Projected cells: red border to distinguish IBNR estimates from actual
  geom_tile(data = df_proj,
            fill = NA, color = "#AE3030", linewidth = 0.5) +
  # Cell value labels
  geom_text(aes(label = label),
            color = "white", size = 1.8, fontface = "bold") +
  # Imprint sequential colormap: brand green -> blue
  scale_fill_gradient(
    low    = "#009E73",
    high   = "#4467A3",
    name   = "Claims ($M)",
    labels = function(x) sprintf("%.0f", x)
  ) +
  # Oldest accident year at top (actuarial convention)
  scale_y_discrete(limits = year_order) +
  labs(
    title    = "heatmap-loss-triangle · r · ggplot2 · anyplot.ai",
    subtitle = ata_str,
    x        = "Development Period (Years)",
    y        = "Accident Year",
    caption  = "▪ Actual (observed)   ▫ Projected / IBNR estimate (red border)"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid        = element_blank(),
    axis.title        = element_text(color = INK,       size = 10),
    axis.text         = element_text(color = INK_SOFT,  size = 8),
    plot.title        = element_text(color = INK,       size = 12, face = "bold"),
    plot.subtitle     = element_text(color = INK_MUTED, size = 7),
    plot.caption      = element_text(color = INK_MUTED, size = 7, hjust = 0),
    legend.background = element_rect(fill = ELEVATED_BG, color = INK_SOFT, linewidth = 0.3),
    legend.text       = element_text(color = INK_SOFT,  size = 8),
    legend.title      = element_text(color = INK,       size = 9),
    legend.position   = "right",
    plot.margin       = margin(t = 10, r = 10, b = 10, l = 10)
  )

# Save: square canvas (2400 x 2400 px at 400 dpi)
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 6,
  height   = 6,
  units    = "in",
  dpi      = 400
)
