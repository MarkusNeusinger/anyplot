# AI Quality Review

Evaluate if the **${LIBRARY}** implementation matches the specification for `${SPEC_ID}`.

## Context

- **Spec ID:** ${SPEC_ID}
- **Library:** ${LIBRARY}
- **PR Number:** #${PR_NUMBER}
- **Attempt:** ${ATTEMPT}/3
- **Regeneration:** ${IS_REGENERATION} (when `true`, step 5f applies: one review, no repair)

## Your Task

### 1. Read the Specification
`plots/${SPEC_ID}/specification.md`
- Understand what the plot should show
- Note all required features

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
- **Flag the specific elements in `weaknesses`** so the repair loop knows exactly what to fix. Example: "Dark render has black tick labels on near-black background — ax.tick_params colors not set from INK_SOFT token."

A plot that's perfect in one theme but unreadable in the other still **fails** — both renders must pass. Be strict: a plot that ships to the website broken on dark mode is worse than one that fails review and gets repaired.

### 5c2. MANDATORY: Canvas dimension gate (if present)

The workflow's pre-check step (`impl-review.yml` → "Canvas dimension gate") measures the saved `plot-light.png` against the two canonical canvas sizes (3200×1800 landscape, 2400×2400 square, ±16 px tolerance). When the gate fails, it writes the synthetic weakness to `/tmp/anyplot-canvas-gate.txt`.

**Before scoring, check whether `/tmp/anyplot-canvas-gate.txt` exists:**

```bash
ls -la /tmp/anyplot-canvas-gate.txt 2>/dev/null && cat /tmp/anyplot-canvas-gate.txt
```

If it **does** exist:
- The file contains a single paragraph: `Canvas dimensions drifted from required target. Actual: WxH. Closest valid target: TWxTH (±16 px tolerance). Signed delta: ±dx × ±dy — direction. Most likely cause: …`
- **Copy that paragraph verbatim into your `weaknesses` array as the FIRST item.** Do not paraphrase; the repair model needs the literal "actual=WxH" and signed delta numbers to know which knob to turn and which direction.
- **Set VQ-05 (Layout & Canvas) to 0/4 regardless of other observations.** Canvas drift is a hard rule; the quality_score must drop low enough to route the PR into impl-repair through the existing 5-review/4-repair cascade.
- Keep scoring the other categories honestly — useful signal for repair is good signal — but do **not** lift VQ-05 just because the visual proportions look fine inside the wrong-sized canvas.
- On a regeneration (`IS_REGENERATION` is `true`) there is no repair: the regen gate reads the same file and keeps the live implementation. Still do step 5f — the comparison is recorded for the next attempt.

If it does **not** exist: the gate passed; no canvas-specific action — score VQ-05 normally based on the visual proportional checks in 5d below.

### 5d. MANDATORY: Proportional Sizing Check (both renders)

Visually estimate from each PNG — no pixel measurement needed. These are soft proportional checks **without hard thresholds**. Violations cost points in the existing VQ-01 (Text Legibility), VQ-02 (No Overlap), and VQ-05 (Layout & Canvas) categories rather than triggering a separate pass/fail item. A single visual problem can reduce points in multiple categories simultaneously (holistic, not strict).

- **Title proportion:** Title comfortably occupies ~50–70% of the plot width. **Note:** the mandated `{spec-id} · {lang} · {lib} · anyplot.ai` title is ~67 chars; at the style-guide default fontsize it naturally fills ~70–85% on landscape. That is **expected and not a deduction** — the AI made the right tradeoff. Only deduct if either: (a) the title overflows beyond ~90% of plot width / clips edges, or (b) the fontsize is too generous for the title length (squeezed look, no breathing room) → VQ-01 + VQ-05.
- **Axis label proportionality:** Short labels with few words ("Date", "Year") must not dominate the axis with oversized fontsizes. Long descriptive labels ("Fläche von Häusern in Quadratmetern", "Average temperature in °C") are completely fine as long as they don't overflow — the "No overflow" check below covers that. Disproportionately oversized short labels → deduct VQ-05.
- **Axis label balance:** X-axis and Y-axis labels are visually similar in size. One much larger than the other without semantic reason → deduct VQ-05.
- **Tick label balance:** X-axis and Y-axis tick labels are visually similar in size. Exception: rotated long categorical labels may legitimately look wider.
- **No overlap:** No text overlaps with other text, with data elements, or with legend/annotation boxes → deduct VQ-02 (severe overlap = 0).
- **No overflow:** No text extends beyond axis bounds, plot bounds, or the canvas frame → deduct VQ-05.
- **Marker / line density appropriateness:** Sparse data (< 50 points) should have prominent markers; dense data (> 500 points) should have smaller markers + `alpha < 1` to combat overplotting → deduct VQ-03 when poorly chosen.

