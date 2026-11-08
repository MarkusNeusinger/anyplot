"""Turn an audit round's results into the owner's pick list (`findings.json` and one self-contained HTML page), and
the picked fixes into a gallery he sees before the queue OK.

Run it from the repository root after the audit workflow's results are saved in the round directory:

    uv run python .claude/skills/audit-catalogue/build_page.py --round "$ROUND" \
        --audit "$ROUND/audit-run1.json" [--audit "$ROUND/audit-run2.json"] [--no-images] \
        [--name reaudit --id-prefix R]

It reads `candidates.json` from the round for the stored scores, ids every finding (`F01`, `F02`, … in the order
the page shows them: confirmed high, confirmed medium, unverified, low notes, refuted last) and writes:

- `findings.json`: every finding with its id, status (`confirmed`, `unverified`, `low`, `refuted`), severity after
  the skeptic, cause and fix, plus the clean and unchecked pairs. The owner's picks name these ids; a low note has
  one too and stays pickable. `unverified` is a high or medium finding whose skeptic returned nothing: re-run its
  skeptic before anyone picks it.
- `page/audit.html`: the page to publish as a private Artifact. It embeds each finding's two `_800.webp` renders
  as data URIs (the Artifact CSP blocks other hosts' images), fetched with a cache-buster; `--no-images` leaves
  them out. No script, no external resource but the JetBrains Mono stylesheet from Google Fonts.

`--name` names another page of the round, such as the re-audit of the marked pairs: it writes
`findings-<name>.json` and `page/<name>.html`, so the round's `findings.json` and its ids stay; `--id-prefix` keeps
the new ids apart (`R01`).

The fixes gallery, after the fixes are rendered locally (SKILL.md, step 7):

    uv run python .claude/skills/audit-catalogue/build_page.py --round "$ROUND" --fixes F01 F03 [--renders DIR]

It shows, per picked pair, the finding ids with their fix sentences, the production `_800.webp` (with a
cache-buster) and the newest local render of `check_fix.py --render` under `--renders` (default `<round>/renders`),
both themes, scaled to 800 px. A pair with no local render (R, Julia, or a plotly or bokeh render that needs a
Chrome) shows the production side and "renders in the pipeline". It writes `page/fixes.html`.

Every file stays in the round directory, outside every checkout. Exit codes: 0 written, 2 bad arguments.
"""

from __future__ import annotations

import argparse
import base64
import html
import io
import json
import re
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import catalogue
from catalogue import Pair


SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}
CARDS = ("confirmed", "unverified")
"""The statuses the page shows as cards with both renders; the others are one-line lists."""


def collect(audits: list[list[dict[str, Any]]], candidates: dict[str, Any], *, prefix: str = "F") -> dict[str, Any]:
    """Merge the workflow's group results into one list of findings with ids, and the clean and unchecked pairs.

    A high or medium finding the skeptic kept is `confirmed` at the skeptic's severity and cause; one it refuted is
    `refuted`; a low finding was never verified and stays `low`. A high or medium finding without a verdict (its
    skeptic died twice) is `unverified` at the auditor's severity: shown apart, never as confirmed."""
    scores = {c["pair"]: c for c in candidates.get("candidates", [])}
    entries: list[dict[str, Any]] = []
    clean: list[str] = []
    unchecked: list[str] = []
    for groups in audits:
        for group in groups or []:
            verified = {(f["pair"], f["what"]): f for f in group.get("verified", [])}
            for finding in group.get("findings", []):
                entry = {
                    key: finding.get(key)
                    for key in ("pair", "severity", "defect_class", "cause", "what", "evidence", "fix", "pr")
                }
                entry["auditor_severity"] = finding.get("severity")
                checked = verified.get((finding["pair"], finding["what"]))
                verdict = (checked or {}).get("verdict")
                if finding.get("severity") == "low":
                    entry["status"] = "low"
                elif not verdict:
                    entry.update(status="unverified", skeptic="no skeptic verdict came back; re-run the skeptic")
                elif verdict.get("refuted"):
                    entry.update(status="refuted", skeptic=verdict.get("reason", ""))
                else:
                    entry.update(
                        status="confirmed",
                        severity=verdict.get("severity", entry["severity"]),
                        cause=verdict.get("cause", entry["cause"]),
                        skeptic=verdict.get("reason", ""),
                    )
                if entry["status"] == "confirmed" and entry["severity"] == "low":
                    entry["status"] = "low"
                stored = scores.get(entry["pair"], {})
                entry["quality_score"] = stored.get("quality_score")
                entry["reasons"] = [r.get("code") for r in stored.get("reasons", [])]
                entries.append(entry)
            for row in group.get("checked", []):
                if row.get("verdict") == "clean":
                    clean.append(row["pair"])
                elif row.get("verdict") == "unchecked":
                    unchecked.append(f"{row['pair']}: {row.get('note', '')}")
    rank = {"confirmed": 0, "unverified": 1, "low": 2, "refuted": 3}
    entries.sort(key=lambda e: (rank[e["status"]], SEVERITY_ORDER.get(e["severity"], 3), e["pair"]))
    for index, entry in enumerate(entries, start=1):
        entry["id"] = f"{prefix}{index:02d}"
    return {"findings": entries, "clean": sorted(set(clean)), "unchecked": sorted(set(unchecked))}


