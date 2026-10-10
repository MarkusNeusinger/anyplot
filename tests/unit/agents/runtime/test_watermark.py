"""Tests for agents/anyplot/render/watermark.py: the footer strip of user plots."""

import hashlib
import io

import pytest
from PIL import Image, ImageColor, ImageFont

from agents.anyplot.code import export
from agents.anyplot.render import watermark
from agents.anyplot.render.backends.fake import fixture_png
from agents.anyplot.render.contract import THEMES, Theme
from agents.anyplot.render.watermark import DOT_ALPHA, GAP_PX, HAIRLINE_ALPHA, INSET_PX, PAGE, add_footer, footer_layout
from core.palette import GREEN, neutral_for


FONT_SHA256 = {
    "JetBrainsMono-Regular.ttf": "a0bf60ef0f83c5ed4d7a75d45838548b1f6873372dfac88f71804491898d138f",
    "JetBrainsMono-Bold.ttf": "5590990c82e097397517f275f430af4546e1c45cff408bde4255dad142479dcb",
    "OFL.txt": "30f0c136e3c88e422d0791acd97238870f9054a9729bc34cf2ff0d4ed8cac4ad",
}
SIZES = [((3200, 1800), (3200, 1864)), ((2400, 2400), (2400, 2448)), ((3200, 1810), (3200, 1874))]


def rgb(colour: str) -> tuple[int, int, int]:
    red, green, blue = ImageColor.getrgb(colour)[:3]
    return red, green, blue


def blend(under: str, over: str, alpha: float) -> tuple[int, int, int]:
    """`over` at `alpha` (as 8 bits, like the overlay) on an opaque `under`."""
    weight = round(alpha * 255) / 255
    (r0, g0, b0), (r1, g1, b1) = rgb(under), rgb(over)
    return (
        round(r0 * (1 - weight) + r1 * weight),
        round(g0 * (1 - weight) + g1 * weight),
        round(b0 * (1 - weight) + b1 * weight),
    )


def decode(png: bytes) -> Image.Image:
    with Image.open(io.BytesIO(png)) as image:
        image.load()
        return image.copy()


@pytest.fixture(scope="module")
def footers() -> dict[tuple[Theme, tuple[int, int]], tuple[bytes, Image.Image]]:
    """Every theme and size once: the raw fixture and the decoded result (a composition takes ~0.2 s)."""
    made = {}
    for theme in THEMES:
        for size, _ in SIZES:
            raw = fixture_png(theme, size)
            made[(theme, size)] = (raw, decode(add_footer(raw, theme=theme, spec_id="scatter-basic")))
    return made


