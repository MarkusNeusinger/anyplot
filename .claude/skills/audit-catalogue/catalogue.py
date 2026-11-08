"""What the audit skill's Python scripts share: the catalogue and the pinned library versions read from a git ref, a
pair's paths and render URLs, the stored review's checklist, and the private round directory.

Nothing here writes to a checkout. The catalogue comes from a commit (`origin/main` by default) through one
`git cat-file --batch` process, so a worktree's uncommitted state or drift never changes what a round reads.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def library_language(library: str) -> str | None:
    """The language of a registered library (`core.constants`), None for any other name."""
    from core.constants import LIBRARY_LANGUAGES

    return LIBRARY_LANGUAGES.get(library)


def library_extension(library: str) -> str:
    from core.constants import library_file_extension

    return library_file_extension(library)


GCS_PLOTS = "https://storage.googleapis.com/anyplot-images/plots"
"""The production renders: `plots/{spec}/{language}/{library}/plot-{theme}.png`, plus `_400/_800/_1200` sizes."""
SITE = "https://anyplot.ai"
REPOSITORY = "MarkusNeusinger/anyplot"
THEMES = ("light", "dark")
RENDERS: tuple[tuple[str, int | None, str], ...] = (
    ("light", None, "png"),
    ("dark", None, "png"),
    ("light", 800, "webp"),
    ("dark", 800, "webp"),
)
"""What a freshness check HEADs per pair, as `(theme, size, ext)`: the PNG the pipeline writes and the `_800.webp` the
site and the audit page show. impl-generate and impl-repair make the sized variants with a command of their own
(`core.images responsive`), so a fresh PNG next to an old or missing webp is a real case."""
TECHNICAL_PREFIXES = ("VQ", "SC", "DQ", "CQ")
"""The 19 technical criteria (`docs/workflows/overview.md`, "Nothing to repair"); DE and LM are design levels."""
METADATA_PATH = re.compile(r"^plots/(?P<spec>[a-z0-9-]+)/metadata/(?P<language>[a-z]+)/(?P<library>[a-z0-9]+)\.yaml$")
SUGGESTION = re.compile(r"^\s*Suggestion:", re.IGNORECASE)


def render_name(theme: str, size: int | None = None, ext: str = "png") -> str:
    """A render's file name in the bucket: `plot-light.png`, `plot-dark_800.webp`."""
    return f"plot-{theme}{f'_{size}' if size else ''}.{ext}"


@dataclass(frozen=True, order=True)
class Pair:
    """One implementation of the catalogue: a spec in one library (the library fixes the language)."""

    spec: str
    language: str
    library: str

    @classmethod
    def parse(cls, text: str) -> Pair:
        """`spec/library` or `spec/language/library`; the language must be the library's."""
        parts = text.strip().strip("/").split("/")
        if len(parts) == 2:
            spec, library = parts
            language = library_language(library) or ""
        elif len(parts) == 3:
            spec, language, library = parts
        else:
            raise ValueError(f"not a pair: {text!r} (expected spec/library)")
        if library_language(library) != language or not re.fullmatch(r"[a-z0-9-]+", spec):
            raise ValueError(f"not a pair: {text!r} (unknown library or language, or a malformed spec id)")
        return cls(spec, language, library)

    @property
    def key(self) -> str:
        return f"{self.spec}/{self.language}/{self.library}"

    @property
    def impl_path(self) -> str:
        return f"plots/{self.spec}/implementations/{self.language}/{self.library}{library_extension(self.library)}"

    @property
    def metadata_path(self) -> str:
        return f"plots/{self.spec}/metadata/{self.language}/{self.library}.yaml"

    @property
    def spec_path(self) -> str:
        return f"plots/{self.spec}/specification.md"

    def render_url(
        self, theme: str, *, size: int | None = None, ext: str = "png", cache_buster: int | None = None
    ) -> str:
        """The production render. Pass `cache_buster` (epoch seconds) for every check: the bucket serves
        `Cache-Control: public, max-age=604800`, so a plain URL can return an edge copy up to a week old."""
        url = f"{GCS_PLOTS}/{self.spec}/{self.language}/{self.library}/{render_name(theme, size, ext)}"
        return f"{url}?cb={cache_buster}" if cache_buster is not None else url

    @property
    def site_url(self) -> str:
        return f"{SITE}/{self.spec}/{self.language}/{self.library}"