def fetch_image(url: str) -> bytes | None:
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                data: bytes = response.read()
                return data
        except urllib.error.HTTPError:
            return None
        except urllib.error.URLError, TimeoutError, OSError:
            time.sleep(2 * (attempt + 1))
    return None


def thumbnails(findings: list[dict[str, Any]], cache_buster: int) -> dict[str, dict[str, str]]:
    """The `_800.webp` render of each theme per pair the page shows a card for, as a data URI (missing when the bucket
    has none)."""
    out: dict[str, dict[str, str]] = {}
    for key in sorted({f["pair"] for f in findings if f["status"] in CARDS}):
        pair = Pair.parse(key)
        for theme in catalogue.THEMES:
            data = fetch_image(pair.render_url(theme, size=800, ext="webp", cache_buster=cache_buster))
            if data:
                out.setdefault(key, {})[theme] = "data:image/webp;base64," + base64.b64encode(data).decode()
    return out


STYLE = """
:root {
  --page: #f5f3ec; --surface: #faf8f1; --ink: #1a1a17; --ink-soft: #4a4a44; --ink-muted: #6b6a63;
  --rule: rgba(26, 26, 23, 0.15); --green: #009e73; --green-text: #007a59;
  --high: #ae3030; --high-bg: rgba(174, 48, 48, 0.1); --medium: #7a6510; --medium-bg: rgba(221, 204, 119, 0.35);
  --low: #6b6a63; --low-bg: rgba(26, 26, 23, 0.06);
  --mono: "JetBrains Mono", ui-monospace, "SFMono-Regular", Menlo, Consolas, monospace;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --page: #121210; --surface: #1a1a17; --ink: #f0efe8; --ink-soft: #b8b7b0; --ink-muted: #a8a79f;
  --rule: rgba(240, 239, 232, 0.15); --green-text: #3fc29a;
  --high: #e88080; --high-bg: rgba(232, 128, 128, 0.14); --medium: #ddcc77; --medium-bg: rgba(221, 204, 119, 0.14);
  --low: #a8a79f; --low-bg: rgba(240, 239, 232, 0.07); color-scheme: dark;
} }
:root[data-theme="dark"] {
  --page: #121210; --surface: #1a1a17; --ink: #f0efe8; --ink-soft: #b8b7b0; --ink-muted: #a8a79f;
  --rule: rgba(240, 239, 232, 0.15); --green-text: #3fc29a;
  --high: #e88080; --high-bg: rgba(232, 128, 128, 0.14); --medium: #ddcc77; --medium-bg: rgba(221, 204, 119, 0.14);
  --low: #a8a79f; --low-bg: rgba(240, 239, 232, 0.07); color-scheme: dark;
}
body { background: var(--page); color: var(--ink); font: 14px/1.55 var(--mono); }
main { max-width: 1120px; margin: 0 auto; padding-block: 32px 64px;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px));
  display: grid; gap: 28px; }
h1 { font-size: 1.6rem; margin: 0; text-wrap: balance; letter-spacing: -0.01em; }
h1 .dot { color: var(--green); }
h2 { font-size: 1.05rem; margin: 0; text-transform: lowercase; color: var(--ink-soft); }
p { margin: 0; max-width: 72ch; }
a { color: var(--green-text); }
a:focus-visible, summary:focus-visible { outline: 2px solid var(--green); outline-offset: 2px; }
.lede { color: var(--ink-soft); }
.stats { display: flex; flex-wrap: wrap; gap: 8px 20px; font-variant-numeric: tabular-nums; color: var(--ink-soft); }
.stats b { color: var(--ink); }
.section { display: grid; gap: 14px; }
.card { background: var(--surface); border: 1px solid var(--rule); border-radius: 6px; padding: 16px;
  display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 400px); gap: 16px; }
.card .text { display: grid; gap: 8px; align-content: start; min-width: 0; }
.head { display: flex; flex-wrap: wrap; align-items: baseline; gap: 6px 10px; }
.id { font-weight: 700; font-variant-numeric: tabular-nums; }
.pair { font-weight: 700; overflow-wrap: anywhere; }
.chip { font-size: 0.78rem; padding: 1px 8px; border-radius: 999px; letter-spacing: 0.02em; white-space: nowrap; }
.high { color: var(--high); background: var(--high-bg); }
.medium { color: var(--medium); background: var(--medium-bg); }
.low { color: var(--low); background: var(--low-bg); }
.meta { color: var(--ink-muted); font-size: 0.85rem; overflow-wrap: anywhere; }
.fix { border-left: 2px solid var(--green); padding-left: 10px; }
details > summary { cursor: pointer; color: var(--ink-soft); }
details p { margin-top: 6px; color: var(--ink-soft); overflow-wrap: anywhere; }
.shots { display: grid; gap: 8px; align-content: start; }
.shots figure { margin: 0; display: grid; gap: 2px; }
.shots img { width: 100%; height: auto; max-width: 100%; border: 1px solid var(--rule); border-radius: 4px; display: block; }
.shots figcaption { font-size: 0.75rem; color: var(--ink-muted); }
ul.plain { margin: 0; padding-left: 18px; display: grid; gap: 4px; }
@media (max-width: 760px) { .card { grid-template-columns: minmax(0, 1fr); } }
"""


