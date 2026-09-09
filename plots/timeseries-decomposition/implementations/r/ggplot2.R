#' anyplot.ai
#' timeseries-decomposition: Time Series Decomposition Plot
#' Library: ggplot2 | R 4.4
#' Quality: pending | Created: 2026-09-09

library(ggplot2)
library(dplyr)
library(tidyr)
library(ragg)

set.seed(42)

# --- Theme tokens -------------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
INK_MUTED   <- if (THEME == "light") "#6B6A63" else "#A8A79F"

# Imprint palette (see prompts/default-style-guide.md "Categorical Palette")
IMPRINT_PALETTE <- c(
  "#009E73", # 1 - brand green (Original)
  "#C475FD", # 2 - lavender
  "#4467A3", # 3 - blue (Trend)
  "#BD8233"  # 4 - ochre (Seasonal)
)

# --- Data: monthly retail sales over 10 years, additive decomposition --------
n_years   <- 10
n_months  <- n_years * 12
month_idx <- 0:(n_months - 1)

trend_component    <- 520 + 7.5 * month_idx
seasonal_component <- 65 * sin(2 * pi * month_idx / 12) + 30 * cos(2 * pi * month_idx / 6)
noise               <- rnorm(n_months, mean = 0, sd = 22)
retail_sales        <- trend_component + seasonal_component + noise

dates <- seq(as.Date("2015-01-01"), by = "month", length.out = n_months)
sales_ts <- ts(retail_sales, start = c(2015, 1), frequency = 12)
decomp <- decompose(sales_ts, type = "additive")

component_levels <- c("Original", "Trend", "Seasonal", "Residual")

df <- tibble(
  date     = dates,
  Original = as.numeric(decomp$x),
  Trend    = as.numeric(decomp$trend),
  Seasonal = as.numeric(decomp$seasonal),
  Residual = as.numeric(decomp$random)
) %>%
  pivot_longer(cols = -date, names_to = "component", values_to = "value") %>%
  mutate(component = factor(component, levels = component_levels))

component_colors <- c(
  "Original" = IMPRINT_PALETTE[1],
  "Trend"    = IMPRINT_PALETTE[3],
  "Seasonal" = IMPRINT_PALETTE[4],
  "Residual" = INK_MUTED
)

zero_ref <- tibble(
  component = factor("Residual", levels = component_levels),
  yint      = 0
)

# --- Title (fontsize scaled to length; baseline adjusted for the narrower
#     6in square canvas vs. the 8in landscape canvas the 67-char/12pt
#     baseline was calibrated against) ------------------------------------
title_text        <- "timeseries-decomposition · r · ggplot2 · anyplot.ai"
title_len         <- nchar(title_text)
square_baseline   <- 67 * (6 / 8)
title_fontsize    <- if (title_len > square_baseline) {
  round(12 * square_baseline / title_len)
} else {
  12
}
title_fontsize <- max(title_fontsize, 8)

# --- Plot -----------------------------------------------------------------------
p <- ggplot(df, aes(x = date, y = value, color = component)) +
  geom_line(
    data = filter(df, component %in% c("Original", "Trend", "Seasonal")),
    linewidth = 1.0
  ) +
  geom_hline(
    data = zero_ref, aes(yintercept = yint),
    color = INK_SOFT, linewidth = 0.4, linetype = "dashed"
  ) +
  geom_point(
    data = filter(df, component == "Residual"),
    size = 1.6, alpha = 0.75
  ) +
  facet_wrap(~component, ncol = 1, scales = "free_y") +
  scale_color_manual(values = component_colors, guide = "none") +
  scale_x_date(date_breaks = "2 years", date_labels = "%Y") +
  labs(
    title = title_text,
    x     = "Date",
    y     = "Retail Sales (thousands $)"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background     = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background    = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.x  = element_blank(),
    panel.grid.minor    = element_blank(),
    panel.grid.major.y  = element_line(color = INK, linewidth = 0.25),
    panel.spacing       = unit(1.1, "lines"),
    strip.background    = element_rect(fill = ELEVATED_BG, color = NA),
    strip.text          = element_text(color = INK, size = 10, face = "bold"),
    axis.title          = element_text(color = INK, size = 10),
    axis.text           = element_text(color = INK_SOFT, size = 8),
    axis.line           = element_line(color = INK_SOFT),
    plot.title          = element_text(color = INK, size = title_fontsize, face = "bold"),
    legend.position      = "none"
  )

# --- Save -----------------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 6,
  height   = 6,
  units    = "in",
  dpi      = 400
)