def pairs_from_paths(paths: Iterable[str]) -> list[Pair]:
    """The pairs whose metadata file is among `paths` (a `git ls-tree` listing), sorted."""
    found = set()
    for path in paths:
        match = METADATA_PATH.match(path)
        if match and library_language(match["library"]) == match["language"]:
            found.add(Pair(match["spec"], match["language"], match["library"]))
    return sorted(found)


def parse_batch(data: bytes, names: list[str]) -> dict[str, bytes | None]:
    """Split `git cat-file --batch` output into one entry per requested name, None for a missing object."""
    out: dict[str, bytes | None] = {}
    position = 0
    for name in names:
        end = data.index(b"\n", position)
        header = data[position:end].decode()
        position = end + 1
        if header.endswith(" missing") or header.endswith(" ambiguous"):
            out[name] = None
            continue
        size = int(header.rsplit(" ", 1)[1])
        out[name] = data[position : position + size]
        position += size + 1  # the object, then one newline
    return out


class GitTree:
    """The files of one commit, read without touching any working tree."""

    def __init__(self, repo: Path, ref: str) -> None:
        self.repo = repo
        self.ref = ref
        self.sha = self._git("rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}").strip()
        if not self.sha:
            raise ValueError(f"{ref} is not a commit in {repo}")

    def _git(self, *args: str, data: bytes | None = None) -> str:
        result = subprocess.run(["git", "-C", str(self.repo), *args], input=data, capture_output=True, check=False)
        if result.returncode != 0 and args[0] != "rev-parse":
            raise RuntimeError(f"git {' '.join(args[:3])} failed: {result.stderr.decode(errors='replace').strip()}")
        return result.stdout.decode()

    def paths(self, prefix: str = "plots/") -> list[str]:
        return self._git("ls-tree", "-r", "--name-only", self.sha, "--", prefix).splitlines()

    def read_many(self, paths: list[str]) -> dict[str, str | None]:
        if not paths:
            return {}
        names = [f"{self.sha}:{path}" for path in paths]
        result = subprocess.run(
            ["git", "-C", str(self.repo), "cat-file", "--batch"],
            input="".join(f"{name}\n" for name in names).encode(),
            capture_output=True,
            check=True,
        )
        raw = parse_batch(result.stdout, names)
        out: dict[str, str | None] = {}
        for path, name in zip(paths, names, strict=True):
            blob = raw[name]
            out[path] = None if blob is None else blob.decode("utf-8")
        return out

    def read(self, path: str) -> str | None:
        return self.read_many([path])[path]

    def merge_base(self, other: str) -> str:
        return self._git("merge-base", other, self.sha).strip()

    def changed_paths(self, base: str) -> list[str]:
        """Every path the commit changes against its merge base with `base` (`git diff base...sha`)."""
        return self._git("diff", "--name-only", f"{base}...{self.sha}").splitlines()


PIN_FILES = (
    ".python-version",
    "uv.lock",
    "package-lock.json",
    "Manifest.toml",
    ".github/actions/setup-r/action.yml",
    ".github/actions/setup-julia/action.yml",
    ".github/actions/setup-node/action.yml",
)
"""The files `core.library_versions` reads the pins from, relative to the repository root."""


def pinned_libraries(tree: GitTree) -> tuple[dict[str, str], list[str]]:
    """`(library -> pinned version, errors)` at the tree's commit.

    `core.library_versions` reads the pins from a checkout's files, so the pin files go from git into a temporary
    directory and are read there: the version a round compares against is the ref's, as the rest of the catalogue is,
    never the working tree's. A pin file the reader needs but `PIN_FILES` misses shows up in the errors."""
    from core.library_versions import pinned_versions

    texts = tree.read_many(list(PIN_FILES))
    with tempfile.TemporaryDirectory(prefix="audit-pins-") as directory:
        root = Path(directory)
        for path, text in texts.items():
            if text is not None:
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(text, encoding="utf-8")
        pins = pinned_versions(root)
    return pins.libraries, pins.errors


