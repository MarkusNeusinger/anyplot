"""Check a fix commit before its ref is pushed or dispatched: scope, header, validator and, on request, a local render.

Run it from the repository root with the agents extra (the validator needs tree-sitter):

    uv run --extra agents python .claude/skills/audit-catalogue/check_fix.py \
        --repo "$W" --ref HEAD --base origin/main [--render --out "$ROUND/renders/fix1"] \
        scatter-basic/muix area-basic/matplotlib ...

Every file is read from `--ref` in `--repo`'s git store, never from a working tree. Per pair:

- `scope`: the commit range `base...ref` changes implementation files only: no metadata, no render (`plot-*.png`,
  `.html`, `.webp`), no `node_modules` link, no spec, nothing else. One line for the whole range; implementation
  files of pairs not named are listed as a note (adopt mode takes only the files it is named).
- `changed`: the file differs from the commit the fix was cut from (the merge base with `--base`); an unchanged pair
  is skipped, not failed. When `--base` changed the file since that commit, the check fails: adopt mode takes the
  whole file, so it would revert main's newer version. Cut the fix again from the current main.
- `header`: the first line still names anyplot.ai, and the header block through its `Quality:` line is byte-identical
  to the file the fix started from: impl-review writes the score and the date, a fix never does.
- `validator`: the agent validator's scan (`catalogue.readiness_of`) refuses nothing the base did not; a new
  `deprecated-api` hint fails too. A clean file that turns coupled is a warning.
- `render` (`--render`): Python and JavaScript render both themes the way adopt mode does, from a temporary copy
  (Python: `MPLBACKEND=Agg python -P` in the project venv with the library's extra; JavaScript:
  `automation/js-render/render.mjs`, which needs `node_modules` in `--repo`), then the canvas gate and the blank
  check of `core.canvas`. The PNGs go to `--out/<spec>/<library>/`. R and Julia are not rendered: adopt mode has
  no R or Julia render, so their fix goes through a `regen_gate=false` generation (SKILL.md, step 6).

Exit codes: 0 every pair passes, 1 a check failed, 2 bad arguments.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path

import catalogue
from catalogue import Pair


RENDER_NAME = re.compile(r"(^|/)plot-[^/]*\.(png|html|webp)$")
HEADER_SCAN = 12
"""Lines from the top in which the header block and its `Quality:` line must lie."""
RENDER_TIMEOUT = 300


@dataclass
class Result:
    pair: str
    changed: bool = True
    problems: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    validator: str = ""
    render: dict[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.problems


IMPLEMENTATION = re.compile(r"^plots/[a-z0-9-]+/implementations/[a-z]+/[a-z0-9]+\.(py|R|jl|js|tsx)$")


def scope_problems(changed: list[str], named: set[str]) -> tuple[list[str], list[str]]:
    """`(problems, unnamed)`: each changed path a fix commit must not carry, with the reason, and the implementation
    files the commit changes that no named pair covers (allowed: adopt mode takes only the files it is named)."""
    problems: list[str] = []
    unnamed: list[str] = []
    for path in changed:
        if path in named:
            continue
        if RENDER_NAME.search(path):
            problems.append(f"{path}: a render; renders never go into a commit")
        elif path == "node_modules" or path.startswith("node_modules/") or path.endswith("/node_modules"):
            problems.append(f"{path}: the node_modules link; stage files by path, never with git add -A")
        elif "/metadata/" in path:
            problems.append(f"{path}: metadata; the pipeline writes it")
        elif IMPLEMENTATION.match(path):
            unnamed.append(path)
        else:
            problems.append(f"{path}: not an implementation file; a spec change goes through the spec issue")
    return problems, unnamed


def header_block(text: str) -> list[str] | None:
    """The leading lines through the first `Quality:` line, or None when the top lines hold none."""
    lines = text.splitlines()
    for index, line in enumerate(lines[:HEADER_SCAN]):
        if "Quality:" in line:
            return lines[: index + 1]
    return None


def header_problems(base: str | None, new: str) -> list[str]:
    first = new.splitlines()[0] if new else ""
    problems = [] if "anyplot.ai" in first else [f"line 1 no longer names anyplot.ai: {first[:60]!r}"]
    old_block = header_block(base) if base else None
    if old_block is not None and header_block(new) != old_block:
        problems.append("the header through its Quality line changed; impl-review writes it, a fix never does")
    return problems


def reason_key(reason: str) -> str:
    """The rule a reason names: `security: <rule>` for a SECURITY finding, else its category."""
    category, _, rest = reason.partition(":")
    if category == "security":
        return f"security: {rest.strip().split(' at ')[0].split()[0] if rest.strip() else ''}"
    return category


def validator_problems(
    base: tuple[str, list[str], list[str]] | None, new: tuple[str, list[str], list[str]]
) -> tuple[list[str], list[str]]:
    """Problems and warnings of the new scan against the base's: new refusals, a new `deprecated-api` hint."""
    new_status, new_reasons, _ = new
    old_status, old_reasons, _ = base if base else ("clean", [], [])
    problems: list[str] = []
    if new_status == "error":
        problems.append(f"the validator could not read the file: {new_reasons[0] if new_reasons else '?'}")
        return problems, []
    old_keys = {reason_key(reason) for reason in old_reasons}
    if new_status == "blocked":
        for reason in catalogue.refusals(new_reasons):
            if reason_key(reason) not in old_keys or old_status != "blocked":
                problems.append(f"the agent chat would refuse it: {reason[:200]}")
    if any(reason_key(r) == "deprecated-api" for r in new_reasons) and "deprecated-api" not in old_keys:
        problems.append("a deprecated-api hint the base did not have")
    warnings = (
        ["clean before, coupled now: the adaptable-code layout got worse"]
        if (old_status, new_status) == ("clean", "coupled")
        else []
    )
    return problems, warnings


