#' anyplot.ai
#' area-basic: Basic Area Chart
#' Library: ggplot2 4.0.3 | R 4.6.1
#' Quality: 83/100 | Updated: 2026-10-29

library(ggplot2)
library(scales)
library(ragg)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
# Raise alpha in dark theme — alpha=0.35 over #1A1A17 composites to near-opaque forest green
FILL_ALPHA  <- if (THEME == "light") 0.40 else 0.50

IMPRINT_PALETTE <- c(
  "#009E73", "#C475FD", "#4467A3", "#BD8233",
  "#AE3030", "#2ABCCD", "#954477", "#99B314"
)

# Columns: set these to your table's column names
DATE     <- "Date (2023)"        # role: x
VISITORS <- "Daily visitors"     # role: y

# Data: replace this block with your own table, for example df <- read.csv("visitors.csv", check.names = FALSE)
# Daily website visitors (thousands) over 13 weeks starting Monday Jan 2 2023
set.seed(42)
days <- seq.Date(as.Date("2023-01-02"), by = "day", length.out = 91)
weekend <- as.integer(format(days, "%u")) >= 6L
base_visitors <- 8.5 + 0.04 * seq_along(days)
weekly_effect <- ifelse(weekend, -2.5, 0.8)
visitors_k <- round(pmax(1, base_visitors + weekly_effect + rnorm(length(days), 0, 0.5)), 1)

df <- tibble::tibble(
  !!DATE     := days,
  !!VISITORS := visitors_k
)

# Plot: reads only df and the constants above
plot_title <- "area-basic · r · ggplot2 · anyplot.ai"

p <- ggplot(df, aes(x = .data[[DATE]], y = .data[[VISITORS]])) +
  geom_area(fill = IMPRINT_PALETTE[1], alpha = FILL_ALPHA) +
  geom_line(color = IMPRINT_PALETTE[1], linewidth = 0.9) +
  scale_x_date(date_labels = "%b %d", date_breaks = "2 weeks") +
  scale_y_continuous(
    labels = label_comma(suffix = "K", accuracy = 1),
    limits = c(0, NA),
    expand = expansion(mult = c(0, 0.08))
  ) +
  labs(title = plot_title, x = DATE, y = VISITORS) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background    = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background   = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.x = element_blank(),
    panel.grid.minor.x = element_blank(),
    panel.grid.major.y = element_line(color = alpha(INK, 0.15), linewidth = 0.3),
    panel.grid.minor.y = element_blank(),
    panel.border       = element_blank(),
    axis.line.x        = element_line(color = INK_SOFT, linewidth = 0.4),
    axis.ticks.x       = element_line(color = INK_SOFT, linewidth = 0.3),
    axis.ticks.y       = element_blank(),
    axis.title         = element_text(color = INK,      size = 10),
    axis.text          = element_text(color = INK_SOFT, size = 8),
    axis.text.x        = element_text(angle = 30, hjust = 1),
    plot.title         = element_text(color = INK,      size = 12, face = "bold"),
    plot.margin        = margin(20, 30, 15, 20, unit = "pt")
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