def load_metadata(text: str | None) -> dict[str, Any]:
    if not text:
        return {}
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def parse_time(value: object) -> datetime | None:
    """A metadata timestamp (`'2026-11-08T04:54:13Z'`, or a datetime YAML already parsed) as aware UTC."""
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def checklist_items(metadata: dict[str, Any]) -> list[dict[str, Any]]:
    """The stored review's 24 items as `{id, score, max}`, in the stored order; empty for an older review."""
    checklist = (metadata.get("review") or {}).get("criteria_checklist") or {}
    items: list[dict[str, Any]] = []
    for category in checklist.values() if isinstance(checklist, dict) else ():
        # Some stored reviews keep a plain number (a category total) beside the categories.
        if not isinstance(category, dict):
            continue
        for item in category.get("items") or []:
            if (
                isinstance(item, dict)
                and isinstance(item.get("score"), int | float)
                and isinstance(item.get("max"), int | float)
            ):
                items.append({"id": str(item.get("id", "")), "score": item["score"], "max": item["max"]})
    return items


def defect_lines(metadata: dict[str, Any]) -> list[str]:
    """The stored review's defect lines: its weaknesses without the `Suggestion:` lines."""
    weaknesses = (metadata.get("review") or {}).get("weaknesses") or []
    return [str(line) for line in weaknesses if isinstance(line, str) and not SUGGESTION.match(line)]


def readiness_of(pair: Pair, code: str) -> tuple[str, list[str], list[str]]:
    """The agent validator's verdict on a catalogue file, as the corpus tests scan it: `(status, reasons, hints)`,
    status `clean`, `coupled` or `blocked`, or `error` when the profile cannot read the file.

    Each language's profile normalises the original first (`agents/anyplot/code/`, `profiles/*/`). The pair's own
    library is the one enabled library, so `library-disabled` never appears. Needs `uv run --extra agents`.
    """
    enabled = [pair.library]
    try:
        if pair.language == "python":
            from agents.anyplot.code.normalise import SUPPORTED_LIBRARIES, normalise
            from agents.anyplot.code.readiness import scan as scan_python

            if pair.library not in SUPPORTED_LIBRARIES:
                return "error", [f"no Python profile for {pair.library}"], []
            result = scan_python(
                normalise(code, library=pair.library),
                spec_id=pair.spec,
                library=pair.library,
                enabled_libraries=enabled,
            )
        elif pair.language == "javascript":
            from agents.anyplot.code.profiles.javascript.normalise import normalise as normalise_js
            from agents.anyplot.code.profiles.javascript.readiness import scan as scan_js

            result = scan_js(
                normalise_js(code, library=pair.library),
                spec_id=pair.spec,
                enabled_libraries=enabled,
                library=pair.library,
            )
        elif pair.language == "r":
            from agents.anyplot.code.profiles.r.normalise import normalise as normalise_r
            from agents.anyplot.code.profiles.r.readiness import scan as scan_r

            result = scan_r(normalise_r(code), spec_id=pair.spec, enabled_libraries=enabled)
        elif pair.language == "julia":
            from agents.anyplot.code.profiles.julia.normalise import normalise as normalise_julia
            from agents.anyplot.code.profiles.julia.readiness import scan as scan_julia

            result = scan_julia(normalise_julia(code), spec_id=pair.spec, enabled_libraries=enabled)
        else:
            return "error", [f"no profile for the language {pair.language}"], []
    except (ValueError, SyntaxError, RuntimeError) as exc:
        return "error", [f"{type(exc).__name__}: {exc}"[:300]], []
    return result.status, list(result.reasons), list(result.hints)


def refusals(reasons: list[str]) -> list[str]:
    """The blocking reasons a file's code causes: every reason but `map-spec`, which blocks the spec whatever the code."""
    return [reason for reason in reasons if not reason.startswith("map-spec:")]


def outside_repository(path: Path) -> bool:
    """True when no directory from `path` up holds a `.git` (a checkout or a worktree): round data stays out of git."""
    resolved = path.expanduser().resolve()
    return not any((directory / ".git").exists() for directory in (resolved, *resolved.parents))


def write_private(path: Path, text: str) -> None:
    """Write `text` with mode 0600, into a directory made with mode 0700 when it is new. A file that already existed
    is tightened to 0600 too: `os.open` applies its mode only when it creates. An existing directory keeps its mode,
    since a `--json /tmp/x.json` must never change `/tmp`; the round directory is 0700 from step 1."""
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.fchmod(descriptor, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(text)