def _e(value: object) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _card(entry: dict[str, Any], images: dict[str, dict[str, str]], cache_buster: int) -> str:
    pair = Pair.parse(entry["pair"])
    links = [f'<a href="{_e(pair.site_url)}" target="_blank" rel="noopener">anyplot.ai</a>']
    if entry.get("pr"):
        links.append(
            f'<a href="https://github.com/{catalogue.REPOSITORY}/pull/{int(entry["pr"])}" target="_blank" rel="noopener">PR #{int(entry["pr"])}</a>'
        )
    links.append(
        f'<a href="https://github.com/{catalogue.REPOSITORY}/blob/main/{_e(pair.spec_path)}" target="_blank" rel="noopener">spec</a>'
    )
    score = entry.get("quality_score")
    severity = entry.get("severity") or "low"
    downgraded = entry.get("auditor_severity") not in (None, severity)
    shots = []
    for theme in catalogue.THEMES:
        full = _e(pair.render_url(theme, cache_buster=cache_buster))
        src = images.get(entry["pair"], {}).get(theme)
        body = (
            f'<img src="{src}" alt="{_e(entry["pair"])}, {theme} theme" loading="lazy">'
            if src
            else '<span class="meta">no thumbnail</span>'
        )
        shots.append(
            f'<figure>{body}<figcaption>{theme} · <a href="{full}" target="_blank" rel="noopener">full size</a></figcaption></figure>'
        )
    skeptic = entry.get("skeptic")
    return f"""
<article class="card" id="{_e(entry["id"])}">
  <div class="text">
    <div class="head"><span class="id">{_e(entry["id"])}</span><span class="pair">{_e(entry["pair"])}</span>
      <span class="chip {_e(severity)}">{_e(severity)}{" (auditor: " + _e(entry["auditor_severity"]) + ")" if downgraded else ""}</span>
      <span class="chip low">{_e(entry.get("cause"))}</span><span class="chip low">{_e(entry.get("defect_class"))}</span></div>
    <p class="meta">stored score {_e(score if score is not None else "none")} · selected for {_e(", ".join(entry.get("reasons") or []) or "a sweep")} · {" · ".join(links)}</p>
    <p>{_e(entry.get("what"))}</p>
    <p class="fix">{_e(entry.get("fix"))}</p>
    <details><summary>evidence</summary><p>{_e(entry.get("evidence"))}</p></details>
    {f"<details><summary>skeptic</summary><p>{_e(skeptic)}</p></details>" if skeptic else ""}
  </div>
  <div class="shots">{"".join(shots)}</div>
</article>"""


