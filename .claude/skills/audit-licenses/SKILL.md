---
name: audit-licenses
description: Audit the repo for license and provenance violations — verify nothing copyrighted or unlicensed is tracked (in HEAD or history), no preview images or hidden binary payloads sit in the repo, and any bundled fonts/assets are covered by notices. Use when asked to audit licenses, check asset provenance, verify nothing copyrighted is tracked, or review new binaries or fonts.
---

# License & provenance audit

Code is MIT (`LICENSE`); the repo is public. Plot implementations are
the pipeline's own generated expression — the risks here are inbound
assets: images, fonts, data files, or embedded payloads whose bytes
carry someone else's license. This skill encodes the audit
*procedure*; findings are **reported, never silently deleted**. All
commands run from the repo root.

## 1 · Hard checks (run the battery)

**Tracked binaries, three nets** — extension sweep, content-type
sweep (catches extensionless/renamed binaries), and size list
(catches payloads hiding in text files). Every hit must fall into an
allowed bucket (§2):

```bash
git ls-files | grep -E '\.(png|jpe?g|woff2?|ttf|otf|eot|pdf|gif|webp|svg|ico|zip|tar|t?gz|bz2|xz|wasm|mp[34]|avif|tiff?|bmp|csv|parquet)$'
git ls-files -z | xargs -0 file | awk -F': +' '$2 !~ /text|JSON|SVG|empty|source|script|program|CSV|SPEC|symbolic link/ {print}'
git ls-files -z | xargs -0 -I{} du -k "{}" 2>/dev/null | sort -rn | head -20
```

**No preview images under `plots/`** (previews live in GCS, never in
the repo — the CLAUDE.md anti-pattern rule):

```bash
git ls-files plots/ | grep -E '\.(png|jpe?g|gif|webp)$' || echo "OK: no preview images tracked"
```

**Hidden payloads** — base64 data-URIs in tracked text and raster
images smuggled inside SVGs:

```bash
git grep -nlI ';base64,' -- . ':!.claude/skills/audit-licenses/SKILL.md' \
  ':!docs/reference/palette-analysis.html' ':!docs/reference/palette-variants/' \
  ':!scripts/_palette_common.py' ':!scripts/palette-variants-v1.py' \
  ':!plots/heatmap-mandelbrot/implementations/python/pygal.py' || echo "OK: no new data-URI embeddings"
git grep -nE '<image|data:image' -- '*.svg' || echo "OK: no raster payload in tracked SVGs"
```

(The excluded files are known OWN-generated embedders — the palette
reports embed their swatch/plot images as data-URIs by design, the
two scripts construct the pattern, and pygal inlines its raster
output. New hits outside this list are findings.)

**History** — a public repo exposes every blob ever committed, not
just HEAD. First: binaries that existed but are gone from HEAD
(eyeball each). Second: all deleted paths, eyeballed for protected
names:

```bash
comm -23 <(git rev-list --objects --all | awk '{print $2}' | grep -iE '\.(png|jpe?g|woff2?|ttf|otf|eot|pdf|gif|webp|zip|tar|t?gz|bz2|xz)$' | sort -u) <(git ls-files | sort)
git log --diff-filter=D --name-only --pretty=format: | sort -u | head -50
```

**Bundled fonts vs. notices** — npm-delivered fonts never appear in
`git ls-files`, so check the imports directly. At baseline the app
bundles NO font packages (system-font stack) and has no notices
file — if this sweep starts returning packages, an
`app/THIRD_PARTY_NOTICES.md` becomes required in the same PR:

```bash
grep -roh '@fontsource/[a-z-]*' app/src app/package.json 2>/dev/null | sort -u
```

**Tracked font files vs. notices** — every tracked font file must have
its licence text AND a `README.md` notice in the same directory, and
the notice must name every font file of that directory with its
version, source URL and SHA-256. Since 2026-10-10 the one hit is
`agents/anyplot/render/fonts/` (JetBrains Mono 2.304, SIL OFL 1.1,
drawn into the footer strip of user plots by `render/watermark.py`);
`tests/unit/agents/runtime/test_watermark.py` pins the hashes the
notice records. Any other directory in this list is a finding:

