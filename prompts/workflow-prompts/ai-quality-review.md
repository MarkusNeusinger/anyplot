# AI Quality Review

Evaluate if the **${LIBRARY}** implementation matches the specification for `${SPEC_ID}`.

## Context

- **Spec ID:** ${SPEC_ID}
- **Library:** ${LIBRARY}
- **PR Number:** #${PR_NUMBER}
- **Attempt:** ${ATTEMPT} (review 1 of up to 5 — 4 repairs; a regeneration gets exactly one review)
- **Regeneration:** ${IS_REGENERATION} (when `true`, steps 5f and 8b apply: one review, no repair)

## Your Task

### 1. Read the Specification
`plots/${SPEC_ID}/specification.md`
- Understand what the plot should show
- Note all required features
- Read the closing `## What a good version looks like` section carefully: it names the observable properties of a good render of this plot type and what it may show without penalty. **Judge against it, not against generic ideals.** Each bullet starts with its kind: `A good version shows:` bullets are *affirmative properties* (what a good version shows), `Expected, not a defect:` bullets are *permissions*. Nothing a permission names is ever a weakness; removing or violating an affirmative property deducts from the criterion it belongs to; the absence of a permitted thing never deducts (`prompts/quality-criteria.md` → "Plot-Type Characteristics"). Read an unlabeled section by meaning. If the spec has no such section, infer the characteristics from Description, Data and Notes before you score, and sort them into the same two kinds.

### 2. Read the Implementation
`plots/${SPEC_ID}/implementations/${LANGUAGE}/${LIBRARY}${EXT}` — the workflow supplies `${LANGUAGE}` and `${EXT}` for this run. Reference: `.py` for the Python libraries (matplotlib, seaborn, plotly, bokeh, altair, plotnine, pygal, letsplot), `.R` for ggplot2 (R), `.jl` for makie (Julia), `.js` for the JavaScript libraries (chartjs, d3, echarts, highcharts), and `.tsx` for muix (JavaScript, React)

### 3. Read Library-Specific Rules
`prompts/library/${LIBRARY}.md`

### 4. Read the Impl-Tags Guide
`prompts/impl-tags-generator.md` (for step 9)

### 5. MANDATORY: View BOTH Generated Plots (Light AND Dark)

You MUST use the Read tool to open **both** `plot_images/plot-light.png` AND `plot_images/plot-dark.png` and visually analyze each image.

- Compare both renders with the spec requirements.
- The Imprint palette data colors (positions 1–7) must be **identical** between light and dark — only chrome (background, text, grid, legend frames) flips.
- A review without seeing both images is **invalid**.
- If one or both images cannot be read, STOP and report the error (pipeline failure — flag in `weaknesses`).
- Your review MUST include an "Image Description" section that describes **both** renders, proving you looked at them.

### 5b. Consult the Style Guide for Palette + Theme Rules

Read `prompts/default-style-guide.md` — the "Categorical Palette" (Imprint palette), "Continuous Data" (`imprint_seq` / `imprint_div` only), and "Theme-adaptive Chrome" sections are the authoritative reference for VQ-07 scoring. Always refer to the palette as **Imprint** (capitalised) in review notes — never "anyplot palette".

### 5c. MANDATORY: Theme-Readability Check (both renders)

Before you begin scoring, run this explicit check on **each** render. This is not the palette check (VQ-07) — it asks the simpler question: "is the plot actually readable in this theme?"

For `plot-light.png` (background should be `#FAF8F1`):
- [ ] Plot background is warm off-white, NOT pure white, NOT dark.
- [ ] Title, axis labels, and tick labels are clearly visible against the light background (dark text).
- [ ] Grid lines are subtle but visible (not invisible, not dominant).
- [ ] Data markers/lines are clearly distinguishable from the background.
- [ ] No text is "light on light" — e.g., near-white text on off-white background.

For `plot-dark.png` (background should be `#1A1A17`):
- [ ] Plot background is warm near-black, NOT pure black, NOT light.
- [ ] Title, axis labels, and tick labels are clearly visible against the dark background (light text).
- [ ] Grid lines are subtle but visible.
- [ ] Data markers/lines are clearly distinguishable from the background.
- [ ] **No text is "dark on dark"** — e.g., near-black text on near-black background. This is the most common theme-adaptation failure.
- [ ] Brand green `#009E73` is still visible (it reads well on both surfaces, so this should hold).

**If any checkbox fails for either render, score aggressively:**
- **VQ-01 (Text Legibility): drop to 0 if any title/label/tick is unreadable in either render** — the implementation failed to thread theme tokens through to that element.
- **VQ-07 (Palette Compliance): drop to 0 if chrome is wrong-theme** (dark-on-dark, light-on-light, pure-white, or pure-black background).
- **Flag the specific elements in `weaknesses`** as defect lines (8a) so the repair loop knows exactly what to fix. Example: "VQ-01 (dark): tick labels render near-black on the #1A1A17 background and cannot be read → light text from the INK_SOFT token. Likely cause: ax.tick_params colors not set from INK_SOFT."

A plot that's perfect in one theme but unreadable in the other still **fails** — both renders must pass. Be strict: a plot that ships to the website broken on dark mode is worse than one that fails review and gets repaired.

### 5c2. MANDATORY: Canvas dimension gate (if present)