def _head(title: str, round_name: str) -> str:
    return f"""<title>{_e(title)} {_e(round_name)}</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap">
<style>{STYLE}</style>"""


def render_html(
    model: dict[str, Any],
    images: dict[str, dict[str, str]],
    *,
    round_name: str,
    cache_buster: int,
    title: str = "Catalogue audit",
) -> str:
    findings = model["findings"]
    status = Counter(f["status"] for f in findings)
    severity = Counter(f["severity"] for f in findings if f["status"] == "confirmed")
    confirmed = [f for f in findings if f["status"] == "confirmed"]
    unverified = [f for f in findings if f["status"] == "unverified"]
    lows = [f for f in findings if f["status"] == "low"]
    refuted = [f for f in findings if f["status"] == "refuted"]
    audited = len(model["clean"]) + len({f["pair"] for f in findings}) + len(model["unchecked"])

    def listing(entries: list[dict[str, Any]]) -> str:
        return "".join(
            f"<li><b>{_e(e['id'])}</b> {_e(e['pair'])} · {_e(e.get('defect_class'))} · {_e(e.get('what'))}"
            + (f' <span class="meta">({_e(e.get("skeptic"))})</span>' if e.get("skeptic") else "")
            + "</li>"
            for e in entries
        )

    cards = (
        "".join(_card(entry, images, cache_buster) for entry in confirmed)
        or "<p>No high or medium finding survived the skeptics.</p>"
    )
    unverified_section = (
        '<section class="section"><h2>unverified, no skeptic verdict</h2>'
        '<p class="meta">A high or medium claim whose skeptic returned nothing, twice. Not confirmed: its skeptic runs'
        " again before it can be picked.</p>"
        + "".join(_card(entry, images, cache_buster) for entry in unverified)
        + "</section>"
        if unverified
        else ""
    )
    return f"""{_head(title, round_name)}
<main>
  <header class="section">
    <h1>{_e(title.lower())}<span class="dot">.</span> {_e(round_name)}</h1>
    <p class="lede">Each card is a defect a skeptic tried and failed to refute. Pick what gets fixed in the session: name
    the ids (a low note's id works too), or a rule such as "all high and medium". Nothing is fixed or dispatched before
    that.</p>
    <div class="stats"><span><b>{audited}</b> pairs audited</span><span><b>{len(model["clean"])}</b> clean</span>
      <span><b>{severity["high"]}</b> high</span><span><b>{severity["medium"]}</b> medium</span>
      <span><b>{status["unverified"]}</b> unverified</span><span><b>{status["low"]}</b> low notes</span><span><b>{status["refuted"]}</b> refuted</span>
      <span><b>{len(model["unchecked"])}</b> unchecked</span></div>
  </header>
  <section class="section"><h2>confirmed</h2>{cards}</section>
  {unverified_section}
  <section class="section"><h2>low notes, not verified, pickable by id</h2>
    {f'<details><summary>{len(lows)} note(s)</summary><ul class="plain">{listing(lows)}</ul></details>' if lows else '<p class="meta">none</p>'}</section>
  <section class="section"><h2>refuted</h2>
    {f'<details><summary>{len(refuted)} claim(s) the skeptics refuted</summary><ul class="plain">{listing(refuted)}</ul></details>' if refuted else '<p class="meta">none</p>'}</section>
  <section class="section"><h2>clean and unchecked</h2>
    <details><summary>{len(model["clean"])} clean pair(s)</summary><ul class="plain">{"".join(f"<li>{_e(p)}</li>" for p in model["clean"])}</ul></details>
    {f'<details><summary>{len(model["unchecked"])} unchecked</summary><ul class="plain">{"".join(f"<li>{_e(u)}</li>" for u in model["unchecked"])}</ul></details>' if model["unchecked"] else ""}
  </section>
</main>
"""


# --- the fixes gallery ------------------------------------------------------------------------------------------


NOT_LOCAL = {
    "r": "not rendered locally: adopt mode has no R render, the pipeline renders the regeneration",
    "julia": "not rendered locally: adopt mode has no Julia render, the pipeline renders the regeneration",
}
"""Why a pair has no local render, by language; any other language: the local render failed or never ran."""


