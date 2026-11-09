/**
 * The case detail's turn matrix as pure functions: how bad each entry of a
 * turn's record is, the chips its row shows, and the worst entry of a turn,
 * so the row flags a refusal, a refused call, a cap or a failed render at a
 * glance. The codes are the agents service's closed sets
 * (`agents/anyplot/turn_record.py`), which the API closes again.
 */

import type { AgentCaseToolCall, AgentCaseTurn, AgentCaseTurns } from 'src/lib/agent';

/** `ok` went as planned, `warn` a refusal, a cap or a check that changed the reply, `bad` a failure. */
export type Severity = 'ok' | 'warn' | 'bad';

const RANK: Record<Severity, number> = { ok: 0, warn: 1, bad: 2 };

/** The verdicts of a guard that say nothing happened: left out of the row, listed in the details. */
const QUIET_VERDICTS: Record<string, readonly string[]> = {
  scope_guard: [
    'in_scope',
    'served_library_in_scope',
    'paste_note_in_scope',
    'language_offer',
    'language_detected',
  ],
  reply_language: ['not_offered'],
  plot_button: ['asked'],
  budget_exempt: ['exempt'],
  queue: ['started'],
};

/** A check that could not do its job, or a turn that lost its reply. */
const BAD_VERDICTS = new Set(['guard_unavailable', 'no_reply', 'reask_failed', 'error']);

export function guardSeverity(guard: string, verdict: string): Severity {
  if (QUIET_VERDICTS[guard]?.includes(verdict)) return 'ok';
  return BAD_VERDICTS.has(verdict) ? 'bad' : 'warn';
}

/**
 * A plot run that failed and a guard or tool that broke are failures; an
 * error answer the root can act on (`invalid_operations`) and a refusal are
 * flags.
 */
export function callSeverity(call: AgentCaseToolCall): Severity {
  if (call.outcome === 'failed' || call.verdict === 'internal' || call.code === 'internal') {
    return 'bad';
  }
  if (call.verdict !== 'allowed') return 'warn';
  return ['error', 'not_ready', 'unconfirmed', 'unfinished'].includes(call.outcome) ? 'warn' : 'ok';
}

/** How the turn itself ended: an error is a failure, except the client's own cancel. */
export function endSeverity(turn: AgentCaseTurn): Severity {
  if (turn.error === 'cancelled') return 'warn';
  if (turn.error !== null || turn.kind === 'error') return 'bad';
  return turn.refusal !== null || turn.kind === 'refused' || turn.kind === 'other' ? 'warn' : 'ok';
}

export function turnSeverity(turn: AgentCaseTurn): Severity {
  return [
    endSeverity(turn),
    ...turn.tools.map(callSeverity),
    ...turn.guards.map(line => guardSeverity(line.guard, line.verdict)),
  ].reduce<Severity>((worst, level) => (RANK[level] > RANK[worst] ? level : worst), 'ok');
}

/** One chip of a turn's row; `count` folds identical neighbours (`get_dataset_profile ×2`). */
export interface TurnChip {
  label: string;
  severity: Severity;
  count: number;
}

/** A tool call as text: `prepare_data: error · invalid_operations`, `plot_pipeline refused: plot_as_confirmed`. */
export function callLabel(call: AgentCaseToolCall): string {
  if (call.verdict !== 'allowed') return `${call.tool} refused: ${call.verdict}`;
  const outcome = call.outcome === 'ok' ? '' : `: ${call.outcome}`;
  return `${call.tool}${outcome}${call.code ? ` · ${call.code}` : ''}`;
}

function folded(items: { label: string; severity: Severity }[]): TurnChip[] {
  const chips: TurnChip[] = [];
  for (const item of items) {
    const last = chips[chips.length - 1];
    if (last && last.label === item.label) last.count += 1;
    else chips.push({ ...item, count: 1 });
  }
  return chips;
}

/**
 * The row's chips: the turn's refusal or error unless a guard's chip already
 * names it (`scope_guard: out_of_scope`), the guards that fired, every tool call.
 */
export function turnChips(turn: AgentCaseTurn): TurnChip[] {
  const end = turn.refusal ?? turn.error;
  const named = turn.guards.some(line => line.verdict === end);
  return folded([
    ...(end && !named
      ? [{ label: `${turn.refusal ? 'refusal' : 'error'}: ${end}`, severity: endSeverity(turn) }]
      : []),
    ...turn.guards
      .map(line => ({
        label: `${line.guard}: ${line.verdict}`,
        severity: guardSeverity(line.guard, line.verdict),
      }))
      .filter(chip => chip.severity !== 'ok'),
    ...turn.tools.map(call => ({ label: callLabel(call), severity: callSeverity(call) })),
  ]);
}

/** `message` for a typed message, else the page's action. */
export function actionLabel(action: string): string {
  return action === 'text' ? 'message' : action;
}

/** How a turn went, as the details' first line: `message → refused (rate_limited)`. */
export function endLine(turn: AgentCaseTurn): string {
  const codes = [turn.refusal, turn.error].filter(Boolean).join(', ');
  return `${actionLabel(turn.action)} → ${turn.kind}${codes ? ` (${codes})` : ''}`;
}

/** The matrix's headline: how many turns, how many failed or flagged, and the older ones the record dropped. */
export function turnsSummary(turns: AgentCaseTurns): string {
  const levels = turns.records.map(turnSeverity);
  const count = (level: Severity) => levels.filter(item => item === level).length;
  const n = turns.records.length;
  return [
    `${n} ${n === 1 ? 'turn' : 'turns'}`,
    count('bad') ? `${count('bad')} failed` : null,
    count('warn') ? `${count('warn')} flagged` : null,
    turns.dropped ? `${turns.dropped} older not kept` : null,
  ]
    .filter((part): part is string => !!part)
    .join(' · ');
}

/** The turn numbers two records share: a turn refused before the scope judge takes the next turn's number. */
export function sharedTurns(turns: AgentCaseTurns): Set<number> {
  const seen = new Set<number>();
  const shared = new Set<number>();
  for (const record of turns.records) {
    if (seen.has(record.turn)) shared.add(record.turn);
    seen.add(record.turn);
  }
  return shared;
}
