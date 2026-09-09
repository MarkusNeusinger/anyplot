#' anyplot.ai
#' survival-kaplan-meier: Kaplan-Meier Survival Plot
#' Library: ggplot2 | R 4.x
#' Quality: pending | Created: 2026-09-09

library(ggplot2)
library(dplyr)
library(survival)
library(ragg)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")

# --- Data: clinical trial follow-up (2 treatment arms, right-censored) -----
n_per_arm  <- 110
follow_up  <- 36  # months of administrative follow-up
arm        <- factor(rep(c("Standard care", "New therapy"), each = n_per_arm),
                      levels = c("Standard care", "New therapy"))
event_rate <- ifelse(arm == "Standard care", 1 / 17, 1 / 25)
event_time   <- rexp(2 * n_per_arm, rate = event_rate)
dropout_time <- runif(2 * n_per_arm, 18, follow_up)
patients <- tibble::tibble(
  time  = pmin(event_time, dropout_time, follow_up),
  event = as.integer(event_time <= pmin(dropout_time, follow_up)),
  arm   = arm
)

fit <- survfit(Surv(time, event) ~ arm, data = patients)
fit_summary <- summary(fit, censored = TRUE)

km_curve <- tibble::tibble(
  time     = fit_summary$time,
  surv     = fit_summary$surv,
  lower    = fit_summary$lower,
  upper    = fit_summary$upper,
  n_censor = fit_summary$n.censor,
  arm      = factor(sub("^arm=", "", as.character(fit_summary$strata)), levels = levels(arm))
)

# Prepend a t=0, survival=1 anchor per arm so the step curve starts at the top
km_start <- tibble::tibble(
  time = 0, surv = 1, lower = 1, upper = 1, n_censor = 0,
  arm = factor(levels(arm), levels = levels(arm))
)
km_curve <- bind_rows(km_start, km_curve) %>% arrange(arm, time)

# Stairstep confidence band: one rectangle per interval, held constant until
# the next event/censoring time (geom_ribbon interpolates linearly, which
# misrepresents a step function; geom_rect renders the true stairs instead)
km_band <- km_curve %>%
  group_by(arm) %>%
  mutate(time_end = lead(time, default = follow_up)) %>%
  ungroup()

censor_marks <- km_curve %>% filter(n_censor > 0)

log_rank   <- survdiff(Surv(time, event) ~ arm, data = patients)
p_value    <- 1 - pchisq(log_rank$chisq, length(log_rank$n) - 1)
p_label    <- if (p_value < 0.001) "p < 0.001" else sprintf("p = %.3f", p_value)

title_text <- "survival-kaplan-meier · r · ggplot2 · anyplot.ai"

# --- Plot --------------------------------------------------------------------
p <- ggplot(km_curve, aes(x = time, y = surv, color = arm, fill = arm)) +
  geom_rect(
    data = km_band,
    aes(xmin = time, xmax = time_end, ymin = lower, ymax = upper, fill = arm),
    inherit.aes = FALSE, alpha = 0.15, color = NA
  ) +
  geom_step(linewidth = 1.0) +
  geom_point(
    data = censor_marks, aes(x = time, y = surv, color = arm),
    shape = 3, size = 2.5, stroke = 1, show.legend = FALSE
  ) +
  scale_color_manual(values = IMPRINT_PALETTE) +
  scale_fill_manual(values = IMPRINT_PALETTE) +
  scale_y_continuous(labels = scales::percent_format(accuracy = 1), limits = c(0, 1)) +
  labs(
    title    = title_text,
    subtitle = sprintf("Log-rank test: %s", p_label),
    x        = "Time Since Enrollment (months)",
    y        = "Survival Probability",
    color    = "Treatment Arm",
    fill     = "Treatment Arm"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background    = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background   = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.y = element_line(color = INK, linewidth = 0.3),
    panel.grid.minor   = element_blank(),
    panel.grid.major.x = element_blank(),
    axis.title         = element_text(color = INK, size = 10),
    axis.text          = element_text(color = INK_SOFT, size = 8),
    axis.line          = element_line(color = INK_SOFT),
    plot.title         = element_text(color = INK, size = 12),
    plot.subtitle      = element_text(color = INK_SOFT, size = 9),
    legend.position        = "inside",
    legend.position.inside = c(0.82, 0.82),
    legend.background  = element_rect(fill = ELEVATED_BG, color = INK_SOFT, linewidth = 0.2),
    legend.text        = element_text(color = INK_SOFT, size = 8),
    legend.title       = element_text(color = INK, size = 9),
    plot.margin        = margin(10, 14, 10, 10)
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
