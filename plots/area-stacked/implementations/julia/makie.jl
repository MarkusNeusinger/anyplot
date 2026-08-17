# anyplot.ai
# area-stacked: Stacked Area Chart
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 89/100 | Created: 2026-08-17

using CairoMakie
using Colors
using Random

Random.seed!(42)

# --- Theme tokens -------------------------------------------------------
const THEME      = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const ELEVATED_BG = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const IMPRINT_PALETTE = [
    colorant"#009E73", colorant"#C475FD", colorant"#4467A3", colorant"#BD8233",
    colorant"#AE3030", colorant"#2ABCCD", colorant"#954477", colorant"#99B314",
]

# --- Data -----------------------------------------------------------------
n_months = 18
months = 1:n_months
month_labels = [
    "Jan 2024", "Feb 2024", "Mar 2024", "Apr 2024", "May 2024", "Jun 2024",
    "Jul 2024", "Aug 2024", "Sep 2024", "Oct 2024", "Nov 2024", "Dec 2024",
    "Jan 2025", "Feb 2025", "Mar 2025", "Apr 2025", "May 2025", "Jun 2025",
]

organic_search = max.(38 .+ 0.9 .* months .+ 3 .* sin.(months ./ 2.5) .+ randn(n_months) .* 2.2, 5)
direct         = max.(24 .+ 0.25 .* months .+ randn(n_months) .* 1.8, 4)
referral       = max.(16 .- 0.1 .* months .+ randn(n_months) .* 1.3, 3)
social_media   = max.(9 .+ 0.55 .* months .+ randn(n_months) .* 1.4, 2)
email          = max.(7 .+ 0.05 .* months .+ randn(n_months) .* 0.9, 1)

cum0 = zeros(n_months)
cum1 = cum0 .+ organic_search
cum2 = cum1 .+ direct
cum3 = cum2 .+ referral
cum4 = cum3 .+ social_media
cum5 = cum4 .+ email

# Callout: Organic Search visibly accelerates from ~month 10 onward.
callout_idx = 13
callout_x   = months[callout_idx]
callout_y   = (cum0[callout_idx] + cum1[callout_idx]) / 2

# --- Plot -------------------------------------------------------------------
fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title             = "area-stacked · julia · makie · anyplot.ai",
    titlesize         = 20,
    titlecolor        = INK,
    xlabel            = "Month",
    ylabel            = "Website Visits (thousands)",
    xlabelsize        = 14,
    ylabelsize        = 14,
    xlabelcolor       = INK,
    ylabelcolor       = INK,
    xticklabelsize    = 12,
    yticklabelsize    = 12,
    xticklabelcolor   = INK_SOFT,
    yticklabelcolor   = INK_SOFT,
    xtickcolor        = INK_SOFT,
    ytickcolor        = INK_SOFT,
    backgroundcolor   = PAGE_BG,
    topspinevisible   = false,
    rightspinevisible = false,
    leftspinecolor    = INK_SOFT,
    bottomspinecolor  = INK_SOFT,
    xgridvisible      = false,
    ygridcolor        = RGBAf(INK.r, INK.g, INK.b, 0.2),
    yticks            = LinearTicks(7),
    xminorgridvisible = false,
    yminorgridvisible = false,
    xticks            = (months[1:3:end], month_labels[1:3:end]),
)

band!(ax, months, cum0, cum1; color = (IMPRINT_PALETTE[1], 0.88), label = "Organic Search")
band!(ax, months, cum1, cum2; color = (IMPRINT_PALETTE[2], 0.88), label = "Direct")
band!(ax, months, cum2, cum3; color = (IMPRINT_PALETTE[3], 0.88), label = "Referral")
band!(ax, months, cum3, cum4; color = (IMPRINT_PALETTE[4], 0.88), label = "Social Media")
band!(ax, months, cum4, cum5; color = (IMPRINT_PALETTE[5], 0.88), label = "Email")

for cum in (cum1, cum2, cum3, cum4)
    lines!(ax, months, cum; color = PAGE_BG, linewidth = 2)
end

text!(
    ax, callout_x, callout_y;
    text     = "Organic search\naccelerating",
    color    = PAGE_BG,
    fontsize = 12,
    font     = :bold,
    align    = (:center, :center),
    justification = :center,
)

xlims!(ax, months[1], months[end])
ylims!(ax, 0, maximum(cum5) * 1.05)

Legend(
    fig[1, 2], ax;
    labelsize       = 12,
    labelcolor      = INK,
    backgroundcolor = (ELEVATED_BG, 0.6),
    framevisible    = false,
    patchsize       = (14, 14),
    padding         = (12, 12, 10, 10),
    rowgap          = 6,
)
colsize!(fig.layout, 1, Relative(0.82))

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
