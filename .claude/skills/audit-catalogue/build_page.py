"""Turn an audit round's results into the owner's pick list: `findings.json` and one self-contained HTML page.

Run it from the repository root after the audit workflow's results are saved in the round directory:

    uv run python .claude/skills/audit-catalogue/build_page.py --round "$ROUND" \
        --audit "$ROUND/audit-run1.json" [--audit "$ROUND/audit-run2.json"] [--no-images]

It reads `candidates.json` from the round for the stored scores, ids every finding (`F01`, `F02`, … in the order
the page shows them: confirmed high, confirmed medium, low notes, refuted last) and writes:

- `findings.json`: every finding with its id, status (`confirmed`, `low`, `refuted`), severity after the skeptic,
  cause and fix, plus the clean and unchecked pairs. The owner's picks name these ids.
- `page/audit.html`: the page to publish as a private Artifact. It embeds each finding's two `_800.webp` renders
  as data URIs (the Artifact CSP blocks other hosts' images), fetched with a cache-buster; `--no-images` leaves
  them out. No script, no external resource but the JetBrains Mono stylesheet from Google Fonts.

Both files stay in the round directory, outside every checkout. Exit codes: 0 written, 2 bad arguments.
"""

from __future__ import annotations

import argparse
import base64
import html
import json
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


def collect(audits: list[list[dict[str, Any]]], candidates: dict[str, Any]) -> dict[str, Any]:
    """Merge the workflow's group results into one list of findings with ids, and the clean and unchecked pairs.

    A high or medium finding the skeptic kept is `confirmed` at the skeptic's severity and cause; one it refuted is
    `refuted`; a low finding was never verified and stays `low`. A finding without a verdict (its skeptic died)
    counts as `low` with a note, never as confirmed."""
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
                    entry.update(status="low", skeptic="no skeptic verdict came back; treat as unverified")
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
    rank = {"confirmed": 0, "low": 1, "refuted": 2}
    entries.sort(key=lambda e: (rank[e["status"]], SEVERITY_ORDER.get(e["severity"], 3), e["pair"]))
    for index, entry in enumerate(entries, start=1):
        entry["id"] = f"F{index:02d}"
    return {"findings": entries, "clean": sorted(set(clean)), "unchecked": sorted(set(unchecked))}


def fetch_image(url: str) -> bytes | None:
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                return response.read()
        except urllib.error.HTTPError:
            return None
        except urllib.error.URLError, TimeoutError, OSError:
            time.sleep(2 * (attempt + 1))
    return None


def thumbnails(findings: list[dict[str, Any]], cache_buster: int) -> dict[str, dict[str, str]]:
    """The `_800.webp` render of each theme per pair as a data URI (missing when the bucket has none)."""
    out: dict[str, dict[str, str]] = {}
    for key in sorted({f["pair"] for f in findings if f["status"] != "refuted"}):
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


def render_html(model: dict[str, Any], images: dict[str, dict[str, str]], *, round_name: str, cache_buster: int) -> str:
    findings = model["findings"]
    status = Counter(f["status"] for f in findings)
    severity = Counter(f["severity"] for f in findings if f["status"] == "confirmed")
    confirmed = [f for f in findings if f["status"] == "confirmed"]
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
    return f"""<title>Catalogue audit {_e(round_name)}</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap">
<style>{STYLE}</style>
<main>
  <header class="section">
    <h1>catalogue audit<span class="dot">.</span> {_e(round_name)}</h1>
    <p class="lede">Each card is a defect a skeptic tried and failed to refute. Pick what gets fixed in the session: name
    the ids, or a rule such as "all high and medium". Nothing is fixed or dispatched before that.</p>
    <div class="stats"><span><b>{audited}</b> pairs audited</span><span><b>{len(model["clean"])}</b> clean</span>
      <span><b>{severity["high"]}</b> high</span><span><b>{severity["medium"]}</b> medium</span>
      <span><b>{status["low"]}</b> low notes</span><span><b>{status["refuted"]}</b> refuted</span>
      <span><b>{len(model["unchecked"])}</b> unchecked</span></div>
  </header>
  <section class="section"><h2>confirmed</h2>{cards}</section>
  <section class="section"><h2>low notes, not verified</h2>
    {f'<details><summary>{len(lows)} note(s)</summary><ul class="plain">{listing(lows)}</ul></details>' if lows else '<p class="meta">none</p>'}</section>
  <section class="section"><h2>refuted</h2>
    {f'<details><summary>{len(refuted)} claim(s) the skeptics refuted</summary><ul class="plain">{listing(refuted)}</ul></details>' if refuted else '<p class="meta">none</p>'}</section>
  <section class="section"><h2>clean and unchecked</h2>
    <details><summary>{len(model["clean"])} clean pair(s)</summary><ul class="plain">{"".join(f"<li>{_e(p)}</li>" for p in model["clean"])}</ul></details>
    {f'<details><summary>{len(model["unchecked"])} unchecked</summary><ul class="plain">{"".join(f"<li>{_e(u)}</li>" for u in model["unchecked"])}</ul></details>' if model["unchecked"] else ""}
  </section>
</main>
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the owner's pick list and page from an audit round.")
    parser.add_argument("--round", type=Path, required=True, help="the round directory")
    parser.add_argument(
        "--audit", type=Path, action="append", required=True, help="a saved workflow result (repeatable)"
    )
    parser.add_argument("--candidates", type=Path, help="default: <round>/candidates.json")
    parser.add_argument("--no-images", action="store_true", help="leave the thumbnails out")
    args = parser.parse_args(argv)
    if not catalogue.outside_repository(args.round):
        print(f"build_page: {args.round} is inside a git checkout; a round's files stay outside", file=sys.stderr)
        return 2
    candidates_path = args.candidates or args.round / "candidates.json"
    candidates = json.loads(candidates_path.read_text(encoding="utf-8")) if candidates_path.is_file() else {}
    audits = [json.loads(path.read_text(encoding="utf-8")) for path in args.audit]
    model = collect(audits, candidates)
    cache_buster = int(time.time())
    images = {} if args.no_images else thumbnails(model["findings"], cache_buster)
    built = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    catalogue.write_private(args.round / "findings.json", json.dumps({"built_at": built, **model}, indent=2) + "\n")
    page = render_html(model, images, round_name=args.round.name, cache_buster=cache_buster)
    catalogue.write_private(args.round / "page" / "audit.html", page)
    counts = Counter(f["status"] for f in model["findings"])
    print(f"findings: {dict(counts)}; clean {len(model['clean'])}; unchecked {len(model['unchecked'])}")
    print(f"wrote {args.round / 'findings.json'} and {args.round / 'page' / 'audit.html'} ({len(page) // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
