# anyplot.ai
# sunburst-basic: Basic Sunburst Chart
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 88/100 | Created: 2026-07-26

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
# Source Code is broken down one level further into a grandchild ring; the
# other branches stop at 2 levels, which mirrors how real directory trees
# vary in depth (the spec allows 2-4 levels).
branches = [
    ("Source Code", [
        ("Core Engine",   420.0, [("Parser", 180.0), ("Renderer", 150.0), ("Optimizer", 90.0)]),
        ("API Layer",     180.0, [("REST", 100.0), ("GraphQL", 80.0)]),
        ("UI Components", 260.0, [("Components", 140.0), ("Hooks", 70.0), ("Styles", 50.0)]),
        ("Utilities",      90.0, [("Helpers", 50.0), ("Validators", 40.0)]),
    ]),
    ("Test Suite", [
        ("Unit Tests", 150.0, nothing),
        ("Integration Tests", 95.0, nothing),
        ("Fixtures", 40.0, nothing),
    ]),
    ("Assets", [
        ("Images", 320.0, nothing),
        ("Fonts", 15.0, nothing),
        ("Icons", 60.0, nothing),
    ]),
    ("Documentation", [
        ("User Guides", 45.0, nothing),
        ("API Reference", 70.0, nothing),
        ("Tutorials", 25.0, nothing),
    ]),
]

branch_totals = [sum(cval for (_, cval, _) in children) for (_, children) in branches]
grand_total = sum(branch_totals)

largest_leaf_name, largest_leaf_value = "", 0.0
for (_, children) in branches, (cname, cval, _) in children
    if cval > largest_leaf_value
        global largest_leaf_name, largest_leaf_value = cname, cval
    end
end

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

r_hole  = 0.24
r1      = 0.52   # branch ring outer / child ring inner
r2      = 0.78   # child ring outer / grandchild ring inner
r_outer = 1.00   # grandchild ring outer (only where a child has grandchildren)
n_arc   = 48
stroke_w = 1.5

legend_elems  = PolyElement[]
legend_labels = String[]

theta = 0.0
for (i, (name, children)) in enumerate(branches)
    global theta
    branch_color = IMPRINT_PALETTE[i]
    span = 2π * branch_totals[i] / grand_total

    outer_pts = [Point2f(r1 * cos(t), r1 * sin(t)) for t in range(theta, theta + span; length = n_arc)]
    inner_pts = [Point2f(r_hole * cos(t), r_hole * sin(t)) for t in range(theta + span, theta; length = n_arc)]
    poly!(ax, vcat(outer_pts, inner_pts); color = branch_color, strokecolor = PAGE_BG, strokewidth = stroke_w)

    push!(legend_elems, PolyElement(color = branch_color))
    push!(legend_labels, "$(name) · $(round(Int, branch_totals[i])) MB")

    branch_lum = 0.299 * Float64(red(branch_color)) + 0.587 * Float64(green(branch_color)) + 0.114 * Float64(blue(branch_color))
    branch_label_color = branch_lum > 0.55 ? colorant"#1A1A17" : colorant"#FAF8F1"

    mid_angle = theta + span / 2
    if span > deg2rad(14)
        r_label = (r_hole + r1) / 2
        rot = (mid_angle > π / 2 && mid_angle < 3π / 2) ? mid_angle + π : mid_angle
        text!(ax, r_label * cos(mid_angle), r_label * sin(mid_angle);
              text = name, rotation = rot, align = (:center, :center),
              color = branch_label_color, fontsize = 15)
    end

    child_theta = theta
    for (j, (cname, cval, grandchildren)) in enumerate(children)
        cspan = span * cval / branch_totals[i]

        child_hsl = HSL(branch_color)
        child_l = clamp(child_hsl.l + 0.14 * j, 0.0, 0.92)
        child_color = RGB(HSL(child_hsl.h, child_hsl.s, child_l))

        c_outer = [Point2f(r2 * cos(t), r2 * sin(t)) for t in range(child_theta, child_theta + cspan; length = n_arc)]
        c_inner = [Point2f(r1 * cos(t), r1 * sin(t)) for t in range(child_theta + cspan, child_theta; length = n_arc)]
        poly!(ax, vcat(c_outer, c_inner); color = child_color, strokecolor = PAGE_BG, strokewidth = stroke_w)

        child_lum = 0.299 * Float64(red(child_color)) + 0.587 * Float64(green(child_color)) + 0.114 * Float64(blue(child_color))
        child_label_color = child_lum > 0.55 ? colorant"#1A1A17" : colorant"#FAF8F1"

        cmid = child_theta + cspan / 2
        is_largest = cname == largest_leaf_name
        if cspan > deg2rad(10)
            r_label = (r1 + r2) / 2
            rot = (cmid > π / 2 && cmid < 3π / 2) ? cmid + π : cmid
            text!(ax, r_label * cos(cmid), r_label * sin(cmid);
                  text = is_largest ? "$(cname) ★" : cname, rotation = rot, align = (:center, :center),
                  color = child_label_color, fontsize = is_largest ? 13 : 12)
        end

        if grandchildren !== nothing
            gc_theta = child_theta
            for (k, (gname, gval)) in enumerate(grandchildren)
                gspan = cspan * gval / cval

                gc_l = clamp(child_hsl.l + 0.12 * k + 0.06, 0.0, 0.95)
                gc_color = RGB(HSL(child_hsl.h, child_hsl.s * 0.9, gc_l))

                g_outer = [Point2f(r_outer * cos(t), r_outer * sin(t)) for t in range(gc_theta, gc_theta + gspan; length = n_arc)]
                g_inner = [Point2f(r2 * cos(t), r2 * sin(t)) for t in range(gc_theta + gspan, gc_theta; length = n_arc)]
                poly!(ax, vcat(g_outer, g_inner); color = gc_color, strokecolor = PAGE_BG, strokewidth = stroke_w)

                gc_lum = 0.299 * Float64(red(gc_color)) + 0.587 * Float64(green(gc_color)) + 0.114 * Float64(blue(gc_color))
                gc_label_color = gc_lum > 0.55 ? colorant"#1A1A17" : colorant"#FAF8F1"

                gmid = gc_theta + gspan / 2
                if gspan > deg2rad(8)
                    r_label = (r2 + r_outer) / 2
                    rot = (gmid > π / 2 && gmid < 3π / 2) ? gmid + π : gmid
                    text!(ax, r_label * cos(gmid), r_label * sin(gmid);
                          text = gname, rotation = rot, align = (:center, :center),
                          color = gc_label_color, fontsize = 10)
                end

                gc_theta += gspan
            end
        end

        child_theta += cspan
    end

    theta += span
end

# --- Center focal point: grand total, as a storytelling anchor ----------------
text!(ax, 0.0, 0.055; text = "TOTAL", align = (:center, :center), color = INK_SOFT, fontsize = 11)
text!(ax, 0.0, -0.06; text = "$(round(Int, grand_total)) MB", align = (:center, :center), color = INK, fontsize = 17)

# --- Inset legend: branch totals, doubling as a Makie GridLayout value table --
Legend(
    fig[1, 1], legend_elems, legend_labels;
    tellwidth = false, tellheight = false,
    halign = :right, valign = :top,
    margin = (10, 10, 10, 10),
    framevisible = false, backgroundcolor = :transparent,
    labelcolor = INK_SOFT, labelsize = 11, patchsize = (12, 12), rowgap = 2,
)

xlims!(ax, -1.15, 1.15)
ylims!(ax, -1.15, 1.15)

# --- Save ------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
