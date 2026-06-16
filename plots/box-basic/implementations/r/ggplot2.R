#' anyplot.ai
#' box-basic: Basic Box Plot
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 92/100 | Created: 2026-05-28

library(ggplot2)
library(scales)
library(ragg)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
INK_MUTED   <- if (THEME == "light") "#6B6A63" else "#A8A79F"
IMPRINT_PALETTE <- c(
    "#009E73", "#C475FD", "#4467A3", "#BD8233",
    "#AE3030", "#2ABCCD", "#954477", "#99B314"
)

# --- Data -------------------------------------------------------------------
departments <- c("Engineering", "Marketing", "Sales", "Design", "Research")
dept_means  <- c(95000, 72000, 78000, 82000, 105000)
dept_sds    <- c(18000, 12000, 15000, 13000, 20000)
n_per_dept  <- 80

dept_data <- lapply(seq_along(departments), function(i) {
    data.frame(
        department = departments[i],
        salary     = rnorm(n_per_dept, mean = dept_means[i], sd = dept_sds[i])
    )
})

df <- do.call(rbind, dept_data)
df$department <- factor(df$department, levels = departments)

# --- Plot -------------------------------------------------------------------
p <- ggplot(df, aes(x = department, y = salary, fill = department)) +
    # Individual salary points behind boxes — exposes distribution shape
    geom_jitter(
        aes(color = department),
        width       = 0.18,
        alpha       = 0.25,
        size        = 0.9,
        show.legend = FALSE
    ) +
    # Box plot overlaid on jitter; suppress default outliers (jitter shows all)
    geom_boxplot(
        color         = INK_SOFT,
        linewidth     = 0.6,
        outlier.shape = NA,
        width         = 0.55,
        alpha         = 0.85
    ) +
    # Diamond marker at the department mean — reveals mean/median divergence
    stat_summary(
        fun    = mean,
        geom   = "point",
        shape  = 23,
        size   = 2.8,
        fill   = PAGE_BG,
        color  = INK_SOFT,
        stroke = 0.8
    ) +
    scale_fill_manual(values = IMPRINT_PALETTE[1:5], guide = "none") +
    scale_color_manual(values = IMPRINT_PALETTE[1:5], guide = "none") +
    scale_y_continuous(
        labels = label_dollar(scale = 0.001, suffix = "k"),
        expand = expansion(mult = c(0.05, 0.08))
    ) +
    labs(
        title    = "box-basic · r · ggplot2 · anyplot.ai",
        subtitle = "Research leads in both median pay and spread; ◆ marks the department mean",
        x        = "Department",
        y        = "Annual Salary (USD)"
    ) +
    theme_minimal(base_size = 8) +
    theme(
        plot.background    = element_rect(fill = PAGE_BG, color = PAGE_BG),
        panel.background   = element_rect(fill = PAGE_BG, color = NA),
        panel.border       = element_blank(),
        panel.grid.major.y = element_line(color = INK_SOFT, linewidth = 0.2),
        panel.grid.major.x = element_blank(),
        panel.grid.minor   = element_blank(),
        axis.line.x        = element_line(color = INK_SOFT, linewidth = 0.4),
        axis.line.y        = element_line(color = INK_SOFT, linewidth = 0.4),
        axis.title         = element_text(color = INK,      size = 10),
        axis.text          = element_text(color = INK_SOFT, size = 8),
        plot.title         = element_text(
            color  = INK,
            size   = 12,
            margin = margin(b = 2)
        ),
        plot.subtitle      = element_text(
            color  = INK_MUTED,
            size   = 8,
            margin = margin(b = 10)
        ),
        plot.margin = margin(t = 16, r = 20, b = 16, l = 16)
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