**Required:** Note specific violations in `weaknesses` with enough context for the repair loop to fix them. Examples:
- "X-axis label 'Date' is oversized at fontsize=18pt, dominates the axis disproportional to its info content — reduce to ~10pt."
- "Title overflows beyond plot edge (~95% width) — reduce title fontsize from 18pt to 12pt."
- "Sparse scatter (32 points) but marker size=4 px makes them barely visible — increase to size=10-14."

**Counter-examples (NOT deductions):**
- "Title spans ~80% of width at fontsize=14pt." → Expected for the long mandated anyplot title; no deduction.
- "Y-axis label 'Fläche von Häusern in Quadratmetern' takes ~40% of axis length at fontsize=12pt." → Genuinely long label at sensible fontsize; no deduction as long as it doesn't overflow the axis.

### 5e. Interactive & JavaScript Libraries — Fairness Rules

**Interactive libraries** (produce `plot-{theme}.html` alongside the PNG): altair, bokeh, chartjs, d3, echarts, highcharts, letsplot, muix, plotly, pygal.

- **DO NOT penalize** interactive features that aren't visible in the PNG — tooltips/hover info, zoom/pan/selection tools, interactive legends, crossfiltering. The PNG is a static preview; these features add real value in the HTML detail view. Treat well-configured interactivity as a strength (e.g. "Uses HoverTool for detailed data inspection in HTML output").
- **Only criticize** interactivity when it hurts the static render: hover-only labels that leave the PNG unreadable, misconfigured features, or errors.

**JavaScript libraries** (chartjs, d3, echarts, highcharts as `.js`; muix as `.tsx`): the snippet renders into the browser harness's pre-sized `#container` mount node and never saves files itself — the harness (`automation/js-render/render.mjs`) captures `plot-{theme}.png` and `plot-{theme}.html`. For CQ-05, check the mount-node contract and current library API instead of `savefig`-style calls; animations must be disabled (`animation: false` or the library's equivalent) so the harness doesn't screenshot mid-animation.

### 5f. Regeneration: before/after (only when `IS_REGENERATION` is `true`)

Skip this section entirely when `IS_REGENERATION` is `false`.

A regeneration replaces an implementation that is already live on main. It gets exactly **one** review — this one — and no repair loop. The workflow's regen gate (`automation/scripts/regen_gate.py`) reads your `review_regen.json` and replaces the live implementation only if **all** of these hold; otherwise the PR is closed and the live implementation stays:

- your score for the new render ≥ your re-score of the predecessor − 1;
- at least one improvement a viewer can see (non-empty `where_visible`);
- no regressions (on a `*-basic` spec, a replaced data scenario or added encodings count as regressions unless a change request asked for them).

Your job is an honest comparison; the gate does the arithmetic. Workflow variables for this step: `PREVIOUS_SCORE` (the stored score — display only), `PREV_RENDERS` (`available` / `missing`), `PREV_LINES` and `NEW_LINES` (line counts of the previous and the new source).

**Blind first, then compare — in this order:**