def picked(findings: list[dict[str, Any]], ids: list[str]) -> tuple[list[tuple[str, list[dict[str, Any]]]], list[str]]:
    """`(pairs, unknown ids)`: the picked findings grouped by pair, in the order of their first id."""
    by_id = {str(f.get("id")): f for f in findings}
    unknown = [i for i in ids if i not in by_id]
    groups: dict[str, list[dict[str, Any]]] = {}
    for i in dict.fromkeys(i for i in ids if i in by_id):
        groups.setdefault(str(by_id[i]["pair"]), []).append(by_id[i])
    return list(groups.items()), unknown


def local_render(renders: Path, pair: Pair, theme: str) -> Path | None:
    """The newest `check_fix.py --render` PNG of the pair and theme under `renders` (`<pkg>/<spec>/<library>/`)."""
    found = [path for path in renders.glob(f"**/{pair.spec}/{pair.library}/plot-{theme}.png") if path.is_file()]
    return max(found, key=lambda path: path.stat().st_mtime) if found else None


def scaled(path: Path, width: int = 800) -> str | None:
    """A local PNG as a webp data URI scaled to `width`, so a page of full-size renders stays small."""
    from PIL import Image, UnidentifiedImageError

    try:
        with Image.open(path) as image:
            image.thumbnail((width, width * 4))
            out = io.BytesIO()
            image.convert("RGB").save(out, format="WEBP", quality=80)
    except OSError, UnidentifiedImageError:
        return None
    return "data:image/webp;base64," + base64.b64encode(out.getvalue()).decode()


def _figure(src: str | None, alt: str, caption: str, missing: str) -> str:
    body = f'<img src="{_e(src)}" alt="{_e(alt)}" loading="lazy">' if src else f'<p class="meta">{_e(missing)}</p>'
    return f"<figure>{body}<figcaption>{caption}</figcaption></figure>"


def render_fixes_html(
    groups: list[tuple[str, list[dict[str, Any]]]],
    production: dict[str, dict[str, str]],
    local: dict[str, dict[str, str]],
    *,
    round_name: str,
    cache_buster: int,
) -> str:
    """One card per picked pair: the ids and fix sentences, then per theme production next to the local render."""
    cards = []
    for key, entries in groups:
        pair = Pair.parse(key)
        missing = NOT_LOCAL.get(pair.language, "no local render (see check_fix.py's log): renders in the pipeline")
        rows = []
        for theme in catalogue.THEMES:
            full = _e(pair.render_url(theme, cache_buster=cache_buster))
            live = f'production {theme} · <a href="{full}" target="_blank" rel="noopener">full size</a>'
            rows.append(
                '<div class="pairs">'
                + _figure(
                    production.get(key, {}).get(theme), f"{key}, production, {theme}", live, "no production render"
                )
                + _figure(local.get(key, {}).get(theme), f"{key}, the fix, {theme}", f"the fix {theme}", missing)
                + "</div>"
            )
        fixes = "".join(
            f'<p><span class="id">{_e(e.get("id"))}</span> <span class="chip {_e(e.get("severity") or "low")}">'
            f'{_e(e.get("severity"))}</span> {_e(e.get("what"))}</p><p class="fix">{_e(e.get("fix"))}</p>'
            for e in entries
        )
        cards.append(
            f'<article class="card wide" id="{_e(key)}"><div class="text"><div class="head">'
            f'<span class="pair">{_e(key)}</span><a href="{_e(pair.site_url)}" target="_blank" rel="noopener">'
            f"anyplot.ai</a></div>{fixes}</div>{''.join(rows)}</article>"
        )
    return f"""{_head("Catalogue fixes", round_name)}
<style>.card.wide {{ grid-template-columns: minmax(0, 1fr); }}
.pairs {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }}
.pairs figure {{ margin: 0; display: grid; gap: 2px; }}
.pairs img {{ width: 100%; height: auto; border: 1px solid var(--rule); border-radius: 4px; display: block; }}
.pairs figcaption {{ font-size: 0.75rem; color: var(--ink-muted); }}
@media (max-width: 760px) {{ .pairs {{ grid-template-columns: minmax(0, 1fr); }} }}</style>
<main>
  <header class="section">
    <h1>catalogue fixes<span class="dot">.</span> {_e(round_name)}</h1>
    <p class="lede">The fixes for the picked findings, production on the left and the local render of the fix on the
    right, both themes. Nothing is dispatched before the OK for the queue.</p>
    <div class="stats"><span><b>{len(groups)}</b> pairs</span><span><b>{sum(len(e) for _, e in groups)}</b>
      findings</span><span><b>{sum(1 for k, _ in groups if not local.get(k))}</b> render in the pipeline only</span></div>
  </header>
  <section class="section">{"".join(cards) or "<p>No pick.</p>"}</section>
</main>
"""