The workflow's pre-check step (`impl-review.yml` → "Canvas dimension gate") measures the saved `plot-light.png` against the two canonical canvas sizes (3200×1800 landscape, 2400×2400 square, ±16 px tolerance). When the gate fails, it writes the synthetic weakness to `/tmp/anyplot-canvas-gate.txt`.

**Before scoring, check whether `/tmp/anyplot-canvas-gate.txt` exists:**

```bash
ls -la /tmp/anyplot-canvas-gate.txt 2>/dev/null && cat /tmp/anyplot-canvas-gate.txt
```

If it **does** exist:
- The file contains a single paragraph, already a defect line (8a): `VQ-05 (both): Canvas dimensions drifted from required target. Actual: WxH. Closest valid target: TWxTH (±16 px tolerance). Signed delta: ±dx × ±dy — direction. Most likely cause: …`
- **Copy that paragraph verbatim into your `weaknesses` array as the FIRST item.** Do not paraphrase; the repair model needs the literal "actual=WxH" and signed delta numbers to know which knob to turn and which direction.
- **Set VQ-05 (Layout & Canvas) to 0/4 regardless of other observations.** Canvas drift is a hard rule; the quality_score must drop low enough to route the PR into impl-repair through the existing 5-review/4-repair cascade.
- Keep scoring the other categories honestly — useful signal for repair is good signal — but do **not** lift VQ-05 just because the visual proportions look fine inside the wrong-sized canvas.
- On a regeneration (`IS_REGENERATION` is `true`) there is no repair: the regen gate reads the same file and keeps the live implementation. Still do step 8b — the comparison is recorded for the next attempt.

If it does **not** exist: the gate passed; no canvas-specific action — score VQ-05 normally based on the visual proportional checks in 5d below.

### 5d. MANDATORY: Proportional Sizing Check (both renders)

Visually estimate from each PNG — no pixel measurement needed. These are soft proportional checks **without hard thresholds**. Violations cost points in the existing VQ-01 (Text Legibility), VQ-02 (No Overlap), VQ-03 (Element Visibility), VQ-05 (Layout & Canvas) and SC-03 (Data Mapping) categories rather than triggering a separate pass/fail item. A single visual problem can reduce points in multiple categories simultaneously (holistic, not strict).

- **Title proportion:** Title comfortably occupies ~50–70% of the plot width. **Note:** the mandated `{spec-id} · {lang} · {lib} · anyplot.ai` title is ~67 chars; at the style-guide default fontsize it naturally fills ~70–85% on landscape. That is **expected and not a deduction** — the AI made the right tradeoff. Only deduct if either: (a) the title overflows beyond ~90% of plot width / clips edges, or (b) the fontsize is too generous for the title length (squeezed look, no breathing room) → VQ-01 + VQ-05.
- **Axis label proportionality:** Short labels with few words ("Date", "Year") must not dominate the axis with oversized fontsizes. Long descriptive labels ("Fläche von Häusern in Quadratmetern", "Average temperature in °C") are completely fine as long as they don't overflow — the "No overflow" check below covers that. Disproportionately oversized short labels → deduct VQ-05.
- **Axis label balance:** X-axis and Y-axis labels are visually similar in size. One much larger than the other without semantic reason → deduct VQ-05.
- **Tick label balance:** X-axis and Y-axis tick labels are visually similar in size. Exception: rotated long categorical labels may legitimately look wider.
- **No overlap:** No text overlaps with other text, with data elements, or with legend/annotation boxes → deduct VQ-02 (severe overlap = 0). **Data marks overlapping each other** is different: it is a weakness only when it hides information (an opaque blob where marks can no longer be told apart). For overlap-native types — bubble, dense scatter, strip, network — overlap handled with translucency or a thin outline (page- or ink-colored) is expected and not a deduction, especially when the spec's characteristic section says so.
- **No overflow:** No text extends beyond axis bounds, plot bounds, or the canvas frame → deduct VQ-05.
- **Marker / line density appropriateness:** Sparse data (< 50 points) should have prominent markers; dense data (> 500 points) should have smaller markers + `alpha < 1` to combat overplotting → deduct VQ-03 when poorly chosen.
- **Legend glyphs visible:** Look at every legend in **both** renders. Size circles, color swatches and line samples must be visible against the page and match the marks they explain (fill, outline, alpha, shape). A glyph drawn in the background color or without the marks' fill → deduct VQ-03 (+ SC-04 when the encoding becomes unreadable), and name the likely fix in the weakness (e.g. ggplot2 `guide_legend(override.aes = list(fill = ...))`).
- **Marks at their data values:** Check the code for force/collision simulations, nudge or declutter passes, or offsets applied to data marks after the data was generated. Displacement deducts SC-03 in proportion to how far marks move relative to the axis range — never list it as a strength. Changing the generated data, the marker size or the alpha is the endorsed answer to overlap. Exempt: categorical strip/swarm jitter, layout-positioned types (networks, treemaps, word clouds), and any jitter, dodge or offset the spec's Data or Notes ask for (then it is a required feature, not displacement).

**Required:** Note specific violations in `weaknesses` as defect lines (8a), with enough context for the repair loop to fix them. Examples:
- "VQ-05 (both): x-axis label 'Date' at 18 pt dominates the axis for its short content → about 10 pt (−8 pt). Likely cause: xlabel fontsize=18."
- "VQ-01, VQ-05 (both): title overflows past the plot edge at about 95 % of the width → under 90 % (about −6 pt). Likely cause: title fontsize=18."
- "VQ-03 (both): 32 sparse points drawn at 4 px are barely visible → 10–14 px (+6 to +10 px). Likely cause: scatter s=4."

