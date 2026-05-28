#' anyplot.ai
#' bar-basic: Basic Bar Chart
#' Library: ggplot2 3.5.1 | R 4.4.1

library(ggplot2)
library(ragg)

# Theme tokens
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
GRID_COLOR  <- adjustcolor(INK, alpha.f = 0.15)

ANYPLOT_PALETTE <- c(
  "#009E73", "#C475FD", "#4467A3", "#BD8233",
  "#AE3030", "#2ABCCD", "#954477", "#99B314"
)

# Data - Annual budget by department (USD millions), descending order
departments <- c(
  "Engineering", "R&D", "Operations", "Sales",
  "Marketing", "Finance", "Design", "HR"
)
budgets     <- c(48.5, 42.1, 35.7, 31.2, 22.8, 18.4, 14.9, 11.3)
mean_budget <- mean(budgets)

df <- data.frame(
  department = factor(departments, levels = departments),
  budget     = budgets,
  highlight  = ifelse(departments == "Engineering", "top", "rest")
)

# Plot
plot_title <- "bar-basic · r · ggplot2 · anyplot.ai"

p <- ggplot(df, aes(x = department, y = budget, fill = highlight)) +
  geom_col(width = 0.70) +
  geom_hline(
    yintercept = mean_budget,
    linetype   = "dashed",
    color      = INK_SOFT,
    linewidth  = 0.5
  ) +
  annotate(
    "text",
    x      = 5,
    y      = mean_budget,
    label  = sprintf("avg $%.1fM", mean_budget),
    vjust  = -0.4,
    hjust  = 0,
    size   = 2.5,
    color  = INK_SOFT
  ) +
  geom_text(
    aes(label = sprintf("$%.1fM", budget)),
    vjust = -0.5,
    size  = 2.8,
    color = INK_SOFT
  ) +
  scale_fill_manual(
    values = c(
      "top"  = ANYPLOT_PALETTE[1],
      "rest" = adjustcolor(ANYPLOT_PALETTE[1], alpha.f = 0.45)
    ),
    guide = "none"
  ) +
  scale_y_continuous(
    expand = expansion(mult = c(0, 0.18)),
    labels = function(x) paste0("$", x, "M")
  ) +
  labs(
    title = plot_title,
    x     = "Department",
    y     = "Annual Budget (USD Millions)"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background    = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background   = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.y = element_line(color = GRID_COLOR, linewidth = 0.4),
    panel.grid.major.x = element_blank(),
    panel.grid.minor   = element_blank(),
    axis.title         = element_text(color = INK,      size = 10),
    axis.text          = element_text(color = INK_SOFT, size = 8),
    plot.title         = element_text(color = INK,      size = 12, face = "bold"),
    axis.line.x        = element_line(color = INK_SOFT, linewidth = 0.5),
    axis.line.y        = element_blank(),
    axis.ticks         = element_blank(),
    plot.margin        = margin(t = 20, r = 20, b = 10, l = 10, unit = "pt")
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
