# Cross-library Implementation Similarity Audit

**YOUR TASK: detect when 2+ libraries' implementations have converged on the same data scenario / domain / visual variant beyond what the spec dictated, and emit one-sentence divergence hints for whoever should change.**

This audit runs in the `daily-regen` pre-flight, before regeneration. The hints you produce are passed to the impl-generate jobs as `change_request` inputs. Library independence is a hard catalog rule (see `prompts/plot-generator.md` → "Library Independence"); convergence on dimensions the spec did NOT name is a defect.

The output is a JSON file at `/tmp/change-requests.json`. Empty object means "no clusters detected."

---

**Variables:**
- SPEC_ID: {SPEC_ID}

## Step 1: Read spec context

Read:

1. `plots/{SPEC_ID}/specification.md`
2. `plots/{SPEC_ID}/specification.yaml`

If the spec **explicitly names** a scenario / domain / sample data / shape, all impls sharing it is correct — that's the spec dictating, not the libs copying. **Only flag convergence on dimensions the spec is silent on.**

## Step 2: Read all image descriptions

For each `plots/{SPEC_ID}/metadata/python/*.yaml`:

- Read the `review.image_description` field. The previous review cycle already wrote a plain-English description of the rendered chart there — this is your primary signal.
- The yaml stem is the library name (`bokeh.yaml` → `bokeh`).

If fewer than 2 metadata files exist (or fewer than 2 have an `image_description`): write `{}` to `/tmp/change-requests.json` and stop. Print `SIMILARITY_DONE` and exit. There is nothing to compare.

## Step 3: Cluster

Look for groups of 2+ libraries where the descriptions reveal the same:

- data formula / random seed / sample size
- example domain (web traffic vs stock prices vs weather is a real, distinguishing choice)
- visual variant when the spec listed multiple (e.g. plain line vs filled-area vs min/max-highlighted)
- chrome / annotation choices beyond the mandated Okabe-Ito + theme palette

### What does NOT count as copying — these are project-mandated

- **Okabe-Ito palette positions 1–7.** The data colors are fixed by the style guide; identical colors there are required, not copied.
- **Plot size and aspect ratio.** Fixed by `prompts/default-style-guide.md` and the per-library prompts. Identical aspect ratios across all 9 libs are correct, expected behavior — never propose "different aspect ratios" as divergence advice.
- **Theme chrome.** Page background `#FAF8F1` (light) / `#1A1A17` (dark), text inks, etc. flip identically across libs by design.

If a candidate cluster's identical signal is *only* one of the mandated items above, it is not a cluster. Skip it.

## Step 4: Inspect ambiguous clusters (optional)

If the `image_description` blobs for a candidate cluster don't conclusively show copying — e.g. you can't tell whether two libraries used the same random seed, or whether their domain is genuinely the same — you MAY use the Read tool on `plots/{SPEC_ID}/implementations/python/{library}.py` for **only those libraries inside the candidate cluster** to verify.

**Do not read .py files for libraries that are not in a candidate cluster.** That wastes tokens and is not what this audit is for.

## Step 5: Build the hint per cluster

For each confirmed cluster:

- **Flag exactly ONE library**, not all of them. Pick the alphabetically later library, or the one with the shorter review history. Switching just one breaks the cluster identity cleanly; flagging multiple risks them re-converging on the same new direction.

For the flagged library, write a **one-sentence** `change_request` that:

1. **States concretely what's identical** — name the sibling and the specific shared signal (random seed, sample size, formula structure, example domain, visual variant, annotation choice, etc.). Be specific.
2. **Adds a brief direction hint** with 2–3 alternative examples along the *same* dimension that's currently shared. If the issue is domain, list a couple of different domains. If the issue is the data formula, suggest different shapes (step function, exponential decay, sinusoidal). If the issue is a visual variant, suggest one of the other variants the spec allows.
3. **Stays at ~1 sentence.** Do NOT pitch library-specific features or APIs (the regenerator already reads `prompts/library/{LIBRARY}.md` and chooses idiomatically). Do NOT suggest different aspect ratios or plot sizes — those are project-mandated and identical across libs by design.

Example:

> `"Spec is vague on data; current series matches plotly exactly (same seed, same sine+noise formula). Pick a different example domain (sensor temperatures, population growth, or daily revenue) or change the data shape to a step function."`

## Step 6: Emit the JSON

Write the JSON object to `/tmp/change-requests.json`. **Do not print the JSON to stdout — write it to the file only.**

Shape:

    {}                                                 # no clusters detected
    {"<library-name>": "<one-sentence change_request>", ...}

The keys must be library names that exist as `plots/{SPEC_ID}/metadata/python/<key>.yaml`. The values are single-sentence English strings.

After writing the file, print exactly `SIMILARITY_DONE` to stdout and stop.

## What you must NOT do

- Do not edit any files under `plots/{SPEC_ID}/`. This audit is read-only.
- Do not flag every library in a cluster — exactly one per cluster.
- Do not propose aspect-ratio or plot-size changes — those are mandated.
- Do not pitch library-specific APIs or visual features in the hint.
- Do not write to `/tmp/change-requests.json` if you printed `NOOP` somewhere — the only valid exit paths are: empty `{}` written + `SIMILARITY_DONE`, or populated JSON written + `SIMILARITY_DONE`.
