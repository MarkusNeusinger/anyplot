# anyplot.ai
# chernoff-basic: Chernoff Faces for Multivariate Data
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 88/100 | Created: 2026-09-02

using CairoMakie
using Colors
using Random

Random.seed!(42)

# --- Theme tokens -------------------------------------------------------------
const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG      = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const ELEVATED_BG  = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
const INK          = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT     = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const BRAND        = colorant"#009E73"  # Imprint palette position 1 -- ALWAYS first series

# --- Data: patient vital-sign profiles -----------------------------------------
n = 12
patient_ids = [string("P", lpad(i, 2, '0')) for i in 1:n]

resting_heart_rate = clamp.(72 .+ 12 .* randn(n), 50, 110)     # bpm            -> eye size
systolic_bp        = clamp.(122 .+ 14 .* randn(n), 95, 165)    # mmHg           -> face width
cholesterol        = clamp.(195 .+ 30 .* randn(n), 130, 280)   # mg/dL          -> eyebrow slant
bmi                = clamp.(26 .+ 4 .* randn(n), 18, 38)       # kg/m^2         -> face height
blood_glucose      = clamp.(100 .+ 18 .* randn(n), 75, 160)    # mg/dL          -> mouth curvature
sleep_hours        = clamp.(6.8 .+ 1.1 .* randn(n), 4.5, 9.0)  # hours          -> mouth width
respiratory_rate   = clamp.(15 .+ 2.5 .* randn(n), 11, 22)     # breaths/minute -> nose length

# Min-max normalize each variable to [0, 1] before mapping to a facial feature
eye_size_n    = (resting_heart_rate .- minimum(resting_heart_rate)) ./ (maximum(resting_heart_rate) - minimum(resting_heart_rate))
face_width_n  = (systolic_bp .- minimum(systolic_bp)) ./ (maximum(systolic_bp) - minimum(systolic_bp))
eyebrow_n     = (cholesterol .- minimum(cholesterol)) ./ (maximum(cholesterol) - minimum(cholesterol))
face_height_n = (bmi .- minimum(bmi)) ./ (maximum(bmi) - minimum(bmi))
mouth_curve_n = (blood_glucose .- minimum(blood_glucose)) ./ (maximum(blood_glucose) - minimum(blood_glucose))
mouth_width_n = (sleep_hours .- minimum(sleep_hours)) ./ (maximum(sleep_hours) - minimum(sleep_hours))
nose_len_n    = (respiratory_rate .- minimum(respiratory_rate)) ./ (maximum(respiratory_rate) - minimum(respiratory_rate))

# --- Grid layout: 4 columns x 3 rows -------------------------------------------
ncols, nrows = 4, 3
spacing_x, spacing_y = 2.0, 2.6

centers = Point2f[]
for i in 1:n
    row = div(i - 1, ncols)
    col = mod(i - 1, ncols)
    push!(centers, Point2f(col * spacing_x, -row * spacing_y))
end

rx_max = 0.55 * 1.30
ry_max = 0.68 * 1.30

# --- Figure -------------------------------------------------------------------
fig = Figure(
    resolution      = (1200, 1200),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title             = "chernoff-basic · julia · makie · anyplot.ai",
    titlesize         = 20,
    titlecolor        = INK,
    backgroundcolor   = PAGE_BG,
    aspect            = DataAspect(),
)
hidedecorations!(ax)
hidespines!(ax)

xlims!(ax, -rx_max - 0.3, (ncols - 1) * spacing_x + rx_max + 0.3)
ylims!(ax, -(nrows - 1) * spacing_y - ry_max - 0.55, ry_max + 0.3)

# --- Draw one Chernoff face per patient ----------------------------------------
for i in 1:n
    cx, cy = centers[i]

    rx = 0.55 * (0.75 + 0.55 * face_width_n[i])
    ry = 0.68 * (0.75 + 0.55 * face_height_n[i])

    face_theta = range(0, 2π; length=80)
    face_pts = [Point2f(cx + rx * cos(t), cy + ry * sin(t)) for t in face_theta]
    poly!(ax, face_pts; color=ELEVATED_BG, strokecolor=BRAND, strokewidth=3)

    eye_r = 0.05 + 0.09 * eye_size_n[i]
    eye_dx = rx * 0.42
    eye_y = cy + ry * 0.15
    eye_theta = range(0, 2π; length=40)

    for side in (-1, 1)
        ex = cx + side * eye_dx
        eye_pts = [Point2f(ex + eye_r * cos(t), eye_y + eye_r * sin(t)) for t in eye_theta]
        poly!(ax, eye_pts; color=PAGE_BG, strokecolor=INK, strokewidth=2)
        pupil_pts = [Point2f(ex + 0.4 * eye_r * cos(t), eye_y + 0.4 * eye_r * sin(t)) for t in eye_theta]
        poly!(ax, pupil_pts; color=INK, strokewidth=0)
    end

    brow_half_len = rx * 0.32
    brow_y = eye_y + eye_r * 1.9
    brow_slope = (0.5 - eyebrow_n[i]) * 0.32 * ry

    for (side, mirror) in ((-1, 1), (1, -1))
        bx = cx + side * eye_dx
        dy = mirror * brow_slope
        lines!(ax, [Point2f(bx - brow_half_len, brow_y - dy), Point2f(bx + brow_half_len, brow_y + dy)];
               color=INK_SOFT, linewidth=4)
    end

    nose_len = ry * (0.22 + 0.30 * nose_len_n[i])
    nose_top = cy + ry * 0.02
    lines!(ax, [Point2f(cx, nose_top), Point2f(cx, nose_top - nose_len)]; color=INK_SOFT, linewidth=2.5)

    mouth_width = rx * (0.55 + 0.55 * mouth_width_n[i])
    mouth_base_y = cy - ry * 0.42
    mouth_a = (0.5 - mouth_curve_n[i]) * 0.9 * ry / max((mouth_width / 2)^2, 1e-6)
    mouth_xs = range(-mouth_width / 2, mouth_width / 2; length=30)
    mouth_pts = [Point2f(cx + xv, mouth_base_y + mouth_a * xv^2) for xv in mouth_xs]
    lines!(ax, mouth_pts; color=INK, linewidth=3.5)

    text!(ax, cx, cy - ry - 0.16; text=patient_ids[i], color=INK_SOFT, fontsize=13,
          align=(:center, :top))
end

# --- Save -----------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