1. **Score the new render blind.** Finish steps 6–8 for the new implementation exactly as in any review, **without** opening `prev_images/`, `/tmp/anyplot-prev-review.md` or the previous source. Your score for the new render is final at that point; do not revise it after seeing the predecessor.
2. **Re-score the predecessor.** If `PREV_RENDERS` is `missing`, skip steps 2–5, do not write `review_regen.json`, and say so in the comment (the gate keeps the live implementation). Otherwise open `prev_images/plot-light.png` and `prev_images/plot-dark.png` (the production renders currently on the website) and `/tmp/anyplot-prev-impl${EXT}` (their source), and score them against the **same** criteria — steps 5c–8, same score caps, same calibration. The result is `prev_rescored`. Score what you see: do not anchor on `PREVIOUS_SCORE` or on the previous review's numbers. Number the predecessor's weaknesses you find `P1`, `P2`, ….
3. **Read the previous review** `/tmp/anyplot-prev-review.md`. Its weaknesses carry stable ids `W1`..`Wn`. When it has a "Characteristic properties" list (`C1`..`Cn`, taken from the spec's "What a good version looks like" section), those are the properties a good version of this plot type must show. When the list is absent, there are no `C` ids — never invent one.
4. **Judge the pair side by side** (light against light, dark against dark):
   - **Improvement** — something a viewer can see in the new renders that is better than in the predecessor. `ref` is the `W` id it resolves, a `P` id, a `C` id it now satisfies, or `"new"`. `where_visible` names the element and the render(s), for example "size legend, both renders: the circles are now visible on the dark background". Code-only changes (refactors, comments, extra code without a visible effect) are **not** improvements. If you cannot point to it in a render, leave `where_visible` empty — it then does not count.
   - **Regression** — anything that was good in the predecessor and is worse now: a lost or unreadable legend, illegible or overlapping text, clipping, a worse layout, a characteristic property lost, or data marks that no longer sit at their data values (jitter, force or declutter passes that move the marks).
   - `scenario_changed` — `true` when the data story (domain, variables, labels) was replaced rather than refined.
   - `encodings_added` — visual encodings the new version maps that the predecessor did not (for example `"color by region"`, `"trend line"`, `"facets"`); empty list when none.
   - `change_request_applied` — when `/tmp/anyplot-change-request.txt` exists, `true` if the new version applies that request, `false` if not; `null` when the file does not exist.
   - Code size: `PREV_LINES` → `NEW_LINES`. A large growth without a visible change is a CQ-04 note for the comparison section and `weaknesses` (so the next regeneration sees it). It is not a regression and not a gate condition.
5. **Write `review_regen.json`** (repository root, next to the other review files):

```json
{
  "prev_rescored": 84,
  "improvements": [
    {"ref": "W2", "what": "Size legend circles are filled like the data marks", "where_visible": "size legend, both renders"}
  ],
  "regressions": [],
  "scenario_changed": false,
  "encodings_added": [],
  "change_request_applied": null
}
```

`regressions` entries use `{"what": "...", "where_visible": "..."}`. Every `W` ref must be an id from `/tmp/anyplot-prev-review.md`, and every `C` ref an id from its characteristic list — an unknown id makes the whole file invalid and the gate keeps the live implementation. Report regressions even when you also found improvements; the gate needs both.

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
| VQ-02 | No Overlap | 6 | All text readable? No collisions with other text or with data? See 5d. |
| VQ-03 | Element Visibility | 6 | Markers/lines adapted to density? See 5d data-density appropriateness. |
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
| SC-01 | Plot Type | 5 | Correct chart type? |
| SC-02 | Required Features | 4 | All features from spec? |
| SC-03 | Data Mapping | 3 | X/Y correct? Axes show all data? |
| SC-04 | Title & Legend | 3 | Title is `{spec-id} · {language} · {library} · anyplot.ai`, optionally prefixed with `{Descriptive Title} · ` (language ∈ {python, r, julia, javascript}). Legend labels match? |

#### Data Quality (15 pts)
| ID | Criterion | Max | Check |
|----|-----------|-----|-------|
| DQ-01 | Feature Coverage | 6 | Shows ALL aspects of plot type? |
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
- Strength 1 (keep these aspects)
- Strength 2

### Weaknesses
- Weakness 1 (AI will fix these - let it decide HOW)

### Issues Found
1. **DE-01 LOW**: Generic styling with default colors and no design thought
   - Fix: Custom palette, remove top/right spines, refine typography
2. **DE-03 LOW**: No visual hierarchy or data storytelling
   - Fix: Use color contrast, size variation, or strategic data choice to create a clear focal point

### AI Feedback for Next Attempt
> Improve design excellence: remove top/right spines, use subtle y-axis-only grid, create visual hierarchy through color contrast or emphasis. Consider a more refined color palette.

### Regeneration comparison
<!-- Only when IS_REGENERATION is true (step 5f); omit the whole section otherwise. -->
| Predecessor (stored) | Predecessor (re-scored) | New |
|---|---|---|
| ${PREVIOUS_SCORE} | XX | XX |

**Predecessor weaknesses found while re-scoring:** P1 …, P2 …
**Improvements:** `W2` size legend circles now visible — size legend, both renders
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

# Structured feedback as JSON arrays
echo '["Strength 1", "Strength 2"]' > review_strengths.json
echo '["Weakness 1"]' > review_weaknesses.json

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
# the before/after judgement from step 5f. Missing or malformed = the regen
# gate keeps the live implementation.
cat > review_regen.json << 'EOF'
{"prev_rescored": 84, "improvements": [{"ref": "W2", "what": "...", "where_visible": "..."}], "regressions": [], "scenario_changed": false, "encodings_added": [], "change_request_applied": null}
EOF
```

All scores and review files above (`quality_score.txt`, `review_checklist.json`, …) describe the **new** implementation. The predecessor's re-score goes only into `review_regen.json`.

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
- Mark criteria as N/A when not applicable (e.g., legend for single-series)
- **Score strictly**: median implementation should score 72-78, not 90+
- **Design Excellence defaults are low**: DE-01=4, DE-02=2, DE-03=2 — raise only with evidence
- All review data (strengths, weaknesses, image_description, criteria_checklist) is saved to metadata for future regeneration. Be specific!
