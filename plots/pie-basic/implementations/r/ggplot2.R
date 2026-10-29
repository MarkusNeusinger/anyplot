#' anyplot.ai
#' pie-basic: Basic Pie Chart
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 86/100 | Created: 2026-05-28

library(ggplot2)
library(dplyr)
library(ragg)

THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

IMPRINT_PALETTE <- c(
  "#009E73", "#C475FD", "#4467A3", "#BD8233",
  "#AE3030", "#2ABCCD", "#954477", "#99B314"
)

# Columns: set these to your table's column names
DEPARTMENT <- "Department"            # role: category
BUDGET     <- "Budget (million USD)"  # role: value

# Data: replace this block with your own table, for example df <- read.csv("budget.csv", check.names = FALSE)
df <- tibble::tibble(
  !!DEPARTMENT := c("R&D", "Marketing", "Operations", "Sales", "HR", "IT"),
  !!BUDGET     := c(32, 22, 18, 14, 10, 4)
)

# Plot: reads only df and the constants above
EXPLODE_OFFSET <- 0.12  # radial shift of the largest slice
LABEL_MIN_PCT  <- 5     # narrower slices get their label outside the pie

df <- df |>
  arrange(desc(.data[[BUDGET]])) |>
  mutate(
    category = factor(.data[[DEPARTMENT]], levels = unique(.data[[DEPARTMENT]])),
    value    = .data[[BUDGET]],
    pct      = value / sum(value) * 100,
    label    = sprintf("%.0f%%", pct),
    inside   = pct >= LABEL_MIN_PCT,
    # coord_polar stacks the last level first
    ymax     = rev(cumsum(rev(value))),
    ymin     = ymax - value,
    ymid     = (ymin + ymax) / 2,
    shift    = if_else(value == max(value), EXPLODE_OFFSET, 0),
    xmin     = shift,
    xmax     = 1 + shift,
    xlabel   = if_else(inside, shift + 0.65, xmax + 0.1)
  )

palette_named <- setNames(IMPRINT_PALETTE[seq_len(nrow(df))], levels(df$category))

p <- ggplot(df) +
  geom_rect(
    aes(xmin = xmin, xmax = xmax, ymin = ymin, ymax = ymax, fill = category),
    color     = PAGE_BG,
    linewidth = 0.8
  ) +
  geom_text(
    aes(x = xlabel, y = ymid, label = label, color = inside),

    size     = 3.8,
    fontface = "bold",
    show.legend = FALSE
  ) +
  scale_color_manual(values = c("TRUE" = "#FAF8F1", "FALSE" = INK)) +
  scale_x_continuous(limits = c(0, 1.45), expand = c(0, 0)) +
  scale_y_continuous(limits = c(0, sum(df$value)), expand = c(0, 0)) +
  coord_polar(theta = "y", start = 0) +
  scale_fill_manual(values = palette_named) +
  labs(
    title = "pie-basic · r · ggplot2 · anyplot.ai",
    fill  = DEPARTMENT
  ) +
  theme_void() +
  theme(
    plot.background     = element_rect(fill = PAGE_BG, color = PAGE_BG),
    plot.title          = element_text(
      color  = INK,
      size   = 12,
      hjust  = 0.5,
      face   = "bold",
      margin = margin(b = 10, t = 10)
    ),
    plot.title.position = "plot",
    legend.text         = element_text(color = INK_SOFT, size = 8),
    legend.title        = element_text(color = INK, size = 10),
    legend.background   = element_rect(fill = ELEVATED_BG, color = INK_SOFT, linewidth = 0.5),
    legend.key.size     = unit(0.5, "cm"),
    legend.margin       = margin(6, 6, 6, 6),
    plot.margin         = margin(30, 40, 30, 40)
  )

ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 6,
  height   = 6,
  units    = "in",
  dpi      = 400
)
