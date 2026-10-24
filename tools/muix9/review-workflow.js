export const meta = {
  name: 'review-gemini-12296-c1b',
  description: 'Independent review of the 88 remaining chunk-1 MUI X 9 migrations on gemini/12296-muix-9-remaining (2db702da7) against the issue checklist, then adversarial verification of high/medium findings',
  phases: [
    { title: 'Review', detail: 'eleven Opus reviewers, eight specs each, checklist + diff only' },
    { title: 'Verify', detail: 'one Opus refuter per high/medium finding, capped' },
  ],
}

const S = '/tmp/claude-1000/-home-meake-projects-anyplot/cd03bb60-b280-4230-bfe2-83fcd57e888f/scratchpad/gemini-muix/c1b/review'
const W = '/home/meake/projects/anyplot/.claude/worktrees/gemini-12296'
const SPECS = args.specs
const GROUPS = []
for (let i = 0; i < SPECS.length; i += 8) GROUPS.push(SPECS.slice(i, i + 8))

const FINDINGS = {
  type: 'object',
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          spec: { type: 'string' },
          severity: { type: 'string', enum: ['high', 'medium', 'low'] },
          checklist_item: { type: 'string' },
          title: { type: 'string' },
          evidence: { type: 'string', description: 'path:line plus the exact code' },
          why: { type: 'string' },
          fix: { type: 'string' },
        },
        required: ['spec', 'severity', 'checklist_item', 'title', 'evidence', 'why', 'fix'],
      },
    },
    clean_specs: { type: 'array', items: { type: 'string' } },
    systematic: { type: 'string', description: 'a pattern that repeats across the files, or "none"' },
  },
  required: ['findings', 'clean_specs', 'systematic'],
}

const VERDICT = {
  type: 'object',
  properties: {
    refuted: { type: 'boolean' },
    reason: { type: 'string' },
    severity: { type: 'string', enum: ['high', 'medium', 'low'] },
  },
  required: ['refuted', 'reason', 'severity'],
}

const reviewPrompt = (specs) => `You review a code change independently. You get the acceptance rules and the diff. Report defects only; no praise.

Inputs:
- The rules (the Constraints and Acceptance sections of the task brief, with a 16-item checklist and a "Design level" paragraph): read ${S}/acceptance.md first.
- Diffs (origin/main -> branch), one per spec: ${specs.map(s => `${S}/${s}.diff`).join(', ')}.
- The full post-change files: ${W}/plots/<spec>/implementations/javascript/muix.tsx. Read each one in full; a diff alone hides what the plot code still types.
- The specification of each spec: ${W}/plots/<spec>/specification.md (needed for the "-basic" variant rule, the Data roles that decide the data shape, and whether an element the old file drew is spec-required).
- The rule files the brief cites: ${W}/prompts/library/muix.md, ${W}/prompts/adaptable-code.md, ${W}/prompts/quality-criteria.md (SC-01 "Variant creep", VQ-01, VQ-07, CQ-01, CQ-04, DQ-02, DQ-03).

Rules: read only. No edits, no git, no npm, no node; a separate process renders the files. Read nothing outside the paths above.

For each of the eight specs, check every checklist item 1 to 16 and the Design-level paragraph, and the header rule (one header block of four lines on top; a square spec has the directive on line 5; no stale second header). Also check scenario drift (chart type, story, data kept) and v9 API misuse that would render blank or wrong. Known patterns from the first ten files of this chunk, check them explicitly: a subtitle built by string-munging column constants (.toLowerCase(), appended plural "s", units nested in parentheses) that states a wrong fact; guards and fallbacks that cannot fire (?? 0, Math.max(1, …) on counts, || after a findIndex that always hits); a sample's scale maximum typed as an axis floor; a marker line or callout added on a -basic spec; fixed px margins while a count-driven layout grows; whiskers or marks clamped instead of extending the axis; label text in t.amber on the light page; a hand-built legend swatch that does not match the mark.

Severity: high = would fail to render, render blank or wrong, or a violation the pipeline's Opus review marks as a defect line (text under 14 px, helper functions or components outside the default export, a truncated label, marks moved off their data, chrome in a palette colour, variant creep on a -basic spec, a dropped spec-required element, a label that misstates the data); medium = convention violation the brief requires (typed limits, modulo palette, nested cells, labels by Set position, unused column constants, scale max as floor); low = cosmetic. Cite path:line for everything. Under "systematic", name any pattern that repeats across your eight files. If a spec has no defects, list it under clean_specs.`

phase('Review')
const reviews = await parallel(GROUPS.map((specs, i) => () =>
  agent(reviewPrompt(specs), { label: `review:g${i + 1}`, phase: 'Review', model: 'opus', schema: FINDINGS })))
const all = reviews.filter(Boolean).flatMap(r => r.findings)
const clean = reviews.filter(Boolean).flatMap(r => r.clean_specs)
const systematic = reviews.filter(Boolean).map(r => r.systematic).filter(s => s && s !== 'none')
log(`review: ${all.length} findings (${all.filter(f => f.severity === 'high').length} high, ${all.filter(f => f.severity === 'medium').length} medium, ${all.filter(f => f.severity === 'low').length} low), clean: ${clean.length}`)

phase('Verify')
const highs = all.filter(f => f.severity === 'high')
const meds = all.filter(f => f.severity === 'medium')
const toVerify = highs.concat(meds).slice(0, 24)
const dropped = highs.length + meds.length - toVerify.length
if (dropped > 0) log(`verify: capped at 24, ${dropped} medium findings left unverified`)
const verified = await parallel(toVerify.map(f => () =>
  agent(`Try to refute this review finding about a MUI X 9 migration. Default to refuted=true when the evidence does not hold up on inspection.

Finding (spec ${f.spec}, claimed severity ${f.severity}, rule ${f.checklist_item}): ${f.title}
Evidence: ${f.evidence}
Why: ${f.why}
Proposed fix: ${f.fix}

Check it against the actual file ${W}/plots/${f.spec}/implementations/javascript/muix.tsx, the diff ${S}/${f.spec}.diff, the spec ${W}/plots/${f.spec}/specification.md, the rules ${S}/acceptance.md, and ${W}/prompts/quality-criteria.md / ${W}/prompts/adaptable-code.md / ${W}/prompts/library/muix.md where the rule comes from. Read only: no edits, no git, no npm, no node. Is the claim true as stated, and does it matter at the claimed severity (high = the pipeline's review would write a defect line or the render is wrong)? If true but over-rated, set refuted=false and give the right severity. State the line numbers you checked.`,
    { label: `verify:${f.spec}`, phase: 'Verify', model: 'opus', schema: VERDICT })
    .then(v => ({ ...f, verdict: v }))))
const confirmed = verified.filter(Boolean).filter(f => f.verdict && !f.verdict.refuted).map(f => ({ ...f, severity: f.verdict.severity }))
const refuted = verified.filter(Boolean).filter(f => f.verdict && f.verdict.refuted)
const unverified = highs.concat(meds).slice(24)
return { confirmed, refuted, unverified_medium: unverified, low_unverified: all.filter(f => f.severity === 'low'), clean_specs: clean, systematic, totals: { findings: all.length, confirmed: confirmed.length, refuted: refuted.length, unverified: unverified.length } }