class TestCanvas:
    @pytest.mark.parametrize("theme", THEMES)
    @pytest.mark.parametrize(("size", "expected"), SIZES)
    def test_the_strip_is_appended_below_the_render(
        self, footers: dict, theme: Theme, size: tuple[int, int], expected: tuple[int, int]
    ) -> None:
        _, image = footers[(theme, size)]

        assert image.size == expected
        assert image.mode == "RGB"
        assert footer_layout(*size, spec_id="scatter-basic").height == expected[1]

    @pytest.mark.parametrize("theme", THEMES)
    @pytest.mark.parametrize(("size", "expected"), SIZES)
    def test_the_raw_render_is_pixel_identical(
        self, footers: dict, theme: Theme, size: tuple[int, int], expected: tuple[int, int]
    ) -> None:
        raw, image = footers[(theme, size)]

        assert image.crop((0, 0, *size)).tobytes() == decode(raw).convert("RGB").tobytes()

    @pytest.mark.parametrize("theme", THEMES)
    def test_the_strip_is_the_page_colour_of_its_theme(self, footers: dict, theme: Theme) -> None:
        _, image = footers[(theme, (3200, 1800))]
        layout = footer_layout(3200, 1800, spec_id="scatter-basic")
        page = rgb(PAGE[theme])

        middle = image.crop((int(layout.left_span[1]) + 20, 1801, int(layout.right_span[0]) - 20, 1864))
        assert middle.getcolors() == [(middle.width * middle.height, page)]
        for x0, x1 in ((0, int(INSET_PX) - 2), (3200 - int(INSET_PX) + 2, 3200)):
            margin = image.crop((x0, 1801, x1, 1864))
            assert margin.getcolors() == [(margin.width * margin.height, page)]

    @pytest.mark.parametrize("theme", THEMES)
    @pytest.mark.parametrize(("size", "expected"), SIZES)
    def test_the_hairline_is_the_strips_top_row_and_spares_the_plot(
        self, footers: dict, theme: Theme, size: tuple[int, int], expected: tuple[int, int]
    ) -> None:
        raw, image = footers[(theme, size)]
        width, height = size
        hairline = image.crop((0, height, width, height + 1))

        assert hairline.getcolors() == [(width, blend(PAGE[theme], neutral_for(theme), HAIRLINE_ALPHA))]
        last_row = (0, height - 1, width, height)
        assert image.crop(last_row).tobytes() == decode(raw).crop(last_row).tobytes()
        assert image.getpixel((width // 2, height + 1)) == rgb(PAGE[theme])

    def test_the_composition_is_deterministic(self) -> None:
        raw = fixture_png("dark")

        assert add_footer(raw, theme="dark", spec_id="line-multi") == add_footer(
            raw, theme="dark", spec_id="line-multi"
        )

    def test_a_palette_or_alpha_render_is_composed_on_its_rgb_pixels(self) -> None:
        image = Image.new("RGBA", (3200, 1800), (250, 248, 241, 255))
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")

        out = decode(add_footer(buffer.getvalue(), theme="light", spec_id="scatter-basic"))

        assert (out.mode, out.size) == ("RGB", (3200, 1864))


class TestDots:
    @pytest.mark.parametrize("theme", THEMES)
    @pytest.mark.parametrize(("size", "side"), [((3200, 1800), 6), ((2400, 2400), 4), ((3200, 1810), 6)])
    def test_each_dot_is_a_brand_green_square_on_the_baseline(
        self, footers: dict, theme: Theme, size: tuple[int, int], side: int
    ) -> None:
        _, image = footers[(theme, size)]
        layout = footer_layout(*size, spec_id="scatter-basic")
        green = blend(PAGE[theme], GREEN, DOT_ALPHA)
        page = rgb(PAGE[theme])

        assert [square.side for square in layout.squares] == [side, side]
        for square in layout.squares:
            assert square.top + square.side == layout.baseline  # the bottom sits on the baseline
            top = layout.plot_height + square.top
            inside = image.crop((square.left, top, square.left + side, top + side))
            assert {colour for _, colour in inside.getcolors() or []} == {green}
            assert image.getpixel((square.left - 1, top)) == page
            assert image.getpixel((square.left + side, top)) == page
            assert image.getpixel((square.left, top - 1)) == page
            assert image.getpixel((square.left, top + side)) == page

    def test_the_dots_sit_in_their_cells_between_the_words(self) -> None:
        layout = footer_layout(3200, 1800, spec_id="scatter-basic")
        runs = {run.text: run for run in layout.runs}
        dot_em = 1.45 * 22
        left, right = layout.squares

        assert left.left == round(runs["any"].end + 0.251 * dot_em)
        assert runs["plot"].x == round(runs["any"].end + 0.640 * dot_em)
        assert right.left == round(runs["anyplot"].end + 0.251 * dot_em)
        assert runs["ai"].x == round(runs["anyplot"].end + 0.640 * dot_em)
        assert (left.left, left.top, left.side) == (217, 34, 6)
        assert (right.left, right.top, right.side) == (2940, 34, 6)


class TestLayout:
    @pytest.mark.parametrize(("width", "height"), [size for size, _ in SIZES])
    def test_lengths_scale_with_the_width(self, width: int, height: int) -> None:
        layout = footer_layout(width, height, spec_id="scatter-basic")
        scale = width / 3200

        assert layout.strip_height == round(64 * scale)
        assert layout.text_px == pytest.approx(22 * scale)
        assert layout.left_span[0] == round(40 * scale)
        assert layout.right_span[1] == pytest.approx(width - 40 * scale, abs=1)

    @pytest.mark.parametrize(("width", "height"), [size for size, _ in SIZES])
    def test_the_cap_height_is_centred_in_the_strip(self, width: int, height: int) -> None:
        layout = footer_layout(width, height, spec_id="scatter-basic")
        cap_middle = layout.baseline - 0.73 * layout.text_px / 2

        assert abs(cap_middle - layout.strip_height / 2) <= 0.5

    def test_the_texts_and_their_weights(self) -> None:
        layout = footer_layout(3200, 1800, spec_id="scatter-basic")

        assert [(run.text, run.bold, run.alpha) for run in layout.runs] == [
            ("made with ", False, 0.56),
            ("any", True, 0.70),
            ("plot", True, 0.70),
            ("()", False, 0.315),
            ("anyplot", True, 0.70),
            ("ai", True, 0.70),
            ("/scatter-basic", False, 0.56),
        ]
        assert layout.shown_spec == "scatter-basic"

    @pytest.mark.parametrize("theme", THEMES)
    def test_text_is_drawn_inside_both_spans(self, footers: dict, theme: Theme) -> None:
        _, image = footers[(theme, (3200, 1800))]
        layout = footer_layout(3200, 1800, spec_id="scatter-basic")
        page = rgb(PAGE[theme])

        for x0, x1 in (layout.left_span, layout.right_span):
            text = image.crop((int(x0), 1801, int(x1), 1864))
            assert len(text.getcolors(maxcolors=4096) or []) > 8  # antialiased glyphs, not a flat strip
            assert any(colour != page for _, colour in text.getcolors(maxcolors=4096) or [])

    def test_a_long_spec_id_is_cut_with_an_ellipsis(self) -> None:
        spec_id = "-".join(["distribution"] * 30)
        layout = footer_layout(3200, 1800, spec_id=spec_id)
        gap = layout.right_span[0] - layout.left_span[1]
        advance = ImageFont.truetype(
            str(watermark.FONT_FILES[False]), layout.text_px, layout_engine=ImageFont.Layout.BASIC
        ).getlength("a")

        assert layout.shown_spec.endswith("…")
        assert spec_id.startswith(layout.shown_spec[:-1])
        assert len(layout.shown_spec) > 100
        assert gap >= GAP_PX * layout.scale  # the texts never touch
        assert gap < GAP_PX * layout.scale + advance + 1  # and the cut keeps as much of the id as fits
        assert layout.runs[-1].text == "/" + layout.shown_spec
        image = decode(add_footer(fixture_png("light", (2400, 2400)), theme="light", spec_id=spec_id))
        assert image.size == (2400, 2448)

    @pytest.mark.parametrize("spec_id", ["", "Scatter", "-scatter", "scatter-", "scatter--basic", "a/b", "a b", "ü"])
    def test_a_spec_id_outside_the_export_pattern_is_refused(self, spec_id: str) -> None:
        with pytest.raises(ValueError, match="not a spec id"):
            footer_layout(3200, 1800, spec_id=spec_id)
        with pytest.raises(ValueError, match="not a spec id"):
            add_footer(fixture_png("light"), theme="light", spec_id=spec_id)

    def test_the_spec_id_pattern_is_the_exports(self) -> None:
        assert watermark.SPEC_ID_PATTERN == export._SPEC_ID.pattern

    def test_a_tiny_image_or_an_unknown_theme_is_refused(self) -> None:
        with pytest.raises(ValueError, match="at least 640"):
            footer_layout(639, 400, spec_id="scatter-basic")
        with pytest.raises(ValueError, match="not a theme"):
            add_footer(fixture_png("light"), theme="sepia", spec_id="scatter-basic")


class TestFonts:
    def test_the_vendored_files_are_the_release_files(self) -> None:
        for name, digest in FONT_SHA256.items():
            assert hashlib.sha256((watermark.FONT_DIR / name).read_bytes()).hexdigest() == digest, name
        assert (watermark.FONT_DIR / "README.md").is_file()

    @pytest.mark.parametrize(("bold", "style"), [(False, "Regular"), (True, "Bold")])
    def test_both_weights_load_with_the_basic_layout(self, bold: bool, style: str) -> None:
        font = ImageFont.truetype(str(watermark.FONT_FILES[bold]), 22, layout_engine=ImageFont.Layout.BASIC)

        assert font.getname() == ("JetBrains Mono", style)
        assert font.getlength("anyplot") == 7 * font.getlength("a")  # monospaced
