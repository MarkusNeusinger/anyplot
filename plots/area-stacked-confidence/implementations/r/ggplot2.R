#' anyplot.ai
#' area-stacked-confidence: Stacked Area Chart with Confidence Bands
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 87/100 | Created: 2026-05-18

library(ggplot2)
library(dplyr)
library(tidyr)
library(ragg)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

IMPRINT   <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                 "#AE3030", "#2ABCCD", "#954477")

# --- Data -------------------------------------------------------------------
# Quarterly energy consumption forecast by source with confidence bands
quarters <- 1:20
sources_order <- c("Solar", "Wind", "Hydro", "Battery")

df_base <- expand.grid(
  quarter = quarters,
  source = factor(sources_order, levels = sources_order)
) %>%
  arrange(quarter, source)

# Generate central values and confidence bands
df_data <- df_base %>%
  mutate(
    base = case_when(
      source == "Solar" ~ 800 + quarter * 50 + rnorm(n(), 0, 30),
      source == "Wind" ~ 1200 + quarter * 30 + rnorm(n(), 0, 40),
      source == "Hydro" ~ 600 - quarter * 10 + rnorm(n(), 0, 25),
      source == "Battery" ~ 200 + quarter * 15 + rnorm(n(), 0, 15)
    ),
    # Confidence bands (uncertainty increases over forecast horizon)
    uncertainty = case_when(
      source == "Solar" ~ 50 + quarter * 3,
      source == "Wind" ~ 60 + quarter * 4,
      source == "Hydro" ~ 40 + quarter * 2,
      source == "Battery" ~ 30 + quarter * 2
    ),
    value = pmax(base, 100),  # Ensure positive values
    value_lower = pmax(value - uncertainty, 50),
    value_upper = value + uncertainty
  ) %>%
  select(quarter, source, value, value_lower, value_upper)

# Calculate cumulative stacked values
df_plot <- df_data %>%
  arrange(quarter, source) %>%
  group_by(quarter) %>%
  mutate(
    # Cumulative sum for stacking
    prev_cumsum = lag(cumsum(value), default = 0),
    y_base = prev_cumsum,
    y_center = y_base + value,
    y_lower = y_base + value_lower,
    y_upper = y_base + value_upper
  ) %>%
  ungroup() %>%
  arrange(quarter, source)

# --- Plot -------------------------------------------------------------------
anyplot_theme <- theme_minimal(base_size = 14) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major  = element_line(color = INK_SOFT, linewidth = 0.2),
    panel.grid.minor  = element_blank(),
    axis.title        = element_text(color = INK, size = 20),
    axis.text         = element_text(color = INK_SOFT, size = 16),
    plot.title        = element_text(color = INK, size = 24, face = "bold"),
    legend.background = element_rect(fill = ELEVATED_BG, color = INK_SOFT),
    legend.text       = element_text(color = INK_SOFT, size = 16),
    legend.title      = element_text(color = INK, size = 18)
  )

p <- ggplot(df_plot, aes(x = quarter, fill = source, color = source)) +
  # Confidence bands (lighter, more transparent)
  geom_ribbon(aes(ymin = y_lower, ymax = y_upper), alpha = 0.2, color = NA) +
  # Central stacked areas
  geom_area(aes(y = y_center), alpha = 0.7, color = NA) +
  scale_fill_manual(values = IMPRINT[1:4]) +
  scale_color_manual(values = IMPRINT[1:4]) +
  labs(
    title = "area-stacked-confidence · R · ggplot2 · anyplot.ai",
    x = "Quarter",
    y = "Energy (MWh)",
    fill = "Source"
  ) +
  anyplot_theme +
  theme(
    legend.position = "top",
    legend.direction = "horizontal"
  ) +
  guides(color = "none")

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
