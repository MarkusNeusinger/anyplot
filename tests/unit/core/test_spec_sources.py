"""The `sources` block of `specification.yaml`: the check itself, and every spec file of the catalogue against it."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from core.spec_sources import DATA_KINDS, normalized_sources, sources_problems


ROOT = Path(__file__).resolve().parents[3]
SPEC_FILES = sorted((ROOT / "plots").glob("*/specification.yaml"))

# Invented values: a test is public text too, and no real work or person is named here.
FULL_BLOCK = """
sources:
  data: computed
  inspired_by:
    - title: "An example plotting project"
      url: "https://example.org/project"
      doi: "10.5281/zenodo.0000001"
  references:
    - title: "On the spectra of an example system"
      url: "https://doi.org/10.1000/xyz123"
      doi: "10.1000/xyz123"
    - title: "An example textbook"
      url: "http://example.org/book"
      isbn: "978-3-16-148410-0"
"""


def _block(text: str) -> object:
    return yaml.safe_load(text)["sources"]


def test_the_catalogue_has_spec_files() -> None:
    assert len(SPEC_FILES) > 300, "the sweep no longer finds the spec files under plots/"


@pytest.mark.parametrize("path", SPEC_FILES, ids=lambda path: path.parent.name)
def test_every_spec_file_has_a_sound_sources_block(path: Path) -> None:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    assert sources_problems(data.get("sources")) == [], f"{path.relative_to(ROOT)}"


class TestSoundBlocks:
    def test_a_full_block_passes(self) -> None:
        assert sources_problems(_block(FULL_BLOCK)) == []

    @pytest.mark.parametrize(
        "text",
        [
            "sources:\n",
            "sources: {}\n",
            "sources:\n  inspired_by: []\n  references: []\n",
            "sources:\n  data: invented\n",
            "sources:\n  references:\n    - title: A paper\n      url: https://example.org/a\n",
        ],
        ids=["null", "empty-mapping", "empty-lists", "data-only", "one-reference"],
    )
    def test_a_missing_or_partial_block_passes(self, text: str) -> None:
        assert sources_problems(_block(text)) == []

    def test_a_missing_block_passes(self) -> None:
        assert sources_problems(None) == []

    @pytest.mark.parametrize("kind", DATA_KINDS)
    def test_every_data_kind_passes(self, kind: str) -> None:
        assert sources_problems({"data": kind}) == []

    @pytest.mark.parametrize("isbn", ["0-306-40615-2", "080442957X", "978 3 16 148410 0", "9783161484100"])
    def test_isbn_forms_pass(self, isbn: str) -> None:
        entry = {"title": "A book", "url": "https://example.org/b", "isbn": isbn}
        assert sources_problems({"references": [entry]}) == []

    @pytest.mark.parametrize("isbn", ["9783161484101", "978-3-16-148410-9", "0-306-40615-3", "0804429570"])
    def test_an_isbn_with_a_wrong_check_digit_fails(self, isbn: str) -> None:
        entry = {"title": "A book", "url": "https://example.org/b", "isbn": isbn}
        problems = sources_problems({"references": [entry]})
        assert problems == [
            f"sources.references[0].isbn: not an ISBN-10 or ISBN-13 with a fitting check digit: {isbn!r}"
        ], problems


class TestBadBlocks:
    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("sources: []\n", "sources: a mapping of data, inspired_by, references, found list"),
            ("sources:\n  code_from: []\n", "sources: unknown key 'code_from'"),
            ("sources:\n  licence: MIT\n", "sources: unknown key 'licence'"),
            ("sources:\n  data: measured\n", "sources.data: one of invented, computed, real, found 'measured'"),
            ("sources:\n  data:\n", "sources.data: one of invented, computed, real, found None"),
            ("sources:\n  references:\n", "sources.references: a list of entries, found NoneType"),
            (
                "sources:\n  inspired_by:\n    title: A\n    url: https://example.org\n",
                "sources.inspired_by: a list of entries, found dict",
            ),
            ("sources:\n  references:\n    - https://example.org\n", "sources.references[0]: an entry is a mapping"),
        ],
        ids=[
            "list",
            "code-relation",
            "licence-key",
            "unknown-data-kind",
            "null-data",
            "null-list",
            "entry-not-in-list",
            "bare-url",
        ],
    )
    def test_a_bad_block_names_its_problem(self, text: str, expected: str) -> None:
        problems = sources_problems(_block(text))
        assert any(problem.startswith(expected) for problem in problems), problems

    @pytest.mark.parametrize(
        ("entry", "expected"),
        [
            ({"url": "https://example.org"}, "sources.references[0].title: missing"),
            ({"title": "A"}, "sources.references[0].url: missing"),
            ({"title": "  ", "url": "https://example.org"}, "sources.references[0].title: empty"),
            ({"title": None, "url": "https://example.org"}, "sources.references[0].title: a string, found NoneType"),
            ({"title": "A", "url": "ftp://example.org/a"}, "sources.references[0].url: not an http or https address"),
            ({"title": "A", "url": "javascript:alert(1)"}, "sources.references[0].url: not an http or https address"),
            ({"title": "A", "url": "https://"}, "sources.references[0].url: not an http or https address"),
            ({"title": "A", "url": "example.org/a"}, "sources.references[0].url: not an http or https address"),
            ({"title": "A", "url": "https://exa mple.org"}, "sources.references[0].url: not an http or https address"),
            (
                {"title": "A", "url": "https://example.org", "doi": "https://doi.org/10.1000/xyz123"},
                "sources.references[0].doi: not a DOI",
            ),
            ({"title": "A", "url": "https://example.org", "doi": "10.1000"}, "sources.references[0].doi: not a DOI"),
            (
                {"title": "A", "url": "https://example.org", "doi": "10.1234/../../target"},
                "sources.references[0].doi: not a DOI",
            ),
            (
                {"title": "A", "url": "https://example.org", "doi": "10.1234/./x"},
                "sources.references[0].doi: not a DOI",
            ),
            ({"title": "A", "url": "https://example.org", "isbn": "12345"}, "sources.references[0].isbn: not an ISBN"),
            (
                {"title": "A", "url": "https://example.org", "isbn": 9783161484100},
                "sources.references[0].isbn: a string (quote it in the YAML), found int",
            ),
            ({"title": "A", "url": "https://example.org", "doi": None}, "sources.references[0].doi: a string"),
            (
                {"title": "A", "url": "https://example.org", "author": "B"},
                "sources.references[0]: unknown key 'author'",
            ),
            (
                {"title": "A", "url": "https://example.org", "licence": "GPL-3.0"},
                "sources.references[0]: unknown key 'licence'",
            ),
        ],
        ids=[
            "no-title",
            "no-url",
            "blank-title",
            "null-title",
            "ftp-url",
            "javascript-url",
            "url-without-host",
            "url-without-scheme",
            "url-with-space",
            "doi-as-url",
            "doi-without-suffix",
            "doi-with-parent-segments",
            "doi-with-a-dot-segment",
            "short-isbn",
            "unquoted-isbn",
            "null-doi",
            "author-key",
            "licence-key",
        ],
    )
    def test_a_bad_entry_names_its_problem(self, entry: dict, expected: str) -> None:
        problems = sources_problems({"references": [entry]})
        assert any(problem.startswith(expected) for problem in problems), problems

    def test_every_problem_is_named_at_once(self) -> None:
        problems = sources_problems(
            {"data": "guessed", "inspired_by": [{"title": "A"}], "references": [{"url": "mailto:a@example.org"}]}
        )
        assert len(problems) == 4, problems

    def test_an_entry_of_the_second_list_is_named_by_its_list_and_position(self) -> None:
        good = {"title": "A", "url": "https://example.org/a"}
        problems = sources_problems({"inspired_by": [good], "references": [good, {"title": "B"}]})
        assert problems == ["sources.references[1].url: missing"]


class TestNormalizedSources:
    def test_a_full_block_keeps_its_entries_in_order(self) -> None:
        assert normalized_sources(_block(FULL_BLOCK)) == {
            "data": "computed",
            "inspired_by": [
                {
                    "title": "An example plotting project",
                    "url": "https://example.org/project",
                    "doi": "10.5281/zenodo.0000001",
                }
            ],
            "references": [
                {
                    "title": "On the spectra of an example system",
                    "url": "https://doi.org/10.1000/xyz123",
                    "doi": "10.1000/xyz123",
                },
                {"title": "An example textbook", "url": "http://example.org/book", "isbn": "978-3-16-148410-0"},
            ],
        }

    @pytest.mark.parametrize("block", [None, {}, {"inspired_by": [], "references": []}])
    def test_a_block_without_content_is_stored_as_nothing(self, block: object) -> None:
        assert normalized_sources(block) is None

    def test_data_alone_is_kept(self) -> None:
        assert normalized_sources({"data": "invented", "references": []}) == {"data": "invented"}

    def test_a_folded_title_becomes_one_line(self) -> None:
        block = _block(
            "sources:\n  references:\n    - title: >\n        A long\n        title\n      url: https://example.org\n"
        )
        assert normalized_sources(block) == {"references": [{"title": "A long title", "url": "https://example.org"}]}

    def test_a_block_with_problems_is_refused(self) -> None:
        with pytest.raises(ValueError, match=r"sources.references\[0\].url: missing"):
            normalized_sources({"references": [{"title": "A"}]})
