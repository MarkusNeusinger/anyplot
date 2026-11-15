export const meta = {
  name: 'anyplot-audit',
  description: 'Fan out repo auditors, domain-route an adversarial cross-validation of the high-severity and the publicly visible findings, return structured findings for the Lead to synthesize',
  phases: [
    { title: 'Analyze', detail: 'one agent per active auditor (general-purpose, on the model its roster row names)' },
    { title: 'Cross-validate', detail: 'domain-routed skeptic verify of every importance>=4 finding and every importance>=3 finding a site or repo visitor meets' },
  ],
}

// ---------------------------------------------------------------------------
// This script is GENERIC and args-driven. It never hardcodes the auditor
// roster, so adding/editing an auditor never requires touching this file.
//
// The Lead (which has filesystem access; this script does not) builds:
//   args = {
//     auditors: [{ name: 'security-auditor',
//                  prompt: '<Shared Rules + the auditor .md file contents>',
//                  model?: 'fable',              // from the roster row; omitted, the agent inherits the session's model
//                  agentType?: 'general-purpose' }],
//     partnerMap: { 'backend-auditor': 'security / db / llm-pipeline', ... },  // Phase 2.5 routing hint per auditor
//     baseline?: { ruff: '...', format: '...' }                               // optional context, echoed back
//   }
// The Lead then performs Phase 3 synthesis (Health Score, Dimension Scorecard,
// dedup, persist) on the returned reports — persistence needs Write, which the
// workflow does not do.
// ---------------------------------------------------------------------------

const FINDING_SCHEMA = {
  type: 'object',
  required: ['title', 'importance', 'dimension', 'seen_by', 'effort', 'autofix', 'files', 'evidence', 'description', 'hint'],
  properties: {
    title: { type: 'string' },
    importance: { type: 'integer', minimum: 1, maximum: 5 },
    dimension: { type: 'string', enum: ['security', 'speed', 'looks', 'modern', 'correctness', 'maintainability'] },
    seen_by: { type: 'string', enum: ['site-visitor', 'repo-visitor', 'code-reader', 'internal'] },
    effort: { type: 'string', enum: ['S', 'M', 'L', 'XL'] },
    autofix: { type: 'string', enum: ['ruff', 'eslint', 'format', 'codemod', 'manual'] },
    files: { type: 'array', items: { type: 'string' } },
    evidence: { type: 'string' },
    description: { type: 'string' },
    hint: { type: 'string' },
  },
}

const REPORT_SCHEMA = {
  type: 'object',
  required: ['auditor', 'coverage', 'findings'],
  properties: {
    auditor: { type: 'string' },
    coverage: { type: 'string', enum: ['full', 'partial', 'blocked', 'structural-only', 'filesystem-only'] },
    limitation: { type: 'string' },
    read: { type: 'array', items: { type: 'string' } },
    not_covered: { type: 'array', items: { type: 'string' } },
    findings: { type: 'array', items: FINDING_SCHEMA },
  },
}

const VERDICT_SCHEMA = {
  type: 'object',
  required: ['verdict', 'reason'],
  properties: {
    verdict: { type: 'string', enum: ['KEEP', 'DOWNGRADE', 'DROP'] },
    reason: { type: 'string' },
  },
}

// args normally arrives as a JSON value, but some invocation paths deliver it
// JSON-stringified; normalize once so the rest of the script sees a real object.
const ARGS = (typeof args === 'string') ? (() => { try { return JSON.parse(args) } catch (e) { return {} } })() : (args || {})
let PARTNER = (ARGS && ARGS.partnerMap) || {}

// Severity alone would leave a typo on the landing page unverified while a rare
// race in a script nobody opens gets a skeptic. A finding that a visitor of the
// site or of the repository page meets is checked one importance level earlier.
const PUBLIC_READERS = ['site-visitor', 'repo-visitor']
function needsCrossValidation(f) {
  return f.importance >= 4 || (f.importance >= 3 && PUBLIC_READERS.includes(f.seen_by))
}