def fixes_page(args: argparse.Namespace) -> int:
    findings_path = args.round / "findings.json"
    if not findings_path.is_file():
        print(f"build_page: no {findings_path}; build the audit page first", file=sys.stderr)
        return 2
    findings = json.loads(findings_path.read_text(encoding="utf-8")).get("findings", [])
    groups, unknown = picked(findings, args.fixes)
    if unknown or not groups:
        print(
            f"build_page: no such finding id in {findings_path}: {', '.join(unknown) or 'none picked'}", file=sys.stderr
        )
        return 2
    renders = args.renders or args.round / "renders"
    cache_buster = int(time.time())
    production: dict[str, dict[str, str]] = {}
    local: dict[str, dict[str, str]] = {}
    for key, _ in groups:
        pair = Pair.parse(key)
        for theme in catalogue.THEMES:
            data = (
                None
                if args.no_images
                else fetch_image(pair.render_url(theme, size=800, ext="webp", cache_buster=cache_buster))
            )
            if data:
                production.setdefault(key, {})[theme] = "data:image/webp;base64," + base64.b64encode(data).decode()
            path = local_render(renders, pair, theme)
            uri = scaled(path) if path and not args.no_images else None
            if uri:
                local.setdefault(key, {})[theme] = uri
    page = render_fixes_html(groups, production, local, round_name=args.round.name, cache_buster=cache_buster)
    catalogue.write_private(args.round / "page" / "fixes.html", page)
    print(f"fixes: {len(groups)} pair(s), {sum(1 for k, _ in groups if k in local)} with a local render")
    print(f"wrote {args.round / 'page' / 'fixes.html'} ({len(page) // 1024} KB)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the owner's pick list and page from an audit round.")
    parser.add_argument("--round", type=Path, required=True, help="the round directory")
    parser.add_argument("--audit", type=Path, action="append", default=[], help="a saved workflow result (repeatable)")
    parser.add_argument("--candidates", type=Path, help="default: <round>/candidates.json")
    parser.add_argument("--no-images", action="store_true", help="leave the thumbnails out")
    parser.add_argument("--name", default="audit", help="the page's name: audit (default), or e.g. reaudit")
    parser.add_argument("--id-prefix", default="F", help="the ids' prefix (default F)")
    parser.add_argument("--fixes", nargs="+", metavar="ID", help="build the fixes gallery for these picked ids")
    parser.add_argument("--renders", type=Path, help="with --fixes: the local renders (default <round>/renders)")
    args = parser.parse_args(argv)
    if not catalogue.outside_repository(args.round):
        print(f"build_page: {args.round} is inside a git checkout; a round's files stay outside", file=sys.stderr)
        return 2
    if args.fixes:
        return fixes_page(args)
    if not args.audit or not re.fullmatch(r"[a-z0-9-]+", args.name) or not re.fullmatch(r"[A-Z]+", args.id_prefix):
        print("build_page: name --audit, a lowercase --name and an uppercase --id-prefix", file=sys.stderr)
        return 2
    candidates_path = args.candidates or args.round / "candidates.json"
    candidates = json.loads(candidates_path.read_text(encoding="utf-8")) if candidates_path.is_file() else {}
    audits = [json.loads(path.read_text(encoding="utf-8")) for path in args.audit]
    model = collect(audits, candidates, prefix=args.id_prefix)
    cache_buster = int(time.time())
    images = {} if args.no_images else thumbnails(model["findings"], cache_buster)
    built = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    findings_path = args.round / ("findings.json" if args.name == "audit" else f"findings-{args.name}.json")
    page_path = args.round / "page" / f"{args.name}.html"
    catalogue.write_private(findings_path, json.dumps({"built_at": built, **model}, indent=2) + "\n")
    title = "Catalogue audit" if args.name == "audit" else f"Catalogue {args.name}"
    page = render_html(model, images, round_name=args.round.name, cache_buster=cache_buster, title=title)
    catalogue.write_private(page_path, page)
    counts = Counter(f["status"] for f in model["findings"])
    print(f"findings: {dict(counts)}; clean {len(model['clean'])}; unchecked {len(model['unchecked'])}")
    print(f"wrote {findings_path} and {page_path} ({len(page) // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
