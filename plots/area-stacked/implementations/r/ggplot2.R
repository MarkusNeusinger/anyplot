#' anyplot.ai
#' area-stacked: Stacked Area Chart
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 88/100 | Created: 2026-08-17

library(ggplot2)
library(dplyr)
library(tidyr)
library(scales)
library(ragg)

set.seed(42)

# --- Theme tokens -------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

# Imprint palette (see prompts/default-style-guide.md "Categorical Palette")
IMPRINT_PALETTE <- c(
  "#009E73",  # 1 — Industrial (largest, brand green)
  "#4467A3",  # 3 — Transportation
  "#C475FD",  # 2 — Residential
  "#BD8233",  # 4 — Commercial
  "#2ABCCD"   # 6 — Agriculture
)

# --- Data -----------------------------------------------------------------
# Annual energy consumption by sector, largest contributor first so the
# stack reads largest-at-bottom (per spec notes).
years   <- 2010:2024
sectors <- c("Industrial", "Transportation", "Residential", "Commercial", "Agriculture")
base_twh  <- c(220, 150, 130, 90, 40)
trend_twh <- c(-1.5, 2.2, 1.6, 1.1, 0.3)  # electrification shifts share toward transport/residential

consumption <- vapply(seq_along(sectors), function(i) {
  pmax(base_twh[i] + trend_twh[i] * (years - years[1]) + rnorm(length(years), 0, 4), 5)
}, numeric(length(years)))

df <- tibble(
  year       = rep(years, times = length(sectors)),
  sector     = factor(rep(sectors, each = length(years)), levels = sectors),
  twh        = as.vector(consumption)
)

# --- Plot -------------------------------------------------------------------
p <- ggplot(df, aes(x = year, y = twh, fill = sector)) +
  geom_area(position = position_stack(reverse = TRUE), alpha = 0.88,
            color = PAGE_BG, linewidth = 0.3) +
  scale_fill_manual(values = IMPRINT_PALETTE, name = "Sector",
                     guide = guide_legend(reverse = TRUE)) +
  scale_x_continuous(breaks = seq(2010, 2024, by = 2), expand = c(0, 0)) +
  scale_y_continuous(labels = label_number(suffix = " TWh"),
                      expand = expansion(mult = c(0, 0.05))) +
  labs(
    title = "area-stacked · r · ggplot2 · anyplot.ai",
    x     = "Year",
    y     = "Energy Consumption"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.x = element_blank(),
    panel.grid.minor   = element_blank(),
    panel.grid.major.y = element_line(color = INK, linewidth = 0.15),
    axis.line          = element_line(color = INK_SOFT, linewidth = 0.3),
    axis.ticks         = element_blank(),
    axis.title         = element_text(color = INK, size = 10),
    axis.text          = element_text(color = INK_SOFT, size = 8),
    plot.title         = element_text(color = INK, size = 12),
    legend.background  = element_blank(),
    legend.key         = element_blank(),
    legend.text        = element_text(color = INK_SOFT, size = 8),
    legend.title       = element_text(color = INK, size = 10),
    legend.position     = "right"
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