function verifyPrompt(finding, auditorName, partnerHint) {
  return [
    `You are a rigorous ${partnerHint} reviewer peer-reviewing a finding raised by the ${auditorName}.`,
    `Bring your own domain expertise and independently check it against the actual repo / live system`,
    `(use Read / Grep / read-only Bash as needed). Do NOT just re-read the original auditor's reasoning.`,
    ``,
    `FINDING: ${finding.title}`,
    `IMPORTANCE: ${finding.importance}`,
    `DIMENSION: ${finding.dimension}`,
    `SEEN_BY: ${finding.seen_by}`,
    `FILES: ${(finding.files || []).join(', ') || '(none)'}`,
    `EVIDENCE: ${finding.evidence || '(none given)'}`,
    `DESCRIPTION: ${finding.description}`,
    ``,
    `This is a specialist peer-review: the BURDEN OF PROOF IS ON DROP. Decide exactly one verdict:`,
    `- KEEP      — real and correctly rated. ALSO keep when you cannot disprove it within your budget;`,
    `              do NOT drop a finding merely because you ran low on tool calls or couldn't fully re-derive it.`,
    `- DOWNGRADE — clearly real but over-rated (the Lead drops it one importance level).`,
    `- DROP      — ONLY with positive primary evidence that it is a false positive (e.g. the code/system`,
    `              actually does the opposite of what the finding claims, or the cited file/line says otherwise).`,
    `              Cite that concrete evidence in your reason.`,
    `Give a one-sentence reason.`,
  ].join('\n')
}

// An agent started without a model inherits the session's, so the roster's choice is passed on when it names one.
function agentOptions(auditor, opts) {
  return auditor.model ? { ...opts, model: auditor.model } : opts
}

// Cross-validate the findings of one auditor that needsCrossValidation selects, each via a domain-routed
// skeptic on the auditor's own model: the skeptic of a high-risk finding is no weaker than its finder.
async function crossValidate(report, auditor) {
  if (!report) return report
  const partnerHint = PARTNER[auditor.name] || 'independent domain'
  const all = report.findings || []
  // A finding is known by its position: two findings of one auditor may share a title and their files.
  const selected = all.map((f, index) => ({ f, index })).filter(({ f }) => needsCrossValidation(f))
  const verdicts = new Map((await parallel(selected.map(({ f, index }) => () =>
    agent(verifyPrompt(f, auditor.name, partnerHint), agentOptions(auditor, {
      label: 'verify:' + auditor.name,
      phase: 'Cross-validate',
      schema: VERDICT_SCHEMA,
      agentType: 'general-purpose',
    })).then((v) => (v ? [index, v] : null))
      // KEEP-biased: a verifier that errors must not drop the finding. parallel()
      // already maps a rejected thunk to null, but catch explicitly so the intent
      // is unmistakable — an unverified finding falls through to merge and is kept.
      .catch(() => null)
  ))).filter(Boolean))

  let dropped = 0
  let downgraded = 0
  const merged = []
  all.forEach((f, index) => {
    const v = verdicts.get(index)
    if (!v) { merged.push(f); return } // not selected for a skeptic, or its verifier errored -> keep as-is
    const reason = v.reason || ''
    if (v.verdict === 'DROP') { dropped++; return }
    if (v.verdict === 'DOWNGRADE') {
      downgraded++
      merged.push({ ...f, importance: Math.max(1, f.importance - 1), crossvalidation: 'DOWNGRADE: ' + reason })
      return
    }
    merged.push({ ...f, crossvalidation: 'KEEP' })
  })
  // Left without a verdict: below the bar, or its verifier failed. Positive patterns (importance 1) need none.
  const unverified = all.filter((f) => f.importance >= 2).length - verdicts.size
  return { ...report, auditor: auditor.name, findings: merged, crossValidationStats: { reviewed: verdicts.size, dropped, downgraded, unverified } }
}

// --- main ------------------------------------------------------------------
const auditors = (ARGS && ARGS.auditors) || []
if (!auditors.length) {
  log('No auditors supplied in args.auditors — nothing to run.')
  return { reports: [], baseline: (ARGS && ARGS.baseline) || null }
}
log('Auditing with ' + auditors.length + ' auditor(s): ' + auditors.map((a) => a.name).join(', '))

// Each item flows Analyze -> Cross-validate independently (no barrier): a fast
// auditor's findings get verified while a slow auditor is still analyzing.
const reports = await pipeline(
  auditors,
  (a) => agent(a.prompt, agentOptions(a, {
    label: a.name,
    phase: 'Analyze',
    schema: REPORT_SCHEMA,
    agentType: a.agentType || 'general-purpose',
  })),
  (report, a) => crossValidate(report, a)
)

const clean = reports.filter(Boolean)
const totalFindings = clean.reduce((n, r) => n + ((r.findings || []).length), 0)
log('Done: ' + clean.length + '/' + auditors.length + ' auditors returned a report; ' + totalFindings + ' findings after cross-validation.')

return { reports: clean, baseline: (ARGS && ARGS.baseline) || null }
