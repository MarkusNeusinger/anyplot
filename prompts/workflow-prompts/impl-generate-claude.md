# Generate Implementation

**YOUR PRIMARY TASK: Create a working plot implementation file.**

You MUST create: `plots/{SPEC_ID}/implementations/{LANGUAGE}/{LIBRARY}.py`

This is NOT optional. The workflow will FAIL if this file does not exist after you finish.

---

**Variables:**
- LANGUAGE: {LANGUAGE}
- LIBRARY: {LIBRARY}
- SPEC_ID: {SPEC_ID}
- Regeneration: {IS_REGENERATION}

## Step 1: Read the rules (quickly)

Read these files to understand the requirements:

1. `prompts/plot-generator.md` - Base generation rules
2. `prompts/default-style-guide.md` - **CRITICAL**: Okabe-Ito palette, continuous-data rules, theme-adaptive chrome tokens. Every new implementation must comply.
3. `prompts/library/{LIBRARY}.md` - Library-specific rules + theme-adaptive chrome mapping for this library
4. `plots/{SPEC_ID}/specification.md` - What to visualize

Optional (if regenerating):
- `plots/{SPEC_ID}/metadata/{LANGUAGE}/{LIBRARY}.yaml` - Previous review feedback
- `plots/{SPEC_ID}/implementations/{LANGUAGE}/{LIBRARY}.py` - Previous implementation

### Feasibility Check (Static Libraries Only)

If LIBRARY is **matplotlib**, **seaborn**, or **plotnine**, AND the specification mentions interactive features (hover, zoom, click, brush, animation, streaming):

1. Is the spec's PRIMARY value its interactivity?
2. If YES → Do NOT generate. Report: `NOT_FEASIBLE: {LIBRARY} cannot provide {required_feature} as static PNG.`
3. If NO (static chart is still valuable) → Generate only the static-achievable features. Do NOT simulate interactive features.

## Step 2: CREATE THE FILE (MANDATORY)

**You MUST use the Write tool to create:**

```
plots/{SPEC_ID}/implementations/{LANGUAGE}/{LIBRARY}.py
```

The script MUST:
- Follow the KISS structure: imports → data → plot → save
- Read `ANYPLOT_THEME` from the environment (`"light"` or `"dark"`, default `"light"`) and render accordingly. The same single script file handles both themes.
- Save output as `plot-{THEME}.png` (theme-suffixed, based on the env var).
- For interactive libraries (plotly, bokeh, altair, highcharts, pygal, letsplot): also save `plot-{THEME}.html`.
- Use `#009E73` (Okabe-Ito position 1) as the **first categorical series**, always. Multi-series follows the canonical order: `#D55E00`, `#0072B2`, `#CC79A7`, `#E69F00`, `#56B4E9`, `#F0E442`.
- For continuous data: `viridis`/`cividis` (sequential) or `BrBG` (diverging). Never `jet`/`hsv`/`rainbow`.
- Plot backgrounds: `#FAF8F1` (light) / `#1A1A17` (dark). Never pure `#FFFFFF` or `#000000`.
- Theme-adaptive chrome (title, axis labels, tick labels, grid, spines, legend frames, annotation boxes) — see `prompts/default-style-guide.md` "Theme-adaptive Chrome" and the library-specific mapping in `prompts/library/{LIBRARY}.md`.

**DO NOT SKIP THIS STEP. The file MUST be created.**

## Step 3: Test and fix (up to 3 attempts)

Run the implementation **twice**, once per theme:
```bash
source .venv/bin/activate
cd plots/{SPEC_ID}/implementations/{LANGUAGE}
MPLBACKEND=Agg ANYPLOT_THEME=light python {LIBRARY}.py
MPLBACKEND=Agg ANYPLOT_THEME=dark  python {LIBRARY}.py
```

Both runs must succeed and produce `plot-light.png` / `plot-dark.png` (plus `plot-light.html` / `plot-dark.html` for interactive libs). If either fails, fix and try again (max 3 attempts).

## Step 4: Visual self-check (BOTH renders)

Look at `plot-light.png` AND `plot-dark.png`:
- Does each match the specification?
- Are axes labeled correctly in both?
- Is the visualization clear on the light surface (`#FAF8F1`) AND the dark surface (`#1A1A17`)?
- Are the data colors **identical** between light and dark (only chrome flipped)?
- Is the first categorical series `#009E73`?

## Step 5: Format the code

```bash
source .venv/bin/activate
ruff format plots/{SPEC_ID}/implementations/{LANGUAGE}/{LIBRARY}.py
ruff check --fix plots/{SPEC_ID}/implementations/{LANGUAGE}/{LIBRARY}.py
```

## Step 6: Verify file exists (CRITICAL)

Before committing, verify the implementation file exists:

```bash
ls -la plots/{SPEC_ID}/implementations/{LANGUAGE}/{LIBRARY}.py
```

**If the file does NOT exist, you MUST go back to Step 2 and create it!**

## Step 7: Commit

```bash
git config user.name "github-actions[bot]"
git config user.email "github-actions[bot]@users.noreply.github.com"
git add plots/{SPEC_ID}/implementations/{LANGUAGE}/{LIBRARY}.py
git commit -m "feat({LIBRARY}): implement {SPEC_ID}"
git push -u origin implementation/{SPEC_ID}/{LIBRARY}
```

## Final Check

Before finishing, confirm:
1. ✅ `plots/{SPEC_ID}/implementations/{LANGUAGE}/{LIBRARY}.py` exists
2. ✅ `plot-light.png` AND `plot-dark.png` were generated successfully (plus `plot-light.html` / `plot-dark.html` for interactive libs)
3. ✅ First categorical series renders in `#009E73` in both themes
4. ✅ Changes were committed and pushed

If any of these failed, DO NOT report success.