**Counter-examples (NOT deductions):**
- "Title spans ~80% of width at fontsize=14pt." → Expected for the long mandated anyplot title; no deduction.
- "Y-axis label 'Fläche von Häusern in Quadratmetern' takes ~40% of axis length at fontsize=12pt." → Genuinely long label at sensible fontsize; no deduction as long as it doesn't overflow the axis.

### 5e. Interactive & JavaScript Libraries — Fairness Rules

**Interactive libraries** (produce `plot-{theme}.html` alongside the PNG): altair, bokeh, chartjs, d3, echarts, highcharts, letsplot, muix, plotly, pygal.

- **DO NOT penalize** interactive features that aren't visible in the PNG — tooltips/hover info, zoom/pan/selection tools, interactive legends, crossfiltering. The PNG is a static preview; these features add real value in the HTML detail view. Treat well-configured interactivity as a strength (e.g. "Uses HoverTool for detailed data inspection in HTML output").
- **Only criticize** interactivity when it hurts the static render: hover-only labels that leave the PNG unreadable, misconfigured features, or errors.

**JavaScript libraries** (chartjs, d3, echarts, highcharts as `.js`; muix as `.tsx`): the snippet renders into the browser harness's pre-sized `#container` mount node and never saves files itself — the harness (`automation/js-render/render.mjs`) captures `plot-{theme}.png` and `plot-{theme}.html`. For CQ-05, check the mount-node contract and current library API instead of `savefig`-style calls; animations must be disabled (`animation: false` or the library's equivalent) so the harness doesn't screenshot mid-animation.

### 5f. Regeneration (only when `IS_REGENERATION` is `true`)

Score this implementation exactly like any other in steps 6–8 — blind, without looking at its predecessor. The before/after comparison comes afterwards, in step 8b.

### 6. Check for Auto-Reject (AR-08, AR-09)

**AR-08 — Fake interactivity (static libraries only — matplotlib, seaborn, plotnine, ggplot2, makie):**

Before scoring, check if the implementation fakes interactive features:
- Simulated tooltips (annotation boxes styled as hover tooltips)
- Simulated selection/hover states
- Drawn UI controls (buttons, sliders)
- Code comments mentioning "simulating hover/click/interactivity"

If found: Score = 0, verdict = REJECTED, note AR-08 violation.

**AR-09 — Edge clipping (all libraries):**

Inspect both renders for any title, axis tick label, axis title, legend, or annotation that has **visible pixels chopped off at the canvas border** — i.e. the element was rendered partially outside the saved PNG's bounding box and the missing pixels are gone for good. This is the single most embarrassing failure mode for the catalog: a chart with chopped-off text publishes broken into the gallery.

**Strict definition:** AR-09 fires only when **pixels of the element are actually missing**. Proximity to the border, touching the border, or being rendered right up against the edge with all pixels visible is **not** AR-09 — that's at most a VQ-05 deduction. The bar is evidence of chopped content, not crowded margins.

Trigger AR-09 if you see ANY of:
- **Title cropped at the top edge** — top of letters cut off, descenders missing, or title not fully visible above the plot area.
- **Y-axis tick labels missing their leftmost digit/character** because the label extends past the left canvas edge (e.g. "500" rendered as "00", "1,000" as ",000").
- **X-axis label cut at the bottom edge** — axis title only partially visible, descender row chopped.
- **Legend entries hidden behind / merged into the canvas edge** with letters chopped off.
- **Any annotation, label, or category text whose bounding box is partially outside the saved PNG** so part of the text is gone.

If found: **Score = 0, verdict = REJECTED, note AR-09 violation** and identify which element(s) were clipped and on which edge (e.g. "title clipped at top edge of light render — top ~10 px of letters missing"). Repair will receive this and shrink the inner-chart dims so vl-convert / matplotlib / etc. don't push content off the canvas.

**False-positive guard — do NOT trigger AR-09 for:**
- Text that extends past the plot/axis bounds but stays *within* the canvas (VQ-05 deduction at most).
- Tooltips, legend swatches, or grid lines aligned with the canvas border by design.
- Tight-but-readable margins where every pixel of the text is visible — proximity ≠ clipping.
- Touching the border without any missing pixels — touching ≠ chopped.

### 7. Evaluate Using 6-Category Criteria

Read `prompts/quality-criteria.md` and evaluate:

#### Visual Quality (30 pts)
| ID | Criterion | Max | Check |
|----|-----------|-----|-------|
| VQ-01 | Text Legibility | 8 | Font sizes explicitly set? Readable at full size in BOTH themes? Mobile-readable when scaled to ~400 px? Apply Proportional Sizing Check (5d). |
| VQ-02 | No Overlap | 6 | All text readable? No collisions with other text or with data? Data-mark overlap only counts when it hides information — expected overlap handled with alpha/outline is not a deduction. See 5d. |
| VQ-03 | Element Visibility | 6 | Markers/lines adapted to density? Legend glyphs (size circles, swatches, line samples) visible in BOTH themes and matching the marks? See 5d. |
| VQ-04 | Color Accessibility | 2 | Adequate contrast + CVD-safe (beyond palette)? No red-green as sole signal? |
| VQ-05 | Layout & Canvas | 4 | Good proportions? Nothing cut off? Title 50–70% width, balanced axis labels, no overflow — see 5d. |
| VQ-06 | Axis Labels & Title | 2 | Descriptive with units? |
| VQ-07 | Palette Compliance | 2 | First categorical series = `#009E73`? Multi-series uses Imprint palette (canonical order, or semantic-exception order when category labels imply real-world colors)? Continuous data uses `imprint_seq` (single-polarity) or `imprint_div` (diverging) — no other colormaps allowed? Plot backgrounds are `#FAF8F1` (light) / `#1A1A17` (dark)? Both renders theme-correct? |