```bash
for dir in $(git ls-files | grep -iE '\.(ttf|otf|woff2?)$' | xargs -r -n1 dirname | sort -u); do
  if [ -f "$dir/README.md" ] && ls "$dir" | grep -qiE '^(OFL|LICENSE)'; then echo "OK: $dir"
  else echo "MISSING notice or licence: $dir"; fi
done
```

## 2 · Judging the hits

Every binary-sweep hit must be one of:

1. **Own-created assets** (logos, icons, UI art under `app/`) — own
   expression, MIT-covered.
2. **Bundled fonts/assets covered by a notices file.** Known entry:
   `agents/anyplot/render/fonts/JetBrainsMono-{Regular,Bold}.ttf` —
   JetBrains Mono 2.304, SIL OFL 1.1 (no Reserved Font Name), copied
   unmodified from the official release zip, with `OFL.txt` and a
   `README.md` notice (source URL, version, SHA-256 of every file)
   beside them. The OFL allows bundling with MIT code as long as the
   fonts are not sold by themselves and the licence travels with them.
   A changed hash, a missing `OFL.txt`, or a modified/renamed font
   without a new notice is a finding.
3. **Pipeline artifacts that should not be tracked at all** (preview
   images, rendered plots) — findings even when self-generated (the
   GCS rule).

Judgment flags the greps can't raise:

- An implementation or prompt that *reproduces* a copyrighted gallery
  example near-verbatim — code is copyrightable expression too;
  spot-check implementations that cite external galleries.
- Data files with real-world datasets: plot code generates synthetic
  data inline; a committed CSV/parquet needs a provenance statement
  or it is a finding.

## Verified baseline (2026-08-17)

- Extension/type/size nets: own-brand assets (`api/static/og-image.png`,
  `app/public/og-image.png`, `favicon.svg`, `logo.svg`), the
  own-generated OG-sample set under `docs/reference/og-samples/`, and
  the palette-report HTMLs under `docs/reference/palette-variants/`
  (largest tracked files, data-URIs by design) — all bucket 1. The
  `file` tool misclassifies ~26 `specification.yaml` as "SPEC" and
  flags the `.claude/commands` symlink — both allowed in the awk net.
- Former wart resolved: `plots/bar-basic/implementations/python/plot-{dark,light}.png`
  were tracked plot renders violating the previews-live-in-GCS rule —
  reported 2026-08-17, removed 2026-08-20 on the user's decision. They
  remain in history, covered by the history net below.
- History net: every history-only binary is a self-generated plot
  render (`plots/*/implementations/*/plot-*.png`, one
  `test_output.png`) — own expression, nothing protected. The
  deleted-paths sweep shows only own workflow/IDE files.
- No `@fontsource` packages, so no `app/THIRD_PARTY_NOTICES.md`
  needed yet.
- Bundled fonts (refreshed 2026-10-10): exactly the two JetBrains Mono
  2.304 TTFs in `agents/anyplot/render/fonts/`, with `OFL.txt` and the
  `README.md` notice beside them (bucket 2). They are the only tracked
  `.ttf` files and the only third-party binaries in HEAD. Re-run the
  sweeps, don't trust these counts.

## Gotchas

- **Filter on the type field, not the whole `file` line** — paths can
  contain trigger words; the type net uses `awk -F': +'` on field 2.
- **Don't rely on the size ranking to catch data-URIs** — the direct
  `;base64,` grep is the detector.
- **A `git rm` does not purge history** — that's what the history
  sweep exists for. If it returns a protected blob, stop: the user
  must decide on a history rewrite; never attempt one yourself.

## Troubleshooting

- A sweep hit fits no bucket → that *is* the finding; report it with
  the bucket you expected it to land in, and do not delete it
  yourself.
