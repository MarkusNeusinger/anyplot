# anyplot.ai
# sunburst-basic: Basic Sunburst Chart
# Library: Makie.jl 0.22 | Julia 1.11
# Quality: pending | Created: 2026-07-26

using CairoMakie
using Colors

# --- Theme tokens -------------------------------------------------------------
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

const IMPRINT_PALETTE = [
    colorant"#009E73", colorant"#C475FD", colorant"#4467A3", colorant"#BD8233",
    colorant"#AE3030", colorant"#2ABCCD", colorant"#954477", colorant"#99B314",
]

# --- Data: repository storage breakdown by directory (MB) ---------------------
branches = [
    ("Source Code",   [("Core Engine", 420.0), ("API Layer", 180.0), ("UI Components", 260.0), ("Utilities", 90.0)]),
    ("Test Suite",    [("Unit Tests", 150.0), ("Integration Tests", 95.0), ("Fixtures", 40.0)]),
    ("Assets",        [("Images", 320.0), ("Fonts", 15.0), ("Icons", 60.0)]),
    ("Documentation", [("User Guides", 45.0), ("API Reference", 70.0), ("Tutorials", 25.0)]),
]

branch_totals = [sum(v for (_, v) in children) for (_, children) in branches]
grand_total = sum(branch_totals)

# --- Figure --------------------------------------------------------------------
fig = Figure(
    size            = (1200, 1200),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

title_str = "sunburst-basic · julia · makie · anyplot.ai"

ax = Axis(
    fig[1, 1];
    title           = title_str,
    titlesize       = 20,
    titlecolor      = INK,
    aspect          = DataAspect(),
    backgroundcolor = PAGE_BG,
)
hidedecorations!(ax)
hidespines!(ax)

r_hole  = 0.28
r_mid   = 0.62
r_outer = 1.0
n_arc   = 48

theta = 0.0
for (i, (name, children)) in enumerate(branches)
    global theta
    branch_color = IMPRINT_PALETTE[i]
    span = 2π * branch_totals[i] / grand_total

    outer_pts = [Point2f(r_mid * cos(t), r_mid * sin(t)) for t in range(theta, theta + span; length = n_arc)]
    inner_pts = [Point2f(r_hole * cos(t), r_hole * sin(t)) for t in range(theta + span, theta; length = n_arc)]
    poly!(ax, vcat(outer_pts, inner_pts); color = branch_color, strokecolor = PAGE_BG, strokewidth = 3)

    branch_lum = 0.299 * Float64(red(branch_color)) + 0.587 * Float64(green(branch_color)) + 0.114 * Float64(blue(branch_color))
    branch_label_color = branch_lum > 0.55 ? colorant"#1A1A17" : colorant"#FAF8F1"

    mid_angle = theta + span / 2
    if span > deg2rad(14)
        r_label = (r_hole + r_mid) / 2
        rot = (mid_angle > π / 2 && mid_angle < 3π / 2) ? mid_angle + π : mid_angle
        text!(ax, r_label * cos(mid_angle), r_label * sin(mid_angle);
              text = name, rotation = rot, align = (:center, :center),
              color = branch_label_color, fontsize = 15)
    end

    child_theta = theta
    for (j, (cname, cval)) in enumerate(children)
        cspan = span * cval / branch_totals[i]

        child_hsl = HSL(branch_color)
        child_l = clamp(child_hsl.l + 0.14 * j, 0.0, 0.92)
        child_color = RGB(HSL(child_hsl.h, child_hsl.s, child_l))

        c_outer = [Point2f(r_outer * cos(t), r_outer * sin(t)) for t in range(child_theta, child_theta + cspan; length = n_arc)]
        c_inner = [Point2f(r_mid * cos(t), r_mid * sin(t)) for t in range(child_theta + cspan, child_theta; length = n_arc)]
        poly!(ax, vcat(c_outer, c_inner); color = child_color, strokecolor = PAGE_BG, strokewidth = 3)

        child_lum = 0.299 * Float64(red(child_color)) + 0.587 * Float64(green(child_color)) + 0.114 * Float64(blue(child_color))
        child_label_color = child_lum > 0.55 ? colorant"#1A1A17" : colorant"#FAF8F1"

        cmid = child_theta + cspan / 2
        if cspan > deg2rad(10)
            r_label = (r_mid + r_outer) / 2
            rot = (cmid > π / 2 && cmid < 3π / 2) ? cmid + π : cmid
            text!(ax, r_label * cos(cmid), r_label * sin(cmid);
                  text = cname, rotation = rot, align = (:center, :center),
                  color = child_label_color, fontsize = 12)
        end

        child_theta += cspan
    end

    theta += span
end

xlims!(ax, -1.15, 1.15)
ylims!(ax, -1.15, 1.15)

# --- Save ------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