def render_pair(pair: Pair, code: str, *, repo: Path, out: Path) -> tuple[dict[str, str], list[str], list[str]]:
    """Render both themes from a temporary copy, then the canvas gate and the blank checks: a canvas that is all
    background by the agents' own cutoff fails, one above the rubric's 95 % only warns (a tree of thin lines is
    97 % background and fine). Returns `(per theme, problems, warnings)`."""
    from agents.anyplot.render.png import MAX_BACKGROUND_RATIO
    from core.canvas import NotAPngError, check_blank, check_png

    if pair.language not in ("python", "javascript"):
        return {"both": "not rendered locally: adopt mode has no R or Julia render"}, [], []
    summary: dict[str, str] = {}
    problems: list[str] = []
    warnings: list[str] = []
    target = out / pair.spec / pair.library
    target.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="audit-render-") as scratch:
        work = Path(scratch)
        source = work / Path(pair.impl_path).name
        source.write_text(code, encoding="utf-8")
        for theme in catalogue.THEMES:
            env = {**os.environ, "ANYPLOT_THEME": theme, "PYTHON_DOTENV_DISABLED": "1"}
            if pair.language == "python":
                env["MPLBACKEND"] = "Agg"
                command = ["uv", "run", "--project", str(repo), "--frozen", "-q", "--extra", f"lib-{pair.library}"]
                command += ["python", "-P", str(source)]
            else:
                command = ["node", str(repo / "automation" / "js-render" / "render.mjs"), str(source)]
            log = target / f"render-{theme}.log"
            try:
                run = subprocess.run(
                    command, cwd=work, env=env, capture_output=True, timeout=RENDER_TIMEOUT, check=False
                )
                log.write_bytes(run.stdout + run.stderr)
                exit_code = run.returncode
            except subprocess.TimeoutExpired:
                exit_code = -1
            png = work / f"plot-{theme}.png"
            if exit_code != 0 or not png.is_file():
                summary[theme] = f"render failed (exit {exit_code}), log {log}"
                problems.append(f"{theme}: the render failed, see {log}")
                continue
            kept = target / png.name
            shutil.copyfile(png, kept)
            try:
                verdict = check_png(kept, pair.library)
            except NotAPngError:
                summary[theme] = "not a PNG"
                problems.append(f"{theme}: the render is not a PNG")
                continue
            summary[theme] = f"{verdict.width}x{verdict.height} (target {verdict.target[0]}x{verdict.target[1]})"
            if not verdict.ok:
                problems.append(f"{theme}: off the canvas target, {summary[theme]}")
            empty, rubric = check_blank(kept, max_blank_ratio=MAX_BACKGROUND_RATIO), check_blank(kept)
            if not empty.passed:
                problems.append(f"{theme}: {empty.message}")
            elif not rubric.passed:
                warnings.append(f"{theme}: {rubric.message}; thin marks do that, look at the PNG")
    return summary, problems, warnings


