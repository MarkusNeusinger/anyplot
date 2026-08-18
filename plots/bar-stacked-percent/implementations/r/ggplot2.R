#' anyplot.ai
#' bar-stacked-percent: 100% Stacked Bar Chart
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 90/100 | Created: 2026-08-18

library(ggplot2)
library(dplyr)
library(scales)
library(ragg)

set.seed(42)

# --- Theme tokens ------------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

# Imprint palette — categorical, theme-independent
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Fixed (theme-independent) label inks, chosen per segment fill's own
# luminance so percentage labels stay legible regardless of page theme.
LABEL_DARK  <- "#1A1A17"
LABEL_LIGHT <- "#FFFDF6"

# --- Data ---------------------------------------------------------------------
fiscal_years <- c("FY2021", "FY2022", "FY2023", "FY2024", "FY2025")
categories   <- c("Compute", "Storage", "Networking", "Support & Security")

base_spend <- c(
  "Compute"             = 24,
  "Storage"             = 12,
  "Networking"          = 7,
  "Support & Security"  = 5
)
compute_growth <- c(0, 4, 9, 15, 22)  # AI-driven compute demand outpaces other spend

df <- expand.grid(fiscal_year = fiscal_years, category = categories, stringsAsFactors = FALSE) %>%
  mutate(
    fiscal_year    = factor(fiscal_year, levels = fiscal_years),
    category       = factor(category, levels = categories),
    year_idx       = as.integer(fiscal_year),
    spend_millions = base_spend[as.character(category)] +
      ifelse(category == "Compute", compute_growth[year_idx], 0) +
      round(rnorm(n(), mean = 0, sd = 1.4), 1)
  ) %>%
  group_by(fiscal_year) %>%
  mutate(share = spend_millions / sum(spend_millions)) %>%
  ungroup() %>%
  mutate(label_text = ifelse(share >= 0.05, sprintf("%.0f%%", share * 100), ""))

label_ink <- c(
  "Compute"             = LABEL_DARK,
  "Storage"             = LABEL_DARK,
  "Networking"          = LABEL_LIGHT,
  "Support & Security"  = LABEL_DARK
)

# --- Plot ----------------------------------------------------------------------
title_text <- "Cloud Infrastructure Spend Mix · bar-stacked-percent · r · ggplot2 · anyplot.ai"
title_size <- round(12 * min(1, 67 / nchar(title_text)))

p <- ggplot(df, aes(x = fiscal_year, y = spend_millions, fill = category)) +
  geom_col(position = "fill", width = 0.65, color = PAGE_BG, linewidth = 1.2) +
  geom_text(
    aes(label = label_text, color = category),
    position  = position_fill(vjust = 0.5),
    size      = 3.4,
    fontface  = "bold",
    show.legend = FALSE
  ) +
  scale_y_continuous(labels = percent_format(), expand = c(0, 0)) +
  scale_fill_manual(values = IMPRINT_PALETTE, name = "Spend Category") +
  scale_color_manual(values = label_ink, guide = "none") +
  labs(
    title = title_text,
    x     = "Fiscal Year",
    y     = "Share of Annual Cloud Spend"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background     = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background     = element_rect(fill = PAGE_BG, color = NA),
    panel.grid           = element_blank(),
    axis.line.x          = element_line(color = INK_SOFT, linewidth = 0.4),
    axis.ticks           = element_blank(),
    axis.title           = element_text(color = INK, size = 10),
    axis.text            = element_text(color = INK_SOFT, size = 8),
    plot.title           = element_text(color = INK, size = title_size, margin = margin(b = 14)),
    legend.title         = element_text(color = INK, size = 10),
    legend.text          = element_text(color = INK_SOFT, size = 8),
    legend.key           = element_rect(fill = PAGE_BG, color = NA),
    plot.margin          = margin(t = 16, r = 16, b = 10, l = 10)
  )

# --- Save -----------------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 8,
  height   = 4.5,
  units    = "in",
  dpi      = 400
)