#### Design Excellence (20 pts)
| ID | Criterion | Max | Check |
|----|-----------|-----|-------|
| DE-01 | Aesthetic Sophistication | 8 | Professional polish? Custom palette? Intentional hierarchy? |
| DE-02 | Visual Refinement | 6 | Spines removed? Grid subtle? Whitespace generous? |
| DE-03 | Data Storytelling | 6 | Visual hierarchy? Clear focal point? Guides the viewer? |

**Defaults:** DE-01=4, DE-02=2, DE-03=2. Raise only with evidence.

#### Spec Compliance (15 pts)
| ID | Criterion | Max | Check |
|----|-----------|-----|-------|
| SC-01 | Plot Type | 5 | Correct chart type? On a `-basic` id: no encodings or elements the spec neither requires nor offers as optional (a Data column or a Notes bullet that allows color by category is asked for; a channel driven by a derived fourth variable is not)? Unasked additions (derived color channel, per-group fits, reference lines, highlights, callouts, annotation layers; one is enough, listed in the variant bullet or not) are the wrong variant (partial SC-01) and earn no DE-03/LM-02 credit. A related but different form (a donut for a pie) is partial SC-01 on any spec. |
| SC-02 | Required Features | 4 | All features from spec? Check each Notes bullet and each `A good version shows:` bullet against the render, and name any missed one in the comment. (Its `Expected, not a defect:` bullets are permissions, not features.) |
| SC-03 | Data Mapping | 3 | X/Y correct? Axes show all data? Marks sit at their data values — no force/collision layout, nudge or declutter pass moving data marks (exempt: categorical jitter, layout-positioned types, and any jitter, dodge or offset the spec's Data or Notes ask for)? A smoothed curve that swings past the values it connects (spline overshoot) shows values the data does not have — deduct in proportion. |
| SC-04 | Title & Legend | 3 | Title is `{spec-id} · {language} · {library} · anyplot.ai`, optionally prefixed with `{Descriptive Title} · ` (language ∈ {python, r, julia, javascript}). Legend labels match? |

#### Data Quality (15 pts)
| ID | Criterion | Max | Check |
|----|-----------|-----|-------|
| DQ-01 | Feature Coverage | 6 | Shows ALL aspects of plot type? (A permission is not an aspect to exhibit: data with little or no overlap loses nothing, and a point count inside the spec's Data range is not a lever.) |
| DQ-02 | Realistic Context | 5 | Real-world plausible AND neutral? |
| DQ-03 | Appropriate Scale | 4 | Sensible values for domain? |

#### Code Quality (10 pts)
| ID | Criterion | Max | Check |
|----|-----------|-----|-------|
| CQ-01 | KISS Structure | 3 | No functions/classes? |
| CQ-02 | Reproducibility | 2 | Seed or deterministic? |
| CQ-03 | Clean Imports | 2 | Only used imports? |
| CQ-04 | Code Elegance | 2 | Appropriate complexity? No fake UI? |
| CQ-05 | Output & API | 1 | Saves as `plot-{THEME}.png` (+ `plot-{THEME}.html` for interactive libs)? No bare `plot.png`? Current API? |

#### Library Mastery (10 pts)
| ID | Criterion | Max | Check |
|----|-----------|-----|-------|
| LM-01 | Idiomatic Usage | 5 | Library's recommended patterns? High-level API? |
| LM-02 | Distinctive Features | 5 | Features unique to this library? |

**Defaults:** LM-01=3, LM-02=1. Raise only with evidence.

### 8. Apply Score Caps

| Condition | Max Score |
|-----------|-----------|
| VQ-02 = 0 (severe overlap) | 49 |
| VQ-03 = 0 (invisible elements) | 49 |
| SC-01 = 0 (wrong plot type) | 40 |
| DQ-02 = 0 (controversial data) | 49 |
| DE-01 ≤ 2 AND DE-02 ≤ 2 (generic + no visual refinement) | 75 |
| CQ-04 = 0 (fake functionality) | 70 |

### 8a. Strengths and weaknesses (every review)

Every weakness is one of two kinds of line. The next generation fixes the defects and never acts on a suggestion.

- **Defect** — the render (or the code, for CQ) visibly violates a named rule: a rubric criterion, a style-guide rule, or an `A good version shows:` bullet of the spec. Write it as `<ID>[, <ID>] (<light|dark|both|code>): <what is wrong, with the observed value> → <target or direction, signed delta when numeric>. Likely cause: <code element>.` The ID is the criterion the defect costs points on (`VQ-01` … `LM-02`), or `AR-06` … `AR-09`. Every criterion you name is below its maximum in your checklist. Any criterion may name a defect, DE and LM included.
- **Suggestion** — everything that names no violated rule: a storytelling layer or a focal highlight, a library showcase ("could use X"), "larger", "more presence" or "more distinctive", an optional feature the spec only allows (asymmetric error bars, percentage labels), or polishing an element the spec's scope excludes. Write it as `Suggestion: <idea>`. At most three; none is fine. A suggestion costs no points.

List the defects first, then the suggestions. Rules:

- A behavior is never both a strength and a weakness.
- A strength may credit a native library idiom and, per 5e, library-native interactivity. It never credits an unrequested addition: an encoding or element the spec neither requires nor offers as optional, a hand-built stand-in for a native feature, an annotation layer, or displaced marks.
- Never write a defect that asks to add something the spec does not ask for (the additions 8b step 3 lists: a derived color channel, a trend, fit or reference line, a band, an annotation layer, facets or marginals).
- On a `-basic` spec, never suggest a layer the spec does not ask for, such as a reference line, a highlight or a callout; removing one is the fix.
- Never propose moving marks off their data values (5d).

Counter-examples:

- A mandated title at 32 % of the width is at most a suggestion: 5d makes a small title no deduction.
- "No distinctive ggplot2 feature" is a suggestion.
- A near-hidden bubble that is still distinguishable by its outline, on a spec whose `Expected, not a defect:` bullet permits overlap, is covered by that bullet. It is not a VQ-02 defect.
- An amber mean-reference line on a `-basic` bar chart is variant creep (SC-01): the line itself is the defect, and removing it is the fix. Recoloring it is a suggestion.

### 8b. Regeneration: before/after (only when `IS_REGENERATION` is `true`)

Skip this section entirely when `IS_REGENERATION` is `false`.

Your score for the new implementation is final now; do not revise it after seeing the predecessor.

A regeneration replaces an implementation that is already live on main. It gets exactly **one** review — this one — and no repair loop. The workflow's regen gate (`automation/scripts/regen_gate.py`) reads your `review_regen.json` and replaces the live implementation only if **all** of these hold; otherwise the PR is closed and the live implementation stays:

- your score for the new render ≥ your re-score of the predecessor − 1;
- at least one improvement a viewer can see (non-empty `where_visible`);
- no regressions (on a `*-basic` spec, a replaced data scenario or added encodings count as regressions unless a change request asked for them).

Your job is an honest comparison; the gate does the arithmetic. Workflow variables for this step: `PREV_RENDERS` (`available` / `missing`), `PREV_RENDER_LIGHT` and `PREV_RENDER_DARK` (paths of the predecessor's renders), `PREV_LINES` and `NEW_LINES` (line counts of the previous and the new source).

1. **Re-score the predecessor.** If `PREV_RENDERS` is `missing`, skip steps 1–4, do not write `review_regen.json`, and say so in the comment (the gate keeps the live implementation). Otherwise open `PREV_RENDER_LIGHT` and `PREV_RENDER_DARK` (the production renders currently on the website) and `/tmp/anyplot-prev-impl${EXT}` (their source — its header reads `Quality: hidden/100` on purpose; do not look the stored score up elsewhere, for example in main's metadata or git history), and score them against the **same** criteria — steps 5c–8, same score caps, same calibration. The result is `prev_rescored`, and its 24 item scores are `prev_checklist` (`{"VQ-01": 7, "VQ-02": 4, …}`: every criterion, each an integer from 0 to its maximum). Number the predecessor's *defects* you find (8a) `P1`, `P2`, … and name each one's criterion.
2. **Read the previous review** `/tmp/anyplot-prev-review.md`. Its weaknesses carry stable ids `W1`..`Wn`, each tagged `(defect)`, `(suggestion)` or `(older review)`. When it has a "Characteristic bullets" list (`C1`..`Cn`, taken from the spec's "What a good version looks like" section), its `A good version shows:` bullets are properties a good version must show; its `Expected, not a defect:` bullets are permissions and can never be an improvement `ref`. When the list is absent, there are no `C` ids — never invent one.

   Then **classify every `W`**, looking at the predecessor's renders only (not the new ones), as one of:
   - `defect` — the predecessor's render visibly violates a named rule (8a). `rule` is the criterion, or the `C` id of the `A good version shows:` bullet it violates.
   - `suggestion` — it names no violated rule (8a), or the predecessor does not show it.
   - `obsolete` — an `Expected, not a defect:` bullet covers it: it asks for less of something that bullet permits. `rule` is that bullet's `C` id.

   A `W` tagged `(suggestion)` becomes `suggestion` or `obsolete`, never `defect`: if the predecessor really shows a defect there, number it as a `P` finding instead. An `(older review)` note predates the current rubric and gets whatever class the current criteria give it. Apply the counter-examples of 8a: a weakness asking for less overlap between bubbles that stay distinguishable by their outline, on a spec that permits overlap, is `obsolete`; a weakness asking to restyle a mean line that a `-basic` spec's scope excludes is a `suggestion` (the line itself is the defect, and the fix is removing it).
3. **Judge the pair side by side** (light against light, dark against dark):
   - **Improvement** — something a viewer can see in the new renders that fixes something visibly wrong or missing in the predecessor. `ref` is the `W` id it resolves, your `P` id, a `C` id of an `A good version shows:` bullet the predecessor missed, or `"new"` for a predecessor defect you did not number. A `P` or `"new"` item also names its `rule`: the criterion, or the `C` id of the `A good version shows:` bullet, it fixes (a `W` carries the rule you gave it in step 2). An encoding or layer the spec does not ask for — a derived color channel, a trend, fit or reference line, a band, an annotation layer, facets or marginals — is never an improvement, on any spec: list it under `encodings_added`. Chrome the criteria require (title format, legend, axis labels, color bar) is not an addition. `where_visible` names the element and the render(s), for example "size legend, both renders: the circles are now visible on the dark background". Code-only changes (refactors, comments, extra code without a visible effect) are **not** improvements. If you cannot point to it in a render, leave `where_visible` empty — it then does not count.
   - **Claims must show in the scores.** A `W` classed `defect` under a criterion names a criterion that `prev_checklist` deducts. An improvement that claims a criterion (a `defect` `W`, or a `P` or `"new"` item) scores higher on that criterion in your checklist for the new render than in `prev_checklist`. When a claim fails either test, change the claim, never the scores: reclass the `W` (`suggestion` or `obsolete`), or remove the improvement from `improvements` — it did not fix that criterion. `prev_checklist` and `review_checklist.json` are final.
   - **Regression** — anything that was good in the predecessor and is worse now: a lost or unreadable legend, illegible or overlapping text, clipping, a worse layout, a lost `A good version shows:` property, or data marks that no longer sit at their data values (force, collision, nudge or declutter passes applied to data marks after the data exists). Exempt, as in SC-03: jitter in categorical strip and swarm plots (the categorical axis carries no value), layout-positioned types where position is not data (networks, treemaps, word clouds, packed circles), and any jitter, dodge or offset the spec's Data or Notes ask for.
   - `scenario_changed` — `true` when the data story (domain, variables, labels) was replaced rather than refined.
   - `encodings_added` — visual encodings the new version maps that the predecessor did not, beyond what the spec's Data, Notes or characteristic section ask for (for example `"color by region"`, `"trend line"`, `"facets"`); a required element the predecessor lacked is an improvement, not an addition. Empty list when none.
   - `change_request_applied` — when `/tmp/anyplot-change-request.txt` exists, `true` if the new version applies that request, `false` if not; `null` when the file does not exist.
   - Code size: `PREV_LINES` → `NEW_LINES`. A large growth without a visible change is a note for the comparison section and, when your checklist deducts CQ-04 for it, a `CQ-04 (code): …` defect in `weaknesses` (so the next regeneration sees it). It is not a regression and not a gate condition.
4. **Write `review_regen.json`** (repository root, next to the other review files) and check that it parses:

```json
{
  "prev_rescored": 84,
  "prev_checklist": {
    "VQ-01": 7, "VQ-02": 4, "VQ-03": 6, "VQ-04": 2, "VQ-05": 4, "VQ-06": 2, "VQ-07": 1,
    "DE-01": 5, "DE-02": 4, "DE-03": 3,
    "SC-01": 5, "SC-02": 4, "SC-03": 3, "SC-04": 3,
    "DQ-01": 6, "DQ-02": 4, "DQ-03": 4,
    "CQ-01": 3, "CQ-02": 2, "CQ-03": 2, "CQ-04": 2, "CQ-05": 1,
    "LM-01": 4, "LM-02": 3
  },
  "prev_weaknesses": [
    {"ref": "W1", "class": "obsolete", "rule": "C2"},
    {"ref": "W2", "class": "suggestion"},
    {"ref": "W3", "class": "defect", "rule": "VQ-07"}
  ],
  "improvements": [
    {"ref": "W3", "what": "Sporting Goods moved off the red loss anchor", "where_visible": "legend and bubbles, both renders"},
    {"ref": "P1", "rule": "VQ-02", "what": "BEAU-001 label clear of the bubble above", "where_visible": "label, both renders"},
    {"ref": "C3", "what": "Overlapping bubbles now have a thin outline", "where_visible": "dense cluster, both renders"}
  ],
  "regressions": [],
  "scenario_changed": false,
  "encodings_added": [],
  "change_request_applied": null
}
```

`regressions` entries use `{"what": "...", "where_visible": "..."}`. Every `W` ref must be an id from `/tmp/anyplot-prev-review.md`, and every `C` ref an id of an `A good version shows:` bullet from its characteristic list — an unknown id makes the whole file invalid and the gate keeps the live implementation, and the gate does not count an improvement that cites an `Expected, not a defect:` bullet. Classification entries never invalidate the file: a missing or malformed `prev_weaknesses` entry leaves that `W` unclassified, and an unclassified `W` counts as a suggestion. Report regressions even when you also found improvements; the gate needs both.

### 9. Post Verdict as PR Comment on PR #${PR_NUMBER}

Use this EXACT format:

```markdown
## AI Review - Attempt ${ATTEMPT}/3

### Image Description

> **Light render (`plot-light.png`):** Describe the plot on the `#FAF8F1` surface —
> colors used, axis labels, title, data representation, overall layout.
> Explicitly state whether all text is readable against the light background.
>
> **Dark render (`plot-dark.png`):** Describe the same elements on the `#1A1A17` surface.
> Confirm the data colors are identical to the light render (only chrome should flip).
> Explicitly state whether all text is readable against the dark background — call out
> any "dark-on-dark" failures (e.g. black tick labels on near-black background).
>
> Both paragraphs are required. A review that only describes one render is invalid.

### Score: XX/100

| Category | Score | Max |
|----------|-------|-----|
| Visual Quality | XX | 30 |
| Design Excellence | XX | 20 |
| Spec Compliance | XX | 15 |
| Data Quality | XX | 15 |
| Code Quality | XX | 10 |
| Library Mastery | XX | 10 |
| **Total** | **XX** | **100** |

### Visual Quality (XX/30)
- [x] VQ-01: Text Legibility (X/8)
- [x] VQ-02: No Overlap (X/6)
- [x] VQ-03: Element Visibility (X/6)
- [x] VQ-04: Color Accessibility (X/2)
- [x] VQ-05: Layout & Canvas (X/4)
- [x] VQ-06: Axis Labels & Title (X/2)
- [x] VQ-07: Palette Compliance (X/2)

### Design Excellence (XX/20)
- [ ] DE-01: Aesthetic Sophistication (X/8) - Generic defaults
- [ ] DE-02: Visual Refinement (X/6) - Minimal customization
- [ ] DE-03: Data Storytelling (X/6) - No visual hierarchy or emphasis

### Spec Compliance (XX/15)
- [x] SC-01: Plot Type (X/5)
- [x] SC-02: Required Features (X/4)
- [x] SC-03: Data Mapping (X/3)
- [x] SC-04: Title & Legend (X/3)

### Data Quality (XX/15)
- [x] DQ-01: Feature Coverage (X/6)
- [x] DQ-02: Realistic Context (X/5)
- [x] DQ-03: Appropriate Scale (X/4)

### Code Quality (XX/10)
- [x] CQ-01: KISS Structure (X/3)
- [x] CQ-02: Reproducibility (X/2)
- [x] CQ-03: Clean Imports (X/2)
- [x] CQ-04: Code Elegance (X/2)
- [x] CQ-05: Output & API (X/1)

### Library Mastery (XX/10)
- [x] LM-01: Idiomatic Usage (X/5)
- [ ] LM-02: Distinctive Features (X/5) - Generic usage

### Score Caps Applied
- [ ] None / [describe cap if applied]

### Strengths
<!-- What the current criteria credit: a native library idiom, library-native interactivity (5e). Never an unrequested addition, a hand-built stand-in for a native feature, an annotation layer or displaced marks (8a). -->
- Strength 1
- Strength 2

### Weaknesses
<!-- Defect lines first, then at most three Suggestion: lines (8a). The same lines go into review_weaknesses.json. -->
- VQ-03, SC-04 (both): the size legend's circles are drawn in the page color and vanish on both backgrounds → fill and outline them like the data marks. Likely cause: `guide_legend()` without `override.aes`.
- VQ-02 (light): the BEAU-001 label overlaps the bubble above it by about 6 px → clear it by at least 4 px (+10 px). Likely cause: the label's `vjust`, not the bubble position.
- CQ-04 (code): the file grew from 62 to 118 lines with no visible change in either render → drop the unused helper and the duplicated theme block. Likely cause: `make_legend()` that is never called.
- Suggestion: a slightly larger legend title would balance the axis titles.

### Regeneration comparison
<!-- Only when IS_REGENERATION is true (step 8b); omit the whole section otherwise. -->
| Predecessor (re-scored) | New |
|---|---|
| XX | XX |

**Predecessor defects:** P1 (VQ-02) the BEAU-001 label overlaps the bubble above it, …
**Previous weaknesses:** W1 obsolete (C2) · W2 suggestion · W3 defect (VQ-07)
**Improvements:** `W3` Sporting Goods moved off the red loss anchor — legend and bubbles, both renders
**Regressions:** none
**Scenario changed:** no · **Encodings added:** none · **Change request applied:** n/a
**Code size:** ${PREV_LINES} → ${NEW_LINES} lines

### Verdict: APPROVED / REJECTED
```

On a regeneration the `Verdict` line is your assessment of the new render only; the regen gate decides merge versus keep.

### 10. Save Review Data to Files

The workflow parses these files — create them all:

```bash
# Quality score (integer 0-100)
echo "XX" > quality_score.txt

# Structured feedback as JSON arrays: the weaknesses are the defect lines,
# then at most three "Suggestion: …" lines (8a)
echo '["Strength 1", "Strength 2"]' > review_strengths.json
echo '["VQ-02 (light): … → …. Likely cause: ….", "Suggestion: …"]' > review_weaknesses.json

# Verdict (APPROVED or REJECTED)
echo "APPROVED" > review_verdict.txt

# Image description (multi-line text proving you viewed BOTH renders and checked legibility)
cat > review_image_description.txt << 'EOF'
Light render (plot-light.png):
  Background: [describe — must be warm off-white around #FAF8F1]
  Chrome: [title, axis labels, ticks — confirm all readable]
  Data: [colors, markers, lines — confirm first series is #009E73]
  Legibility verdict: PASS | FAIL (explain if FAIL)

Dark render (plot-dark.png):
  Background: [describe — must be warm near-black around #1A1A17]
  Chrome: [title, axis labels, ticks — confirm all readable; FLAG any dark-on-dark]
  Data: [confirm colors are identical to light render]
  Legibility verdict: PASS | FAIL (explain if FAIL)
EOF

# Criteria checklist as structured JSON.
# Use EXACTLY these six keys — visual_quality, design_excellence,
# spec_compliance, data_quality, code_quality, library_mastery — with these
# maxima (30/20/15/15/10/10, matching step 7). The website's quality tab and
# the stored metadata rely on this exact shape; no other keys, no renames.
cat > review_checklist.json << 'EOF'
{
  "visual_quality": {
    "score": 24,
    "max": 30,
    "items": [
      {"id": "VQ-01", "name": "Text Legibility", "score": 7, "max": 8, "passed": true, "comment": "All text readable in both themes"},
      {"id": "VQ-02", "name": "No Overlap", "score": 5, "max": 6, "passed": true, "comment": "No collisions"}
    ]
  },
  "design_excellence": {"score": 12, "max": 20, "items": [...]},
  "spec_compliance": {"score": 13, "max": 15, "items": [...]},
  "data_quality": {"score": 12, "max": 15, "items": [...]},
  "code_quality": {"score": 9, "max": 10, "items": [...]},
  "library_mastery": {"score": 6, "max": 10, "items": [...]}
}
EOF

# Regeneration only (IS_REGENERATION = true and PREV_RENDERS = available):
# the before/after judgement from step 8b, in the shape of its example (all
# 24 prev_checklist items, one prev_weaknesses entry per W). Missing or
# malformed = the regen gate keeps the live implementation — so check that it parses.
cat > review_regen.json << 'EOF'
{"prev_rescored": 84, "prev_checklist": {"VQ-01": 7, "VQ-02": 4, "VQ-03": 6, "VQ-04": 2, "VQ-05": 4, "VQ-06": 2, "VQ-07": 1, "DE-01": 5, "DE-02": 4, "DE-03": 3, "SC-01": 5, "SC-02": 4, "SC-03": 3, "SC-04": 3, "DQ-01": 6, "DQ-02": 4, "DQ-03": 4, "CQ-01": 3, "CQ-02": 2, "CQ-03": 2, "CQ-04": 2, "CQ-05": 1, "LM-01": 4, "LM-02": 3}, "prev_weaknesses": [{"ref": "W1", "class": "obsolete", "rule": "C2"}, {"ref": "W2", "class": "suggestion"}, {"ref": "W3", "class": "defect", "rule": "VQ-07"}], "improvements": [{"ref": "W3", "what": "...", "where_visible": "..."}, {"ref": "P1", "rule": "VQ-02", "what": "...", "where_visible": "..."}], "regressions": [], "scenario_changed": false, "encodings_added": [], "change_request_applied": null}
EOF
python3 -c "import json; json.load(open('review_regen.json'))"

# Self-check, last: the weakness lines against your checklist and, on a
# regeneration that wrote review_regen.json, the classes and claims of step 8b.
# /tmp/anyplot-regen-gate.py is the workflow's own copy of the regen gate; skip
# the check when it is missing.
if [ -f /tmp/anyplot-regen-gate.py ]; then
  python3 /tmp/anyplot-regen-gate.py check-feedback --weaknesses review_weaknesses.json --checklist review_checklist.json
  # Regeneration with review_regen.json written — run this form instead:
  # python3 /tmp/anyplot-regen-gate.py check-feedback --weaknesses review_weaknesses.json --checklist review_checklist.json \
  #   --regen review_regen.json --prev-weaknesses /tmp/anyplot-prev-weaknesses.json --spec-file plots/${SPEC_ID}/specification.md
fi
```

All scores and review files above (`quality_score.txt`, `review_checklist.json`, …) describe the **new** implementation. The predecessor's re-score goes only into `review_regen.json`.

Fix what `check-feedback` lists by changing the claim — a weakness line, a class or `rule` in `prev_weaknesses`, a `rule` on an improvement, or an entry in `improvements` — never `prev_checklist` or `review_checklist.json`, which are final. Then run the check once more.

### 11. Generate impl_tags

Analyze the implementation code and create impl_tags based on `prompts/impl-tags-generator.md`:

```bash
cat > review_impl_tags.json << 'EOF'
{
  "dependencies": [],
  "techniques": ["colorbar", "annotations"],
  "patterns": ["data-generation"],
  "dataprep": [],
  "styling": ["publication-ready"]
}
EOF
```

The 5 dimensions:
- `dependencies`: External packages beyond numpy/pandas/plotting library
- `techniques`: Visualization techniques (twin-axes, colorbar, etc.)
- `patterns`: Code patterns (data-generation, iteration-over-groups, etc.)
- `dataprep`: Data transformations (kde, binning, correlation-matrix, etc.)
- `styling`: Visual style (publication-ready, alpha-blending, etc.)

## Important

- **DO NOT add ai-approved or ai-rejected labels** — the workflow adds them after updating metadata
- This is a **${LIBRARY}-only** review — focus only on this library
- Post feedback to **PR #${PR_NUMBER}**
- Be specific about what failed and how to fix it
- Every weakness line is a defect (`<ID> (<light|dark|both|code>): …`, a violated rule the next generation fixes) or a `Suggestion: …` line (at most three, never acted on) — see 8a. A behavior is never both a strength and a weakness
- Never write a defect that asks to add something the spec does not ask for, and never list something an `Expected, not a defect:` bullet of the spec's "What a good version looks like" section names. Phrase an overlap defect so that its fix is data generation, marker size or alpha — never moving marks off their values
- On a `-basic` spec, never suggest a layer the spec does not ask for, such as a reference line, a highlight or a callout; removing one is the fix
- Mark criteria as N/A when not applicable (e.g., legend for single-series)
- **Score strictly**: median implementation should score 72-78, not 90+
- **Design Excellence defaults are low**: DE-01=4, DE-02=2, DE-03=2 — raise only with evidence
- All review data (strengths, weaknesses, image_description, criteria_checklist) is saved to metadata for future regeneration. Be specific!
