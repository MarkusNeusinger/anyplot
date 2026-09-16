"""Tests for automation.scripts.monolisa_fonts_css — the fonts.css generator.

The builder CSS from the MonoLisa order page is an external input that never
enters the repo, so these tests feed synthetic blocks in the builder's shape
and lock the parts of the output the app depends on: the family names, the
GCS paths, the `swap`/`optional` display policy and the `unicode-range`
pass-through.
"""

import pytest

from automation.scripts.monolisa_fonts_css import Subset, build, parse_builder_css, render_family


BUILDER_CSS = """/*!
* @preserve
* MonoLisa 3.000
*/

@font-face {
  src: url(/woff2/0-MonoLisaCode-normal.woff2) format("woff2");
  font-family: MonoLisaCode;
  font-weight: 1 900;
  font-style: normal;
  unicode-range: U+0020-007F;
}

@font-face {
  src: url(/woff2/1-MonoLisaCode-italic.woff2) format("woff2");
  font-family: MonoLisaCode;
  font-weight: 1 900;
  font-style: italic;
  unicode-range: U+0020-007F;
}

@font-face {
  src: url(/woff2/2-MonoLisaCode-normal.woff2) format("woff2");
  font-family: MonoLisaCode;
  font-weight: 1 900;
  font-style: normal;
  unicode-range: U+0080-00FF;
}
"""

PREFIX = "https://storage.googleapis.com/anyplot-static/fonts/v3"


class TestParseBuilderCss:
    """The builder's @font-face blocks become (file, style, range) triples."""

    def test_parses_every_block_in_order(self):
        subsets = parse_builder_css(BUILDER_CSS)

        assert subsets == [
            Subset("0-MonoLisaCode-normal.woff2", "normal", "U+0020-007F"),
            Subset("1-MonoLisaCode-italic.woff2", "italic", "U+0020-007F"),
            Subset("2-MonoLisaCode-normal.woff2", "normal", "U+0080-00FF"),
        ]

    def test_strips_directory_and_quotes_from_src(self):
        css = """@font-face {
  src: url('./woff2/5-MonoLisaText-italic.woff2') format("woff2");
  font-style: italic;
  unicode-range: U+0100-017F;
}"""
        assert parse_builder_css(css)[0].filename == "5-MonoLisaText-italic.woff2"

    def test_rejects_block_without_unicode_range(self):
        css = """@font-face {
  src: url(/woff2/0-MonoLisaCode-normal.woff2) format("woff2");
  font-style: normal;
}"""
        with pytest.raises(ValueError, match="Unparseable"):
            parse_builder_css(css)

    def test_rejects_css_without_blocks(self):
        with pytest.raises(ValueError, match="No @font-face"):
            parse_builder_css("body { color: red; }")


class TestRenderFamily:
    """Family name, GCS path, display policy and range comments per subset."""

    def test_basic_latin_swaps_and_the_rest_is_optional(self):
        out = render_family("MonoLisa Code", "code", parse_builder_css(BUILDER_CSS), PREFIX, {})

        blocks = [b for b in out.split("@font-face {") if "font-display" in b]
        assert len(blocks) == 3
        assert "font-display: swap;" in blocks[0]
        assert "font-display: swap;" in blocks[1]
        assert "font-display: optional;" in blocks[2]

    def test_renders_family_path_style_and_range(self):
        out = render_family("MonoLisa Text", "text", parse_builder_css(BUILDER_CSS), PREFIX, {})

        assert "font-family: 'MonoLisa Text';" in out
        assert f"src: url('{PREFIX}/text/1-MonoLisaCode-italic.woff2')" in out
        assert "font-style: italic;" in out
        assert "unicode-range: U+0080-00FF;" in out
        assert "font-weight: 100 900;" in out

    def test_range_comment_once_per_range_with_human_name(self):
        out = render_family("MonoLisa Code", "code", parse_builder_css(BUILDER_CSS), PREFIX, {})

        assert out.count("/* Basic Latin */") == 1
        assert out.count("/* Latin-1 Supplement */") == 1

    def test_swap_comment_only_on_swap_faces(self):
        out = render_family("MonoLisa Code", "code", parse_builder_css(BUILDER_CSS), PREFIX, {"italic": "script voice"})

        assert out.count("/* script voice */") == 1


class TestBuild:
    """The assembled stylesheet: header, fallback face, both families, no double blank lines."""

    def test_contains_both_families_and_fallback(self):
        css = build(BUILDER_CSS, BUILDER_CSS, PREFIX, "3.000")

        assert "MonoLisa 3.000" in css
        assert "font-family: 'MonoLisa Fallback';" in css
        assert css.count("font-family: 'MonoLisa Code';") == 3
        assert css.count("font-family: 'MonoLisa Text';") == 3
        assert f"{PREFIX}/code/0-MonoLisaCode-normal.woff2" in css
        assert f"{PREFIX}/text/0-MonoLisaCode-normal.woff2" in css

    def test_is_prettier_clean_on_blank_lines(self):
        css = build(BUILDER_CSS, BUILDER_CSS, PREFIX + "/", "3.000")

        assert "\n\n\n" not in css
        assert PREFIX + "//" not in css
