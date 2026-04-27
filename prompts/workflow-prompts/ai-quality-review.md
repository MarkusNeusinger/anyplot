# AI Quality Review

Evaluate if the **${LIBRARY}** implementation matches the specification for `${SPEC_ID}`.

## Context

- **Spec ID:** ${SPEC_ID}
- **Library:** ${LIBRARY}
- **PR Number:** #${PR_NUMBER}
- **Attempt:** ${ATTEMPT}/3

## Your Task

### 1. Read the Specification
`plots/${SPEC_ID}/specification.md`
- Understand what the plot should show
- Note all required features

### 2. Read the Implementation
`plots/${SPEC_ID}/implementations/${LANGUAGE}/${LIBRARY}.py`

### 3. Read Library-Specific Rules
`prompts/library/${LIBRARY}.md`

### 4. Read the Impl-Tags Guide
`prompts/impl-tags-generator.md` (for step 9)

### 5. MANDATORY: View BOTH Generated Plots (Light AND Dark)

You MUST use the Read tool to open **both** `plot_images/plot-light.png` AND `plot_images/plot-dark.png` and visually analyze each image.

- Compare both renders with the spec requirements.
- The Okabe-Ito data colors (positions 1–7) must be **identical** between light and dark — only chrome (background, text, grid, legend frames) flips.
- A review without seeing both images is **invalid**.
- If one or both images cannot be read, STOP and report the error (pipeline failure — flag in `weaknesses`).
- Your review MUST include an "Image Description" section that describes **both** renders, proving you looked at them.

### 5b. Consult the Style Guide for Palette + Theme Rules

Read `prompts/default-style-guide.md` — the "Categorical Palette" (Okabe-Ito), "Continuous Data" (viridis/cividis/BrBG), and "Theme-adaptive Chrome" sections are the authoritative reference for VQ-07 scoring.

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

### 6. Check for Auto-Reject (AR-08)

**For static libraries (matplotlib, seaborn, plotnine) only:**

Before scoring, check if the implementation fakes interactive features:
- Simulated tooltips (annotation boxes styled as hover tooltips)
- Simulated selection/hover states
- Drawn UI controls (buttons, sliders)
- Code comments mentioning "simulating hover/click/interactivity"

If found: Score = 0, verdict = REJECTED, note AR-08 violation.

### 7. Evaluate Using 6-Category Criteria

Read `prompts/quality-criteria.md` and evaluate:

#### Visual Quality (30 pts)
| ID | Criterion | Max | Check |
|----|-----------|-----|-------|
| VQ-01 | Text Legibility | 8 | Font sizes explicitly set? Readable at full size in BOTH themes? |
| VQ-02 | No Overlap | 6 | All text readable? No collisions? |
| VQ-03 | Element Visibility | 6 | Markers/lines adapted to density? |
| VQ-04 | Color Accessibility | 2 | Adequate contrast + CVD-safe (beyond palette)? No red-green as sole signal? |
| VQ-05 | Layout & Canvas | 4 | Good proportions? Nothing cut off? |
| VQ-06 | Axis Labels & Title | 2 | Descriptive with units? |
| VQ-07 | Palette Compliance | 2 | First categorical series = `#009E73`? Multi-series follows Okabe-Ito order? Continuous data uses `viridis`/`cividis`/`BrBG`? Plot backgrounds are `#FAF8F1` (light) / `#1A1A17` (dark)? Both renders theme-correct? |

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
| SC-04 | Title & Legend | 3 | `{spec-id} · {library} · anyplot.ai`? Legend labels match? |

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

### Verdict: APPROVED / REJECTED
```

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

# Criteria checklist as structured JSON
cat > review_checklist.json << 'EOF'
{
  "visual_quality": {
    "score": 36,
    "max": 40,
    "items": [
      {"id": "VQ-01", "name": "Text Legibility", "score": 10, "max": 10, "passed": true, "comment": "All text readable"},
      {"id": "VQ-02", "name": "No Overlap", "score": 8, "max": 8, "passed": true, "comment": "No overlapping elements"}
    ]
  },
  "spec_compliance": {"score": 23, "max": 25, "items": [...]},
  "data_quality": {"score": 18, "max": 20, "items": [...]},
  "code_quality": {"score": 10, "max": 10, "items": [...]},
  "library_features": {"score": 5, "max": 5, "items": [...]}
}
EOF
```

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