def check(
    pairs: list[Pair], *, tree: catalogue.GitTree, base: catalogue.GitTree, render_out: Path | None
) -> tuple[list[str], list[str], list[Result]]:
    """`(scope problems, unnamed implementation files, per pair)`. The fix is read against the commit it was cut
    from (the merge base); `base` itself only shows whether main changed a file since, which an adoption would
    silently revert."""
    scope, unnamed = scope_problems(tree.changed_paths(base.sha), {pair.impl_path for pair in pairs})
    start = catalogue.GitTree(tree.repo, tree.merge_base(base.sha))
    paths = [pair.impl_path for pair in pairs]
    new_code, old_code, tip_code = tree.read_many(paths), start.read_many(paths), base.read_many(paths)
    results = []
    for pair in pairs:
        result = Result(pair.key)
        new, old = new_code[pair.impl_path], old_code[pair.impl_path]
        if new is None:
            result.problems.append(f"{pair.impl_path} does not exist at the ref")
            results.append(result)
            continue
        if new == old:
            result.changed = False
            results.append(result)
            continue
        if tip_code[pair.impl_path] != old:
            result.problems.append("main changed this file since the fix was cut; an adoption would revert that")
        result.problems += header_problems(old, new)
        scanned = catalogue.readiness_of(pair, new)
        before = catalogue.readiness_of(pair, old) if old is not None else None
        result.validator = scanned[0] if before is None else f"{before[0]} -> {scanned[0]}"
        problems, warnings = validator_problems(before, scanned)
        result.problems += problems
        result.warnings += warnings
        if render_out is not None:
            result.render, problems, warnings = render_pair(pair, new, repo=tree.repo, out=render_out)
            result.problems += problems
            result.warnings += warnings
        results.append(result)
    return scope, unnamed, results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check a fix commit before it is pushed or dispatched.")
    parser.add_argument("pairs", nargs="+", help="spec/library, one per pair the fix changes")
    parser.add_argument("--repo", type=Path, default=catalogue.REPO_ROOT, help="the checkout or worktree to read from")
    parser.add_argument("--ref", default="HEAD", help="the fix commit (default HEAD of --repo)")
    parser.add_argument("--base", default="origin/main", help="what the fix is compared with")
    parser.add_argument("--render", action="store_true", help="render Python and JavaScript pairs locally")
    parser.add_argument("--out", type=Path, help="with --render: where the PNGs go (outside every checkout)")
    parser.add_argument("--json", type=Path, help="also write the results to this file")
    args = parser.parse_args(argv)
    try:
        pairs = [Pair.parse(text) for text in args.pairs]
    except ValueError as exc:
        print(f"check_fix: {exc}", file=sys.stderr)
        return 2
    if args.render and (args.out is None or not catalogue.outside_repository(args.out)):
        print("check_fix: --render needs --out outside every git checkout", file=sys.stderr)
        return 2
    tree, base = catalogue.GitTree(args.repo, args.ref), catalogue.GitTree(args.repo, args.base)
    scope, unnamed, results = check(pairs, tree=tree, base=base, render_out=args.out if args.render else None)
    print(f"ref {tree.sha[:9]} against {args.base} ({base.sha[:9]})")
    print("scope ok" if not scope else "scope FAILED\n" + "\n".join(f"  {line}" for line in scope))
    if unnamed:
        print(f"  note: {len(unnamed)} other implementation file(s) on the ref, not named here: {', '.join(unnamed)}")
    for result in results:
        if not result.changed:
            print(f"{result.pair} unchanged, skipped")
            continue
        state = "ok" if result.ok else "FAILED"
        render = " ".join(f"{theme}={text}" for theme, text in result.render.items())
        print(f"{result.pair} {state} validator={result.validator}{' ' + render if render else ''}")
        for line in result.problems:
            print(f"  problem: {line}")
        for line in result.warnings:
            print(f"  warning: {line}")
    if args.json:
        payload = {
            "ref": tree.sha,
            "base": base.sha,
            "scope": scope,
            "unnamed": unnamed,
            "results": [asdict(r) for r in results],
        }
        catalogue.write_private(args.json, json.dumps(payload, indent=2) + "\n")
    return 0 if not scope and all(result.ok for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
