export const meta = {
  name: 'anyplot-audit',
  description: 'Fan out repo auditors, domain-route an adversarial cross-validation of high-severity findings, return structured findings for the Lead to synthesize',
  phases: [
    { title: 'Analyze', detail: 'one agent per active auditor (general-purpose, inherits Opus)' },
    { title: 'Cross-validate', detail: 'domain-routed skeptic verify of every importance>=4 finding' },
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
  required: ['title', 'importance', 'dimension', 'effort', 'autofix', 'files', 'description', 'hint'],
  properties: {
    title: { type: 'string' },
    importance: { type: 'integer', minimum: 1, maximum: 5 },
    dimension: { type: 'string', enum: ['security', 'speed', 'looks', 'modern', 'correctness', 'maintainability'] },
    effort: { type: 'string', enum: ['S', 'M', 'L', 'XL'] },
    autofix: { type: 'string', enum: ['ruff', 'eslint', 'format', 'codemod', 'manual'] },
    files: { type: 'array', items: { type: 'string' } },
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

function fkey(f) {
  return f.title + '::' + ((f.files || []).join(','))
}

function verifyPrompt(finding, auditorName, partnerHint) {
  return [
    `You are a rigorous ${partnerHint} reviewer peer-reviewing a finding raised by the ${auditorName}.`,
    `Bring your own domain expertise and independently check it against the actual repo / live system`,
    `(use Read / Grep / Serena / read-only Bash as needed). Do NOT just re-read the original auditor's reasoning.`,
    ``,
    `FINDING: ${finding.title}`,
    `IMPORTANCE: ${finding.importance}`,
    `DIMENSION: ${finding.dimension}`,
    `FILES: ${(finding.files || []).join(', ') || '(none)'}`,
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

// Cross-validate one auditor's importance>=4 findings, each via a domain-routed skeptic.
async function crossValidate(report, auditor) {
  if (!report) return report
  const partnerHint = PARTNER[auditor.name] || 'independent domain'
  const all = report.findings || []
  const high = all.filter((f) => f.importance >= 4)
  if (!high.length) {
    return { ...report, auditor: auditor.name, crossValidationStats: { reviewed: 0, dropped: 0, downgraded: 0 } }
  }
  const verified = (await parallel(high.map((f) => () =>
    agent(verifyPrompt(f, auditor.name, partnerHint), {
      label: 'verify:' + auditor.name,
      phase: 'Cross-validate',
      schema: VERDICT_SCHEMA,
      agentType: 'general-purpose',
    }).then((v) => ({ ...f, verdict: v }))
      // KEEP-biased: a verifier that errors must not drop the finding. parallel()
      // already maps a rejected thunk to null, but catch explicitly so the intent
      // is unmistakable — an unverified finding falls through to merge and is kept.
      .catch(() => null)
  ))).filter(Boolean)

  const vmap = new Map(verified.map((v) => [fkey(v), v]))
  let dropped = 0
  let downgraded = 0
  const merged = []
  for (const f of all) {
    const v = vmap.get(fkey(f))
    if (!v) { merged.push(f); continue } // importance<4, or its verifier errored -> keep as-is
    const verdict = v.verdict && v.verdict.verdict
    const reason = (v.verdict && v.verdict.reason) || ''
    if (verdict === 'DROP') { dropped++; continue }
    if (verdict === 'DOWNGRADE') {
      downgraded++
      merged.push({ ...f, importance: Math.max(1, f.importance - 1), crossvalidation: 'DOWNGRADE: ' + reason })
      continue
    }
    merged.push({ ...f, crossvalidation: 'KEEP' })
  }
  return { ...report, auditor: auditor.name, findings: merged, crossValidationStats: { reviewed: verified.length, dropped, downgraded } }
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
  (a) => agent(a.prompt, {
    label: a.name,
    phase: 'Analyze',
    schema: REPORT_SCHEMA,
    agentType: a.agentType || 'general-purpose',
  }),
  (report, a) => crossValidate(report, a)
)

const clean = reports.filter(Boolean)
const totalFindings = clean.reduce((n, r) => n + ((r.findings || []).length), 0)
log('Done: ' + clean.length + '/' + auditors.length + ' auditors returned a report; ' + totalFindings + ' findings after cross-validation.')

return { reports: clean, baseline: (ARGS && ARGS.baseline) || null }
